from pydantic import BaseModel


class FiltersValuesOut(BaseModel):
    name: list[str]
    faculty: list[str]
    level: list[str]
    university_name: list[str]
    city: list[str]
    budget_places: list[float]
    paid_places: list[float]
    tuition_cost_rub_year: list[float]
    budget_passing_score: list[float]
    paid_min_score: list[float]
    duration: list[str]
    study_format: list[str]
    language: list[str]
    accreditation: list[str]