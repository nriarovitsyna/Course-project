from typing import Any, Dict

from app.ml.features import program_to_dict
from app.ml.rank import (
    _normalize_program,
    _normalize_query_data,
    _compute_match_score,
    _build_explanation,
)


def explain_program(program: Any, query_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Возвращает объяснение рекомендации по программе с учётом запроса пользователя.
    Совместим с данными:
    - из формы RecommendationRequest
    - из text.py / analyze_text (TextAnalysisResponse)
    """
    raw = program_to_dict(program)
    p = _normalize_program(raw)
    q = _normalize_query_data(query_data)

    score = _compute_match_score(p, q)
    explanation = _build_explanation(p, q, score)

    return {
        "program_id": p.get("id"),
        "match_score": round(score, 3),
        "explanation": explanation,
        "factors": {
            "query": q.get("query", ""),
            "detected_cities": q.get("detected_cities", []),
            "detected_levels": q.get("detected_levels", []),
            "detected_faculties": q.get("detected_faculties", []),
            "detected_universities": q.get("detected_universities", []),
            "detected_study_formats": q.get("detected_study_formats", []),
            "detected_languages": q.get("detected_languages", []),
            "detected_accreditations": q.get("detected_accreditations", []),
            "detected_budget": q.get("detected_budget"),
            "detected_price_min": q.get("detected_price_min"),
            "detected_price_max": q.get("detected_price_max"),
            "detected_min_score": q.get("detected_min_score"),
            "detected_max_score": q.get("detected_max_score"),
            "detected_duration_min": q.get("detected_duration_min"),
            "detected_duration_max": q.get("detected_duration_max"),
            "program_name": p.get("name"),
            "university_name": p.get("university_name"),
            "city": p.get("city"),
            "faculty": p.get("faculty"),
            "level": p.get("level"),
            "study_format": p.get("study_format"),
            "language": p.get("language"),
            "accreditation": p.get("accreditation"),
            "has_budget": p.get("has_budget"),
            "budget_places": p.get("budget_places"),
            "paid_places": p.get("paid_places"),
            "budget_passing_score": p.get("budget_passing_score"),
            "price": p.get("price"),
            "duration": p.get("duration"),
        },
    }