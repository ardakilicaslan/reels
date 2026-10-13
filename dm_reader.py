"""
Instagram DM okuma ve video indirme modülü.

DM'lerden gelen videoları okur, indirir ve paylaşım bilgilerini çıkarır.
Mesaj formatı:
    - Video gönder (DM'den direkt video at)
    - Ardından metin mesajı gönder → bu caption (açıklama) olur
    - Opsiyonel: Fotoğraf gönder → bu kapak fotoğrafı olur
"""

import os
import json
import logging
import requests
from pathlib import Path
from dataclasses import dataclass, field
from instagrapi import Client

from config import Config

logger = logging.getLogger(__name__)


@dataclass
class ReelTask:
    """DM'den çıkarılan bir Reels paylaşım görevi."""

    message_id: str
    video_url: str
    video_path: str | None = None
    caption: str = ""
    cover_url: str | None = None
    cover_path: str | None = None
    timestamp: str = ""


class DMReader:
    """Instagram DM'lerini okuyup video indiren sınıf."""

    def __init__(self, client: Client):
        self.client = client
        self.download_dir = Path(Config.DOWNLOAD_DIR)
        self.download_dir.mkdir(exist_ok=True)
        self.processed_ids = self._load_processed()

    def _load_processed(self) -> set[str]:
        """Daha önce işlenmiş mesaj ID'lerini yükler (tekrar işlememek için)."""
        try:
            if os.path.exists(Config.PROCESSED_FILE):
                with open(Config.PROCESSED_FILE, "r") as f:
                    return set(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
        return set()

    def _save_processed(self) -> None:
        """İşlenmiş mesaj ID'lerini kaydeder."""
        try:
            with open(Config.PROCESSED_FILE, "w") as f:
                json.dump(list(self.processed_ids), f)
        except IOError as e:
            logger.error(f"İşlenmiş mesajlar kaydedilemedi: {e}")

    def mark_processed(self, message_id: str) -> None:
        """Mesajı işlenmiş olarak işaretle."""
        self.processed_ids.add(message_id)
        self._save_processed()

    def _find_owner_thread(self) -> str | None:
        """
        Bot sahibinin (OWNER_USERNAME) DM thread'ini bulur.

        Returns:
            Thread ID veya None.
        """
        try:
            owner_user_id = self.client.user_id_from_username(Config.OWNER_USERNAME)
            threads = self.client.direct_threads(amount=20)

            for thread in threads:
                user_ids = [u.pk for u in thread.users]
                if owner_user_id in user_ids:
                    logger.info(
                        f"Owner thread bulundu: {thread.id} "
                        f"(kullanıcı: {Config.OWNER_USERNAME})"
                    )
                    return thread.id

            logger.warning(f"Owner ({Config.OWNER_USERNAME}) ile DM thread'i bulunamadı.")
            return None

        except Exception as e:
            logger.error(f"Owner thread aranırken hata: {e}")
            return None

    def _download_video_from_url(self, url: str, filename: str) -> str | None:
        """URL'den video indirir."""
        file_path = self.download_dir / filename
        try:
            response = requests.get(url, stream=True, timeout=120)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Video indirildi: {file_path}")
                return str(file_path)
            else:
                logger.error(f"Video indirme başarısız (HTTP {response.status_code})")
                return None
        except Exception as e:
            logger.error(f"Video indirme hatası: {e}")
            return None

    def _download_image_from_url(self, url: str, filename: str) -> str | None:
        """URL'den resim indirir."""
        file_path = self.download_dir / filename
        try:
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                logger.info(f"Resim indirildi: {file_path}")
                return str(file_path)
            else:
                logger.error(f"Resim indirme başarısız (HTTP {response.status_code})")
                return None
        except Exception as e:
            logger.error(f"Resim indirme hatası: {e}")
            return None

    def check_new_tasks(self) -> list[ReelTask]:
        """
        DM'leri kontrol eder ve yeni Reel paylaşım görevlerini çıkarır.

        Beklenen DM formatı (sırayla):
            1. Video mesajı (zorunlu)
            2. Metin mesajı = caption (zorunlu)
            3. Fotoğraf mesajı = kapak fotoğrafı (opsiyonel)

        Sadece OWNER_USERNAME'den gelen mesajlar işlenir.

        Returns:
            Yeni ReelTask listesi.
        """
        tasks = []

        thread_id = self._find_owner_thread()
        if not thread_id:
            return tasks

        try:
            # Son mesajları al (en yeniler önce gelir)
            messages = self.client.direct_messages(thread_id=thread_id, amount=20)
            # Kronolojik sırala (eski → yeni)
            messages.reverse()

            owner_user_id = self.client.user_id_from_username(Config.OWNER_USERNAME)

            # Mesajları tara ve video + caption eşleştirmesi yap
            i = 0
            while i < len(messages):
                msg = messages[i]

                # Sadece owner'dan gelen mesajları işle
                if msg.user_id != owner_user_id:
                    i += 1
                    continue

                # Zaten işlenmiş mesajı atla
                if str(msg.id) in self.processed_ids:
                    i += 1
                    continue

                # Video mesajı bul
                video_url = self._extract_video_url(msg)
                if not video_url:
                    i += 1
                    continue

                # Video bulundu! Şimdi sonraki mesajlarda caption ve kapak ara
                caption = ""
                cover_url = None
                consumed_indices = [i]  # İşlenecek mesaj indeksleri

                # Sonraki mesajlara bak
                j = i + 1
                while j < len(messages):
                    next_msg = messages[j]
                    if next_msg.user_id != owner_user_id:
                        j += 1
                        continue

                    # Zaten işlenmiş mi?
                    if str(next_msg.id) in self.processed_ids:
                        j += 1
                        continue

                    # Metin mesajı → caption
                    if next_msg.item_type == "text" and next_msg.text and not caption:
                        caption = next_msg.text
                        consumed_indices.append(j)
                        j += 1
                        continue

                    # Fotoğraf mesajı → kapak
                    img_url = self._extract_image_url(next_msg)
                    if img_url and not cover_url:
                        cover_url = img_url
                        consumed_indices.append(j)
                        j += 1
                        continue

                    # Başka bir video geldiyse dur (yeni görev demektir)
                    if self._extract_video_url(next_msg):
                        break

                    j += 1

                # Caption zorunlu — yoksa bu görevi atla (henüz caption gelmemiş olabilir)
                if not caption:
                    logger.info(
                        f"Video mesajı bulundu (ID: {msg.id}) ama henüz caption yok, bekleniyor..."
                    )
                    i += 1
                    continue

                # Video'yu indir
                video_filename = f"reel_{msg.id}.mp4"
                video_path = self._download_video_from_url(video_url, video_filename)
                if not video_path:
                    i += 1
                    continue

                # Kapak fotoğrafını indir (varsa)
                cover_path = None
                if cover_url:
                    cover_filename = f"cover_{msg.id}.jpg"
                    cover_path = self._download_image_from_url(cover_url, cover_filename)

                # Görev oluştur
                task = ReelTask(
                    message_id=str(msg.id),
                    video_url=video_url,
                    video_path=video_path,
                    caption=caption,
                    cover_url=cover_url,
                    cover_path=cover_path,
                    timestamp=str(msg.timestamp),
                )
                tasks.append(task)

                # Tüm ilgili mesajları işlenmiş olarak işaretle
                for idx in consumed_indices:
                    self.mark_processed(str(messages[idx].id))

                logger.info(
                    f"Yeni görev oluşturuldu: video={video_filename}, "
                    f"caption='{caption[:50]}...', kapak={'var' if cover_path else 'yok'}"
                )

                # consumed_indices'ten sonraki mesaja geç
                i = max(consumed_indices) + 1
                continue

            i += 1  # noqa: bu satıra ulaşılmaz ama güvenlik için

        except Exception as e:
            logger.error(f"DM okuma hatası: {e}", exc_info=True)

        return tasks

    def _extract_video_url(self, message) -> str | None:
        """Mesajdan video URL'sini çıkarır."""
        try:
            # Durum 1: media_share (paylaşılmış Reel/post)
            if message.item_type == "media_share" and message.media:
                if hasattr(message.media, "video_versions") and message.media.video_versions:
                    return message.media.video_versions[0].url

            # Durum 2: clip (Reel paylaşımı)
            if message.item_type == "clip" and message.clip:
                media = message.clip.get("clip") if isinstance(message.clip, dict) else message.clip
                if hasattr(media, "video_versions") and media.video_versions:
                    return media.video_versions[0].url

            # Durum 3: raven_media (kaybolan medya)
            if message.item_type == "raven_media" and message.visual_media:
                media = message.visual_media.media
                if media and hasattr(media, "video_versions") and media.video_versions:
                    return media.video_versions[0].url

            # Durum 4: Direkt video gönderimi
            if message.item_type == "video":
                # video_versions veya video attr'u olabilir
                if hasattr(message, "video_versions") and message.video_versions:
                    return message.video_versions[0].url
                if hasattr(message, "media") and message.media:
                    if hasattr(message.media, "video_versions") and message.media.video_versions:
                        return message.media.video_versions[0].url

        except Exception as e:
            logger.debug(f"Video URL çıkarma hatası (msg {message.id}): {e}")

        return None

    def _extract_image_url(self, message) -> str | None:
        """Mesajdan fotoğraf URL'sini çıkarır."""
        try:
            # Direkt fotoğraf gönderimi
            if message.item_type in ("photo", "image"):
                if hasattr(message, "media") and message.media:
                    if hasattr(message.media, "image_versions2"):
                        candidates = message.media.image_versions2.get("candidates", [])
                        if candidates:
                            return candidates[0].get("url")
                    if hasattr(message.media, "thumbnail_url"):
                        return message.media.thumbnail_url

            # raven_media foto
            if message.item_type == "raven_media" and message.visual_media:
                media = message.visual_media.media
                if media and hasattr(media, "image_versions2"):
                    candidates = media.image_versions2.get("candidates", [])
                    if candidates:
                        return candidates[0].get("url")

        except Exception as e:
            logger.debug(f"Resim URL çıkarma hatası (msg {message.id}): {e}")

        return None

    def send_reply(self, thread_id: str, text: str) -> None:
        """Thread'e yanıt mesajı gönderir."""
        try:
            self.client.direct_send(text=text, thread_ids=[thread_id])
            logger.info(f"DM yanıtı gönderildi: {text[:50]}...")
        except Exception as e:
            logger.error(f"DM yanıtı gönderilemedi: {e}")
