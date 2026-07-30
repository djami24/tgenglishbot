"""
Ingliz tili (General English / IELTS General) postini Google Gemini orqali
generatsiya qilib, Telegram kanaliga avtomatik yuboradi.

Kuniga 5 marta, har doim quyidagi tartibda ishlaydi:
  1) Grammar   2) Lug'at (vocabulary)   3) Qiziqarli faktlar
  4) Grammar   5) Tip (maslahat)

Tartib workflow'dagi cron vaqtiga bog'liq (har bir vaqt o'zining
turkumiga mos keladi), shuning uchun run'lar orasida holat saqlash
shart emas.

Kerakli muhit o'zgaruvchilari (GitHub Secrets orqali beriladi):
  GEMINI_API_KEY      - Google AI Studio'dan olingan bepul API kalit
  TELEGRAM_BOT_TOKEN  - BotFather'dan olingan bot tokeni
  TELEGRAM_CHAT_ID    - Kanal ID'si (masalan: @mening_kanalim yoki -1001234567890)
"""

import html
import os
import sys
import random
from datetime import datetime, timezone

import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
CHANNEL_LINK = "https://t.me/djami_teacher"

# ---------------------------------------------------------------------------
# Kunlik aylanish tartibi: grammar -> lugat -> fakt -> grammar -> tip
# Workflow'dagi cron vaqtlari (UTC soat) shu tartibga mos qilib sozlangan:
#   02:00 -> grammar | 06:00 -> vocab | 09:00 -> fact | 12:00 -> grammar | 15:00 -> tip
# ---------------------------------------------------------------------------
SCHEDULE_BY_HOUR = {
    2: "grammar",
    6: "vocab",
    9: "fact",
    12: "grammar",
    15: "tip",
}
DAILY_ORDER = ["grammar", "vocab", "fact", "grammar", "tip"]


def pick_category() -> str:
    override = os.environ.get("POST_CATEGORY")
    if override:
        return override
    hour = datetime.now(timezone.utc).hour
    # Eng yaqin belgilangan soatni topamiz (workflow_dispatch orqali qo'lda
    # ishga tushirilganda soat aniq mos kelmasligi mumkin)
    closest_hour = min(SCHEDULE_BY_HOUR, key=lambda h: abs(h - hour))
    return SCHEDULE_BY_HOUR[closest_hour]


GRAMMAR_TOPICS = [
    "foydali frazaviy fe'llar (phrasal verbs)",
    "Present Simple va Present Continuous farqi",
    "o'tgan zamon (Past Simple) qoidalari",
    "kelasi zamon shakllari (will / going to)",
    "modal fe'llar (can, could, must, should)",
    "ingliz tilida taqqoslash darajalari (comparatives/superlatives)",
    "kundalik hayotda ishlatiladigan qisqartmalar (contractions)",
    "prepozitsiyalar (in, on, at) qo'llanilishi",
    "ingliz tilida savol berish qoidalari",
    "Present Perfect va Past Simple farqi",
    "artikllar (a, an, the) qo'llanilishi",
    "ingliz tilida shart gaplar (conditionals)",
]

VOCAB_TOPICS = [
    "kundalik muloqotda ishlatiladigan idiomalar",
    "sinonim so'zlar va ularning farqi",
    "biznes ingliz tilida foydali iboralar",
    "sayohat paytida kerak bo'ladigan iboralar",
    "ish joyida ishlatiladigan so'zlar",
    "his-tuyg'ularni ifodalovchi so'zlar",
    "restoran va ovqatlanish bilan bog'liq lug'at",
    "sog'liqni saqlash bilan bog'liq lug'at",
    "texnologiya va internet bilan bog'liq so'zlar",
    "kundalik hayotdagi phrasal verb'lar",
]

# Faktlar va tiplar endi faqat ingliz tili / IELTS General English mavzusida
FACT_TOPICS = [
    "ingliz tili tarixi haqida qiziqarli fakt",
    "ingliz tilidagi eng qiziq so'zlar yoki iboralar",
    "IELTS General Training imtihoni haqida foydali fakt",
    "ingliz tilidagi eng qisqa yoki eng uzun so'zlar",
    "ingliz tilida ko'p ma'noli so'zlar haqida qiziqarli fakt",
    "IELTS Writing Task 1 (letter) haqida qiziqarli fakt",
    "IELTS Speaking qismi haqida qiziqarli fakt",
    "ingliz tili va boshqa tillar orasidagi qiziq o'xshashlik yoki farq",
]

TIP_TOPICS = [
    "yangi so'zlarni tezroq yodlash usuli",
    "IELTS Listening qismida ball oshirish maslahati",
    "IELTS Speaking paytida ikkilanmaslik uchun maslahat",
    "IELTS Reading qismida vaqtni to'g'ri taqsimlash maslahati",
    "IELTS Writing Task 1 uchun foydali maslahat",
    "har kuni ingliz tilida o'qish odatini shakllantirish",
    "grammatik xatolarni kamaytirish maslahati",
    "ingliz tilida fikrlashni o'rganish maslahati",
]

CATEGORY_INFO = {
    "grammar": {
        "topics": GRAMMAR_TOPICS,
        "instruction": """Bu GRAMMAR (grammatika) darsi. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Qisqacha tushuntirish (o'zbek tilida, 2-4 gap)
3. Kamida 3 ta misol jumla (ingliz tili + o'zbekcha tarjimasi)
4. Oxirida qisqa maslahat yoki eslatma""",
    },
    "vocab": {
        "topics": VOCAB_TOPICS,
        "instruction": """Bu LUG'AT (vocabulary) posti. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Qisqacha kirish (o'zbek tilida, 1-2 gap)
3. Kamida 5 ta foydali so'z/ibora, har biri uchun: ingliz tilida so'z/ibora,
   o'zbekcha ma'nosi, va bitta misol jumla
4. Oxirida qisqa maslahat""",
    },
    "fact": {
        "topics": FACT_TOPICS,
        "instruction": """Bu ingliz tili yoki IELTS General English haqida QIZIQARLI FAKT
posti (mavzu boshqa umumiy bilimlarga emas, faqat ingliz tili/IELTS'ga oid bo'lsin). Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Faktning o'zi (o'zbek tilida, 3-5 gap, qiziqarli va tushunarli qilib yoz)
3. Agar mos bo'lsa, faktga bog'liq 1-2 ta ingliz tilidagi misol/so'z
4. Oxirida qisqa xulosa yoki qiziqarli savol""",
    },
    "tip": {
        "topics": TIP_TOPICS,
        "instruction": """Bu ingliz tilini o'rganish yoki IELTS General English'ga tayyorlanish
bo'yicha TIP (maslahat) posti. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli qilib yoz)
3. Kamida bitta amaliy misol yoki qadam
4. Oxirida qisqa rag'batlantiruvchi jumla""",
    },
}

PROMPT_TEMPLATE = """Sen tajribali ingliz tili o'qituvchisisan. Telegram kanali uchun
qisqa va foydali post tayyorla. Mavzu: {topic}.

MUHIM: Javobda HECH QANDAY HTML yoki Markdown belgisi ishlatma (masalan <b>, <i>, **, __, #
kabi belgilar butunlay taqiqlangan). Faqat oddiy matn, emoji va qator ko'chirish (enter)
dan foydalan.

MUHIM: Javobning birinchi qatori albatta postning SARLAVHASI bo'lsin (emoji bilan),
ikkinchi qatordan boshlab qolgan matn kelsin.

{instruction}

Javobni FAQAT tayyor post matni sifatida qaytar, boshqa hech qanday izoh qo'shma.
Umumiy uzunlik 600-1000 belgidan oshmasin."""


def generate_post() -> str:
    category = pick_category()
    info = CATEGORY_INFO[category]
    topic = random.choice(info["topics"])
    prompt = PROMPT_TEMPLATE.format(topic=topic, instruction=info["instruction"])

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.9,
            "maxOutputTokens": 2048,
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
        text = candidate["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini javobi kutilmagan formatda: {data}") from e

    return text


def build_html_message(raw_text: str) -> str:
    """Sarlavhani (birinchi qator) qalin qilib, qolgan matnni xavfsiz
    HTML formatga o'giradi. Model matnida tasodifan < yoki > belgisi
    chiqib qolsa ham, html.escape orqali bu Telegram teglariga
    aralashib ketmaydi."""
    lines = raw_text.split("\n", 1)
    title = lines[0].strip()
    rest = lines[1] if len(lines) > 1 else ""

    escaped_title = html.escape(title)
    escaped_rest = html.escape(rest)

    body = f"<b>{escaped_title}</b>\n{escaped_rest}"
    body += "\n\nShare\n📢 @djami_teacher"
    body += "\n\n<i>AI</i>"
    return body


def send_to_telegram(text: str) -> None:
    message = build_html_message(text)

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    resp = requests.post(url, json=payload, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga yuborishda xato: {result}")


def main():
    try:
        post = generate_post()
        print("Yaratilgan post:\n", post)
        send_to_telegram(post)
        print("Muvaffaqiyatli yuborildi!")
    except Exception as e:
        print(f"XATOLIK: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
