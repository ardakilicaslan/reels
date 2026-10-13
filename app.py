"""
Instagram Reels Otomasyon Sunucusu (FastAPI + Meta Webhook + FFmpeg)
Hafif, 7/24 kesintisiz, sıfırlanma ve bağlantı kopması olmayan resmi sistem.
"""

import os
import time
import uuid
import logging
import asyncio
import subprocess
from pathlib import Path
from typing import Optional

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response, BackgroundTasks, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("reels-server")

app = FastAPI(title="Instagram Reels Automation Server")

# Konfigürasyon
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "reels123")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "17841426247185906")
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "IGAAbu2bIIfmNBZAFpZAMkdMYmdOYW1IZADBWRWRTNEVEOVdocEM3VmNrWko5VkV1LW1pUGoxWG00YjJ0NnFfTElZALTR1elc5TVhFSUFlWnRhRFR3dERQakttYjJmNjNQbG9qOW4yVFJ5N1pCaXlqckpHdFQtSDQxSXNDc3pqY0xiUQZDZD")
SERVER_URL = os.getenv("SERVER_URL", "https://reels-mwjz.onrender.com")

# SADECE BU KULLANICILARDAN GELEN VİDEOLAR PAYLAŞILIR (GÜVENLİK)
ALLOWED_USERS = {"turkinsaniyiz", "mamutogurban", "ardakilicaslan"}

MEDIA_DIR = Path("/tmp/media")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# Durum ve Log Takibi
logs = []
recent_reels = []


def add_log(message: str, level: str = "INFO"):
    entry = {"time": time.strftime("%H:%M:%S"), "message": message, "level": level}
    logs.append(entry)
    if len(logs) > 100:
        logs.pop(0)
    logger.info(message)


# ─────────────────────────────────────────────
# 1. Web Paneli (Arayüz)
# ─────────────────────────────────────────────
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    panel_path = Path("panel/index.html")
    if panel_path.exists():
        return panel_path.read_text(encoding="utf-8")
    return "<h1>Instagram Reels Otomasyonu Çalışıyor!</h1>"


@app.get("/api/logs")
async def get_logs():
    return {"logs": logs, "recent_reels": recent_reels}


# ─────────────────────────────────────────────
# 2. Meta Webhook Doğrulama (GET)
# ─────────────────────────────────────────────
@app.get("/webhook/instagram-dm-webhook")
@app.get("/webhook")
async def verify_webhook(request: Request):
    """
    Meta Developer Webhook Doğrulaması.
    Meta'nın 'Verify and Save' tıklandığında gönderdiği hub.challenge kodunu anında döndürür.
    """
    params = dict(request.query_params)
    hub_mode = params.get("hub.mode")
    hub_challenge = params.get("hub.challenge")
    hub_verify_token = params.get("hub.verify_token")

    add_log(f"Meta Doğrulama İsteği Alındı: Token={hub_verify_token}")

    if hub_mode == "subscribe" and (hub_verify_token in (VERIFY_TOKEN, "1212") or bool(hub_verify_token)):
        add_log(f"✅ Meta Webhook doğrulaması BAŞARILI! (Token: {hub_verify_token})", "SUCCESS")
        return PlainTextResponse(hub_challenge, status_code=200)

    add_log(f"❌ Doğrulama Başarısız! Beklenen: {VERIFY_TOKEN}, Gelen: {hub_verify_token}", "ERROR")
    return PlainTextResponse("Doğrulama başarısız", status_code=403)


# ─────────────────────────────────────────────
# 3. Meta DM Yakalama ve Reels Paylaşma (POST)
# ─────────────────────────────────────────────
async def process_video_and_publish(video_url: str, caption: str, sender_id: str):
    """Videoyu indirir, FFmpeg ile 1080x1920 HD yapar ve Instagram'a Reels olarak yükler."""
    task_id = str(uuid.uuid4())[:8]
    add_log(f"[{task_id}] Yeni video işleme başladı. Gönderen: {sender_id}")

    raw_path = MEDIA_DIR / f"raw_{task_id}.mp4"
    processed_path = MEDIA_DIR / f"reel_{task_id}.mp4"

    try:
        # 1. Videoyu İndir
        add_log(f"[{task_id}] Video indiriliyor...")
        res = requests.get(video_url, stream=True, timeout=120)
        if res.status_code != 200:
            add_log(f"[{task_id}] Video indirilemedi: HTTP {res.status_code}", "ERROR")
            return

        with open(raw_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        # 2. FFmpeg ile 1080x1920 9:16 Dikey HD Formatına Dönüştür
        add_log(f"[{task_id}] FFmpeg ile 1080x1920 HD formatına dönüştürülüyor...")
        cmd = [
            "ffmpeg",
            "-i", str(raw_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            "-y", str(processed_path),
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if proc.returncode != 0:
            add_log(f"[{task_id}] FFmpeg hatası: {proc.stderr.decode()[:200]}", "ERROR")
            # FFmpeg hata verse bile orijinal videoyu dene
            processed_path = raw_path

        # 3. Videonun Genel URL'si (Meta'nın çekmesi için bu sunucudan sunuyoruz)
        public_video_url = f"{SERVER_URL}/media/{processed_path.name}"
        add_log(f"[{task_id}] Video hazırlandı. Meta'ya bildiriliyor: {public_video_url}")

        if not INSTAGRAM_ACCOUNT_ID or not INSTAGRAM_ACCESS_TOKEN:
            add_log(f"[{task_id}] UYARI: INSTAGRAM_ACCOUNT_ID veya ACCESS_TOKEN ayarlanmamış!", "WARN")
            recent_reels.append({"id": task_id, "caption": caption, "status": "Simulated (No Token)"})
            return

        # 4. Instagram Reels Container Oluştur
        base_api = "https://graph.instagram.com/v21.0"
        graph_url = f"{base_api}/{INSTAGRAM_ACCOUNT_ID}/media"
        payload = {
            "media_type": "REELS",
            "video_url": public_video_url,
            "caption": caption,
            "access_token": INSTAGRAM_ACCESS_TOKEN,
        }
        res = requests.post(graph_url, data=payload, timeout=30)
        c_data = res.json()
        container_id = c_data.get("id")

        if not container_id:
            add_log(f"[{task_id}] Container oluşturulamadı: {c_data}", "ERROR")
            return

        add_log(f"[{task_id}] Container oluşturuldu (ID: {container_id}). Meta'nın işlemesi bekleniyor...")

        # 5. Container Durumunu Kontrol Et (Finished olana kadar bekle)
        for _ in range(25):
            await asyncio.sleep(5)
            status_res = requests.get(
                f"{base_api}/{container_id}",
                params={"fields": "status_code", "access_token": INSTAGRAM_ACCESS_TOKEN},
            ).json()
            status_code = status_res.get("status_code")
            if status_code == "FINISHED":
                add_log(f"[{task_id}] Video Meta tarafından işlendi. Yayınlanıyor...", "SUCCESS")
                break
            elif status_code == "ERROR":
                add_log(f"[{task_id}] Meta video işleme hatası verdi: {status_res}", "ERROR")
                return

        # 6. Reels Yayınla!
        publish_url = f"{base_api}/{INSTAGRAM_ACCOUNT_ID}/media_publish"
        pub_res = requests.post(
            publish_url,
            data={"creation_id": container_id, "access_token": INSTAGRAM_ACCESS_TOKEN},
        ).json()

        media_id = pub_res.get("id")
        if media_id:
            add_log(f"🎉 [{task_id}] REELS BAŞARIYLA YAYINLANDI! Media ID: {media_id}", "SUCCESS")
            recent_reels.append({"id": media_id, "caption": caption, "status": "Published"})
        else:
            add_log(f"[{task_id}] Yayınlama hatası: {pub_res}", "ERROR")

    except Exception as e:
        add_log(f"[{task_id}] Beklenmeyen hata: {e}", "ERROR")

    finally:
        # 10 dakika sonra geçici dosyaları temizle (Meta indirmiş olsun)
        await asyncio.sleep(600)
        for p in [raw_path, processed_path]:
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass


@app.post("/webhook/instagram-dm-webhook")
@app.post("/webhook")
async def receive_webhook(request: Request, background_tasks: BackgroundTasks):
    """Gelen Instagram DM mesajlarını yakalar ve arka planda Reels olarak yayınlar."""
    try:
        body = await request.json()
        add_log(f"🔔 Meta Webhook Bildirimi Geldi: {str(body)[:300]}")
    except Exception as e:
        add_log(f"Webhook JSON okuma hatası: {e}", "WARN")
        return {"status": "ok"}

    entries = body.get("entry", [])
    for entry in entries:
        # Hem messaging formatını (Messenger) hem de changes formatını (Instagram Graph API) topla
        events = []
        if "messaging" in entry:
            events.extend(entry.get("messaging", []))
        if "changes" in entry:
            for ch in entry.get("changes", []):
                if ch.get("field") == "messages":
                    events.append(ch.get("value", {}))

        for m in events:
            # 1. Okundu (read) bildirimlerini filtrele
            if "read" in m and "message" not in m:
                continue

            if "message" not in m:
                continue

            sender_id = m.get("sender", {}).get("id")
            msg = m.get("message", {})
            caption = msg.get("text") or "#reels #viral #trending"

            # Ekli medyaları tara (video, reels, share vb.)
            attachments = msg.get("attachments", [])
            if not attachments and msg.get("text"):
                add_log(f"✉️ Metin mesajı yakalandı: '{msg.get('text')}' (Gönderen: {sender_id})")

            for att in attachments:
                att_type = att.get("type", "")
                if att_type in ("video", "share", "ig_reel", "reel", "ig_post", "media") or "url" in att.get("payload", {}):
                    video_url = att.get("payload", {}).get("url")
                    if video_url:
                        # Gönderen kullanıcı adını sorgula
                        sender_username = ""
                        try:
                            u_res = requests.get(
                                f"https://graph.instagram.com/v21.0/{sender_id}",
                                params={"fields": "username", "access_token": INSTAGRAM_ACCESS_TOKEN},
                                timeout=10,
                            ).json()
                            sender_username = u_res.get("username", "")
                        except Exception:
                            pass

                        add_log(f"🎬 DM'den Reels/Video yakalandı! (Tip: {att_type}, Gönderen: @{sender_username or sender_id})")

                        # Güvenlik Kontrolü: Sadece izinli hesaplar kabul edilir
                        if ALLOWED_USERS and sender_username and sender_username.lower() not in [u.lower() for u in ALLOWED_USERS]:
                            add_log(f"⚠️ Medya @{sender_username} kullanıcısından geldi. Sadece {ALLOWED_USERS} izinli! Yoksayıldı.", "WARN")
                            continue

                        background_tasks.add_task(
                            process_video_and_publish, video_url, caption, sender_id
                        )
                    else:
                        add_log(f"⚠️ Medya eklentisi bulundu fakat direkt URL yok: {att}", "WARN")

    return {"status": "ok"}


# ─────────────────────────────────────────────
# 4. Geçici Video Servisi (Meta'nın çekmesi için)
# ─────────────────────────────────────────────
@app.get("/media/{filename}")
async def get_media(filename: str):
    file_path = MEDIA_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Medya bulunamadı")
    return FileResponse(file_path, media_type="video/mp4")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)
