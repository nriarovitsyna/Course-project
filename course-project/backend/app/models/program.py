from sqlalchemy import Integer, String, Boolean, Date
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    name: Mapped[str | None] = mapped_column(String, nullable=True)
    department: Mapped[str | None] = mapped_column(String, nullable=True)
    educationallevel: Mapped[str | None] = mapped_column(String, nullable=True)

    universityname: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True, index=True)

    budgetplaces: Mapped[int | None] = mapped_column(Integer, nullable=True)
    paidplaces: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tuitionfee: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    passingscore: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entrancesubjects: Mapped[str | None] = mapped_column(String, nullable=True)

    duration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    studyform: Mapped[str | None] = mapped_column(String, nullable=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)

    accreditation: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    subjectsurl: Mapped[str | None] = mapped_column(String, nullable=True)
    lastupdated: Mapped["Date | None"] = mapped_column(Date, nullable=True)
