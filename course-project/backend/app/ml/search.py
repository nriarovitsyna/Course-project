from typing import Any, Dict, List, Optional

from app.ml.features import program_to_dict
from app.ml.utils import safe_lower


# ---------------------------------------------------------------------------
# Вспомогательные функции
# ---------------------------------------------------------------------------

def _to_float(value: Any) -> Optional[float]:
    """Преобразует значение в float, если это возможно."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_str(value: Any) -> str:
    """Безопасно приводит значение к строке в нижнем регистре."""
    return safe_lower(value) if value is not None else ""


def _contains_any(text: str, values: List[str]) -> bool:
    """Проверяет, содержит ли строка хотя бы одно значение из списка."""
    if not text or not values:
        return False
    return any(v in text for v in values if v)


def _equals_any(text: str, values: List[str]) -> bool:
    """Проверяет, совпадает ли строка хотя бы с одним значением из списка."""
    if not text or not values:
        return False
    return any(text == v for v in values if v)


def _normalize_query_list(values: Optional[List[Any]]) -> List[str]:
    """Нормализует список строк из фильтра пользователя."""
    if not values:
        return []
    result = []
    for value in values:
        lowered = _safe_str(value).strip()
        if lowered and lowered not in result:
            result.append(lowered)
    return result


def _match_text_field(program_value: Any, query_values: List[str], exact: bool = False) -> bool:
    """Сравнивает текстовое поле программы со списком значений из запроса."""
    if not query_values:
        return True

    text = _safe_str(program_value)
    if not text:
        return False

    if exact:
        return _equals_any(text, query_values)

    return _contains_any(text, query_values)


def _match_numeric_min(program_value: Any, min_value: Optional[float]) -> bool:
    """Проверяет, что значение программы не меньше минимального порога."""
    if min_value is None:
        return True

    value = _to_float(program_value)
    if value is None:
        return False

    return value >= min_value


def _match_numeric_max(program_value: Any, max_value: Optional[float]) -> bool:
    """Проверяет, что значение программы не больше максимального порога."""
    if max_value is None:
        return True

    value = _to_float(program_value)
    if value is None:
        return False

    return value <= max_value


def _match_numeric_range(program_value: Any, min_value: Optional[float], max_value: Optional[float]) -> bool:
    """Проверяет попадание числового поля программы в диапазон."""
    return _match_numeric_min(program_value, min_value) and _match_numeric_max(program_value, max_value)


def _normalize_duration_to_years(duration_value: Any) -> Optional[float]:
    """Преобразует длительность вида '4 года' или '6 лет' в число лет."""
    if duration_value is None:
        return None

    text = _safe_str(duration_value)
    if not text:
        return None

    import re
    match = re.search(r"(\d+(?:[.,]\d+)?)", text)
    if not match:
        return None

    try:
        return float(match.group(1).replace(",", "."))
    except ValueError:
        return None


def _match_duration(program_value: Any, min_value: Optional[float], max_value: Optional[float]) -> bool:
    """Проверяет, подходит ли длительность обучения под диапазон."""
    if min_value is None and max_value is None:
        return True

    years = _normalize_duration_to_years(program_value)
    if years is None:
        return False

    if min_value is not None and years < min_value:
        return False
    if max_value is not None and years > max_value:
        return False

    return True


# ---------------------------------------------------------------------------
# Основная логика фильтрации одной программы
# ---------------------------------------------------------------------------

def program_matches(program: Any, query_data: Dict[str, Any]) -> bool:
    """Проверяет, подходит ли одна программа под фильтры запроса."""
    p = program_to_dict(program)

    # --- Текстовые списки ---
    detected_names = _normalize_query_list(query_data.get("detected_names"))
    detected_cities = _normalize_query_list(query_data.get("detected_cities"))
    detected_faculties = _normalize_query_list(query_data.get("detected_faculties"))
    detected_universities = _normalize_query_list(query_data.get("detected_universities"))
    detected_levels = _normalize_query_list(query_data.get("detected_levels"))
    detected_languages = _normalize_query_list(query_data.get("detected_languages"))
    detected_accreditations = _normalize_query_list(query_data.get("detected_accreditations"))
    detected_study_formats = _normalize_query_list(query_data.get("detected_study_formats"))

    # --- Булево поле ---
    detected_budget = query_data.get("detected_budget")

    # --- Числовые диапазоны ---
    detected_duration_min = _to_float(query_data.get("detected_duration_min"))
    detected_duration_max = _to_float(query_data.get("detected_duration_max"))

    detected_price_min = _to_float(query_data.get("detected_price_min"))
    detected_price_max = _to_float(query_data.get("detected_price_max"))

    detected_budget_score_min = _to_float(query_data.get("detected_budget_score_min"))
    detected_budget_score_max = _to_float(query_data.get("detected_budget_score_max"))

    detected_paid_score_min = _to_float(query_data.get("detected_paid_score_min"))
    detected_paid_score_max = _to_float(query_data.get("detected_paid_score_max"))

    detected_budget_places_min = _to_float(query_data.get("detected_budget_places_min"))
    detected_budget_places_max = _to_float(query_data.get("detected_budget_places_max"))

    detected_paid_places_min = _to_float(query_data.get("detected_paid_places_min"))
    detected_paid_places_max = _to_float(query_data.get("detected_paid_places_max"))

    # -----------------------------------------------------------------------
    # Текстовые проверки
    # -----------------------------------------------------------------------

    # name
    if detected_names:
        if not _match_text_field(p.get("name"), detected_names, exact=False):
            return False

    # city
    if detected_cities:
        if not _match_text_field(p.get("city"), detected_cities, exact=False):
            return False

    # faculty
    if detected_faculties:
        faculty_ok = _match_text_field(p.get("faculty"), detected_faculties, exact=False)
        name_ok = _match_text_field(p.get("name"), detected_faculties, exact=False)
        if not (faculty_ok or name_ok):
            return False

    # university
    if detected_universities:
        if not _match_text_field(p.get("university_name"), detected_universities, exact=False):
            return False

    # level
    if detected_levels:
        if not _match_text_field(p.get("level"), detected_levels, exact=False):
            return False

    # language
    if detected_languages:
        if not _match_text_field(p.get("language"), detected_languages, exact=False):
            return False

    # accreditation
    if detected_accreditations:
        if not _match_text_field(p.get("accreditation"), detected_accreditations, exact=False):
            return False

    # study format
    if detected_study_formats:
        if not _match_text_field(p.get("study_format"), detected_study_formats, exact=False):
            return False

    # -----------------------------------------------------------------------
    # Булево поле бюджет / платное
    # -----------------------------------------------------------------------

    if detected_budget is True:
        budget_places = _to_float(p.get("budget_places"))
        if budget_places is None or budget_places <= 0:
            return False

    if detected_budget is False:
        paid_places = _to_float(p.get("paid_places"))
        if paid_places is None or paid_places <= 0:
            return False

    # -----------------------------------------------------------------------
    # Числовые проверки
    # -----------------------------------------------------------------------

    # tuition_cost_rub_year
    if not _match_numeric_range(p.get("tuition_cost_rub_year"), detected_price_min, detected_price_max):
        return False

    # duration
    if not _match_duration(p.get("duration"), detected_duration_min, detected_duration_max):
        return False

    # budget_passing_score
    if not _match_numeric_range(p.get("budget_passing_score"), detected_budget_score_min, detected_budget_score_max):
        return False

    # paid_min_score
    if not _match_numeric_range(p.get("paid_min_score"), detected_paid_score_min, detected_paid_score_max):
        return False

    # budget_places
    if not _match_numeric_range(p.get("budget_places"), detected_budget_places_min, detected_budget_places_max):
        return False

    # paid_places
    if not _match_numeric_range(p.get("paid_places"), detected_paid_places_min, detected_paid_places_max):
        return False

    return True


# ---------------------------------------------------------------------------
# Фильтрация списка программ
# ---------------------------------------------------------------------------

def filter_programs(programs: List[Any], query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Фильтрует список программ и возвращает только подходящие."""
    result = []

    for program in programs:
        if program_matches(program, query_data):
            result.append(program_to_dict(program))

    return result


# ---------------------------------------------------------------------------
# Удобная обёртка для анализа причин отсева
# ---------------------------------------------------------------------------

def explain_program_mismatch(program: Any, query_data: Dict[str, Any]) -> List[str]:
    """Возвращает список причин, по которым программа не прошла фильтр."""
    p = program_to_dict(program)
    reasons = []

    detected_cities = _normalize_query_list(query_data.get("detected_cities"))
    detected_faculties = _normalize_query_list(query_data.get("detected_faculties"))
    detected_universities = _normalize_query_list(query_data.get("detected_universities"))
    detected_levels = _normalize_query_list(query_data.get("detected_levels"))
    detected_languages = _normalize_query_list(query_data.get("detected_languages"))
    detected_accreditations = _normalize_query_list(query_data.get("detected_accreditations"))
    detected_study_formats = _normalize_query_list(query_data.get("detected_study_formats"))

    detected_budget = query_data.get("detected_budget")

    detected_duration_min = _to_float(query_data.get("detected_duration_min"))
    detected_duration_max = _to_float(query_data.get("detected_duration_max"))
    detected_price_min = _to_float(query_data.get("detected_price_min"))
    detected_price_max = _to_float(query_data.get("detected_price_max"))
    detected_budget_score_min = _to_float(query_data.get("detected_budget_score_min"))
    detected_budget_score_max = _to_float(query_data.get("detected_budget_score_max"))
    detected_paid_score_min = _to_float(query_data.get("detected_paid_score_min"))
    detected_paid_score_max = _to_float(query_data.get("detected_paid_score_max"))
    detected_budget_places_min = _to_float(query_data.get("detected_budget_places_min"))
    detected_budget_places_max = _to_float(query_data.get("detected_budget_places_max"))
    detected_paid_places_min = _to_float(query_data.get("detected_paid_places_min"))
    detected_paid_places_max = _to_float(query_data.get("detected_paid_places_max"))

    if detected_cities and not _match_text_field(p.get("city"), detected_cities):
        reasons.append("Не совпадает город")

    if detected_faculties:
        faculty_ok = _match_text_field(p.get("faculty"), detected_faculties)
        name_ok = _match_text_field(p.get("name"), detected_faculties)
        if not (faculty_ok or name_ok):
            reasons.append("Не совпадает факультет или направление")

    if detected_universities and not _match_text_field(p.get("university_name"), detected_universities):
        reasons.append("Не совпадает университет")

    if detected_levels and not _match_text_field(p.get("level"), detected_levels):
        reasons.append("Не совпадает уровень образования")

    if detected_languages and not _match_text_field(p.get("language"), detected_languages):
        reasons.append("Не совпадает язык обучения")

    if detected_accreditations and not _match_text_field(p.get("accreditation"), detected_accreditations):
        reasons.append("Не совпадает тип аккредитации")

    if detected_study_formats and not _match_text_field(p.get("study_format"), detected_study_formats):
        reasons.append("Не совпадает формат обучения")

    if detected_budget is True:
        budget_places = _to_float(p.get("budget_places"))
        if budget_places is None or budget_places <= 0:
            reasons.append("Нет бюджетных мест")

    if detected_budget is False:
        paid_places = _to_float(p.get("paid_places"))
        if paid_places is None or paid_places <= 0:
            reasons.append("Нет платных мест")

    if not _match_numeric_range(p.get("tuition_cost_rub_year"), detected_price_min, detected_price_max):
        reasons.append("Не подходит стоимость")

    if not _match_duration(p.get("duration"), detected_duration_min, detected_duration_max):
        reasons.append("Не подходит длительность")

    if not _match_numeric_range(p.get("budget_passing_score"), detected_budget_score_min, detected_budget_score_max):
        reasons.append("Не подходит проходной балл на бюджет")

    if not _match_numeric_range(p.get("paid_min_score"), detected_paid_score_min, detected_paid_score_max):
        reasons.append("Не подходит минимальный балл на платное")

    if not _match_numeric_range(p.get("budget_places"), detected_budget_places_min, detected_budget_places_max):
        reasons.append("Не подходит количество бюджетных мест")

    if not _match_numeric_range(p.get("paid_places"), detected_paid_places_min, detected_paid_places_max):
        reasons.append("Не подходит количество платных мест")

    return reasons