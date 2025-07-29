<?php
// İstemciden video ID al
$videoId = isset($_GET['id']) ? $_GET['id'] : '';

if (!$videoId) {
  http_response_code(400);
  echo "❌ Video ID gerekli.";
  exit;
}

// ".m3u8" varsa sonundan sil
$videoId = preg_replace('/\.m3u8$/', '', $videoId);

// YouTube video sayfası URL’si oluştur
$targetUrl = "https://www.youtube.com/watch?v=" . $videoId;

// YouTube sayfasını çekmek için cURL fonksiyonu
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
    CURLOPT_USERAGENT => "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    CURLOPT_COOKIEJAR => __DIR__ . '/cookies.txt',
    CURLOPT_COOKIEFILE => __DIR__ . '/cookies.txt',
  ]);

  $response = curl_exec($ch);

  if (curl_errno($ch)) {
    echo '❌ cURL hatası: ' . curl_error($ch);
    curl_close($ch);
    return false;
  }

  curl_close($ch);
  return $response;
}

// Sayfa içeriğini al
$response = fetchUrl($targetUrl);

if (!$response) {
  http_response_code(500);
  echo "❌ Sayfa içeriği alınamadı.";
  exit;
}

// HLS manifest URL’sini regex ile yakala
if (preg_match('/"hlsManifestUrl":"(https:\\\\/\\\\/[^"]+index\\.m3u8[^"]*)"/', $response, $matches)) {
  $streamUrl = str_replace('\\/', '/', $matches[1]); // JSON'dan gelen \\/ düzeltmesi

  header('Content-Type: application/vnd.apple.mpegurl');
  header('Content-Disposition: inline; filename="stream.m3u8"');
  header('Location: ' . $streamUrl);
  exit;

}
// Yedek desen: doğrudan m3u8 URL varsa
elseif (preg_match('/https:\/\/[^"]+\/index\.m3u8[^"]*/', $response, $matches)) {
  $streamUrl = $matches[0];

  header('Content-Type: application/vnd.apple.mpegurl');
  header('Content-Disposition: inline; filename="stream.m3u8"');
  header('Location: ' . $streamUrl);
  exit;

} else {
  http_response_code(404);
  echo "❌ index.m3u8 bulunamadı. Bu video canlı yayın olmayabilir.";
}
?>
