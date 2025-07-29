<?php
// İstemciden video ID al
$videoId = isset($_GET['id']) ? $_GET['id'] : '';

if (!$videoId) {
http_response_code(400);
echo "Video ID gerekli.";
exit;
}

// Eğer videoId sonunda .m3u8 uzantısı varsa temizle
$videoId = preg_replace('/\.m3u8$/', '', $videoId);

// Base URL tanımı
$baseUrl = "https://www.youtube.com/watch?v=";
$targetUrl = $baseUrl . $videoId;

// cURL ile tarayıcı gibi YouTube sayfasını çek
function fetchUrl($url) {
$ch = curl_init();

curl_setopt($ch, CURLOPT_URL, $url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 1);
curl_setopt($ch, CURLOPT_MAXREDIRS, 10);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);
curl_setopt($ch, CURLOPT_HEADER, 0);
curl_setopt($ch, CURLOPT_COOKIEJAR, __DIR__ . '/cookies.txt');
curl_setopt($ch, CURLOPT_COOKIEFILE, __DIR__ . '/cookies.txt');
curl_setopt($ch, CURLOPT_AUTOREFERER, true);

curl_setopt($ch, CURLOPT_HTTPHEADER, [
'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
'Accept-Language: en-US,en;q=0.5',
'Connection: keep-alive'
]);

curl_setopt($ch, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36");

$response = curl_exec($ch);

if (curl_errno($ch)) {
echo 'cURL hatası: ' . curl_error($ch);
curl_close($ch);
return false;
}

curl_close($ch);
return $response;
}

// URL'yi fetch et
$response = fetchUrl($targetUrl);

if (!$response) {
http_response_code(500);
echo "Bağlantı alınamadı.";
exit;
}

// Güncellenmiş regex pattern'i
if (preg_match('/"hlsManifestUrl":"(https:\\\/\\\/[^"]+index\.m3u8[^"]*)"/', $response, $matches)) {
$streamUrl = str_replace('\/', '/', $matches[1]);

// HLS stream MIME tipi
header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename="stream.m3u8"');

// İstemciye doğrudan m3u8 bağlantısını döndür
header('Location: ' . $streamUrl);
exit;
}
// Eski regex pattern'i (fallback)
elseif (preg_match('/https:\/\/[^"]+\/index\.m3u8/', $response, $matches)) {
$streamUrl = $matches[0];

header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename="stream.m3u8"');
header('Location: ' . $streamUrl);
exit;
} else {
http_response_code(404);
echo "index.m3u8 dosyası bulunamadı. YouTube yapısı değişmiş olabilir.";
}
?>
