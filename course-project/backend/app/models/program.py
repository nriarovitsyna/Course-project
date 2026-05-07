from sqlalchemy import Integer, String, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    program_code: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)

    faculty: Mapped[str | None] = mapped_column(String, nullable=True)
    level: Mapped[str | None] = mapped_column(String, nullable=True)

    university_name: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    budget_places: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid_places: Mapped[float | None] = mapped_column(Float, nullable=True)
    tuition_cost_rub_year: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)

    budget_passing_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid_min_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    duration: Mapped[str | None] = mapped_column(String, nullable=True)
    study_format: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    
    accreditation: Mapped[str | None] = mapped_column(String, nullable=True)