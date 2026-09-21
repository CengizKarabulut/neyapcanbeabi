# Telegram ASELS Komut Gönderici

Bu repo yalnızca **ASELS** için Telegram komut otomasyonu çalıştırır.

## Gün içi komutlar

Pazartesi-Cuma, Türkiye saatiyle 10:05-17:35 arasında her 30 dakikada bir (`:05` ve `:35`) ve ayrıca 18:05'te:

```text
/akd ASELS
/derinlik ASELS
/kurum ASELS
```

Komutlar arasında 10 saniye beklenir.

## Gün sonu takas

Pazartesi-Cuma, Türkiye saatiyle 19:30'da:

```text
/takas ASELS
```

## Telegram hedefi

ASELS komutları şu Telegram grubuna gönderilir:

```text
@aselsanhissee
```

## Gerekli GitHub Secrets

Repo > Settings > Secrets and variables > Actions bölümünde aşağıdaki secret'lar bulunmalıdır:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
```

`TELEGRAM_CHAT_ID` secret'ı bu ASELS-only sürümünde kullanılmaz; hedef workflow içinde `@aselsanhissee` olarak tanımlıdır.

## TELEGRAM_SESSION üretme

Bilgisayarda:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_session.py
```

Program API_ID ve API_HASH ister. Telegram hesabına giriş yaptıktan sonra oluşan uzun oturum değerini `TELEGRAM_SESSION` secret'ına kaydet.

## Manuel test

GitHub > Actions bölümünde:

- `ASELS 30 Minute Commands` > `Run workflow`
- `ASELS End of Day Takas` > `Run workflow`

Gün içi workflow'u piyasa saatleri dışında komut göndermemek için ayrıca saat kontrolü yapar.
