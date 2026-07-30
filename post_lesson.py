"""
Ingliz tili darsini Google Gemini orqali generatsiya qilib,
Telegram kanaliga avtomatik yuboradi.

Kerakli muhit o'zgaruvchilari (GitHub Secrets orqali beriladi):
  GEMINI_API_KEY      - Google AI Studio'dan olingan bepul API kalit
  TELEGRAM_BOT_TOKEN  - BotFather'dan olingan bot tokeni
  TELEGRAM_CHAT_ID    - Kanal ID'si (masalan: @mening_kanalim yoki -1001234567890)
"""

import os
import sys
import random
import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")

# Darslar bir xil bo'lib qolmasligi uchun mavzular ro'yxatidan tasodifiy tanlanadi
TOPICS = [
    "foydali frazaviy fe'llar (phrasal verbs)",
    "kundalik muloqotda ishlatiladigan idiomalar",
    "Present Simple va Present Continuous farqi",
    "o'tgan zamon (Past Simple) qoidalari",
    "kelasi zamon shakllari (will / going to)",
    "sinonim so'zlar va ularning farqi",
    "biznes ingliz tilida foydali iboralar",
    "sayohat paytida kerak bo'ladigan iboralar",
    "eng ko'p uchraydigan grammatik xatolar",
    "modal fe'llar (can, could, must, should)",
    "ingliz tilida taqqoslash darajalari (comparatives/superlatives)",
    "kundalik hayotda ishlatiladigan qisqartmalar (contractions)",
    "prepozitsiyalar (in, on, at) qo'llanilishi",
    "ingliz tilida savol berish qoidalari",
    "vocabulary: ish joyida ishlatiladigan so'zlar",
]

PROMPT_TEMPLATE = """Sen tajribali ingliz tili o'qituvchisisan. Telegram kanali uchun
qisqa va foydali ingliz tili darsi tayyorla. Mavzu: {topic}.

MUHIM: Javobda HECH QANDAY HTML yoki Markdown belgisi ishlatma (masalan <b>, <i>, **, __, #
kabi belgilar butunlay taqiqlangan). Faqat oddiy matn, emoji va qator ko'chirish (enter)
dan foydalan.

Format:
1. Qiziqarli sarlavha (emoji bilan, hech qanday teg yoki yulduzchasiz)
2. Qisqacha tushuntirish (o'zbek tilida, 2-4 gap)
3. Kamida 3 ta misol jumla (ingliz tili + o'zbekcha tarjimasi)
4. Oxirida qisqa maslahat yoki eslatma

Javobni FAQAT tayyor post matni sifatida qaytar, boshqa hech qanday izoh qo'shma.
Umumiy uzunlik 600-900 belgidan oshmasin."""


def generate_lesson() -> str:
    topic = random.choice(TOPICS)
    prompt = PROMPT_TEMPLATE.format(topic=topic)

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 1024,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    try:
        candidate = data["candidates"][0]
        finish_reason = candidate.get("finishReason")
        if finish_reason and finish_reason not in ("STOP",):
            print(f"Ogohlantirish: finishReason={finish_reason} (matn to'liq bo'lmasligi mumkin)")
        return candidate["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini javobi kutilmagan formatda: {data}") from e


def send_to_telegram(text: str) -> None:
    # Ehtiyot chorasi: agar model baribir < yoki > belgi qo'shib qo'ysa,
    # ularni olib tashlaymiz, shunda Telegram hech qachon uni teg deb
    # o'ylab, matnni kesib tashlamaydi.
    safe_text = text.replace("<", "").replace(">", "")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": safe_text,
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga yuborishda xato: {result}")


def main():
    try:
        lesson = generate_lesson()
        print("Yaratilgan dars:\n", lesson)
        send_to_telegram(lesson)
        print("Muvaffaqiyatli yuborildi!")
    except Exception as e:
        print(f"XATOLIK: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
