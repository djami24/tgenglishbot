# Ingliz tili darslarini Telegram kanaliga avtomatik yuborish

Bu loyiha GitHub Actions yordamida Google Gemini orqali qisqa ingliz tili darsini
generatsiya qilib, Telegram kanalingizga avtomatik yuboradi. **Butunlay bepul** ishlaydi.

Joriy jadval (Toshkent vaqti bo'yicha):

- **Umumiy aylanma** — har 30 daqiqada (grammar, vocab, fact, ielts_tips,
  beginner_grammar, synonyms, listening_tips, reading_tips, cefr_tips,
  motivational_quotes, grammar_tests navbat bilan).
- **IELTS Speaking lug'ati** — kuniga 2 marta (09:00 va 19:00), 50 ta
  mavzudan navbatdagi mavzu bo'yicha 10 ta so'z.
- **Kunlik grammar seriyasi** — kuniga 5 marta (08:00, 11:00, 14:00, 17:00,
  20:00), bitta mavzuni umumiy tushuncha → darak → inkor → so'roq →
  amaliyot tartibida 5 postga bo'lib beradi.

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

> Bepul tarifda kunlik so'rovlar soni cheklangan. Joriy jadvalda kuniga ~55 ta post
> yuboriladi (48 aylanma + 5 grammar + 2 lug'at); agar Gemini limitiga urilib
> qolsangiz, `.github/workflows/post_lesson.yml` dagi `cron` qatorlarini
> kamaytiring.

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

Shundan keyin u avtomatik ravishda yuqoridagi jadval bo'yicha ishlaydi — hech narsa qilish shart emas.

## Vaqtni yoki mavzularni o'zgartirish

- Vaqtni o'zgartirish: `.github/workflows/post_lesson.yml` faylidagi `cron` qatorlarini tahrirlang
  (vaqtlar UTC bo'yicha, Toshkent = UTC+5). Lug'at/grammar cron vaqtlarini o'zgartirsangiz, shu
  fayldagi "Turkumni cron vaqtiga qarab aniqlash" qadamidagi `case` bloklarini ham mos ravishda
  yangilang.
- Mavzular ro'yxati: `post_lesson.py` faylida har turkum uchun alohida ro'yxat bor —
  `TOPIC_VOCAB_TOPICS` (IELTS Speaking 50 mavzu), `GRAMMAR_DAILY_TOPICS` (kunlik grammar
  seriyasi, 21 mavzu), va boshqa turkumlar uchun `*_TOPICS` ro'yxatlari. Istalganiga yangi
  qator qo'shishingiz mumkin.

## Eslatma

- GitHub Actions **public** repo uchun butunlay bepul (cheksiz daqiqa), **private** repo uchun oyiga 2000 daqiqa bepul —
  bu loyiha uchun bu son ancha yetarli (har bir ishga tushish ~10-20 soniya davom etadi).
- Agar workflow ishlamay qolsa, Actions bo'limidagi loglarni tekshiring — odatda xato sababi
  (noto'g'ri token, kanal ID yoki API kalit) shu yerda aniq ko'rinadi.
- **Muhim:** GitHub Actions'ning `schedule` (cron) trigger'i "eng yaxshi urinish" (best-effort)
  asosida ishlaydi — yuklama yuqori bo'lgan paytlarda run bir necha daqiqa (kamdan-kam holda
  ko'proq) kechikishi yoki juda kam holatlarda o'tkazib yuborilishi mumkin; bu GitHub'ning o'zi,
  kod emas. Shuningdek, agar repo 60 kun davomida umuman commit qilinmasa, GitHub scheduled
  workflow'larni avtomatik **to'xtatib qo'yadi** — shunda Actions bo'limiga kirib workflow'ni
  qayta yoqish (re-enable) kerak bo'ladi.
