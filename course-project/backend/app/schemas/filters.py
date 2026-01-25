"""
Схема ответа для /api/v1/filters/values.
"""

from pydantic import BaseModel


class FiltersValuesOut(BaseModel):
    cities: list[str]
    levels: list[str]
    study_forms: list[str]
    languages: list[str]
