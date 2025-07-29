<?php
$videoId = isset($_GET['id']) ? $_GET['id'] : '';

if (!$videoId) {
    http_response_code(400);
    echo "Video ID gerekli.";
    exit;
}

$videoUrl = escapeshellarg("https://www.youtube.com/watch?v=" . $videoId);

// yt-dlp komutunu çalıştır, JSON çıktısını al
$cmd = "yt-dlp -j {$videoUrl} 2>&1";

exec($cmd, $output, $return_var);

if ($return_var !== 0) {
    http_response_code(500);
    echo "yt-dlp komutu başarısız: " . implode("\n", $output);
    exit;
}

$jsonStr = implode("\n", $output);
$videoInfo = json_decode($jsonStr, true);

if (!$videoInfo) {
    http_response_code(500);
    echo "Video bilgisi çözümlenemedi.";
    exit;
}

// M3U8 linklerini ara
$m3u8Url = null;
foreach ($videoInfo['formats'] as $format) {
    if (isset($format['protocol']) && $format['protocol'] === 'm3u8_native') {
        $m3u8Url = $format['url'];
        break;
    }
}

if (!$m3u8Url) {
    http_response_code(404);
    echo "M3U8 linki bulunamadı.";
    exit;
}

// Yönlendir
header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename="stream.m3u8"');
header('Location: ' . $m3u8Url);
exit;
?>
