"""
Pydantic-схемы для отдачи программ наружу (response_model).
"""

from datetime import date
from pydantic import BaseModel


class ProgramOut(BaseModel):
    id: int

    name: str | None = None
    department: str | None = None
    educationallevel: str | None = None

    universityname: str | None = None
    city: str | None = None

    budgetplaces: int | None = None
    paidplaces: int | None = None
    tuitionfee: int | None = None

    passingscore: int | None = None
    entrancesubjects: str | None = None

    duration: int | None = None
    studyform: str | None = None
    language: str | None = None

    accreditation: bool | None = None
    subjectsurl: str | None = None
    lastupdated: date | None = None

    class Config:
        from_attributes = True


class ProgramsListOut(BaseModel):
    items: list[ProgramOut]
    total: int
