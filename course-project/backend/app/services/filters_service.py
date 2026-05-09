from sqlalchemy import select, distinct
from sqlalchemy.orm import Session

from app.models.program import Program


class FiltersService:
    def __init__(self, db: Session):
        self.db = db

    def _distinct_nonnull(self, column):
        stmt = (
            select(distinct(column))
            .where(column.is_not(None))
            .order_by(column.asc())
        )
        return [x for (x,) in self.db.execute(stmt).all() if x is not None and str(x).strip() != ""]

    def get_values(self):
        return {
            "faculty": self._distinct_nonnull(Program.faculty),
            "university_name": self._distinct_nonnull(Program.university_name),
            "level": self._distinct_nonnull(Program.level),
            "city": self._distinct_nonnull(Program.city),
            "duration": self._distinct_nonnull(Program.duration),
            "study_format": self._distinct_nonnull(Program.study_format),
            "language": self._distinct_nonnull(Program.language),
            "accreditation": self._distinct_nonnull(Program.accreditation),
        }