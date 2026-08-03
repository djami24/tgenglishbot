# Ingliz tili darslarini Telegram kanaliga avtomatik yuborish

Bu loyiha GitHub Actions yordamida Google Gemini orqali IELTS Speaking lug'ati va
kunlik grammar seriyasini generatsiya qilib, Telegram kanalingizga avtomatik
yuboradi. Har bir post oldidan mavzu nomi yozilgan chiroyli sarlavha-karta
rasmi ham avtomatik yaratilib yuboriladi. **Butunlay bepul** ishlaydi.

Bot FAQAT ikkita turkumda post qiladi (Toshkent vaqti bo'yicha):

- **IELTS Speaking lug'ati** — kuniga 2 marta (09:00 va 19:00), 50 ta
  mavzudan navbatdagi mavzu bo'yicha 10 ta so'z. 50 tasi tugamaguncha
  bironta mavzu takrorlanmaydi.
- **Kunlik grammar seriyasi** — kuniga 5 marta (08:00, 11:00, 14:00, 17:00,
  20:00). Har kuni bitta yangi mavzu tanlanadi va shu kun davomida
  umumiy tushuncha → darak gap → inkor gap → so'roq gap → amaliyot
  tartibida 5 postga bo'linadi. 21 mavzu tugamaguncha takrorlanmaydi.
  Ixtiyoriy `YOUTUBE_API_KEY` berilsa, har kungi mavzuga mos YouTube video
  havolasi ham shu kunning barcha 5 ta postiga qo'shib yuboriladi
  (link kuniga faqat 1 marta qidiriladi va kun davomida takror ishlatiladi).

Har bir post (grammar ham, lug'at ham) yuborilishidan oldin, o'sha mavzu nomi
yozilgan gradient fonli sarlavha-rasm alohida post sifatida avtomatik
yuboriladi. Bu rasm to'liq mahalliy ravishda (Pillow bilan) yaratiladi -
uchun hech qanday qo'shimcha API kalit yoki internet ulanishi shart emas.

## 1-qadam: Telegram bot yaratish

1. Telegram'da [@BotFather](https://t.me/BotFather) ga o'ting.
2. `/newbot` buyrug'ini yuboring, botga nom bering.
3. BotFather sizga **token** beradi (masalan `123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ`) — uni saqlab qo'ying.
4. Botni kanalingizga **admin** qilib qo'shing (kanal sozlamalari → Administrators → botni qidiring va qo'shing).

## 2-qadam: Kanal ID'sini topish

- Agar kanal **public** bo'lsa (username bor, masalan `@mening_kanalim`) — shu username'ni ishlating.
- Agar kanal **private** bo'lsa, ID odatda `-100` bilan boshlanadi. Buni topish uchun:
  - Kanalga biror xabar yuboring va uni [@userinfobot](https://t.me/userinfobot) yoki
    `https://api.telegram.org/bot<TOKEN>/getUpdates` orqali tekshiring.

## 3-qadam: Google Gemini API kalitini olish (bepul)

1. https://aistudio.google.com/apikey manziliga o'ting.
2. Google hisobingiz bilan kiring va **"Create API key"** tugmasini bosing.
3. Chiqqan kalitni nusxalab oling.

> Bepul tarifda kunlik so'rovlar soni cheklangan. Joriy jadvalda kuniga 7 ta post
> yuboriladi (5 grammar + 2 lug'at) — bu bepul limitga bemalol sig'adi.

## 4-qadam (ixtiyoriy): YouTube API kalitini olish

Har kungi grammar mavzusiga mos video linki qo'shilishini istasangiz:

1. https://console.cloud.google.com/apis/library/youtube.googleapis.com manziliga o'ting
   (Google hisobingiz bilan kiring, kerak bo'lsa yangi loyiha yarating).
2. **"Enable"** tugmasini bosib, "YouTube Data API v3" ni yoqing.
3. Chap menyudan **"Credentials" → "Create Credentials" → "API key"** ni tanlang.
4. Chiqqan kalitni nusxalab oling.

> Bu ham bepul: bepul kvota kuniga 10 000 birlik, har bir qidiruv atigi 100 birlik
> sarflaydi va kunlik grammar mavzusi uchun faqat 1 marta qidiriladi — bemalol yetadi.
> Bu qadamni o'tkazib yuborsangiz ham bot ishlayveradi, faqat video linksiz.

## 5-qadam: Loyihani GitHub'ga yuklash

1. GitHub'da yangi **repository** yarating (public yoki private — farqi yo'q).
2. Shu papkadagi barcha fayllarni ("post_lesson.py", "requirements.txt", ".github/" papkasi) o'sha repo'ga yuklang
   (GitHub saytida "Add file → Upload files" orqali ham qilsa bo'ladi).

## 6-qadam: Maxfiy kalitlarni (Secrets) qo'shish

Repo ichida: **Settings → Secrets and variables → Actions → New repository secret**

Quyidagi secret'larni qo'shing:

| Nomi | Qiymati |
|---|---|
| `GEMINI_API_KEY` | 3-qadamda olingan Gemini kaliti |
| `TELEGRAM_BOT_TOKEN` | 1-qadamda olingan bot tokeni |
| `TELEGRAM_CHAT_ID` | 2-qadamda topilgan kanal ID/username |
| `YOUTUBE_API_KEY` | *(ixtiyoriy)* 4-qadamda olingan YouTube API kaliti |

## 7-qadam: Tekshirish

1. Repo'ning **Actions** bo'limiga o'ting.
2. Chap tomondan workflow'ni tanlang ("Ingliz tili postini Telegramga yuborish").
3. **"Run workflow"** tugmasini bosib, qo'lda bir marta ishga tushiring (kerak bo'lsa `category`
   maydonida `grammar` yoki `topic_vocab` ni tanlang).
4. Bir necha soniyadan so'ng kanalingizga post kelishi kerak.

Shundan keyin u avtomatik ravishda yuqoridagi jadval bo'yicha ishlaydi — hech narsa qilish shart emas.

## Vaqtni yoki mavzularni o'zgartirish

- Vaqtni o'zgartirish: `.github/workflows/post_lesson.yml` faylidagi `cron` qatorlarini tahrirlang
  (vaqtlar UTC bo'yicha, Toshkent = UTC+5). Vaqtlarni o'zgartirsangiz, shu fayldagi
  "Turkumni cron vaqtiga qarab aniqlash" qadamidagi `case` blokini ham mos ravishda yangilang.
- Mavzular ro'yxati: `post_lesson.py` faylida `TOPIC_VOCAB_TOPICS` (IELTS Speaking, 50 mavzu) va
  `GRAMMAR_DAILY_TOPICS` (kunlik grammar seriyasi, 21 mavzu) ro'yxatlari bor — istalganiga yangi
  qator qo'shishingiz mumkin.

## Eslatma

- GitHub Actions **public** repo uchun butunlay bepul (cheksiz daqiqa), **private** repo uchun oyiga 2000 daqiqa bepul —
  bu loyiha uchun bu son ancha yetarli (har bir ishga tushish ~10-20 soniya davom etadi).
- Agar workflow ishlamay qolsa, Actions bo'limidagi loglarni tekshiring — odatda xato sababi
  (noto'g'ri token, kanal ID yoki API kalit) shu yerda aniq ko'rinadi.
- **Muhim:** GitHub Actions'ning `schedule` (cron) trigger'i "eng yaxshi urinish" (best-effort)
  asosida ishlaydi — yuklama yuqori bo'lgan paytlarda run bir necha daqiqa kechikishi yoki juda
  kam holatlarda o'tkazib yuborilishi mumkin; bu GitHub'ning o'zi, kod emas. Shuningdek, agar repo
  60 kun davomida umuman commit qilinmasa, GitHub scheduled workflow'larni avtomatik
  **to'xtatib qo'yadi** — shunda Actions bo'limiga kirib workflow'ni qayta yoqish kerak bo'ladi.
