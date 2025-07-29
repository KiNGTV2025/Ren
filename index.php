<?php
// İstemciden video ID al
$videoId = isset($_GET['id']) ? $_GET['id'] : '';

if (!$videoId) {
    http_response_code(400);
    echo "Video ID gerekli.";
    exit;
}

// videoId sonunda .m3u8 varsa temizle
$videoId = preg_replace('/\.m3u8$/', '', $videoId);

// YouTube video URL’si
$baseUrl = "https://www.youtube.com/watch?v=";
$targetUrl = $baseUrl . $videoId;

function fetchUrl($url) {
    $ch = curl_init();
    curl_setopt_array($ch, [
        CURLOPT_URL => $url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_MAXREDIRS => 10,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_SSL_VERIFYPEER => false,
        CURLOPT_SSL_VERIFYHOST => false,
        CURLOPT_HEADER => false,
        CURLOPT_COOKIEJAR => __DIR__ . '/cookies.txt',
        CURLOPT_COOKIEFILE => __DIR__ . '/cookies.txt',
        CURLOPT_AUTOREFERER => true,
        CURLOPT_HTTPHEADER => [
            'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language: en-US,en;q=0.5',
            'Connection: keep-alive'
        ],
        CURLOPT_USERAGENT => "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36"
    ]);

    $response = curl_exec($ch);

    if (curl_errno($ch)) {
        echo 'cURL hatası: ' . curl_error($ch);
        curl_close($ch);
        return false;
    }

    curl_close($ch);
    return $response;
}

$response = fetchUrl($targetUrl);

if (!$response) {
    http_response_code(500);
    echo "Bağlantı alınamadı.";
    exit;
}

// Regex ile hlsManifestUrl yakala
if (preg_match('/"hlsManifestUrl":"(https:\\\\/\\\\/[^"]+index\\.m3u8[^"]*)"/', $response, $matches)) {
    $streamUrl = str_replace('\\/', '/', $matches[1]);

    header('Content-Type: application/vnd.apple.mpegurl');
    header('Content-Disposition: inline; filename="stream.m3u8"');
    header('Location: ' . $streamUrl);
    exit;
}
// Fallback regex
elseif (preg_match('/https:\/\/[^"]+\/index\.m3u8/', $response, $matches)) {
    $streamUrl = $matches[0];

    header('Content-Type: application/vnd.apple.mpegurl');
    header('Content-Disposition: inline; filename="stream.m3u8"');
    header('Location: ' . $streamUrl);
    exit;
} else {
    http_response_code(404);
    echo "index.m3u8 dosyası bulunamadı. YouTube yapısı değişmiş olabilir veya video canlı yayın olmayabilir.";
}
?>
