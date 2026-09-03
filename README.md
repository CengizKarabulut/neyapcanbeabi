# Telegram ZGYO Komut Gönderici

Bu repo hafta içi Türkiye saatiyle 10:05-18:15 arasında belirli zamanlarda Telegram grubuna kullanıcı hesabı üzerinden şu komutları gönderir:

```text
/akd ZGYO
/derinlik ZGYO
```

## Zamanlama
- 10:05-17:50 arası 15 dakikada bir
- 18:05 normal son tur
- 18:15 özel kapanış turu
- Pazartesi-Cuma

## Gerekli GitHub Secrets
Repo > Settings > Secrets and variables > Actions > New repository secret

Şunları ekle:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
TELEGRAM_CHAT_ID
```

Bu grup için mevcut aday CHAT_ID:

```text
-3740330661
```

## TELEGRAM_SESSION üretme
Bilgisayarda:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_session.py
```

Program API_ID ve API_HASH ister. Ardından Telegram hesabına giriş yaparsın ve oluşan uzun değeri `TELEGRAM_SESSION` secret'ına kaydedersin.

## Test
GitHub'da:

Actions > Telegram ZGYO Commands > Run workflow

İlk canlı testte hedef grubun doğru olduğundan emin ol. `TELEGRAM_SESSION` ve `TELEGRAM_API_HASH` değerlerini asla normal dosyaya yazma.
