"""
Сервис значений фильтров.

ТЗ: backend должен отдавать значения для выпадающих списков/чекбоксов. [file:1]
"""

from sqlalchemy import select, distinct
from sqlalchemy.orm import Session

from app.models.program import Program


class FiltersService:
    def __init__(self, db: Session):
        self.db = db

    def _distinct_nonnull(self, column):
        stmt = select(distinct(column)).where(column.is_not(None)).order_by(column.asc())
        return [x for (x,) in self.db.execute(stmt).all() if x is not None and str(x).strip() != ""]

    def get_values(self):
        return {
            "cities": self._distinct_nonnull(Program.city),
            "levels": self._distinct_nonnull(Program.educationallevel),
            "study_forms": self._distinct_nonnull(Program.studyform),
            "languages": self._distinct_nonnull(Program.language),
        }
