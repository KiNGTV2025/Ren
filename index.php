<?php
$videoId = isset($_GET['id']) ? $_GET['id'] : '';
if (!$videoId) {
  http_response_code(400);
  echo "Video ID gerekli.";
  exit;
}
$videoId = preg_replace('/\.m3u8$/', '', $videoId);
$targetUrl = "https://www.youtube.com/watch?v=" . $videoId;

function fetchUrl($url) {
  $ch = curl_init();
  curl_setopt_array($ch, [
    CURLOPT_URL => $url,
    CURLOPT_RETURNTRANSFER => 1,
    CURLOPT_FOLLOWLOCATION => 1,
    CURLOPT_MAXREDIRS => 10,
    CURLOPT_TIMEOUT => 30,
    CURLOPT_SSL_VERIFYPEER => false,
    CURLOPT_SSL_VERIFYHOST => 0,
    CURLOPT_USERAGENT => "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
  ]);
  curl_setopt($ch, CURLOPT_COOKIEJAR, __DIR__ . '/cookies.txt');
  curl_setopt($ch, CURLOPT_COOKIEFILE, __DIR__ . '/cookies.txt');
  $resp = curl_exec($ch);
  if (curl_errno($ch)) {
    curl_close($ch);
    return false;
  }
  curl_close($ch);
  return $resp;
}

$response = fetchUrl($targetUrl);
if (!$response) {
  http_response_code(500);
  echo "Bağlantı alınamadı.";
  exit;
}

if (preg_match('/"hlsManifestUrl":"(https:\\\/\\\/[^"]+index\.m3u8[^"]*)"/', $response, $m)) {
  $streamUrl = str_replace('\/','/',$m[1]);
} elseif (preg_match('/https:\/\/[^"]+\/index\.m3u8/', $response, $m)) {
  $streamUrl = $m[0];
} else {
  http_response_code(404);
  echo "index.m3u8 bulunamadı.";
  exit;
}

header('Content-Type: application/vnd.apple.mpegurl');
header('Content-Disposition: inline; filename="stream.m3u8"');
header('Location: ' . $streamUrl);
exit;
?>
