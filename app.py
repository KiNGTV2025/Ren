from flask import Flask, request, redirect, Response
from cachetools import TTLCache
import yt_dlp
import logging
import os

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

app = Flask(__name__)

# Cache: max 100 entries, TTL = 6 hours
cache = TTLCache(maxsize=100, ttl=21600)

def get_stream_url(youtube_url):
    logger.info(f"Fetching stream URL for: {youtube_url}")
    
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'forcejson': True,
        'extract_flat': False,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)

            # Direct livestream
            if info.get('is_live'):
                logger.info("Livestream detected")
                return info.get('url')

            # Playlist or channel with entries
            if 'entries' in info and info['entries']:
                for entry in info['entries']:
                    if entry.get('is_live'):
                        logger.info(f"Livestream found in entries: {entry.get('title')}")
                        return entry.get('url')

                first_entry = info['entries'][0]
                logger.info(f"Using first video: {first_entry.get('title')}")
                return first_entry.get('url')

            # Single video
            return info.get('url')
            
    except Exception as e:
        logger.error(f"Error extracting stream: {str(e)}")
        raise e

@app.route('/')
def home():
    return """
    <h1>🚀 YouTube IPTV Server</h1>
    <p><strong>Public URL Service - Herkes İzleyebilir!</strong></p>
    
    <h3>📺 Kullanım Örnekleri:</h3>
    <ul>
        <li><a href="/stream?url=https://www.youtube.com/@Sozcutelevizyonu/live&name=sozcu">Sözcü TV</a></li>
        <li><a href="/stream?url=https://www.youtube.com/@HaberGlobal/live&name=haberglobal">Haber Global</a></li>
        <li><a href="/stream?url=https://www.youtube.com/@TRTHaber/live&name=trthaber">TRT Haber</a></li>
    </ul>
    
    <h3>🎯 M3U Playlist:</h3>
    <p><a href="/playlist.m3u">Tüm Kanalların Playlist'i</a></p>
    
    <h3>🔗 API Endpoint:</h3>
    <code>/stream?url=YOUTUBE_URL&name=UNIQUE_NAME</code>
    """

@app.route('/stream')
def stream():
    youtube_url = request.args.get('url')
    custom_name = request.args.get('name')

    if not youtube_url:
        return "❌ Missing 'url' parameter", 400

    # Name parametresi yoksa URL'den otomatik üret
    if not custom_name:
        custom_name = youtube_url.split('/')[-1]
    
    key = f"name:{custom_name.strip().lower()}"

    try:
        # Cache'den dene
        stream_url = cache[key]
        logger.info("✅ Cache hit")
    except KeyError:
        # Yeni URL al
        logger.info("🔄 Cache miss - fetching new URL")
        try:
            stream_url = get_stream_url(youtube_url)
            cache[key] = stream_url
            logger.info("✅ New URL fetched and cached")
        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            return f"❌ Error: {str(e)}", 500

    logger.info(f"🔀 Redirecting to: {stream_url}")
    return redirect(stream_url)

@app.route('/playlist.m3u')
def playlist():
    """IPTV Player'lar için M3U playlist"""
    channels = [
        {
            "name": "Sözcü TV",
            "url": "https://www.youtube.com/@Sozcutelevizyonu/live",
            "id": "sozcutv",
            "logo": "https://i.ytimg.com/vi/UCqFKN6T1gktxFCWBWxurywg/hqdefault.jpg"
        },
        {
            "name": "Haber Global", 
            "url": "https://www.youtube.com/@HaberGlobal/live",
            "id": "haberglobal",
            "logo": "https://i.ytimg.com/vi/UCG3_0y4i1s99UZeOmV6CvTQ/hqdefault.jpg"
        },
        {
            "name": "TRT Haber",
            "url": "https://www.youtube.com/@TRTHaber/live", 
            "id": "trthaber",
            "logo": "https://i.ytimg.com/vi/UCqFKN6T1gktxFCWBWxurywg/hqdefault.jpg"
        },
        {
            "name": "TV100",
            "url": "https://www.youtube.com/@TV100/live",
            "id": "tv100",
            "logo": "https://i.ytimg.com/vi/UCl5Ua2UrXQkK5dM0qKUR7A/hqdefault.jpg"
        }
    ]
    
    base_url = request.url_root.rstrip('/')
    
    m3u_content = '#EXTM3U\n'
    
    for channel in channels:
        stream_url = f"{base_url}/stream?url={channel['url']}&name={channel['id']}"
        m3u_content += f'#EXTINF:-1 tvg-id="{channel["id"]}" tvg-name="{channel["name"]}" tvg-logo="{channel["logo"]}" group-title="YouTube",{channel["name"]}\n'
        m3u_content += f"{stream_url}\n"
    
    return Response(m3u_content, mimetype='audio/x-mpegurl')

@app.route('/health')
def health():
    return "✅ Server is running!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
