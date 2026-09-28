# Telegram ASELS Komut Gönderici

Bu repo yalnızca **ASELS** için Telegram komut otomasyonu çalıştırır.

## Çalışma mimarisi

Üretimde iki GitHub Actions workflow'u vardır:

- `ASELS Live Loop`
- `ASELS Loop Recovery`

Ana gönderimler GitHub cronuna bağlı değildir. `ASELS Live Loop`, `scripts/asels_scheduler.py` içinde Türkiye saatini takip eder. `ASELS Loop Recovery` ise Live Loop kapanır, hata verir, takılır veya eski çalışma koduyla açık kalırsa güncel döngüyü yeniden başlatır.

Telegram gönderimleri artık kişisel kullanıcı oturumu ile değil, BotFather üzerinden oluşturulan botun **Telegram Bot API** erişimiyle yapılır. Bu nedenle `TELEGRAM_SESSION`, `TELEGRAM_API_ID` ve `TELEGRAM_API_HASH` gerekmez.

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

Komutlar arasında 10 saniye beklenir. Her komut ayrı ayrı gönderilir ve hata alırsa o komut üç kez denenir; önceki başarılı komutların tamamı yeniden başlatılmaz.

Scheduler planlanan dakikayı kaçırırsa 6 dakikalık catch-up penceresinde ilgili slotu tamamlamaya çalışır. Aynı çalışan döngü içinde tamamlanan slotlar tekrar gönderilmez.

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

Gönderen bot:

```text
@napcanbeabi_bot
```

## Gerekli GitHub Secret

Repo > Settings > Secrets and variables > Actions bölümünde yalnızca:

```text
TELEGRAM_BOT_TOKEN
```

zorunludur.

Token BotFather tarafından verilen `@napcanbeabi_bot` tokenıdır. Token kaynak koda yazılmaz ve loglarda gösterilmez.

`TELEGRAM_CHAT_ID` secret olarak tutulmaz; hedef grup scheduler içinde `@aselsanhissee` olarak tanımlıdır.

## Manuel kontrol

GitHub > Actions bölümünde normal durumda:

```text
ASELS Live Loop
ASELS Loop Recovery
```

akışları görülür.

`ASELS Live Loop` uzun süre `in_progress` görünür; bu normaldir. Zamanlayıcı bu çalışan job içinde saatleri takip eder.
