"""
Konfigürasyon yönetimi.
Tüm ortam değişkenlerini merkezi olarak yönetir.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Uygulama konfigürasyon sınıfı."""

    # Instagram Hesap Bilgileri
    INSTAGRAM_USERNAME: str = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD: str = os.getenv("INSTAGRAM_PASSWORD", "")

    # Bot'a DM atan kullanıcının Instagram kullanıcı adı (senin hesabın)
    # Sadece bu kullanıcıdan gelen DM'ler işlenir (güvenlik)
    OWNER_USERNAME: str = os.getenv("OWNER_USERNAME", "")

    # DM kontrol aralığı (saniye)
    DM_CHECK_INTERVAL: int = int(os.getenv("DM_CHECK_INTERVAL", "30"))

    # Dosya yolları
    SESSION_FILE: str = os.getenv("SESSION_FILE", "session.json")
    DOWNLOAD_DIR: str = os.getenv("DOWNLOAD_DIR", "downloads")
    PROCESSED_FILE: str = os.getenv("PROCESSED_FILE", "processed_messages.json")

    # Instagram video gereksinimleri
    MAX_VIDEO_DURATION_SEC: int = 90
    MIN_VIDEO_DURATION_SEC: int = 5

    # Render.com - health check için port
    PORT: int = int(os.getenv("PORT", "10000"))

    @classmethod
    def validate(cls) -> list[str]:
        """Gerekli konfigürasyonların ayarlanıp ayarlanmadığını kontrol eder."""
        errors = []
        if not cls.INSTAGRAM_USERNAME:
            errors.append("INSTAGRAM_USERNAME ayarlanmamış")
        if not cls.INSTAGRAM_PASSWORD:
            errors.append("INSTAGRAM_PASSWORD ayarlanmamış")
        if not cls.OWNER_USERNAME:
            errors.append("OWNER_USERNAME ayarlanmamış")
        return errors
