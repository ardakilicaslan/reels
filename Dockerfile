# 1. FFmpeg statik ikili dosyaları
FROM mwader/static-ffmpeg:6.0 AS ffmpeg-source

# 2. Hafif Python tabanı
FROM python:3.11-slim

WORKDIR /app

# FFmpeg kopyala
COPY --from=ffmpeg-source /ffmpeg /usr/local/bin/
COPY --from=ffmpeg-source /ffprobe /usr/local/bin/

# Bağımlılıkları yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodlarını kopyala
COPY . .

# Render portu
ENV PORT=10000
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-10000}"]
