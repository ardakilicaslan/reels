# 📖 Instagram Reels 7/24 Bulut Otomasyonu - Eksiksiz Kurulum Rehberi

Bu rehber, bilgisayarın **tamamen kapalıyken bile** telefonundan attığın DM'leri otomatik olarak Reels olarak paylaşan sistemi **0 TL bütçe ile, domain ve sunucu satın almadan** nasıl kuracağını adım adım anlatır.

---

## 📑 İçindekiler
1. [Gereksinimler](#1-gereksinimler)
2. [Adım 1: Facebook Developers (Meta) Ayarları](#adım-1-facebook-developers-meta-ayarları)
3. [Adım 2: Render.com Üzerinde 7/24 N8N Kurulumu](#adım-2-rendercom-üzerinde-724-n8n-kurulumu)
4. [Adım 3: N8N İş Akışını (Workflow) Yükleme](#adım-3-n8n-iş-akışını-workflow-yükleme)
5. [Adım 4: Meta Webhook'u N8N'e Bağlama](#adım-4-meta-webhooku-n8ne-bağlama)
6. [Adım 5: Web Panelini Açma ve Test Etme](#adım-5-web-panelini-açma-ve-test-etme)
7. [7/24 Uykusuz Çalıştırma (Render Keep-Alive)](#724-uykusuz-çalıştırma-render-keep-alive)

---

## 1. Gereksinimler
- Instagram Profesyonel (İşletme veya İçerik Üretici) Hesabı
- Instagram hesabına bağlı bir Facebook Sayfası
- Bir GitHub hesabı (ücretsiz)
- Bir Render.com hesabı (ücretsiz)

---

## Adım 1: Facebook Developers (Meta) Ayarları

1. [developers.facebook.com](https://developers.facebook.com/) adresine git ve giriş yap.
2. Sağ üstten **Uygulama Oluştur (Create App)** butonuna bas.
3. Uygulama Türü: **İşletme (Business)** veya **Diğer** seçeneğini seç.
4. Uygulamana bir isim ver (örn: `ReelsOtomasyonu`) ve oluştur.
5. Sol panelden **Ürünler (Products)** bölümüne git:
   - **Instagram Graph API** $\rightarrow$ Kur
   - **Webhooks** $\rightarrow$ Kur

### 🔑 Test Kullanıcısı Ekleme (App Review / İnceleme Gerekmez!)
1. Sol menüden **Roller (App Roles) $\rightarrow$ Roller** bölümüne tıkla.
2. **Instagram Test Kullanıcıları (Instagram Testers)** bölümünde **Instagram Test Kullanıcıları Ekle** de.
3. Kendi Instagram kullanıcı adını yaz ve ekle.
4. Telefonundan Instagram uygulamasını aç:
   - **Ayarlar ve Gizlilik $\rightarrow$ Uygulama İzinleri $\rightarrow$ Test Davetleri** yolunu izle.
   - Gelen daveti **Kabul Et**.
   *(Artık Meta incelemesi beklemeden kendi hesabında %100 yetkiyle çalışır!)*

---

## Adım 2: Render.com Üzerinde 7/24 N8N Kurulumu

1. Bu proje klasörünü kendi GitHub hesabına yeni bir repo olarak yükle:
   ```bash
   git init
   git add .
   git commit -m "N8N Reels Cloud Setup"
   git remote add origin https://github.com/KULLANICI_ADIN/instagram-reels-bot.git
   git push -u origin main
   ```
2. [render.com](https://render.com/) adresine git ve ücretsiz kayıt ol.
3. Dashboard ekranında **New $\rightarrow$ Web Service** de.
4. GitHub reponu seç.
5. Render ayarları otomatik olarak `Dockerfile` dosyasını algılayacaktır:
   - **Runtime:** `Docker` (FFmpeg otomatik dahil edilir!)
   - **Instance Type:** `Free ($0/month)`
6. **Deploy Web Service** butonuna bas.
7. Birkaç dakika içinde Render sana ücretsiz bir HTTPS linki verecektir:
   `https://senin-servisin.onrender.com`

---

## Adım 3: N8N İş Akışını (Workflow) Yükleme

1. Render'ın verdiği `https://senin-servisin.onrender.com` adresini tarayıcında aç.
2. N8N için ilk yönetici kullanıcı adını ve şifreni belirle.
3. Sol menüden **Workflows $\rightarrow$ Add Workflow $\rightarrow$ Import from File** seçeneğini tıkla.
4. Projedeki [`n8n_reels_workflow.json`](n8n_reels_workflow.json) dosyasını seç.
5. İş akışındaki düğümler otomatik olarak yüklenecektir:
   - **Meta Webhook Trigger**
   - **DM Verisini Ayrıştır**
   - **Videoyu İndir**
   - **FFmpeg ile 1080x1920 HD Düzenle**
   - **Instagram Container Oluştur & Yayınla**
6. Sağ üstten **Active** butonunu açarak iş akışını yayına al.

---

## Adım 4: Meta Webhook'u N8N'e Bağlama

1. Facebook Developers paneline geri dön $\rightarrow$ **Webhooks** sekmesini aç.
2. Ürün olarak **Instagram** seçeneğini seç.
3. **Abonelikleri Düzenle (Edit Subscription)** de:
   - **Callback URL:** `https://senin-servisin.onrender.com/webhook/instagram-dm-webhook`
   - **Verify Token:** N8N iş akışında belirlediğin gizli kelime (veya rastgele bir kelime).
4. Doğrula ve Kaydet dedikten sonra `messages` alanına **Abone Ol (Subscribe)** tıkla.

---

## Adım 5: Web Panelini Açma ve Test Etme

Sistemini takip etmek ve manuel testler yapmak için hazırladığımız paneli açabilirsin:
- Projedeki [`panel/index.html`](panel/index.html) dosyasını çift tıklayarak tarayıcında aç.
- Panel üzerinden:
  - Kurulum aşamalarını kontrol edebilirsin.
  - Render URL'ini girip doğrudan tek tıkla test videosu tetikleyebilirsin.
  - Canlı logları ve kuyruk durumunu izleyebilirsin.

---

## 7/24 Uykusuz Çalıştırma (Render Keep-Alive)

Render.com free tier, 15 dakika istek gelmezse uyku moduna geçer. Uykusuz 7/24 çalışması için:
1. [cron-job.org](https://cron-job.org/) veya [uptimerobot.com](https://uptimerobot.com/) adresine ücretsiz üye ol.
2. Yeni bir monitor oluştur:
   - **URL:** `https://senin-servisin.onrender.com`
   - **Aralık:** 10 dakikada bir (Every 10 minutes)
3. Bu sayede sunucun asla uyumaz, bilgisayarın kapalıyken bile telefonundan attığın DM saniyeler içinde işlenip Reels olarak yayına girer! 🚀
