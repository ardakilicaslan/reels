# 🎬 Instagram Reels Otomatik Paylaşım Botu

Instagram DM'den video al → otomatik Reels olarak paylaş!

## ✨ Nasıl Çalışıyor?

```
Sen (DM'den video at) → Bot (videoyu alır) → Instagram'a Reels olarak paylaşır → Sana DM'den bildirim atar
```

1. Bot hesabına DM'den **video** at
2. Ardından **açıklamayı** (caption) metin olarak yaz
3. İstersen **kapak fotoğrafı** gönder
4. Bot otomatik olarak Reels paylaşır ve sana DM'den haber verir ✅

## 🚀 Kurulum (5 Dakikada)

### 1. Gereksinimler
- Python 3.10+
- Bir Instagram hesabı (botun çalışacağı hesap)

### 2. Projeyi Kur

```bash
# Projeyi indir
git clone https://github.com/KULLANICI_ADIN/instagram-reels-bot.git
cd instagram-reels-bot

# Sanal ortam oluştur
python -m venv venv
venv\Scripts\activate    # Windows
# source venv/bin/activate  # macOS/Linux

# Bağımlılıkları yükle
pip install -r requirements.txt
```

### 3. Ayarları Gir

```bash
copy .env.example .env
```

`.env` dosyasını düzenle:

```env
# Bot'un çalışacağı Instagram hesabı
INSTAGRAM_USERNAME=bot_hesabi
INSTAGRAM_PASSWORD=bot_sifresi

# Senin kişisel Instagram kullanıcı adın (sadece senden gelen DM'ler işlenir)
OWNER_USERNAME=senin_hesabin

# Kaç saniyede bir DM kontrol etsin
DM_CHECK_INTERVAL=30
```

### 4. Çalıştır!

```bash
python bot.py
```

## 📱 Kullanım

Bot çalışırken:

1. **Bot hesabına** Instagram'dan DM at
2. Önce **video** gönder
3. Sonra **açıklama** yaz (metin mesajı olarak)
4. (İstersen) **kapak fotoğrafı** gönder
5. Bot otomatik algılar, Reels olarak paylaşır ve sana bildirir! 🎉

### Örnek DM Akışı:
```
Sen: [video gönderir]
Sen: Bu harika bir gün! ☀️ #reels #günlük
Sen: [kapak fotoğrafı gönderir]  ← opsiyonel

Bot: ⏳ Reels yükleniyor...
Bot: ✅ Reels paylaşıldı! 🎉
     🔗 https://instagram.com/reel/ABC123/
```

## 🌐 Ücretsiz Hosting (Render.com)

### Adım 1: GitHub'a Yükle
```bash
git init
git add .
git commit -m "initial commit"
git remote add origin https://github.com/KULLANICI/instagram-reels-bot.git
git push -u origin main
```

### Adım 2: Render.com'da Deploy Et
1. [render.com](https://render.com) → GitHub ile kayıt ol
2. **New → Web Service** → GitHub reposunu seç
3. Ayarlar:
   - **Runtime:** Python
   - **Build:** `pip install -r requirements.txt`
   - **Start:** `python bot.py`
4. **Environment Variables** ekle:
   - `INSTAGRAM_USERNAME`
   - `INSTAGRAM_PASSWORD`
   - `OWNER_USERNAME`
   - `DM_CHECK_INTERVAL`
5. Deploy! 🚀

### Uyku Önleme (Opsiyonel)
Render free tier 15dk sonra uyur. Engellemek için:
1. [UptimeRobot](https://uptimerobot.com) → Ücretsiz kayıt
2. Yeni monitor → URL: `https://YOUR-APP.onrender.com`
3. Her 5 dakikada ping atar, bot uyanık kalır

## 📁 Proje Yapısı

```
instagram-reels-bot/
├── bot.py              # Ana bot döngüsü
├── dm_reader.py        # DM okuma & video indirme
├── reels_uploader.py   # Reels yükleme (instagrapi)
├── config.py           # Konfigürasyon
├── requirements.txt    # 3 bağımlılık
├── Procfile            # Render.com
├── render.yaml         # Render.com config
├── .env.example        # Ayar şablonu
└── .gitignore
```

## ⚠️ Önemli Notlar

- **Güvenlik:** Bot sadece `OWNER_USERNAME`'den gelen DM'leri işler
- **Hesap riski:** `instagrapi` resmi olmayan bir API kullanır. Aşırı kullanımda hesap kısıtlanabilir
- **Öneri:** Mümkünse ayrı bir bot hesabı kullan, asıl hesabını değil
- **Video limiti:** 5-90 saniye, dikey (9:16), MP4 formatı önerilir
- **İlk giriş:** İlk çalıştırmada Instagram güvenlik doğrulaması isteyebilir

## 📄 Lisans

MIT License
