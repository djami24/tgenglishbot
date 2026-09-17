"""
IELTS SPEAKING PART 1 mashqi - kuniga 1 marta, biror mavzu bo'yicha 3 ta
oddiy Speaking Part 1 uslubidagi savol yozma shaklda post qilinadi, va
shu savollarning "mashq audiosi" ham qo'shib yuboriladi:

  savol (2 marta o'qiladi, shoshilmasdan) -> 30 soniya jimlik (talaba javob
  berishi uchun) -> keyingi savol ...

Audio pydub + ffmpeg yordamida gTTS bo'laklarini va real jimlikni
birlashtirib tuziladi. ffmpeg GitHub Actions'ning ubuntu-latest runner'ida
standart o'rnatilgan bo'ladi, shuning uchun qo'shimcha o'rnatish shart emas.
"""

import json

SPEAKING_PART1_PROMPT = """Sen tajribali IELTS Speaking imtihonchisisan. "{topic}" mavzusi
bo'yicha AYNAN 3 ta IELTS SPEAKING PART 1 uslubidagi savol tuz va har biriga
qisqa namunaviy javob yoz.

QOIDALAR:
- Savollar oddiy, qisqa va suhbat uslubida bo'lsin (haqiqiy IELTS Part 1'da
  so'raladigan darajada) - masalan "Do you...", "What...", "How often...",
  "Can you describe..." kabi boshlanishi mumkin.
- Har bir savol ingliz tilida, 20 so'zdan oshmasin.
- 3 ta savol bir-biridan farq qilib, mavzuning turli qirralarini qamrab olsin.
- Namunaviy javob: 2-3 ta to'liq gap, IELTS band 6-7 darajasida, tabiiy va
  speaking uslubida yozilsin. Javob savol so'ragan narsaga to'g'ridan-to'g'ri
  javob bersin.

Javobni FAQAT quyidagi JSON formatida qaytar, boshqa HECH QANDAY matn, izoh
yoki markdown belgisi qo'shma, javob to'g'ridan-to'g'ri "{{" belgisidan
boshlansin:

{{"questions": [
  {{"q": "...", "example": "..."}},
  {{"q": "...", "example": "..."}},
  {{"q": "...", "example": "..."}}
]}}"""


def _clean_json_text(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return text


def generate_speaking_questions(topic: str, call_gemini_fn) -> list:
    """call_gemini_fn - post_lesson._call_gemini (prompt, max_output_tokens)
    -> (text, finish_reason). AYNAN 3 ta {"q": ..., "example": ...} dict qaytaradi."""
    prompt = SPEAKING_PART1_PROMPT.format(topic=topic)
    text, _finish_reason = call_gemini_fn(prompt, max_output_tokens=700)
    cleaned = _clean_json_text(text)
    data = json.loads(cleaned)

    raw = data.get("questions", [])
    pairs = []
    for item in raw:
        if isinstance(item, dict):
            q = str(item.get("q", "")).strip()
            ex = str(item.get("example", "")).strip()
        else:
            # Eski format: faqat string (fallback)
            q = str(item).strip()
            ex = ""
        if q:
            pairs.append({"q": q, "example": ex})

    if len(pairs) < 3:
        raise ValueError(f"Gemini kutilganidek 3 ta savol qaytarmadi: {pairs}")
    return pairs[:3]



def build_speaking_post_text(topic: str, questions: list) -> str:
    """Postning yozma (matnli) qismini tuzadi. Birinchi qator sarlavha
    sifatida ishlatiladi (post_lesson.build_html_message shu birinchi
    qatorni avtomatik qalin qiladi). Har bir savoldan keyin namunaviy
    javob ko'rsatiladi. questions - [{"q": ..., "example": ...}] formatida."""
    clean_topic = topic.split("(")[0].strip()
    lines = [
        f"🗣️ Speaking Part 1 mashqi: {clean_topic}",
        "",
        "Quyidagi 3 ta savolga o'zingiz avval javob bering, so'ng namunaviy"
        " javob bilan solishtiring.",
        "",
    ]
    for i, item in enumerate(questions, start=1):
        q = item["q"] if isinstance(item, dict) else str(item)
        ex = item.get("example", "") if isinstance(item, dict) else ""
        lines.append(f"<b>{i}. {q}</b>")
        if ex:
            lines.append(f"💬 Namunaviy javob: <i>{ex}</i>")
        lines.append("")
    lines.append("✏️ O'z javobingizni yozib, ularni solishtiring!")
    return "\n".join(lines)
