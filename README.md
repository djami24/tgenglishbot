# Ingliz tili darslarini Telegram kanaliga avtomatik yuborish

Bu loyiha GitHub Actions yordamida **kuniga 3 marta** (07:00, 14:00, 20:00 Toshkent vaqti bilan)
Google Gemini orqali qisqa ingliz tili darsini generatsiya qilib, Telegram kanalingizga
avtomatik yuboradi. **Butunlay bepul** ishlaydi.

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

> Bepul tarifda kunlik so'rovlar soni cheklangan, lekin kuniga 3 ta post uchun bu yetarlicha ko'p zaxira bilan yetadi.

## 4-qadam: Loyihani GitHub'ga yuklash

1. GitHub'da yangi **repository** yarating (public yoki private — farqi yo'q).
2. Shu papkadagi barcha fayllarni ("post_lesson.py", "requirements.txt", ".github/" papkasi) o'sha repo'ga yuklang
   (GitHub saytida "Add file → Upload files" orqali ham qilsa bo'ladi).

## 5-qadam: Maxfiy kalitlarni (Secrets) qo'shish

Repo ichida: **Settings → Secrets and variables → Actions → New repository secret**

Quyidagi 3 ta secret'ni qo'shing:

| Nomi | Qiymati |
|---|---|
| `GEMINI_API_KEY` | 3-qadamda olingan Gemini kaliti |
| `TELEGRAM_BOT_TOKEN` | 1-qadamda olingan bot tokeni |
| `TELEGRAM_CHAT_ID` | 2-qadamda topilgan kanal ID/username |

## 6-qadam: Tekshirish

1. Repo'ning **Actions** bo'limiga o'ting.
2. Chap tomondan workflow'ni tanlang ("Ingliz tili darsini Telegramga yuborish").
3. **"Run workflow"** tugmasini bosib, qo'lda bir marta ishga tushiring.
4. Bir necha soniyadan so'ng kanalingizga dars posti kelishi kerak.

Shundan keyin u avtomatik ravishda har kuni belgilangan 3 vaqtda ishlaydi — hech narsa qilish shart emas.

## Vaqtni yoki mavzularni o'zgartirish

- Vaqtni o'zgartirish: `.github/workflows/post_lesson.yml` faylidagi `cron` qatorlarini tahrirlang
  (vaqtlar UTC bo'yicha, Toshkent = UTC+5).
- Mavzular ro'yxati: `post_lesson.py` faylidagi `TOPICS` ro'yxatiga istalgancha yangi mavzu qo'shishingiz mumkin.

## Eslatma

- GitHub Actions **public** repo uchun butunlay bepul (cheksiz daqiqa), **private** repo uchun oyiga 2000 daqiqa bepul —
  bu loyiha uchun bu son ancha yetarli (har bir ishga tushish ~10-20 soniya davom etadi).
- Agar workflow ishlamay qolsa, Actions bo'limidagi loglarni tekshiring — odatda xato sababi
  (noto'g'ri token, kanal ID yoki API kalit) shu yerda aniq ko'rinadi.
