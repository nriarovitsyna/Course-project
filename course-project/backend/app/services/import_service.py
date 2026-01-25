from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.program import Program


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_int(x):
        try:
            if pd.isna(x):
                return None
            return int(x)
        except Exception:
            return None

    @staticmethod
    def _to_bool(x):
        # В CSV встречается TRUE/FALSE и иногда мусор — приводим аккуратно.
        if pd.isna(x):
            return None
        if isinstance(x, bool):
            return x
        s = str(x).strip().lower()
        if s in {"true", "1", "yes", "да"}:
            return True
        if s in {"false", "0", "no", "нет"}:
            return False
        return None

    @staticmethod
    def _to_date(x):
        if pd.isna(x):
            return None
        # В твоём CSV дата вида 13.01.2026 встречается в конце строк. [file:2]
        return pd.to_datetime(str(x), dayfirst=True, errors="coerce").date()

    def import_csv(self, path: str) -> int:
        df = pd.read_csv(path)

        # Приводим названия колонок к нижнему регистру без пробелов — под модель.
        df.columns = [c.strip().lower() for c in df.columns]

        created = 0
        for _, row in df.iterrows():
            program = Program(
                id=self._to_int(row.get("id")),

                name=row.get("name"),
                department=row.get("department"),
                educationallevel=row.get("educationallevel"),

                universityname=row.get("universityname"),
                city=row.get("city"),

                budgetplaces=self._to_int(row.get("budgetplaces")),
                paidplaces=self._to_int(row.get("paidplaces")),
                tuitionfee=self._to_int(row.get("tuitionfee")),

                passingscore=self._to_int(row.get("passingscore")),
                entrancesubjects=row.get("entrancesubjects"),

                duration=self._to_int(row.get("duration")),
                studyform=row.get("studyform"),
                language=row.get("language"),

                accreditation=self._to_bool(row.get("accreditation")),
                subjectsurl=row.get("subjectsurl"),
                lastupdated=self._to_date(row.get("lastupdated")),
            )
            self.db.add(program)
            created += 1

        self.db.commit()
        return created
