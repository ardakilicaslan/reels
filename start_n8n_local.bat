@echo off
chcp 65001 > nul
echo ===================================================
echo 🚀 N8N ve Tünel Başlatıcı (Ücretsiz & Domainsiz)
echo ===================================================

echo [1/2] N8N başlatılıyor... (http://localhost:5678)
start cmd /k "npx n8n"

echo [2/2] Meta Webhook için Tünel açılıyor...
echo.
echo NOT: Gelen HTTPS adresini Meta Webhooks Callback URL kısmına yapıştıracaksınız.
echo ===================================================
npx localtunnel --port 5678
pause
