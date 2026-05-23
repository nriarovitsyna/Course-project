from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter
from fastapi.responses import Response
from pydantic import BaseModel

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Table, TableStyle
from reportlab.lib import colors

from pathlib import Path
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# РЕГИСТРАЦИЯ ШРИФТА (важно: путь /app/fonts/DejaVuSans.ttf)
FONT_PATH = Path("/app/fonts/DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", str(FONT_PATH)))

router = APIRouter(tags=["export"])


class Program(BaseModel):
    id: int
    name: str
    faculty: Optional[str] = None
    level: Optional[str] = None
    university_name: Optional[str] = None
    city: Optional[str] = None
    budget_places: Optional[int] = None
    paid_places: Optional[int] = None
    tuition_cost_rub_year: Optional[float] = None
    budget_passing_score: Optional[float] = None
    paid_min_score: Optional[float] = None
    duration: Optional[str] = None
    study_format: Optional[str] = None
    language: Optional[str] = None
    accreditation: Optional[str] = None


@router.post("/pdf", response_class=Response)
def export_pdf(programs: List[Program]):
    """
    Генерация PDF: каждая программа выводится одной строкой текста.
    """
    buffer = BytesIO()

    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Заголовок
    c.setFont("DejaVuSans", 16)
    c.setFillColorRGB(0, 0, 0)
    c.drawString(40, height - 40, "Сравнение образовательных программ")

    y = height - 70
    line_height = 12

    c.setFont("DejaVuSans", 8)

    for p in programs:
        line = (
            f"ID: {p.id}; "
            f"Название: {p.name}; "
            f"Вуз: {p.university_name or ''}; "
            f"Город: {p.city or ''}; "
            f"Уровень: {p.level or ''}; "
            f"Форма: {p.study_format or ''}; "
            f"Язык: {p.language or ''}; "
            f"Бюджетных мест: {p.budget_places or ''}; "
            f"Платных мест: {p.paid_places or ''}; "
            f"Стоимость (руб/год): {p.tuition_cost_rub_year or ''}; "
            f"Баллы бюджет: {p.budget_passing_score or ''}; "
            f"Баллы платно: {p.paid_min_score or ''}; "
            f"Длительность: {p.duration or ''}; "
            f"Аккредитация: {p.accreditation or ''}"
        )

        # Перенос по строкам, если слишком длинная
        max_width = width - 80  # справа небольшой отступ
        words = line.split(" ")
        current = ""
        lines_block = []

        for word in words:
            test = (current + " " + word).strip()
            if c.stringWidth(test, "DejaVuSans", 8) <= max_width:
                current = test
            else:
                lines_block.append(current)
                current = word
        if current:
            lines_block.append(current)

        # Если не помещается на странице — новая страница
        needed_height = line_height * (len(lines_block) + 1)
        if y - needed_height < 40:
            c.showPage()
            c.setFont("DejaVuSans", 8)
            y = height - 40

        for l in lines_block:
            c.drawString(40, y, l)
            y -= line_height

        # пустая строка между программами
        y -= line_height

    c.showPage()
    c.save()

    pdf_bytes = buffer.getvalue()
    buffer.close()

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="export.pdf"'
        },
    )