from flask import Flask, request, Response
import requests
from urllib.parse import urlparse, urljoin, quote, unquote
import re
import traceback
import json

app = Flask(__name__)

# --- Yardımcı Fonksiyonlar ---
def detect_m3u_type(content):
    if "#EXTM3U" in content and "#EXTINF" in content:
        return "m3u8"
    return "m3u"

def replace_key_uri(line, headers_query):
    match = re.search(r'URI="([^"]+)"', line)
    if match:
        key_url = match.group(1)
        proxied_key_url = f"/proxy/key?url={quote(key_url)}&{headers_query}"
        return line.replace(key_url, proxied_key_url)
    return line

# --- Vavoo M3U8 çözümleme ---
def resolve_vavoo_m3u8(url, headers):
    try:
        session = requests.Session()
        res = session.get(url, headers=headers, timeout=(10,15))
        res.raise_for_status()
        text = res.text

        # iframe src bul
        iframe_match = re.search(r'<iframe src="([^"]+)"', text)
        if not iframe_match:
            # fallback: direkt M3U8
            if text.strip().startswith("#EXTM3U"):
                return text, headers
            else:
                return None, headers

        iframe_url = iframe_match.group(1)
        # iframe isteği
        iframe_res = session.get(iframe_url, headers=headers, timeout=(10,15))
        iframe_res.raise_for_status()
        iframe_text = iframe_res.text

        # Dynamic token parametreleri
        token_match = re.search(r'channelKey\s*=\s*"([^"]+)"', iframe_text)
        auth_ts_match = re.search(r'authTs\s*=\s*"([^"]+)"', iframe_text)
        auth_rnd_match = re.search(r'authRnd\s*=\s*"([^"]+)"', iframe_text)
        auth_sig_match = re.search(r'authSig\s*=\s*"([^"]+)"', iframe_text)
        server_match = re.search(r'n fetchWithRetry\(\s*\'([^\']+)\'', iframe_text)

        if not all([token_match, auth_ts_match, auth_rnd_match, auth_sig_match, server_match]):
            return None, headers

        channel_key = token_match.group(1)
        auth_ts = auth_ts_match.group(1)
        auth_rnd = auth_rnd_match.group(1)
        auth_sig = quote(auth_sig_match.group(1))
        server_lookup = server_match.group(1)

        # server lookup isteği
        server_url = f"https://{urlparse(iframe_url).netloc}{server_lookup}{channel_key}"
        server_res = session.get(server_url, headers=headers, timeout=(10,15))
        server_res.raise_for_status()
        server_key = server_res.json().get("server_key")
        if not server_key:
            return None, headers

        # m3u8 final URL
        host_match = re.search(r'm3u8\s*=.*?"([^"]+)"', iframe_text)
        if not host_match:
            return None, headers
        host = host_match.group(1)
        final_url = f"https://{server_key}{host}{server_key}/{channel_key}/mono.m3u8"

        return final_url, headers
    except Exception as e:
        traceback.print_exc()
        return None, headers

# --- Proxy M3U ---
@app.route('/proxy/m3u')
def proxy_m3u():
    m3u_url = request.args.get('url', '').strip()
    if not m3u_url:
        return "Hata: 'url' parametresi eksik", 400

    # Headers
    request_headers = {
        unquote(k[2:]).replace("_", "-"): unquote(v).strip()
        for k,v in request.args.items() if k.lower().startswith("h_")
    }

    headers = {
        "User-Agent": request_headers.get("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"),
        "Referer": request_headers.get("Referer", "https://vavoo.to/"),
        "Origin": request_headers.get("Origin", "https://vavoo.to")
    }

    try:
        # Vavoo çözümleme
        resolved_url, headers_for_proxy = resolve_vavoo_m3u8(m3u_url, headers)
        if not resolved_url:
            return "Vavoo M3U8 çözümü başarısız", 500

        res = requests.get(resolved_url, headers=headers_for_proxy, timeout=(10,20))
        res.raise_for_status()
        content = res.text
        file_type = detect_m3u_type(content)

        if file_type == "m3u":
            return Response(content, content_type="application/vnd.apple.mpegurl")

        parsed = urlparse(resolved_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/',1)[0]}/"
        headers_query = "&".join([f"h_{quote(k)}={quote(v)}" for k,v in headers_for_proxy.items()])

        modified_lines = []
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("#EXT-X-KEY") and 'URI="' in line:
                line = replace_key_uri(line, headers_query)
            elif line and not line.startswith("#"):
                seg_url = urljoin(base_url, line)
                line = f"/proxy/ts?url={quote(seg_url)}&{headers_query}"
            modified_lines.append(line)

        modified_content = "\n".join(modified_lines)
        return Response(modified_content, content_type="application/vnd.apple.mpegurl")

    except Exception as e:
        traceback.print_exc()
        return f"Genel hata: {str(e)}", 500

# --- TS Proxy ---
@app.route('/proxy/ts')
def proxy_ts():
    ts_url = request.args.get('url', '').strip()
    if not ts_url:
        return "Hata: 'url' parametresi eksik", 400
    headers = {unquote(k[2:]).replace("_","-"): unquote(v).strip() for k,v in request.args.items() if k.lower().startswith("h_")}
    try:
        r = requests.get(ts_url, headers=headers, stream=True, timeout=(10,30))
        r.raise_for_status()
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), content_type="video/mp2t")
    except Exception as e:
        traceback.print_exc()
        return f"TS segment hatası: {str(e)}", 500

# --- Key Proxy ---
@app.route('/proxy/key')
def proxy_key():
    key_url = request.args.get('url', '').strip()
    if not key_url:
        return "Hata: 'url' parametresi eksik", 400
    headers = {unquote(k[2:]).replace("_","-"): unquote(v).strip() for k,v in request.args.items() if k.lower().startswith("h_")}
    try:
        r = requests.get(key_url, headers=headers, timeout=(5,15))
        r.raise_for_status()
        return Response(r.content, content_type="application/octet-stream")
    except Exception as e:
        traceback.print_exc()
        return f"AES-128 key hatası: {str(e)}", 500

@app.route('/')
def index():
    return "✅ Vavoo Proxy Render sürümü aktif!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
