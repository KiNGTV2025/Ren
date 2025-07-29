# Resmi PHP Apache image kullanıyoruz
FROM php:8.2-apache

# Sistemi güncelle ve python3, pip kur
RUN apt-get update && apt-get install -y python3 python3-pip curl unzip git

# yt-dlp yükle
RUN pip3 install yt-dlp

# Apache mod_rewrite aktif et (isteğe bağlı)
RUN a2enmod rewrite

# Çalışma dizinine dosyaları kopyala
COPY ./ /var/www/html/

# Apache default port
EXPOSE 80
