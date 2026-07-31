"""
Ingliz tili (General English / IELTS General) postini Google Gemini orqali
generatsiya qilib, Telegram kanaliga avtomatik yuboradi.

Har kuni 09:00 dan 22:00 gacha (Toshkent vaqti), har YARIM SOATDA 1 marta,
jami 27 marta post yuboradi. Turkumlar CATEGORY_ORDER ro'yxatidagi tartibda
ketma-ket aylanib turadi (kunlar chegarasiga bog'liq emas, doim davom etadi):

  1) Grammar              8)  Listening tips
  2) Lug'at (Vocabulary)  9)  Reading tips
  3) Ingliz tiliga oid    10) CEFR tips
     fakt                 11) Motivational quotes
  4) Advanced grammar     12) Grammar tests
  5) IELTS tips           13) Mavzuga oid lug'atlar
  6) Grammar for
     beginners
  7) 10 synonyms

Joriy holat (qaysi turkum navbati va har turkumda qaysi mavzular
ishlatilgani) used_topics.json faylida saqlanadi. Workflow har run'dan
keyin bu faylni repoga commit qiladi, shuning uchun tartib va
takrorlanmaslik run'lar orasida buzilmaydi.

Kerakli muhit o'zgaruvchilari (GitHub Secrets orqali beriladi):
  GEMINI_API_KEY      - Google AI Studio'dan olingan bepul API kalit
  TELEGRAM_BOT_TOKEN  - BotFather'dan olingan bot tokeni
  TELEGRAM_CHAT_ID    - Kanal ID'si (masalan: @mening_kanalim yoki -1001234567890)
"""

import html
import json
import os
import sys
import random

import requests

GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
CHANNEL_LINK = "https://t.me/djami_teacher"

# ---------------------------------------------------------------------------
# Holatni saqlash: qaysi turkum navbati (category_index) va har bir turkumda
# qaysi mavzular allaqachon ishlatilgani (topics). Workflow bu faylni har
# run'dan keyin repoga commit qiladi.
# ---------------------------------------------------------------------------
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "used_topics.json")


def _load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("category_index", 0)
    data.setdefault("topics", {})
    return data


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Turkumlar tartibi - foydalanuvchi belgilagan ketma-ketlik. Har run'da
# navbatdagi turkum tanlanadi va ro'yxat oxiriga yetgach boshidan davom etadi.
# ---------------------------------------------------------------------------
CATEGORY_ORDER = [
    "grammar",
    "vocab",
    "fact",
    "advanced_grammar",
    "ielts_tips",
    "beginner_grammar",
    "synonyms",
    "listening_tips",
    "reading_tips",
    "cefr_tips",
    "motivational_quotes",
    "grammar_tests",
    "topic_vocab",
]


def pick_category(state: dict) -> str:
    override = os.environ.get("POST_CATEGORY")
    if override:
        return override
    idx = state["category_index"] % len(CATEGORY_ORDER)
    return CATEGORY_ORDER[idx]


def advance_category_index(state: dict) -> None:
    # Qo'lda POST_CATEGORY berilganda ham navbat davom etaversin (ketma-ketlik
    # buzilmasin), shuning uchun override bo'lsa ham indexni oshiramiz.
    state["category_index"] = (state["category_index"] + 1) % len(CATEGORY_ORDER)


def choose_topic(state: dict, category: str, topics: list) -> str:
    """Shu turkum uchun hali ishlatilmagan mavzuni tanlaydi. Barcha mavzular
    bir marta ishlatib bo'lingach, ro'yxat qaytadan boshidan boshlanadi
    (lekin darhol oldingi mavzu bilan bir xil bo'lmaydi, agar boshqa variant
    mavjud bo'lsa)."""
    used = state["topics"].get(category, [])

    available = [t for t in topics if t not in used]
    if not available:
        last_used = used[-1] if used else None
        available = [t for t in topics if t != last_used] or list(topics)
        used = []

    topic = random.choice(available)
    used.append(topic)
    state["topics"][category] = used
    return topic


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

ADVANCED_GRAMMAR_TOPICS = [
    "shart gaplarning aralash turlari (mixed conditionals)",
    "subjunctive mood (istak va taklif gaplari)",
    "inversion (urg'u uchun teskari so'z tartibi)",
    "cleft sentences (it is / what... urg'u qurilmalari)",
    "passive voice'ning murakkab holatlari",
    "reported speech (ko'chirma nutqni o'zgartirish)",
    "participle clauses (ing/ed qo'shimchali qisqartirilgan gaplar)",
    "modal fe'llarning o'tgan zamon shakllari (could have, should have, must have)",
    "relative clauses (defining va non-defining)",
    "future perfect va future continuous farqi",
    "causative constructions (have/get something done)",
]

IELTS_TIPS_TOPICS = [
    "IELTS General Training haqida umumiy strategiya",
    "IELTS imtihoniga ruhiy tayyorgarlik",
    "IELTS Writing Task 2 uchun maslahat",
    "IELTS Speaking Part 2 uchun maslahat",
    "IELTS imtihonida vaqtni to'g'ri boshqarish",
    "IELTS band ballarini oshirish uchun umumiy maslahat",
    "IELTS imtihonida ko'p uchraydigan xatolar",
    "IELTS Writing uchun linking words'dan foydalanish",
]

BEGINNER_GRAMMAR_TOPICS = [
    "to be fe'li (am / is / are)",
    "shaxs olmoshlari (I, you, he, she...)",
    "ko'plik son qoidalari",
    "oddiy hozirgi zamon (Present Simple) asoslari",
    "there is / there are qurilmasi",
    "oddiy savol va inkor gaplar tuzish",
    "sonlar: sanoq son va tartib son",
    "boshlang'ich daraja uchun asosiy prepozitsiyalar",
]

SYNONYMS_TOPICS = [
    "\"good\" so'ziga sinonimlar",
    "\"bad\" so'ziga sinonimlar",
    "\"happy\" so'ziga sinonimlar",
    "\"sad\" so'ziga sinonimlar",
    "\"big\" so'ziga sinonimlar",
    "\"small\" so'ziga sinonimlar",
    "\"beautiful\" so'ziga sinonimlar",
    "\"important\" so'ziga sinonimlar",
    "\"difficult\" so'ziga sinonimlar",
    "\"say\" fe'liga sinonimlar",
    "\"look\" fe'liga sinonimlar",
    "\"smart\" so'ziga sinonimlar",
]

LISTENING_TIPS_TOPICS = [
    "IELTS Listening'da raqamlarni to'g'ri yozib olish",
    "listening paytida kalit so'zlarni aniqlash",
    "listening qismida distractorlarga aldanmaslik",
    "native speaker nutqini tushunish mashqi",
    "listening ko'nikmasi uchun kundalik mashq rejasi",
    "podkastlar orqali listening'ni oshirish",
]

READING_TIPS_TOPICS = [
    "skimming va scanning texnikalari",
    "IELTS Reading'da vaqtni to'g'ri taqsimlash",
    "noma'lum so'zlarni kontekstdan topish",
    "True / False / Not Given savollariga strategiya",
    "matnni tez va to'g'ri tushunish usullari",
]

CEFR_TIPS_TOPICS = [
    "A1 darajadan A2 ga o'tish uchun maslahat",
    "B1 darajani mustahkamlash yo'llari",
    "B2 darajaga yetish uchun strategiya",
    "C1 darajasida erkin gapirish maslahati",
    "o'z CEFR darajangizni aniqlash usullari",
    "har bir CEFR darajasida qaysi ko'nikmalarga e'tibor berish kerak",
]

MOTIVATIONAL_TOPICS = [
    "ingliz tilini o'rganishda motivatsiyani yo'qotmaslik",
    "kichik qadamlar bilan katta natijalarga erishish",
    "til o'rganishda intizom va izchillik",
    "xato qilishdan qo'rqmaslik kerakligi",
    "har kungi kichik harakatlarning kuchi",
    "o'z-o'zini rag'batlantirish usullari",
]

GRAMMAR_TESTS_TOPICS = [
    "Present Simple va Present Continuous bo'yicha test",
    "Past Simple bo'yicha test",
    "modal fe'llar bo'yicha test",
    "prepozitsiyalar bo'yicha test",
    "artikllar (a, an, the) bo'yicha test",
    "comparatives/superlatives bo'yicha test",
    "Present Perfect bo'yicha test",
]

TOPIC_VOCAB_TOPICS = [
    "oila va qarindoshlar mavzusidagi lug'at",
    "ob-havo mavzusidagi lug'at",
    "sport mavzusidagi lug'at",
    "transport mavzusidagi lug'at",
    "kiyim-kechak mavzusidagi lug'at",
    "uy va mebel mavzusidagi lug'at",
    "tabiat va atrof-muhit mavzusidagi lug'at",
    "bank va moliya mavzusidagi lug'at",
    "ta'lim mavzusidagi lug'at",
    "sog'liqni saqlash mavzusidagi lug'at",
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
    "advanced_grammar": {
        "topics": ADVANCED_GRAMMAR_TOPICS,
        "instruction": """Bu ADVANCED GRAMMAR (yuqori daraja grammatikasi, B2-C1) darsi.
Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "Advanced" so'zi yoki B2/C1
   belgisi bo'lishi mumkin
2. Qisqacha tushuntirish (o'zbek tilida, 3-5 gap), yuqori darajaga mos
   chuqurroq tushuntirish
3. Kamida 3 ta murakkab misol jumla (ingliz tili + o'zbekcha tarjimasi)
4. Oxirida ushbu qoidada ko'p uchraydigan xato haqida ogohlantirish""",
    },
    "ielts_tips": {
        "topics": IELTS_TIPS_TOPICS,
        "instruction": """Bu umumiy IELTS TIPS (IELTS bo'yicha maslahat) posti. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli qilib yoz)
3. Kamida bitta amaliy misol yoki qadam
4. Oxirida qisqa rag'batlantiruvchi jumla""",
    },
    "beginner_grammar": {
        "topics": BEGINNER_GRAMMAR_TOPICS,
        "instruction": """Bu GRAMMAR FOR BEGINNERS (boshlang'ich daraja, A1-A2) darsi.
Format:
1. Qiziqarli va sodda sarlavha (emoji bilan)
2. Juda sodda va tushunarli tushuntirish (o'zbek tilida, 2-3 gap, murakkab
   grammatik atamalardan qochib, sodda tilda tushuntir)
3. Kamida 3 ta oddiy misol jumla (ingliz tili + o'zbekcha tarjimasi)
4. Oxirida qisqa va rag'batlantiruvchi maslahat""",
    },
    "synonyms": {
        "topics": SYNONYMS_TOPICS,
        "instruction": """Bu "10 SYNONYMS" posti - berilgan so'zga 10 ta sinonim taqdim et.
Format:
1. Qiziqarli sarlavha (emoji bilan), asosiy so'zni ko'rsating
2. Qisqacha kirish (o'zbek tilida, 1 gap)
3. Aynan 10 ta sinonim so'z/ibora ro'yxati, har biri uchun qisqa o'zbekcha
   ma'no farqi (nuance) va agar zarur bo'lsa qaysi holatda ishlatilishi
4. Oxirida 1-2 ta sinonimdan foydalangan misol jumla""",
    },
    "listening_tips": {
        "topics": LISTENING_TIPS_TOPICS,
        "instruction": """Bu LISTENING TIPS (tinglab tushunish bo'yicha maslahat) posti.
Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli)
3. Kamida bitta aniq mashq yoki amaliy qadam
4. Oxirida qisqa rag'batlantiruvchi jumla""",
    },
    "reading_tips": {
        "topics": READING_TIPS_TOPICS,
        "instruction": """Bu READING TIPS (o'qib tushunish bo'yicha maslahat) posti. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap, amaliy va tushunarli)
3. Kamida bitta aniq mashq yoki amaliy qadam
4. Oxirida qisqa rag'batlantiruvchi jumla""",
    },
    "cefr_tips": {
        "topics": CEFR_TIPS_TOPICS,
        "instruction": """Bu CEFR TIPS (CEFR darajalari - A1/A2/B1/B2/C1/C2 - bo'yicha
maslahat) posti. Format:
1. Qiziqarli sarlavha (emoji bilan), kerak bo'lsa daraja belgisini kiriting
2. Maslahatning o'zi (o'zbek tilida, 3-5 gap)
3. Ushbu darajada e'tibor berish kerak bo'lgan 2-3 ta aniq ko'nikma yoki
   qadam
4. Oxirida qisqa rag'batlantiruvchi jumla""",
    },
    "motivational_quotes": {
        "topics": MOTIVATIONAL_TOPICS,
        "instruction": """Bu MOTIVATIONAL QUOTE (rag'batlantiruvchi original iqtibos) posti.
Haqiqiy odamlarga tegishli mashhur iqtiboslarni AYNAN keltirma - buning
o'rniga o'zing original, qisqa va ta'sirchan ingliz tilidagi jumla (quote
uslubida) yoz. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Original ingliz tilidagi qisqa motivatsion jumla (tirnoq ichida)
3. Uning o'zbekcha tarjimasi
4. Jumla ma'nosi haqida qisqa izoh (o'zbek tilida, 2-3 gap) va ingliz tili
   o'rganishga qanday tatbiq etilishi""",
    },
    "grammar_tests": {
        "topics": GRAMMAR_TESTS_TOPICS,
        "instruction": """Bu GRAMMAR TEST (kichik test/viktorina) posti. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Qisqa kirish (o'zbek tilida, 1 gap)
3. Aynan 5 ta ko'p tanlovli savol (har birida A, B, C variantlar), ingliz
   tilidagi jumlalarda bo'sh joy to'ldirish yoki xato topish uslubida
4. Oxirida "Javoblar:" deb nomlangan qism - barcha to'g'ri javoblarni
   qisqacha ko'rsating (masalan: 1-B, 2-A, 3-C...)""",
    },
    "topic_vocab": {
        "topics": TOPIC_VOCAB_TOPICS,
        "instruction": """Bu MAVZUGA OID LUG'AT posti - berilgan mavzu bo'yicha so'zlar
to'plami. Format:
1. Qiziqarli sarlavha (emoji bilan)
2. Qisqacha kirish (o'zbek tilida, 1-2 gap)
3. Kamida 8 ta ushbu mavzuga oid so'z/ibora, har biri uchun: ingliz tilida
   so'z, o'zbekcha ma'nosi, va bitta qisqa misol jumla
4. Oxirida qisqa maslahat""",
    },
}

PROMPT_TEMPLATE = """Sen tajribali ingliz tili o'qituvchisisan. Telegram kanali uchun
chiroyli, tartibli va o'qishga oson post tayyorla. Mavzu: {topic}.

FORMATLASH QOIDALARI (Telegram HTML):
- Faqat quyidagi ikkita tegdan foydalanishga ruxsat bor: <b>...</b> (qalin) va
  <i>...</i> (kursiv). Boshqa HECH QANDAY HTML yoki Markdown belgisi ishlatma
  (masalan <u>, <code>, <ul>, **, __, # kabi belgilar butunlay taqiqlangan).
- Har bir asosiy qism/band boshida mazmuniga mos 1 ta emoji qo'y (masalan 📌, 💡,
  ✅, 📖, 🔤, ❗, 🗣️, 📝), lekin haddan tashqari ko'p ishlatma - qatorda bittadan
  yetarli va o'rinli bo'lsin.
- Yangi lug'at so'zi, grammatik qoida nomi, muhim ibora yoki misol jumlaning
  kalit qismini <b>qalin</b> qilib ajratib ko'rsat. Butun paragrafni yoki uzun
  jumlani qalin qilib yubormang - faqat aynan muhim so'z/ibora qalin bo'lsin.
- Matn tartibli va bo'sh joylar bilan nafas oladigan bo'lsin: har bir band yoki
  fikr orasida bo'sh qator qoldir, ro'yxat elementlari alohida qatorlarda bo'lsin.

MUHIM: Javobning birinchi qatori albatta postning SARLAVHASI bo'lsin (boshida mos
emoji bilan, kerak bo'lsa sarlavhaning kalit so'zini <b>qalin</b> qilib), ikkinchi
qatordan boshlab bo'sh qator va qolgan matn kelsin.

{instruction}

Javobni FAQAT tayyor post matni sifatida qaytar, boshqa hech qanday izoh qo'shma.
Umumiy uzunlik 600-1000 belgidan oshmasin."""


def generate_post() -> tuple[str, dict]:
    state = _load_state()
    category = pick_category(state)
    info = CATEGORY_INFO[category]
    topic = choose_topic(state, category, info["topics"])
    advance_category_index(state)

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

    return text, state


ALLOWED_TAGS = ("b", "i")


def sanitize_telegram_html(text: str) -> str:
    """Matndagi HAMMA HTML belgilarini avval escape qiladi (xavfsizlik uchun),
    so'ng FAQAT ruxsat etilgan <b> va <i> teglarini asl holiga qaytaradi.
    Shu tariqa model tasodifan boshqa/singan teg yozib qo'ysa ham (yoki < > kabi
    oddiy belgi chiqsa ham), Telegram API xatolik bermaydi va faqat qalin/kursiv
    formatlash ishlaydi."""
    escaped = html.escape(text)
    for tag in ALLOWED_TAGS:
        escaped = escaped.replace(f"&lt;{tag}&gt;", f"<{tag}>")
        escaped = escaped.replace(f"&lt;/{tag}&gt;", f"</{tag}>")
    return escaped


def strip_allowed_tags(text: str) -> str:
    """Ruxsat etilgan teglarni matndan olib tashlaydi (masalan sarlavhani
    yagona <b>...</b> bilan o'rash uchun, model o'zi allaqachon qalin
    qilgan bo'lsa ham ikki marta ichma-ich bo'lib qolmasligi uchun)."""
    for tag in ALLOWED_TAGS:
        text = text.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
    return text


def build_html_message(raw_text: str) -> str:
    """Sarlavhani (birinchi qator) yagona <b>...</b> bilan qalin qilib,
    qolgan matndagi model qo'ygan <b>/<i> formatlashni saqlab qoladi.
    Boshqa har qanday HTML/belgi xavfsiz tarzda escape qilinadi, shuning
    uchun Telegram API "can't parse entities" xatosi bermaydi."""
    lines = raw_text.split("\n", 1)
    title = lines[0].strip()
    rest = lines[1].strip("\n") if len(lines) > 1 else ""

    clean_title = strip_allowed_tags(title)
    sanitized_title = html.escape(clean_title)
    sanitized_rest = sanitize_telegram_html(rest)

    body = f"<b>{sanitized_title}</b>\n\n{sanitized_rest}"
    body += "\n\n<i> Ai </i>"
    body += "\n\n Ulashing: @djami_teacher"
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
        post, state = generate_post()
        print("Yaratilgan post:\n", post)
        send_to_telegram(post)
        _save_state(state)
        print("Muvaffaqiyatli yuborildi!")
    except Exception as e:
        print(f"XATOLIK: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
