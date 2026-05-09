from typing import Dict, Any, List, Tuple

from app.ml.utils import safe_lower
from app.ml.features import program_to_dict


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _norm(value: Any) -> str:
    return safe_lower(str(value or "")).strip()


def _contains_text(query_value: str, candidate_value: str) -> bool:
    q = _norm(query_value)
    c = _norm(candidate_value)
    if not q or not c:
        return False
    return q in c or c in q


def _format_price(value):
    val = _to_float(value)
    if val is None:
        return None
    return f"{int(val):,}".replace(",", " ")


def _clean_list(values) -> List[str]:
    if values is None:
        return []
    if isinstance(values, (list, tuple, set)):
        result = []
        for v in values:
            if v is None:
                continue
            s = str(v).strip()
            if s:
                result.append(s)
        return result
    s = str(values).strip()
    return [s] if s else []


def _normalize_query_data(query_data: Dict[str, Any]) -> Dict[str, Any]:
    detected_cities = query_data.get("detected_cities")
    if detected_cities is None:
        detected_cities = query_data.get("detectedCities")
    if detected_cities is None:
        single_city = (
            query_data.get("detected_city")
            or query_data.get("detectedCity")
            or query_data.get("city")
        )
        detected_cities = [single_city] if single_city else []

    detected_levels = query_data.get("detected_levels")
    if detected_levels is None:
        detected_levels = query_data.get("detectedLevels")
    if detected_levels is None:
        single_level = (
            query_data.get("detected_level")
            or query_data.get("detectedLevel")
            or query_data.get("level")
        )
        detected_levels = [single_level] if single_level else []

    detected_study_formats = query_data.get("detected_study_formats")
    if detected_study_formats is None:
        detected_study_formats = query_data.get("detectedStudyFormats")
    if detected_study_formats is None:
        single_format = (
            query_data.get("detected_study_format")
            or query_data.get("detectedStudyFormat")
            or query_data.get("study_format")
        )
        detected_study_formats = [single_format] if single_format else []

    detected_languages = query_data.get("detected_languages")
    if detected_languages is None:
        detected_languages = query_data.get("detectedLanguages")
    if detected_languages is None:
        single_language = (
            query_data.get("detected_language")
            or query_data.get("detectedLanguage")
            or query_data.get("language")
        )
        detected_languages = [single_language] if single_language else []

    detected_accreditations = query_data.get("detected_accreditations")
    if detected_accreditations is None:
        detected_accreditations = query_data.get("detectedAccreditations")
    if detected_accreditations is None:
        single_accreditation = (
            query_data.get("detected_accreditation")
            or query_data.get("detectedAccreditation")
            or query_data.get("accreditation")
        )
        detected_accreditations = [single_accreditation] if single_accreditation else []

    detected_faculties = query_data.get("detected_faculties")
    if detected_faculties is None:
        detected_faculties = query_data.get("detectedFaculties")
    if detected_faculties is None:
        single_faculty = (
            query_data.get("detected_faculty")
            or query_data.get("detectedFaculty")
            or query_data.get("faculty")
        )
        detected_faculties = [single_faculty] if single_faculty else []

    detected_universities = query_data.get("detected_universities")
    if detected_universities is None:
        detected_universities = query_data.get("detectedUniversities")
    if detected_universities is None:
        single_university = (
            query_data.get("detected_university")
            or query_data.get("detectedUniversity")
            or query_data.get("university_name")
            or query_data.get("university")
        )
        detected_universities = [single_university] if single_university else []

    detected_min_score = (
        query_data.get("detected_min_score")
        if "detected_min_score" in query_data
        else query_data.get("detectedMinScore")
    )
    if detected_min_score is None:
        detected_min_score = (
            query_data.get("budget_score_min")
            if "budget_score_min" in query_data
            else query_data.get("min_score")
        )
    if detected_min_score is None:
        detected_min_score = query_data.get("detected_budget_score_min") or query_data.get("detectedBudgetScoreMin")

    detected_max_score = (
        query_data.get("detected_max_score")
        if "detected_max_score" in query_data
        else query_data.get("detectedMaxScore")
    )
    if detected_max_score is None:
        detected_max_score = (
            query_data.get("budget_score_max")
            if "budget_score_max" in query_data
            else query_data.get("max_score")
        )
    if detected_max_score is None:
        detected_max_score = query_data.get("detected_budget_score_max") or query_data.get("detectedBudgetScoreMax")

    detected_price_min = (
        query_data.get("detected_price_min")
        if "detected_price_min" in query_data
        else query_data.get("detectedPriceMin")
    )
    if detected_price_min is None:
        detected_price_min = query_data.get("price_min")

    detected_price_max = (
        query_data.get("detected_price_max")
        if "detected_price_max" in query_data
        else query_data.get("detectedPriceMax")
    )
    if detected_price_max is None:
        detected_price_max = query_data.get("price_max")

    detected_duration_min = (
        query_data.get("detected_duration_min")
        if "detected_duration_min" in query_data
        else query_data.get("detectedDurationMin")
    )
    if detected_duration_min is None:
        detected_duration_min = query_data.get("duration_min")

    detected_duration_max = (
        query_data.get("detected_duration_max")
        if "detected_duration_max" in query_data
        else query_data.get("detectedDurationMax")
    )
    if detected_duration_max is None:
        detected_duration_max = query_data.get("duration_max")

    if "detected_budget" in query_data:
        detected_budget = query_data.get("detected_budget")
    elif "detectedBudget" in query_data:
        detected_budget = query_data.get("detectedBudget")
    elif "has_budget" in query_data:
        detected_budget = query_data.get("has_budget")
    else:
        detected_budget = None

    detected_min_budget_places = (
        query_data.get("detected_min_budget_places")
        if "detected_min_budget_places" in query_data
        else query_data.get("detectedMinBudgetPlaces")
    )
    if detected_min_budget_places is None:
        detected_min_budget_places = query_data.get("min_budget_places")
    if detected_min_budget_places is None:
        detected_min_budget_places = query_data.get("budget_places_min")
    if detected_min_budget_places is None:
        detected_min_budget_places = query_data.get("detected_budget_places_min") or query_data.get("detectedBudgetPlacesMin")

    detected_max_budget_places = (
        query_data.get("detected_max_budget_places")
        if "detected_max_budget_places" in query_data
        else query_data.get("detectedMaxBudgetPlaces")
    )
    if detected_max_budget_places is None:
        detected_max_budget_places = query_data.get("max_budget_places")
    if detected_max_budget_places is None:
        detected_max_budget_places = query_data.get("budget_places_max")
    if detected_max_budget_places is None:
        detected_max_budget_places = query_data.get("detected_budget_places_max") or query_data.get("detectedBudgetPlacesMax")

    detected_min_paid_places = (
        query_data.get("detected_min_paid_places")
        if "detected_min_paid_places" in query_data
        else query_data.get("detectedMinPaidPlaces")
    )
    if detected_min_paid_places is None:
        detected_min_paid_places = query_data.get("min_paid_places")
    if detected_min_paid_places is None:
        detected_min_paid_places = query_data.get("paid_places_min")
    if detected_min_paid_places is None:
        detected_min_paid_places = query_data.get("detected_paid_places_min") or query_data.get("detectedPaidPlacesMin")

    detected_max_paid_places = (
        query_data.get("detected_max_paid_places")
        if "detected_max_paid_places" in query_data
        else query_data.get("detectedMaxPaidPlaces")
    )
    if detected_max_paid_places is None:
        detected_max_paid_places = query_data.get("max_paid_places")
    if detected_max_paid_places is None:
        detected_max_paid_places = query_data.get("paid_places_max")
    if detected_max_paid_places is None:
        detected_max_paid_places = query_data.get("detected_paid_places_max") or query_data.get("detectedPaidPlacesMax")

    query_text = (
        query_data.get("query")
        or query_data.get("normalized_query")
        or query_data.get("normalizedQuery")
        or ""
    )

    return {
        "query": str(query_text).strip(),
        "detected_cities": _clean_list(detected_cities),
        "detected_levels": _clean_list(detected_levels),
        "detected_study_formats": _clean_list(detected_study_formats),
        "detected_languages": _clean_list(detected_languages),
        "detected_accreditations": _clean_list(detected_accreditations),
        "detected_faculties": _clean_list(detected_faculties),
        "detected_universities": _clean_list(detected_universities),
        "detected_budget": detected_budget,
        "detected_duration_min": detected_duration_min,
        "detected_duration_max": detected_duration_max,
        "detected_price_min": detected_price_min,
        "detected_price_max": detected_price_max,
        "detected_min_score": detected_min_score,
        "detected_max_score": detected_max_score,
        "detected_min_budget_places": detected_min_budget_places,
        "detected_max_budget_places": detected_max_budget_places,
        "detected_min_paid_places": detected_min_paid_places,
        "detected_max_paid_places": detected_max_paid_places,
    }


def _normalize_program(program: Dict[str, Any]) -> Dict[str, Any]:
    price = program.get("price")
    if price is None:
        price = program.get("tuition_cost_rub_year") or program.get("tuitionCostRubYear")

    budget_passing_score = (
        program.get("budget_passing_score")
        or program.get("budgetPassingScore")
        or program.get("passing_score")
        or program.get("passingScore")
        or program.get("score")
    )

    return {
        "id": program.get("id"),
        "name": program.get("name"),
        "university_name": program.get("university_name") or program.get("universityName"),
        "city": program.get("city"),
        "faculty": program.get("faculty"),
        "level": program.get("level"),
        "study_format": program.get("study_format") or program.get("studyFormat"),
        "price": price,
        "has_budget": program.get("has_budget") if "has_budget" in program else program.get("hasBudget"),
        "description": program.get("description"),
        "duration": program.get("duration"),
        "language": program.get("language"),
        "accreditation": program.get("accreditation"),
        "budget_places": program.get("budget_places") or program.get("budgetPlaces"),
        "paid_places": program.get("paid_places") or program.get("paidPlaces"),
        "budget_passing_score": budget_passing_score,
    }


def _score_exact_list_match(query_values: List[str], program_value: str) -> float:
    if not query_values:
        return 0.0

    p = _norm(program_value)
    if not p:
        return 0.0

    for value in query_values:
        q = _norm(value)
        if not q:
            continue
        if q == p:
            return 1.0
        if q in p or p in q:
            return 0.9
    return 0.0


def _score_city(query_cities: List[str], program_city: str) -> float:
    if not query_cities:
        return 0.0

    p_city = _norm(program_city)
    q_cities = [_norm(c) for c in query_cities if c]
    if not p_city:
        return 0.0

    if p_city in q_cities:
        return 1.0

    moscow_group = {"москва", "московская область", "мытищи", "химки", "одинцово", "подмосковье", "фрязино"}
    spb_group = {"санкт-петербург", "спб", "ленинградская область", "петербург"}

    for q_city in q_cities:
        if q_city in moscow_group and p_city in moscow_group:
            return 0.85
        if q_city in spb_group and p_city in spb_group:
            return 0.85

    return 0.0


def _score_name_match(query: str, program_name: str, faculty: str = "", university_name: str = "") -> float:
    q_norm = _norm(query)
    if not q_norm:
        return 0.0

    target = " ".join([
        _norm(program_name),
        _norm(faculty),
        _norm(university_name),
    ]).strip()

    if not target:
        return 0.0

    query_words = [w for w in q_norm.split() if len(w) >= 3]
    if not query_words:
        return 0.0

    matched = sum(1 for w in query_words if w in target)
    ratio = matched / len(query_words)

    if ratio >= 0.8:
        return 1.0
    if ratio >= 0.6:
        return 0.85
    if ratio >= 0.4:
        return 0.7
    if ratio >= 0.2:
        return 0.5
    return 0.0


def _soft_range_score(q_min, q_max, p_value, lower_is_better_below_min=False, upper_is_better_above_max=False) -> float:
    q_min = _to_float(q_min)
    q_max = _to_float(q_max)
    p = _to_float(p_value)

    if q_min is None and q_max is None:
        return 0.0
    if p is None:
        return 0.0

    if (q_min is None or p >= q_min) and (q_max is None or p <= q_max):
        return 1.0

    if q_min is not None and p < q_min:
        if lower_is_better_below_min:
            diff = q_min - p
            rel = diff / q_min if q_min > 0 else 1.0
            if rel <= 0.10:
                return 0.98
            if rel <= 0.20:
                return 0.95
            if rel <= 0.40:
                return 0.9
            return 0.85

        diff = q_min - p
        rel = diff / q_min if q_min > 0 else 1.0
        if rel <= 0.05:
            return 0.85
        if rel <= 0.15:
            return 0.65
        if rel <= 0.30:
            return 0.35
        return 0.0

    if q_max is not None and p > q_max:
        if upper_is_better_above_max:
            return 1.0

        diff = p - q_max
        rel = diff / q_max if q_max > 0 else 1.0
        if rel <= 0.05:
            return 0.9
        if rel <= 0.10:
            return 0.75
        if rel <= 0.20:
            return 0.55
        if rel <= 0.40:
            return 0.25
        return 0.0

    return 0.0


def _score_price(q_min, q_max, p_price) -> float:
    return _soft_range_score(q_min, q_max, p_price, lower_is_better_below_min=True, upper_is_better_above_max=False)


def _score_score(q_min_score, q_max_score, p_score) -> float:
    return _soft_range_score(q_min_score, q_max_score, p_score, lower_is_better_below_min=False, upper_is_better_above_max=True)


def _score_duration(q_min, q_max, p_duration) -> float:
    return _soft_range_score(q_min, q_max, p_duration, lower_is_better_below_min=False, upper_is_better_above_max=False)


def _score_places(q_min, q_max, p_places) -> float:
    return _soft_range_score(q_min, q_max, p_places, lower_is_better_below_min=False, upper_is_better_above_max=False)


def _score_level(query_levels: List[str], p_level: str) -> float:
    return _score_exact_list_match(query_levels, p_level)


def _score_study_format(query_formats: List[str], p_format: str) -> float:
    return _score_exact_list_match(query_formats, p_format)


def _score_language(query_languages: List[str], p_language: str) -> float:
    return _score_exact_list_match(query_languages, p_language)


def _score_accreditation(query_accs: List[str], p_accreditation: str) -> float:
    return _score_exact_list_match(query_accs, p_accreditation)


def _score_faculty(query_faculties: List[str], p_faculty: str) -> float:
    return _score_exact_list_match(query_faculties, p_faculty)


def _score_university(query_universities: List[str], p_university: str) -> float:
    return _score_exact_list_match(query_universities, p_university)


def _score_budget(q_budget, p_has_budget) -> float:
    if q_budget is None:
        return 0.0
    return 1.0 if bool(q_budget) == bool(p_has_budget) else 0.0


def _sigmoid(x: float) -> float:
    if x >= 8:
        return 0.999
    if x <= -8:
        return 0.001
    import math
    return 1.0 / (1.0 + math.exp(-x))


def _compute_match_score(program: Dict[str, Any], query_data: Dict[str, Any]) -> float:
    """
    Регрессионный score в диапазоне [0, 1]:
    - строим набор признаков совместимости;
    - считаем взвешенную линейную комбинацию;
    - прогоняем через sigmoid;
    - score зависит только от реально заполненных критериев.
    """
    q = _normalize_query_data(query_data)
    p = _normalize_program(program)

    features: List[Tuple[str, float, float]] = []

    has_structured_filters = any([
        bool(q["detected_cities"]),
        bool(q["detected_levels"]),
        bool(q["detected_study_formats"]),
        bool(q["detected_languages"]),
        bool(q["detected_accreditations"]),
        bool(q["detected_faculties"]),
        bool(q["detected_universities"]),
        q["detected_budget"] is not None,
        q["detected_duration_min"] is not None,
        q["detected_duration_max"] is not None,
        q["detected_price_min"] is not None,
        q["detected_price_max"] is not None,
        q["detected_min_score"] is not None,
        q["detected_max_score"] is not None,
        q["detected_min_budget_places"] is not None,
        q["detected_max_budget_places"] is not None,
        q["detected_min_paid_places"] is not None,
        q["detected_max_paid_places"] is not None,
    ])

    if q["detected_cities"]:
        features.append(("city", 2.2, _score_city(q["detected_cities"], p.get("city"))))

    if q["detected_levels"]:
        features.append(("level", 1.2, _score_level(q["detected_levels"], p.get("level"))))

    if q["detected_price_min"] is not None or q["detected_price_max"] is not None:
        features.append(("price", 2.0, _score_price(q["detected_price_min"], q["detected_price_max"], p.get("price"))))

    if q["detected_min_score"] is not None or q["detected_max_score"] is not None:
        features.append(("budget_passing_score", 2.1, _score_score(q["detected_min_score"], q["detected_max_score"], p.get("budget_passing_score"))))

    if q["detected_min_budget_places"] is not None or q["detected_max_budget_places"] is not None:
        features.append(("budget_places", 1.8, _score_places(q["detected_min_budget_places"], q["detected_max_budget_places"], p.get("budget_places"))))

    if q["detected_min_paid_places"] is not None or q["detected_max_paid_places"] is not None:
        features.append(("paid_places", 1.2, _score_places(q["detected_min_paid_places"], q["detected_max_paid_places"], p.get("paid_places"))))

    if q["detected_universities"]:
        features.append(("university", 0.8, _score_university(q["detected_universities"], p.get("university_name"))))

    if q["detected_faculties"]:
        features.append(("faculty", 0.7, _score_faculty(q["detected_faculties"], p.get("faculty"))))

    if q["detected_study_formats"]:
        features.append(("study_format", 0.5, _score_study_format(q["detected_study_formats"], p.get("study_format"))))

    if q["detected_languages"]:
        features.append(("language", 0.4, _score_language(q["detected_languages"], p.get("language"))))

    if q["detected_accreditations"]:
        features.append(("accreditation", 0.3, _score_accreditation(q["detected_accreditations"], p.get("accreditation"))))

    if q["detected_budget"] is not None:
        features.append(("budget_type", 0.5, _score_budget(q["detected_budget"], p.get("has_budget"))))

    if q["detected_duration_min"] is not None or q["detected_duration_max"] is not None:
        features.append(("duration", 0.5, _score_duration(q["detected_duration_min"], q["detected_duration_max"], p.get("duration"))))

    query_text = (q.get("query") or "").strip()
    if query_text and not has_structured_filters:
        features.append(("name", 0.9, _score_name_match(query_text, p.get("name", ""), p.get("faculty", ""), p.get("university_name", ""))))

    if not features:
        return 0.0

    if len(features) == 1 and features[0][0] == "city":
        return 1.0 if features[0][2] >= 0.999 else 0.0

    total_weight = sum(weight for _, weight, _ in features)
    if total_weight <= 0:
        return 0.0

    weighted_mean = sum(weight * value for _, weight, value in features) / total_weight

    missing_penalty = 0.0
    critical_feature_names = {"city", "price", "budget_passing_score", "budget_places", "paid_places", "level"}
    active_critical = [item for item in features if item[0] in critical_feature_names]
    if active_critical:
        critical_scores = [value for _, _, value in active_critical]
        if any(v == 0.0 for v in critical_scores):
            missing_penalty += 0.35
        elif any(v < 0.5 for v in critical_scores):
            missing_penalty += 0.18

    z = (weighted_mean - 0.55) * 6.0 - missing_penalty
    score = _sigmoid(z)

    score = max(0.0, min(1.0, score))
    return round(score, 3)


def _build_explanation(program: Dict[str, Any], query_data: Dict[str, Any], score: float) -> str:
    q = _normalize_query_data(query_data)
    p = _normalize_program(program)

    compatibility_percent = int(round(score * 100))
    program_name = p.get("name") or "Программа"
    university = p.get("university_name") or "неизвестный вуз"

    if score >= 0.9:
        intro = (
            f"Совместимость с запросом — {compatibility_percent}%. "
            f"«{program_name}» в вузе «{university}» очень хорошо подходит под ваши требования."
        )
    elif score >= 0.75:
        intro = (
            f"Совместимость с запросом — {compatibility_percent}%. "
            f"«{program_name}» в вузе «{university}» хорошо подходит, есть небольшие отклонения по отдельным критериям."
        )
    elif score >= 0.5:
        intro = (
            f"Совместимость с запросом — {compatibility_percent}%. "
            f"«{program_name}» подходит частично: совпадает не по всем важным параметрам."
        )
    else:
        intro = (
            f"Совместимость с запросом — {compatibility_percent}%. "
            f"«{program_name}» слабо соответствует указанным условиям."
        )

    parts = []

    if q["detected_cities"]:
        city_score = _score_city(q["detected_cities"], p.get("city"))
        city = p.get("city") or "город не указан"
        if city_score >= 0.999:
            parts.append(f"город полностью совпадает с запросом — {city}")
        elif city_score > 0:
            parts.append(f"город частично соответствует желаемому региону — {city}")
        else:
            parts.append(f"город не совпадает с запросом — {city}")

    if q["detected_levels"]:
        level_score = _score_level(q["detected_levels"], p.get("level"))
        if level_score >= 0.9:
            parts.append(f"уровень образования совпадает — {p.get('level')}")
        else:
            parts.append(f"уровень образования отличается — {p.get('level')}")

    if q["detected_price_min"] is not None or q["detected_price_max"] is not None:
        p_price = _to_float(p.get("price"))
        q_min = _to_float(q["detected_price_min"])
        q_max = _to_float(q["detected_price_max"])

        if p_price is None:
            parts.append("по программе нет данных о стоимости")
        else:
            price_str = _format_price(p_price)
            if (q_min is None or p_price >= q_min) and (q_max is None or p_price <= q_max):
                if q_max is not None and q_min is None:
                    parts.append(f"стоимость обучения {price_str} руб. соответствует требованию (не более {_format_price(q_max)} руб.)")
                elif q_min is not None and q_max is None:
                    parts.append(f"стоимость обучения {price_str} руб. соответствует требованию (от {_format_price(q_min)} руб.)")
                elif q_min is not None and q_max is not None:
                    parts.append(f"стоимость обучения {price_str} руб. попадает в диапазон {_format_price(q_min)}-{_format_price(q_max)} руб.")
            else:
                if q_max is not None and p_price > q_max:
                    parts.append(f"стоимость обучения {price_str} руб. выше допустимого лимита {_format_price(q_max)} руб.")
                elif q_min is not None and p_price < q_min:
                    parts.append(f"стоимость обучения {price_str} руб. ниже указанного минимума {_format_price(q_min)} руб.")

    if q["detected_min_score"] is not None or q["detected_max_score"] is not None:
        p_score = _to_float(p.get("budget_passing_score"))
        q_min = _to_float(q["detected_min_score"])
        q_max = _to_float(q["detected_max_score"])

        if p_score is None:
            parts.append("по программе нет данных о проходном балле")
        else:
            if (q_min is None or p_score >= q_min) and (q_max is None or p_score <= q_max):
                if q_min is not None and q_max is None:
                    parts.append(f"проходной балл {int(p_score)} соответствует требованию (от {int(q_min)} баллов)")
                elif q_max is not None and q_min is None:
                    parts.append(f"проходной балл {int(p_score)} соответствует требованию (до {int(q_max)} баллов)")
                elif q_min is not None and q_max is not None:
                    parts.append(f"проходной балл {int(p_score)} попадает в диапазон {int(q_min)}-{int(q_max)}")
            else:
                if q_min is not None and p_score < q_min:
                    parts.append(f"проходной балл {int(p_score)} ниже требуемого минимума {int(q_min)}")
                elif q_max is not None and p_score > q_max:
                    parts.append(f"проходной балл {int(p_score)} выше указанного максимума {int(q_max)}")

    if q["detected_min_budget_places"] is not None or q["detected_max_budget_places"] is not None:
        p_val = _to_float(p.get("budget_places"))
        q_min = _to_float(q["detected_min_budget_places"])
        q_max = _to_float(q["detected_max_budget_places"])

        if p_val is None:
            parts.append("по программе нет данных о количестве бюджетных мест")
        else:
            if (q_min is None or p_val >= q_min) and (q_max is None or p_val <= q_max):
                if q_min is not None and q_max is None:
                    parts.append(f"количество бюджетных мест ({int(p_val)}) соответствует требованию (не менее {int(q_min)})")
                elif q_max is not None and q_min is None:
                    parts.append(f"количество бюджетных мест ({int(p_val)}) соответствует требованию (не более {int(q_max)})")
                elif q_min is not None and q_max is not None:
                    parts.append(f"количество бюджетных мест ({int(p_val)}) попадает в диапазон {int(q_min)}-{int(q_max)}")
            else:
                if q_min is not None and p_val < q_min:
                    parts.append(f"количество бюджетных мест ({int(p_val)}) меньше требуемых {int(q_min)}")
                elif q_max is not None and p_val > q_max:
                    parts.append(f"количество бюджетных мест ({int(p_val)}) больше допустимых {int(q_max)}")

    if q["detected_min_paid_places"] is not None or q["detected_max_paid_places"] is not None:
        p_val = _to_float(p.get("paid_places"))
        q_min = _to_float(q["detected_min_paid_places"])
        q_max = _to_float(q["detected_max_paid_places"])

        if p_val is None:
            parts.append("по программе нет данных о количестве платных мест")
        else:
            if (q_min is None or p_val >= q_min) and (q_max is None or p_val <= q_max):
                if q_min is not None and q_max is None:
                    parts.append(f"количество платных мест ({int(p_val)}) соответствует требованию (не менее {int(q_min)})")
                elif q_max is not None and q_min is None:
                    parts.append(f"количество платных мест ({int(p_val)}) соответствует требованию (не более {int(q_max)})")
                elif q_min is not None and q_max is not None:
                    parts.append(f"количество платных мест ({int(p_val)}) попадает в диапазон {int(q_min)}-{int(q_max)}")
            else:
                if q_min is not None and p_val < q_min:
                    parts.append(f"количество платных мест ({int(p_val)}) меньше требуемых {int(q_min)}")
                elif q_max is not None and p_val > q_max:
                    parts.append(f"количество платных мест ({int(p_val)}) больше допустимых {int(q_max)}")

    explanation = intro
    if parts:
        explanation += " " + "; ".join(parts).capitalize() + "."
    return explanation


def rank_programs(programs: List[Any], query_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = []

    for raw_program in programs:
        program = program_to_dict(raw_program)
        program_norm = _normalize_program(program)

        score = _compute_match_score(program_norm, query_data)

        item = dict(program_norm)
        item["score"] = score
        item["explanation"] = _build_explanation(program_norm, query_data, score)
        result.append(item)

    result.sort(
        key=lambda x: (
            -(x.get("score") or 0.0),
            -(x.get("budget_passing_score") or -1) if x.get("budget_passing_score") is not None else 1,
            x.get("price") if x.get("price") is not None else 10**12,
            _norm(x.get("name")),
        )
    )
    return result


def filter_programs(programs: List[Any], query_data: Dict[str, Any], threshold: float = 0.0) -> List[Dict[str, Any]]:
    ranked = rank_programs(programs, query_data)
    return [p for p in ranked if (p.get("score") or 0.0) >= threshold]