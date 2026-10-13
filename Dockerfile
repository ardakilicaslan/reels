# AŞAMA 1: Resmi statik FFmpeg ikili dosyalarını al
FROM mwader/static-ffmpeg:6.0 AS ffmpeg-source

# AŞAMA 2: Resmi n8n taban imajı
FROM n8nio/n8n:latest

USER root

# FFmpeg ve FFprobe ikili dosyalarını n8n PATH'ine kopyala
COPY --from=ffmpeg-source /ffmpeg /usr/local/bin/
COPY --from=ffmpeg-source /ffprobe /usr/local/bin/

# Port ve Host ortam değişkenleri
ENV PORT=5678
ENV N8N_PORT=5678
ENV N8N_HOST=0.0.0.0
ENV N8N_PROTOCOL=https

# Execute Command (FFmpeg çalıştırma) düğümünü aktifleştir
ENV NODES_EXCLUDE="[]"

# n8n kullanıcısına geri dön
USER node

EXPOSE 5678
