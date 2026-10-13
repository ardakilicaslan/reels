"""
Instagram Reels Otomatik Paylaşım Botu.

DM'den video alır → Reels olarak paylaşır.

Kullanım:
    1. Bot hesabına DM'den video at
    2. Ardından açıklamayı (caption) metin olarak yaz
    3. İstersen kapak fotoğrafı gönder
    4. Bot otomatik olarak Reels paylaşır ve sana DM'den bildirir

Çalışma mantığı:
    - Bot belirli aralıklarla (varsayılan 30sn) DM kutusunu kontrol eder
    - Sadece OWNER_USERNAME'den gelen mesajları işler (güvenlik)
    - Video + caption eşleşmesi bulunca Reels olarak paylaşır
    - Sonucu DM'den bildirir
"""

import os
import sys
import time
import logging
import pathlib
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
)

from config import Config
from dm_reader import DMReader
from reels_uploader import ReelsUploader

# ─────────────────────────────────────────────
# Logging
# ─────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("bot.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("reels-bot")


# ─────────────────────────────────────────────
# Health Check Server (Render.com uyku engellemek için)
# ─────────────────────────────────────────────
class HealthHandler(BaseHTTPRequestHandler):
    """Basit health check endpoint'i."""

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Instagram Reels Bot is running!")

    def log_message(self, format, *args):
        pass  # Health check loglarını sustur


def start_health_server():
    """Background thread'de health check sunucusu başlatır."""
    server = HTTPServer(("0.0.0.0", Config.PORT), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Health check sunucusu başlatıldı: port {Config.PORT}")


# ─────────────────────────────────────────────
# Instagram Client Yönetimi
# ─────────────────────────────────────────────
def create_client() -> Client:
    """
    Instagram client oluşturur ve giriş yapar.
    Session dosyası varsa yeniden kullanır (login challenge'ları önler).
    """
    cl = Client()

    # Cihaz ayarları - gerçek bir telefon gibi görünsün
    cl.delay_range = [1, 3]  # İstekler arası bekleme (saniye)

    session_path = pathlib.Path(Config.SESSION_FILE)

    try:
        if session_path.exists():
            logger.info("Mevcut oturum yükleniyor...")
            cl.load_settings(str(session_path))
            cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)

            # Oturumun hala geçerli olduğunu doğrula
            try:
                cl.get_timeline_feed()
                logger.info("✅ Mevcut oturum geçerli!")
            except LoginRequired:
                logger.warning("Oturum süresi dolmuş, yeniden giriş yapılıyor...")
                cl = Client()
                cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
                cl.dump_settings(str(session_path))
        else:
            logger.info("İlk giriş yapılıyor...")
            cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
            cl.dump_settings(str(session_path))
            logger.info("✅ Giriş başarılı, oturum kaydedildi.")

    except TwoFactorRequired:
        logger.error(
            "❌ İki faktörlü doğrulama gerekiyor!\n"
            "Çözüm: Instagram ayarlarından 2FA'yı kapatın veya\n"
            "uygulama şifresi (app password) oluşturun."
        )
        sys.exit(1)

    except ChallengeRequired:
        logger.error(
            "❌ Instagram güvenlik doğrulaması gerekiyor!\n"
            "Çözüm: Instagram uygulamasından veya tarayıcıdan giriş yapıp\n"
            "güvenlik doğrulamasını tamamlayın, sonra botu tekrar çalıştırın."
        )
        sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Giriş başarısız: {e}")
        sys.exit(1)

    return cl


# ─────────────────────────────────────────────
# Ana Bot Döngüsü
# ─────────────────────────────────────────────
def run_bot():
    """Ana bot döngüsü - DM'leri kontrol eder ve Reels paylaşır."""

    logger.info("=" * 50)
    logger.info("🎬 Instagram Reels Otomatik Paylaşım Botu")
    logger.info("=" * 50)

    # Konfigürasyon doğrulama
    errors = Config.validate()
    if errors:
        for err in errors:
            logger.error(f"  ❌ {err}")
        logger.error("Lütfen .env dosyasını düzenleyin.")
        sys.exit(1)

    # Health check sunucusu (Render.com için)
    if os.getenv("RENDER"):
        start_health_server()

    # Instagram'a giriş yap
    client = create_client()

    # Modülleri başlat
    dm_reader = DMReader(client)
    uploader = ReelsUploader(client)

    # Owner thread'ini bul (DM yanıtları için)
    owner_thread_id = None

    logger.info(f"📬 DM kontrol aralığı: {Config.DM_CHECK_INTERVAL} saniye")
    logger.info(f"👤 İzlenen kullanıcı: @{Config.OWNER_USERNAME}")
    logger.info("🔄 DM izleme başlıyor...\n")

    while True:
        try:
            # DM'leri kontrol et
            tasks = dm_reader.check_new_tasks()

            if tasks:
                logger.info(f"📥 {len(tasks)} yeni görev bulundu!")

                # Owner thread ID'sini bul (yanıt göndermek için)
                if not owner_thread_id:
                    owner_user_id = client.user_id_from_username(Config.OWNER_USERNAME)
                    threads = client.direct_threads(amount=20)
                    for t in threads:
                        if owner_user_id in [u.pk for u in t.users]:
                            owner_thread_id = t.id
                            break

                for task in tasks:
                    try:
                        logger.info(f"\n{'─' * 40}")
                        logger.info(f"🎬 Reels paylaşılıyor...")
                        logger.info(f"   Caption: {task.caption[:80]}...")
                        logger.info(f"   Video: {task.video_path}")
                        logger.info(f"   Kapak: {'Var' if task.cover_path else 'Yok'}")

                        # Durum mesajı gönder
                        if owner_thread_id:
                            dm_reader.send_reply(
                                owner_thread_id,
                                f"⏳ Reels yükleniyor...\n📝 {task.caption[:100]}"
                            )

                        # Reels olarak yükle
                        result = uploader.upload_reel(
                            video_path=task.video_path,
                            caption=task.caption,
                            thumbnail_path=task.cover_path,
                        )

                        # Başarı mesajı gönder
                        success_msg = (
                            f"✅ Reels paylaşıldı! 🎉\n\n"
                            f"🔗 {result['url']}\n"
                            f"📝 {task.caption[:100]}"
                        )
                        logger.info(f"✅ Paylaşıldı: {result['url']}")

                        if owner_thread_id:
                            dm_reader.send_reply(owner_thread_id, success_msg)

                    except Exception as e:
                        error_msg = f"❌ Paylaşım hatası: {str(e)}"
                        logger.error(error_msg, exc_info=True)

                        if owner_thread_id:
                            dm_reader.send_reply(owner_thread_id, error_msg)

                    finally:
                        # Geçici dosyaları temizle
                        for path in [task.video_path, task.cover_path]:
                            if path and os.path.exists(path):
                                try:
                                    os.remove(path)
                                except OSError:
                                    pass

            else:
                logger.debug("📭 Yeni görev yok.")

        except LoginRequired:
            logger.warning("⚠️ Oturum düştü, yeniden giriş yapılıyor...")
            client = create_client()
            dm_reader = DMReader(client)
            uploader = ReelsUploader(client)

        except Exception as e:
            logger.error(f"❌ Döngü hatası: {e}", exc_info=True)

        # Bir sonraki kontrolü bekle
        time.sleep(Config.DM_CHECK_INTERVAL)


# ─────────────────────────────────────────────
# Giriş Noktası
# ─────────────────────────────────────────────
if __name__ == "__main__":
    run_bot()
