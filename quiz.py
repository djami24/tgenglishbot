"""
Kunlik grammar mavzusi tugagach (5/5-qism yuborilgach), o'sha mavzu bo'yicha
5 ta HAQIQIY BOSILADIGAN Telegram viktorina (quiz poll) savoli generatsiya
qilib yuboradi. Odamlar variantni bosadi va to'g'ri/xato darhol ko'rinadi.
"""

import json

import requests

QUIZ_PROMPT_TEMPLATE = """Sen tajribali ingliz tili o'qituvchisisan. Quyidagi grammatik mavzu
bo'yicha ANIQ 5 ta variantli test savoli (multiple-choice quiz) tuzib ber.

Mavzu: {topic}

QOIDALAR:
- Har bir savol ingliz tilida bo'lsin (odatda bo'sh joy to'ldirish yoki eng
  to'g'ri variantni tanlash uslubida), shu grammatik qoidani sinovdan
  o'tkazsin.
- Har bir savolda ANIQ 4 ta variant (options) bo'lsin, ular orasida faqat
  bittasi to'g'ri.
- "correct_index" - to'g'ri variantning ro'yxatdagi tartib raqami (0 dan
  boshlab hisoblanadi).
- "explanation" - o'zbek tilida, nima uchun aynan shu variant to'g'ri
  ekanini 1 ta QISQA gap bilan tushuntirsin (150 belgidan oshmasin).
- Savol matni 250 belgidan, har bir variant esa 90 belgidan oshmasin.
- Standart adabiy o'zbek tilida, imlo va grammatik xatolarsiz yoz.
- 5 ta savol bir-biridan farq qilsin (bir xil gap tuzilishini takrorlama).

Javobni FAQAT quyidagi JSON massividan iborat holda qaytar - boshqa HECH
QANDAY matn, izoh, sarlavha yoki markdown belgisi (masalan ```json) qo'shma,
javob to'g'ridan-to'g'ri "[" belgisidan boshlansin:

[
  {{"question": "...", "options": ["...", "...", "...", "..."], "correct_index": 0, "explanation": "..."}}
]

Jami ANIQ 5 ta shu ko'rinishdagi obyekt bo'lsin."""


def _clean_json_text(text: str) -> str:
    """Model ba'zan ```json ... ``` bilan o'rab yuborishi mumkin - buni
    tozalaydi."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]
        text = text.strip()
        if text.startswith("json"):
            text = text[4:].strip()
    return text


def generate_quiz_questions(topic: str, call_gemini_fn) -> list:
    """call_gemini_fn - post_lesson._call_gemini funksiyasi (prompt,
    max_output_tokens) -> (text, finish_reason). Bu yerda dependency
    sifatida uzatiladi, chunki quiz.py Gemini kalitidan mustaqil bo'lishi
    kerak (faqat post_lesson orqali chaqiriladi)."""
    prompt = QUIZ_PROMPT_TEMPLATE.format(topic=topic)
    text, _finish_reason = call_gemini_fn(prompt, max_output_tokens=2048)
    cleaned = _clean_json_text(text)
    questions = json.loads(cleaned)

    if not isinstance(questions, list):
        raise ValueError("Gemini javobi JSON ro'yxati emas")

    validated = []
    for q in questions[:5]:
        question = str(q["question"]).strip()[:250]
        options = [str(o).strip()[:90] for o in q["options"]][:10]
        if len(options) < 2:
            continue
        correct_index = int(q["correct_index"])
        if not (0 <= correct_index < len(options)):
            correct_index = 0
        explanation = str(q.get("explanation", "")).strip()[:195]
        validated.append(
            {
                "question": question,
                "options": options,
                "correct_index": correct_index,
                "explanation": explanation,
            }
        )
    return validated


def send_quiz_poll(bot_token: str, chat_id: str, question: dict) -> None:
    url = f"https://api.telegram.org/bot{bot_token}/sendPoll"
    payload = {
        "chat_id": chat_id,
        "question": question["question"],
        "options": json.dumps(question["options"], ensure_ascii=False),
        "type": "quiz",
        "correct_option_id": question["correct_index"],
        "is_anonymous": True,
    }
    if question.get("explanation"):
        payload["explanation"] = question["explanation"]

    resp = requests.post(url, data=payload, timeout=30)
    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Telegramga quiz yuborishda xato: {result}")


def send_daily_quiz(bot_token: str, chat_id: str, topic: str, call_gemini_fn) -> int:
    """Kunlik mavzu uchun 5 ta quiz generatsiya qilib yuboradi. Muvaffaqiyatli
    yuborilgan savollar sonini qaytaradi. Har bir savol alohida try/except
    bilan yuboriladi - bittasi xato bersa ham qolganlari yuborilishga
    harakat qilinadi."""
    questions = generate_quiz_questions(topic, call_gemini_fn)
    sent = 0
    for q in questions:
        try:
            send_quiz_poll(bot_token, chat_id, q)
            sent += 1
        except Exception as e:
            print(f"Ogohlantirish: bitta quiz savoli yuborilmadi: {e}")
    return sent
