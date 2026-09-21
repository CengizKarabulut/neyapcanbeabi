# Telegram ASELS Komut Gönderici

Bu repo yalnızca **ASELS** için Telegram komut otomasyonu çalıştırır.

## Çalışma mimarisi

Üretimde yalnızca iki GitHub Actions workflow'u vardır:

- `ASELS Live Loop`
- `ASELS Loop Recovery`

Ana gönderimler GitHub `schedule` cronuna bağlı değildir. `ASELS Live Loop`, kendi Python zamanlayıcısı (`scripts/asels_scheduler.py`) içinde Türkiye saatini takip eder.

`ASELS Loop Recovery` ise Live Loop kapanır, hata verir, takılır veya eski çalışma koduyla açık kalırsa bunu tespit eder ve güncel Live Loop'u yeniden başlatır. Cron burada yalnız üçüncü/yedek güvenlik katmanıdır.

Live Loop yaklaşık 4 saatlik bloklar halinde çalışır. Blok normal veya hatalı şekilde bittiğinde `workflow_run` üzerinden Recovery devreye girer ve sonraki sağlıklı bloğu başlatır.

## Açılış öncesi teorik fiyat komutu

Pazartesi-Cuma, Türkiye saatiyle:

```text
09:40
09:45
09:50
09:55
09:58
```

şu komut gönderilir:

```text
/teorik ASELS
```

## Gün içi komutlar

Pazartesi-Cuma, Türkiye saatiyle **10:05'ten başlayarak 15 dakikada bir** 17:50'ye kadar ve ayrıca **18:05 ile 18:15'te**:

```text
/akd ASELS
/derinlik ASELS
/kurum ASELS
```

Komutlar arasında 10 saniye beklenir.

Python scheduler planlanan dakikayı birkaç saniye veya birkaç dakika kaçırsa bile 4 dakikalık catch-up penceresinde turu tamamlamaya çalışır. Telegram gönderiminde hata alınırsa otomatik tekrar deneme yapılır.

## Gün sonu takas

Pazartesi-Cuma, Türkiye saatiyle **19:30'da yalnızca**:

```text
/takas ASELS
```

## Çift gönderim koruması

`src/main.py`, aynı komut yakın zamanda gönderilmişse Telegram geçmişini kontrol ederek tekrarı engeller. Böylece Recovery veya deployment sırasında kısa süreli yeniden başlama olsa bile aynı komutun gereksiz yere yinelenmesi azaltılır.

## Telegram hedefi

ASELS komutları şu Telegram grubuna gönderilir:

```text
@aselsanhissee
```

## Gerekli GitHub Secrets

Repo > Settings > Secrets and variables > Actions bölümünde:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
```

bulunmalıdır.

`TELEGRAM_CHAT_ID` kullanılmaz; ASELS hedefi uygulamada `@aselsanhissee` olarak tanımlıdır.

## TELEGRAM_SESSION üretme

Bilgisayarda:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_session.py
```

Program API_ID ve API_HASH ister. Telegram hesabına giriş yaptıktan sonra oluşan uzun oturum değerini `TELEGRAM_SESSION` secret'ına kaydet.

## Manuel kontrol

GitHub > Actions bölümünde yalnız şu iki akışın görülmesi beklenir:

```text
ASELS Live Loop
ASELS Loop Recovery
```

Normal durumda `ASELS Live Loop` uzun süre `in_progress` görünür. Bu beklenen davranıştır; zamanlayıcı bu çalışan job içinde saatleri takip eder.

Recovery logunda sağlıklı durumda şu tip kayıt görülür:

```text
Healthy ASELS loop: ... status=in_progress
Healthy active/queued ASELS Live Loop count: 1
ASELS Live Loop healthy; no dispatch needed.
```
