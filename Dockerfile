FROM php:8.2-apache

# Gerekli paketleri kur (curl vs)
RUN apt-get update && apt-get install -y curl unzip git

# yt-dlp binary dosyasını indir ve çalıştırılabilir yap
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

# Apache mod_rewrite aktif et (isteğe bağlı)
RUN a2enmod rewrite

# Uygulama dosyalarını kopyala
COPY ./ /var/www/html/

# Apache port aç
EXPOSE 80
