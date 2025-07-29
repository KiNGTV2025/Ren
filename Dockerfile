FROM php:8.2-apache

# Python3, curl ve diğer bağımlılıkları kur
RUN apt-get update && apt-get install -y python3 curl unzip git

# yt-dlp binary'sini indir ve çalıştırılabilir yap
RUN curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp \
    && chmod a+rx /usr/local/bin/yt-dlp

RUN a2enmod rewrite

COPY ./ /var/www/html/

EXPOSE 80
