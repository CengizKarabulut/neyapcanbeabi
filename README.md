# Telegram ASELS Komut Gönderici

Bu repo yalnızca **ASELS** için Telegram komut otomasyonu çalıştırır.

## Çalışma mimarisi

Üretimde iki GitHub Actions workflow'u vardır:

- `ASELS Live Loop`
- `ASELS Loop Recovery`

Ana gönderimler GitHub cronuna bağlı değildir. `ASELS Live Loop`, `scripts/asels_scheduler.py` içinde Türkiye saatini takip eder. `ASELS Loop Recovery` ise Live Loop kapanır, hata verir, takılır veya eski çalışma koduyla açık kalırsa güncel döngüyü yeniden başlatır.

Telegram gönderimleri **Telethon kullanıcı oturumu** üzerinden gerçek Telegram kullanıcı hesabından yapılır. Böylece `@ucretsizderinlikbot` tarafından uygulanan kanal üyeliği kontrolü kullanıcı hesabı üzerinden çalışır.

## Açılış öncesi teorik fiyat komutu

Pazartesi-Cuma, Türkiye saatiyle 09:40, 09:45, 09:50, 09:55 ve 09:58'de:

```text
/teorik ASELS
```

gönderilir. Açılış öncesi tekrar koruma penceresi 2 dakikadır; böylece 09:55 ve 09:58 komutları birbirini engellemez.

## Gün içi komutlar

Pazartesi-Cuma, Türkiye saatiyle **90 dakikada bir**, **10:05, 11:35, 13:05, 14:35, 16:05 ve 17:35** saatlerinde; ayrıca **17:55'te kapanış öncesi** ve **18:15'te kapanış sonrası** birer ek kontrol:

```text
/akd ASELS
/derinlik ASELS
/kurum
```

Komutlar arasında 10 saniye beklenir. Her komut ayrı ayrı gönderilir. Gönderim hata verirse üç kez denenir; Telegram geçmişindeki yakın tarihli aynı komut kontrol edilerek gereksiz tekrarlar azaltılır.

Scheduler planlanan dakikayı kaçırırsa 6 dakikalık catch-up penceresinde ilgili slotu tamamlamaya çalışır.

## Gün sonu takas

Pazartesi-Cuma, Türkiye saatiyle **19:30'da yalnızca**:

```text
/takas ASELS
```

## Telegram hedefi

ASELS komutları şu Telegram grubuna gönderilir:

```text
@aselsanhissee
```

## Gerekli GitHub Secrets

Repo > Settings > Secrets and variables > Actions bölümünde şu üç secret bulunmalıdır:

```text
TELEGRAM_API_ID
TELEGRAM_API_HASH
TELEGRAM_SESSION
```

`TELEGRAM_SESSION`, bu API değerleriyle yetkilendirilmiş gerçek Telegram kullanıcı hesabının Telethon StringSession değeridir. Secret değerleri kaynak koda yazılmaz ve loglarda gösterilmez.

`TELEGRAM_CHAT_ID` secret olarak tutulmaz; hedef grup scheduler içinde `@aselsanhissee` olarak tanımlıdır.

## Manuel kontrol

GitHub > Actions bölümünde normal durumda:

```text
ASELS Live Loop
ASELS Loop Recovery
```

akışları görülür. `ASELS Live Loop` uzun süre `in_progress` görünür; bu normaldir. Zamanlayıcı bu çalışan job içinde saatleri takip eder.
