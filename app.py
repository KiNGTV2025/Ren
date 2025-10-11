from flask import Flask, request, Response
import requests
from urllib.parse import urlparse, urljoin, quote, unquote
import re
import os

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

# --- Proxy M3U ---
@app.route('/proxy/m3u')
def proxy_m3u():
    """Proxy M3U/M3U8 dosyası"""
    m3u_url = request.args.get('url', '').strip()
    if not m3u_url:
        return "Hata: 'url' parametresi eksik", 400

    headers = {
        unquote(k[2:]).replace("_", "-"): unquote(v).strip()
        for k, v in request.args.items() if k.lower().startswith("h_")
    }
    headers.setdefault("User-Agent", "Mozilla/5.0")
    headers.setdefault("Referer", "https://vavoo.to")
    headers.setdefault("Origin", "https://vavoo.to")

    try:
        # M3U8 isteği
        res = requests.get(m3u_url, headers=headers, timeout=(10, 20))
        res.raise_for_status()
        content = res.text
        file_type = detect_m3u_type(content)

        if file_type == "m3u":
            return Response(content, content_type="application/vnd.apple.mpegurl")

        parsed = urlparse(m3u_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path.rsplit('/', 1)[0]}/"
        headers_query = "&".join([f"h_{quote(k)}={quote(v)}" for k, v in headers.items()])

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

    except requests.RequestException as e:
        return f"M3U/M3U8 indirme hatası: {str(e)}", 500


# --- Proxy TS ---
@app.route('/proxy/ts')
def proxy_ts():
    ts_url = request.args.get('url', '').strip()
    if not ts_url:
        return "Hata: 'url' parametresi eksik", 400

    headers = {
        unquote(k[2:]).replace("_", "-"): unquote(v).strip()
        for k, v in request.args.items() if k.lower().startswith("h_")
    }

    try:
        r = requests.get(ts_url, headers=headers, stream=True, timeout=(10, 30))
        r.raise_for_status()
        def generate():
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        return Response(generate(), content_type="video/mp2t")
    except requests.RequestException as e:
        return f"TS segment hatası: {str(e)}", 500


# --- Proxy Key ---
@app.route('/proxy/key')
def proxy_key():
    key_url = request.args.get('url', '').strip()
    if not key_url:
        return "Hata: 'url' parametresi eksik", 400

    headers = {
        unquote(k[2:]).replace("_", "-"): unquote(v).strip()
        for k, v in request.args.items() if k.lower().startswith("h_")
    }

    try:
        r = requests.get(key_url, headers=headers, timeout=(5, 15))
        r.raise_for_status()
        return Response(r.content, content_type="application/octet-stream")
    except requests.RequestException as e:
        return f"AES-128 anahtar hatası: {str(e)}", 500


# --- Proxy List ---
@app.route('/proxy')
def proxy_list():
    m3u_url = request.args.get('url', '').strip()
    if not m3u_url:
        return "Hata: 'url' parametresi eksik", 400
    try:
        server_ip = request.host
        res = requests.get(m3u_url, timeout=(10, 30))
        res.raise_for_status()
        lines = []
        for line in res.text.splitlines():
            line = line.strip()
            if line and not line.startswith('#'):
                line = f"https://{server_ip}/proxy/m3u?url={line}"
            lines.append(line)
        return Response("\n".join(lines), content_type="application/vnd.apple.mpegurl")
    except Exception as e:
        return f"Liste proxy hatası: {str(e)}", 500


@app.route('/')
def index():
    return "✅ IPTV Proxy aktif (Render sürümü)!"


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
