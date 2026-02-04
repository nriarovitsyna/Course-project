from datetime import date
from pydantic import BaseModel, ConfigDict

class ProgramOut(BaseModel):
    id: int

    program_code: str | None = None
    name: str | None = None
    faculty: str | None = None
    level: str | None = None

    university_name: str | None = None
    city: str | None = None

    budget_places: float | None = None
    paid_places: float | None = None
    tuition_cost_rub_year: float | None = None

    budget_passing_score: float | None = None
    paid_min_score: float | None = None

    duration: str | None = None
    study_format: str | None = None
    language: str | None = None

    accreditation: str | None = None

    model_config = ConfigDict(from_attributes=True)


class ProgramsListOut(BaseModel):
    items: list[ProgramOut]
    total: int