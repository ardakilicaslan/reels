"""
Instagram Reels yükleme modülü.

instagrapi kütüphanesi ile doğrudan Instagram'a Reels paylaşır.
Cloudinary veya harici hosting gerekmez.
"""

import logging
from pathlib import Path
from instagrapi import Client

logger = logging.getLogger(__name__)


class ReelsUploader:
    """Instagram'a Reels yükleyen sınıf."""

    def __init__(self, client: Client):
        self.client = client

    def upload_reel(
        self,
        video_path: str,
        caption: str = "",
        thumbnail_path: str | None = None,
    ) -> dict:
        """
        Videoyu Instagram'a Reels (Clip) olarak yükler.

        Args:
            video_path: Video dosyasının yerel yolu (.mp4).
            caption: Gönderi açıklaması (hashtag'ler dahil).
            thumbnail_path: Kapak fotoğrafı dosya yolu (.jpg, opsiyonel).

        Returns:
            dict: {
                "media_id": str,  # Yayınlanan medyanın ID'si
                "code": str,      # Instagram kısa kodu (URL için)
                "url": str,       # Reels URL'i
            }

        Raises:
            Exception: Yükleme başarısız olursa.
        """
        video = Path(video_path)
        if not video.exists():
            raise FileNotFoundError(f"Video dosyası bulunamadı: {video_path}")

        # Yükleme parametreleri
        upload_kwargs = {
            "path": video,
            "caption": caption,
        }

        # Kapak fotoğrafı varsa ekle
        if thumbnail_path:
            thumb = Path(thumbnail_path)
            if thumb.exists():
                upload_kwargs["thumbnail"] = thumb
                logger.info(f"Kapak fotoğrafı eklendi: {thumbnail_path}")
            else:
                logger.warning(f"Kapak fotoğrafı bulunamadı: {thumbnail_path}, atlanıyor")

        logger.info(
            f"Reels yükleniyor: {video_path} "
            f"(caption: '{caption[:50]}...')"
        )

        # Instagram'a yükle
        media = self.client.clip_upload(**upload_kwargs)

        result = {
            "media_id": str(media.pk),
            "code": media.code,
            "url": f"https://www.instagram.com/reel/{media.code}/",
        }

        logger.info(f"✅ Reels başarıyla yüklendi! URL: {result['url']}")
        return result
