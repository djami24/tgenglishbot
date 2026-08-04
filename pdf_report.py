"""
21 ta grammar mavzusining bir to'liq aylanishi tugagach (barcha mavzular
kamida bir marta ishlatilgach), shu davrda yig'ilgan barcha kontentni
birlashtirib, "to'liq qo'llanma" PDF fayl yaratadi. Tashqi servis yoki API
kalit shart emas - fpdf2 kutubxonasi bilan mahalliy ravishda tuziladi.
"""

import os
import re

from fpdf import FPDF
from fpdf.enums import XPos, YPos

_ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "fonts")
_REGULAR_FONT_PATH = os.path.join(_ASSETS_DIR, "DejaVuSans.ttf")
_BOLD_FONT_PATH = os.path.join(_ASSETS_DIR, "DejaVuSans-Bold.ttf")

_PART_TITLES = {
    "1": "1) Umumiy tushuncha",
    "2": "2) Darak gap (affirmative)",
    "3": "3) Inkor gap (negative)",
    "4": "4) So'roq gap (question)",
    "5": "5) Amaliyot",
}


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


def _clean_topic_title(topic: str) -> str:
    return topic.split("(")[0].strip()


def _line(pdf: FPDF, h: float, text: str, align: str = "L") -> None:
    """pdf.multi_cell'ning xavfsiz o'ramasi - har doim kursorni chap
    marginga va keyingi qatorga qaytaradi (fpdf2'da align='C' bilan
    multi_cell chaqirilganda kursor o'ng chetda qolib ketishi mumkin,
    bu keyingi chaqiruvda "Not enough horizontal space" xatosiga olib
    keladi)."""
    pdf.multi_cell(0, h, text, align=align, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def build_grammar_compendium_pdf(archive: list) -> bytes:
    """archive - [{"date":..., "topic":..., "parts": {"1": text, ...}}]
    ko'rinishidagi ro'yxat. PDF bytes qaytaradi."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_font("DejaVu", "", _REGULAR_FONT_PATH)
    pdf.add_font("DejaVu", "B", _BOLD_FONT_PATH)

    # Muqova
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 24)
    pdf.ln(60)
    _line(pdf, 14, "Ingliz tili grammatikasi", align="C")
    pdf.set_font("DejaVu", "", 15)
    _line(pdf, 10, "To'liq qo'llanma", align="C")
    pdf.ln(10)
    pdf.set_font("DejaVu", "", 12)
    _line(
        pdf, 8,
        f"Ushbu qo'llanma {len(archive)} ta grammatik mavzuni, har biri "
        "5 qismli (umumiy tushuncha, darak, inkor, so'roq, amaliyot) "
        "ko'rinishida o'z ichiga oladi.",
        align="C",
    )
    pdf.ln(4)
    pdf.set_font("DejaVu", "", 11)
    _line(pdf, 7, "@djami_teacher", align="C")

    # Mundarija
    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    _line(pdf, 10, "Mundarija")
    pdf.ln(2)
    pdf.set_font("DejaVu", "", 11)
    for i, entry in enumerate(archive, start=1):
        _line(pdf, 7, f"{i}. {_clean_topic_title(entry['topic'])}")

    # Har bir mavzu uchun alohida sahifa(lar)
    for i, entry in enumerate(archive, start=1):
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 17)
        _line(pdf, 10, f"{i}. {_clean_topic_title(entry['topic'])}")
        pdf.ln(3)

        parts = entry.get("parts", {})
        for part_num in ("1", "2", "3", "4", "5"):
            text = parts.get(part_num)
            if not text:
                continue
            # Sarlavha qatorini (birinchi qator) alohida ko'rsatib, qolgan
            # matnni tag'laridan tozalab bosamiz.
            lines = text.split("\n", 1)
            body = lines[1].strip() if len(lines) > 1 else ""

            pdf.set_font("DejaVu", "B", 13)
            _line(pdf, 8, _PART_TITLES.get(part_num, f"{part_num}-qism"))
            pdf.set_font("DejaVu", "", 11)
            _line(pdf, 6, _strip_tags(body).strip())
            pdf.ln(4)

    output = pdf.output()
    return bytes(output)
