# AŞAMA 1: Resmi statik FFmpeg ikili dosyalarını al
FROM mwader/static-ffmpeg:6.0 AS ffmpeg-source

# AŞAMA 2: Resmi n8n taban imajı
FROM n8nio/n8n:latest

USER root

# FFmpeg ve FFprobe çalıştırılabilir dosyalarını n8n yoluna kopyala
COPY --from=ffmpeg-source /ffmpeg /usr/local/bin/
COPY --from=ffmpeg-source /ffprobe /usr/local/bin/

# Güvenlik için yetkisiz node kullanıcısına geri dön
USER node

# n8n varsayılan portu
EXPOSE 5678

CMD ["n8n", "start"]
