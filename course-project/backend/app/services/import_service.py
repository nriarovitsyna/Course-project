from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.program import Program


class ImportService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def _to_float(x):
        if pd.isna(x):
            return None
        try:
            return float(x)
        except Exception:
            return None

    @staticmethod
    def _to_str(x):
        if pd.isna(x):
            return None
        s = str(x).strip()
        return s if s != "" else None

    def import_csv(self, path: str) -> int:
        df = pd.read_csv(path)
        df.columns = [c.strip().lower() for c in df.columns]

        created = 0
        for _, row in df.iterrows():
            program = Program(
                id=int(row["id"]) if not pd.isna(row.get("id")) else None,

                program_code=self._to_str(row.get("program_code")),
                name=self._to_str(row.get("name")),
                faculty=self._to_str(row.get("faculty")),
                level=self._to_str(row.get("level")),

                university_name=self._to_str(row.get("university_name")),
                city=self._to_str(row.get("city")),

                budget_places=self._to_float(row.get("budget_places")),
                paid_places=self._to_float(row.get("paid_places")),
                tuition_cost_rub_year=self._to_float(row.get("tuition_cost_rub_year")),

                budget_passing_score=self._to_float(row.get("budget_passing_score")),
                paid_min_score=self._to_float(row.get("paid_min_score")),

                duration=self._to_str(row.get("duration")),
                study_format=self._to_str(row.get("study_format")),
                language=self._to_str(row.get("language")),

                accreditation=self._to_str(row.get("accreditation")),
            )
            self.db.add(program)
            created += 1

        self.db.commit()
        return created