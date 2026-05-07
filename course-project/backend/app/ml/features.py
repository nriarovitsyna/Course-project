from typing import Any, Dict
from app.ml.utils import safe_lower, bool_to_num


def get_attr(obj, *names, default=None):
    """Возвращает первый найденный атрибут объекта из списка имён."""
    for name in names:
        if hasattr(obj, name):
            return getattr(obj, name)
    return default


def program_to_dict(program) -> Dict[str, Any]:
    """Преобразует объект Program в словарь с полями для поиска и выдачи."""
    budget_places = get_attr(program, "budget_places")
    has_budget = bool(budget_places and budget_places > 0)

    tuition_cost = get_attr(program, "tuition_cost_rub_year", "price", "tuition_fee")

    return {
        "id": get_attr(program, "id"),
        "name": get_attr(program, "name", "program_name"),
        "program_code": get_attr(program, "program_code"),
        "university_name": get_attr(program, "university_name", "university"),
        "city": get_attr(program, "city"),
        "faculty": get_attr(program, "faculty"),
        "level": get_attr(program, "level"),
        "study_format": get_attr(program, "study_format", "format"),
        "language": get_attr(program, "language"),
        "accreditation": get_attr(program, "accreditation"),
        "duration": get_attr(program, "duration"),

        # цена
        "tuition_cost_rub_year": tuition_cost,
        "price": tuition_cost,

        # места
        "budget_places": budget_places,
        "paid_places": get_attr(program, "paid_places"),

        # баллы
        "budget_passing_score": get_attr(program, "budget_passing_score"),
        "paid_min_score": get_attr(program, "paid_min_score"),

        # остальное
        "has_budget": get_attr(program, "has_budget", default=has_budget),
        "description": get_attr(program, "description", "about"),
    }


def numeric_features(program) -> Dict[str, float]:
    """Возвращает числовые признаки программы для ML-моделей."""
    data = program_to_dict(program)
    price = data["price"] if isinstance(data["price"], (int, float)) else 0.0

    return {
        "price": float(price or 0),
        "has_budget": float(bool_to_num(data["has_budget"])),
        "name_len": float(len(safe_lower(data["name"]))),
        "desc_len": float(len(safe_lower(data["description"]))),
        "budget_places": float(data.get("budget_places") or 0),
        "paid_places": float(data.get("paid_places") or 0),
        "budget_passing_score": float(data.get("budget_passing_score") or 0),
        "paid_min_score": float(data.get("paid_min_score") or 0),
    }