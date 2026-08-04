"""
Lug'at (topic_vocab) postidagi kalit so'z/iboralarni (model <b>...</b> bilan
belgilagan) ajratib olib, ularning talaffuzini Google Text-to-Speech (gTTS
kutubxonasi orqali, API kalit talab qilinmaydi) yordamida bitta audio
xabarga aylantiradi.
"""

import re
from io import BytesIO

from gtts import gTTS


def extract_key_terms(raw_text: str, max_terms: int = 12) -> list:
    """Model javobining birinchi qatori (sarlavha) dan keyingi qismidan
    <b>...</b> bilan belgilangan so'z/iboralarni ajratib oladi, takrorlarni
    olib tashlaydi va ketma-ketlikni saqlaydi."""
    lines = raw_text.split("\n", 1)
    body = lines[1] if len(lines) > 1 else raw_text

    raw_terms = re.findall(r"<b>(.*?)</b>", body, flags=re.DOTALL)

    seen = set()
    terms = []
    for t in raw_terms:
        clean = re.sub(r"<.*?>", "", t).strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            terms.append(clean)
    return terms[:max_terms]


def build_pronunciation_audio(words: list) -> bytes:
    """Har bir so'zni ikki marta o'qiydigan (aniqroq eshitilishi uchun),
    so'zlar orasida tabiiy pauza bo'ladigan yagona ingliz tilidagi MP3 audio
    yaratadi. gTTS Google Translate'ning ochiq TTS endpointidan foydalanadi
    - alohida API kalit shart emas."""
    script = ". ".join(f"{w}, {w}" for w in words)
    tts = gTTS(text=script, lang="en", slow=False)
    buf = BytesIO()
    tts.write_to_fp(buf)
    return buf.getvalue()
