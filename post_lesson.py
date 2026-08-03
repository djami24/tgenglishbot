"""
Ingliz tili (IELTS Speaking Vocabulary + Grammar) postini Google Gemini
orqali generatsiya qilib, Telegram kanaliga avtomatik yuboradi.

Bot FAQAT ikkita turkumda post qiladi:

  1) MAVZUGA OID LUG'AT (topic_vocab) - kuniga 2 marta, har safar 50 ta
     IELTS Speaking mavzusidan (TOPIC_VOCAB_TOPICS) navbatdagi mavzu
     bo'yicha 10 ta so'z post qilinadi. 50 tasi tugamaguncha bironta mavzu
     takrorlanmaydi, tugagach qaytadan boshidan aylanadi.
  2) KUNLIK GRAMMAR SERIYASI (grammar) - kuniga 5 marta. Har kuni
     GRAMMAR_DAILY_TOPICS ro'yxatidan BITTA yangi mavzu tanlanadi va o'sha
     kun davomida 5 ta postga bo'linadi: umumiy tushuncha -> darak gap ->
     inkor gap -> so'roq gap -> amaliyot/xato tahlili. Ertasi kuni yangi
     mavzuga o'tiladi, 21 tasi tugamaguncha takrorlanmaydi.

Qaysi run qaysi turkumni post qilishini .github/workflows/post_lesson.yml
dagi cron jadvali (va shu jadvalga mos POST_CATEGORY muhit o'zgaruvchisi)
belgilaydi.

Joriy holat (kunlik grammar mavzusi/qismi va har turkumda qaysi mavzular
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
from datetime import datetime, timedelta, timezone

import requests

# Toshkent DST bilmaydi (doim UTC+5), shuning uchun sodda fixed-offset yetarli.
TASHKENT_TZ = timezone(timedelta(hours=5))


def _tashkent_today() -> str:
    return datetime.now(TASHKENT_TZ).date().isoformat()


GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
CHANNEL_LINK = "https://t.me/djami_teacher"

# ---------------------------------------------------------------------------
# Holatni saqlash: kunlik grammar mavzusi/qismi va har turkumda qaysi
# mavzular allaqachon ishlatilgani (topics). Workflow bu faylni har run'dan
# keyin repoga commit qiladi.
# ---------------------------------------------------------------------------
STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "used_topics.json")


def _load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data.setdefault("topics", {})
    data.setdefault("grammar_daily", {})
    return data


def _save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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


# ---------------------------------------------------------------------------
# 1) KUNLIK GRAMMAR SERIYASI - har kuni shundan BITTA mavzu tanlanadi va
#    o'sha kun davomida 5 ta postga bo'lib beriladi (umumiy tushuncha /
#    darak / inkor / so'roq / amaliyot). Mavzu tugab, hammasi bir marta
#    ishlatilgach, ro'yxat qaytadan boshidan aylanadi.
# ---------------------------------------------------------------------------
GRAMMAR_DAILY_TOPICS = [
    "Present Perfect Continuous (hozirgacha davom etayotgan harakatning davomiyligini ta'kidlash)",
    "Past Perfect Continuous (o'tmishdagi boshqa harakatdan oldingi davomiylikni ta'kidlash)",
    "Future Continuous (kelajakda davom etayotgan harakatlar)",
    "Future Perfect (kelajakdagi ma'lum vaqtga qadar tugallanadigan harakatlar)",
    "Future Perfect Continuous (kelajakdagi ma'lum vaqtga qadar davom etadigan harakat davomiyligi)",
    "Modals for deduction and speculation (must have, might have, could have)",
    "Modals for past advice, obligation and necessity (should have, could have, would have)",
    "Third Conditional (o'tmishdagi xayoliy vaziyatlar)",
    "Mixed Conditionals (turli vaqtlardagi shart va natijalarni birlashtirish)",
    "Passive voice - turli zamonlardagi murakkab qurilmalar",
    "Passive reporting structures (It is said that..., He is known to...)",
    "Reported speech - fe'l zamoni, olmosh va vaqt ifodalarining o'zgarishi",
    "Reported speech - buyruq, iltimos va savollarni ko'chirish",
    "Reduced relative clauses (nisbiy olmoshni tushirib qoldirish)",
    "Whose, where, when so'zlarining yuqori darajadagi qo'llanilishi",
    "Wish / If only - hozirgi vaqtdagi afsus va xayoliy istaklar",
    "Wish / If only - o'tmishdagi afsuslanishlarni ifodalash",
    "Linking adverbials - sabab, natija, qo'shimcha va qarama-qarshilik (therefore, however, moreover, consequently)",
    "Cleft sentences va inversion - urg'u berish uchun (It was John who..., Hardly had I...)",
    "Quantifiers va intensifiers - miqdor va urg'u ifodalari (a great deal of, plenty of, such, so, quite, rather)",
    "Subjunctive mood - zarurat va muhimlikni ifodalovchi that-clause'lar (It's essential that he be informed.)",
]

# Har kuni tanlangan mavzu shu 5 ta qismga bo'lib post qilinadi.
GRAMMAR_DAILY_PARTS = {
    1: """Bu kunlik GRAMMAR seriyasining 1/5-QISMI - "{topic}" mavzusi bo'yicha
UMUMIY TUSHUNCHA posti. Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "1/5" belgisini ko'rsating
2. Ushbu qoida nima uchun va qachon ishlatilishi (o'zbek tilida, 3-5 gap,
   tushunarli va aniq tushuntirish)
3. Kamida 2 ta oddiy misol jumla (ingliz tili + o'zbekcha tarjimasi)
4. Oxirida bugungi seriyaning keyingi qismlarida darak, inkor va so'roq gap
   tuzilishi ko'rib chiqilishi haqida qisqa eslatma""",
    2: """Bu kunlik GRAMMAR seriyasining 2/5-QISMI - "{topic}" mavzusi bo'yicha
DARAK GAP (affirmative) tuzilishi posti. Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "2/5" belgisini ko'rsating
2. Darak gap tuzilish formulasi aniq va <b>qalin</b> qilib ko'rsatilsin
   (masalan: Subject + have/has + been + V-ing)
3. Kamida 4 ta darak gap ko'rinishidagi misol jumla (ingliz tili +
   o'zbekcha tarjimasi)
4. Oxirida qisqa eslatma yoki tez-tez uchraydigan xato haqida ogohlantirish""",
    3: """Bu kunlik GRAMMAR seriyasining 3/5-QISMI - "{topic}" mavzusi bo'yicha
INKOR GAP (negative) tuzilishi posti. Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "3/5" belgisini ko'rsating
2. Inkor gap tuzilish formulasi aniq va <b>qalin</b> qilib ko'rsatilsin
   (masalan: Subject + haven't/hasn't + been + V-ing)
3. Kamida 4 ta inkor gap ko'rinishidagi misol jumla (ingliz tili +
   o'zbekcha tarjimasi)
4. Oxirida qisqa eslatma yoki tez-tez uchraydigan xato haqida ogohlantirish""",
    4: """Bu kunlik GRAMMAR seriyasining 4/5-QISMI - "{topic}" mavzusi bo'yicha
SO'ROQ GAP (question) tuzilishi posti. Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "4/5" belgisini ko'rsating
2. Umumiy (yes/no) va maxsus (wh-) so'roq gap tuzilish formulalari aniq va
   <b>qalin</b> qilib ko'rsatilsin
3. Kamida 4 ta so'roq gap ko'rinishidagi misol jumla (ingliz tili +
   o'zbekcha tarjimasi, kamida bittasi wh-so'roq bo'lsin)
4. Oxirida qisqa eslatma""",
    5: """Bu kunlik GRAMMAR seriyasining 5/5 - YAKUNIY QISMI - "{topic}" mavzusi
bo'yicha AMALIYOT posti. Format:
1. Qiziqarli sarlavha (emoji bilan), sarlavhada "5/5" belgisini ko'rsating
2. Ushbu mavzuda o'quvchilar ko'p qiladigan 1-2 ta xato haqida qisqa
   ogohlantirish (o'zbek tilida)
3. Aynan 4 ta bo'sh joy to'ldirish uslubidagi mashq jumlasi (ingliz tilida,
   bo'sh joy ___ bilan ko'rsatilsin)
4. Oxirida "Javoblar:" deb nomlangan qismda to'g'ri javoblarni qisqacha
   ko'rsating""",
}


def _next_grammar_daily_part(state: dict) -> tuple[str, int]:
    """Bugungi kun uchun grammar-of-the-day mavzusini va navbatdagi (1-5)
    qismni aniqlaydi. Kun almashganda (yoki hali hech narsa tanlanmagan
    bo'lsa) yangi mavzu tanlaydi va 1-qismdan boshlaydi; aks holda shu kunning
    davomida navbatdagi qismga o'tadi. Agar bir kunda 5 martadan ortiq run
    bo'lib qolsa (masalan workflow qayta ishga tushirilsa), 5-qism
    (amaliyot posti) qaytaveradi - xato bermaydi."""
    today = _tashkent_today()
    gd = state.setdefault("grammar_daily", {})

    if gd.get("date") != today or "topic" not in gd:
        topic = choose_topic(state, "grammar_daily_topic", GRAMMAR_DAILY_TOPICS)
        gd["date"] = today
        gd["topic"] = topic
        gd["part"] = 1
    else:
        gd["part"] = min(gd.get("part", 0) + 1, 5)

    return gd["topic"], gd["part"]


# ---------------------------------------------------------------------------
# 2) IELTS SPEAKING LUG'ATI - kuniga 2 marta, har safar 50 ta mavzudan
#    navbatdagi mavzu bo'yicha 10 ta so'z post qilinadi. Barcha 50 tasi bir
#    marta ishlatilmaguncha takrorlanmaydi.
# ---------------------------------------------------------------------------
TOPIC_VOCAB_TOPICS = [
    "Family & Relationships (Oila va munosabatlar)",
    "Friends (Do'stlar)",
    "Education (Ta'lim)",
    "School Life (Maktab hayoti)",
    "University (Universitet)",
    "Work & Career (Ish va karyera)",
    "Jobs (Kasblar)",
    "Hobbies (Qiziqishlar)",
    "Free Time (Bo'sh vaqt)",
    "Sports & Exercise (Sport va mashqlar)",
    "Health & Lifestyle (Sog'liq va hayot tarzi)",
    "Food & Cooking (Ovqat va pishirish)",
    "Restaurants & Cafes (Restoran va kafelar)",
    "Travel & Holidays (Sayohat va ta'til)",
    "Tourism (Turizm)",
    "Transport (Transport)",
    "Cities (Shaharlar)",
    "The Countryside (Qishloq hududi)",
    "Home & Accommodation (Uy va yashash joyi)",
    "Neighborhood (Mahalla / yashash hududi)",
    "Technology (Texnologiya)",
    "The Internet (Internet)",
    "Social Media (Ijtimoiy tarmoqlar)",
    "Mobile Phones (Mobil telefonlar)",
    "Artificial Intelligence (Sun'iy intellekt)",
    "Shopping (Xarid qilish)",
    "Clothes & Fashion (Kiyim va moda)",
    "Money & Saving (Pul va jamg'arma)",
    "Environment (Atrof-muhit)",
    "Climate & Weather (Iqlim va ob-havo)",
    "Animals & Pets (Hayvonlar va uy hayvonlari)",
    "Nature (Tabiat)",
    "Books & Reading (Kitoblar va o'qish)",
    "Films & Cinema (Filmlar va kino)",
    "Music (Musiqa)",
    "Art & Creativity (San'at va ijodkorlik)",
    "Television (Televizor)",
    "News & Media (Yangiliklar va media)",
    "Photography (Fotografiya)",
    "Festivals & Celebrations (Bayramlar va tantanalar)",
    "Culture & Traditions (Madaniyat va an'analar)",
    "Languages (Tillar)",
    "Learning English (Ingliz tilini o'rganish)",
    "Goals & Ambitions (Maqsadlar va orzular)",
    "Success & Failure (Muvaffaqiyat va muvaffaqiyatsizlik)",
    "Memories & Childhood (Xotiralar va bolalik)",
    "People & Personality (Insonlar va xarakter)",
    "Communication (Muloqot)",
    "Society & Community (Jamiyat va hamjamiyat)",
    "Future & Technology (Kelajak va texnologiyalar)",
]

TOPIC_VOCAB_INSTRUCTION = """Bu IELTS SPEAKING uchun MAVZUGA OID LUG'AT posti - berilgan mavzu
IELTS Speaking (Part 1/2/3) intervyusida ishlatilishi mumkin bo'lgan so'zlar
to'plami. Format:
1. Qiziqarli sarlavha (emoji bilan), mavzu nomini ko'rsating
2. Qisqacha kirish (o'zbek tilida, 1-2 gap) - bu so'zlar IELTS Speaking'da
   qanday foydali ekani haqida
3. AYNAN 10 ta ushbu mavzuga oid so'z yoki ibora (oddiy so'zlardan tashqari,
   IELTS'da band ballini oshiradigan collocation/idioma ham bo'lishi mumkin),
   har biri uchun: ingliz tilida so'z/ibora, o'zbekcha ma'nosi, va IELTS
   Speaking javobida ishlatsa bo'ladigan bitta qisqa misol jumla
4. Oxirida ushbu so'zlarni Speaking javobida qanday qo'llash haqida qisqa
   maslahat"""


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

MUHIM: Standart adabiy o'zbek tilida, IMLO VA GRAMMATIK XATOLARSIZ yoz. So'zlarni
yarim qoldirma, gaplarni oxirigacha tugalla, bir xil fikrni ikki marta takrorlama.

MUHIM: Javobning birinchi qatori albatta postning SARLAVHASI bo'lsin (boshida mos
emoji bilan, kerak bo'lsa sarlavhaning kalit so'zini <b>qalin</b> qilib), ikkinchi
qatordan boshlab bo'sh qator va qolgan matn kelsin.

{instruction}

Javobni FAQAT tayyor post matni sifatida qaytar, boshqa hech qanday izoh qo'shma.
Odatda umumiy uzunlik 600-1000 belgi atrofida bo'lsin; lekin agar yuqoridagi
formatda aniq sonli band (masalan 10 ta so'z yoki mashq savollari) talab
qilingan bo'lsa, hammasini to'liq kiritish uchun 1600 belgigacha borishga
ruxsat bor - biroq bundan ortiq cho'zma. Javob albatta to'liq gap bilan
tugasin, hech qanday band yarim qoldirilmasin."""


def _call_gemini(prompt: str, max_output_tokens: int = 2048) -> tuple[str, str | None]:
    """Gemini'ga so'rov yuboradi va (matn, finish_reason) qaytaradi."""
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            # Pastroq temperatura - imlo/grammatikada tasodifiy xatolar
            # va chalkash so'zlarni kamaytiradi, shu bilan birga matn
            # hamon xilma-xil va qiziqarli chiqadi.
            "temperature": 0.6,
            "maxOutputTokens": max_output_tokens,
        },
    }

    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    try:
        candidate = data["candidates"][0]
        finish_reason = candidate.get("finishReason")
        text = candidate["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Gemini javobi kutilmagan formatda: {data}") from e

    return text, finish_reason


def generate_post() -> tuple[str, dict]:
    state = _load_state()
    category = os.environ.get("POST_CATEGORY") or "grammar"

    if category == "topic_vocab":
        topic = choose_topic(state, "topic_vocab", TOPIC_VOCAB_TOPICS)
        prompt = PROMPT_TEMPLATE.format(topic=topic, instruction=TOPIC_VOCAB_INSTRUCTION)
    else:
        # Default/"grammar" - kunlik grammar seriyasi.
        topic, part = _next_grammar_daily_part(state)
        instruction = GRAMMAR_DAILY_PARTS[part].format(topic=topic)
        prompt = PROMPT_TEMPLATE.format(
            topic=f"{topic} ({part}/5-qism)", instruction=instruction
        )

    # Javob token limitiga yetib o'rtada kesilib qolsa (masalan so'z yarim
    # qoldirilsa), buni "MAX_TOKENS" finishReason orqali aniqlaymiz va
    # kattaroq token limiti bilan qayta so'raymiz - shunda kesilgan/yarim
    # so'zli post Telegramga yuborilmaydi.
    text, finish_reason = _call_gemini(prompt, max_output_tokens=2048)
    attempts = 1
    while finish_reason == "MAX_TOKENS" and attempts < 3:
        attempts += 1
        text, finish_reason = _call_gemini(prompt, max_output_tokens=2048 + 1024 * (attempts - 1))

    if finish_reason and finish_reason not in ("STOP",):
        print(f"Ogohlantirish: finishReason={finish_reason} (matn to'liq bo'lmasligi mumkin)")

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
    body += "\n\n<i>🤖 AI tomonidan tayyorlandi</i>"
    body += "\n\n📢 Ulashing: @djami_teacher"
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
