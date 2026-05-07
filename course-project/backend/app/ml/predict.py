from pathlib import Path
from typing import List, Any, Dict, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from app.schemas.ml import (
    PredictionRequest,
    PredictionResponse,
    PredictPassingScoreRequest,
    PredictPassingScoreResponse,
    ClassifyCompetitivenessRequest,
    ClassifyCompetitivenessResponse,
)
from app.ml.features import program_to_dict


# ===== СТАРЫЕ ФУНКЦИИ (оставлены для совместимости) =====

def predict_price_from_programs(programs: List[Any], req: PredictionRequest) -> PredictionResponse:
    prices = []
    for p in programs:
        price = program_to_dict(p).get("price")
        if isinstance(price, (int, float)) and price > 0:
            prices.append(float(price))

    if not prices:
        return PredictionResponse(
            value=0.0,
            model_name="baseline_mean",
            details={"message": "нет данных для прогноза"},
        )

    mean_price = sum(prices) / len(prices)

    adjustment = 0.0
    if req.has_budget is True:
        adjustment -= mean_price * 0.1
    if req.level and req.level.lower() == "магистратура":
        adjustment += mean_price * 0.08

    predicted = max(0.0, mean_price + adjustment)

    return PredictionResponse(
        value=round(predicted, 2),
        model_name="baseline_mean",
        details={"sample_size": len(prices), "base_mean": round(mean_price, 2)},
    )


def predict_popularity_from_programs(programs: List[Any], req: PredictionRequest) -> PredictionResponse:
    score = 50.0

    if req.has_budget:
        score += 15
    if req.level and req.level.lower() in ["бакалавриат", "магистратура"]:
        score += 10
    if req.study_format and req.study_format.lower() in ["очная", "очно"]:
        score += 10
    if req.description:
        score += min(len(req.description) / 20.0, 15)

    score = min(score, 100.0)

    return PredictionResponse(
        value=round(score, 2),
        model_name="heuristic_popularity",
        details={"range": "0-100"},
    )


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def _norm_text(value: Any) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    return text if text else "unknown"


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_encode(encoder: LabelEncoder, value: str) -> int:
    value = _norm_text(value)
    try:
        return int(encoder.transform([value])[0])
    except ValueError:
        if "unknown" in encoder.classes_:
            return int(encoder.transform(["unknown"])[0])
        return 0


def _fit_label_encoder_with_unknown(series: pd.Series) -> LabelEncoder:
    values = series.fillna("unknown").astype(str).replace("", "unknown").tolist()
    if "unknown" not in values:
        values.append("unknown")
    le = LabelEncoder()
    le.fit(values)
    return le


def _build_feature_dataframe(programs: List[Any], with_target: bool = True) -> pd.DataFrame:
    """
    Расширенная сборка признаков:
    - базовые: city, level, duration, university_name, price, budget_places, paid_places
    - новые: total_places, budget_ratio, price_log
    """
    data = []

    for p in programs:
        d = program_to_dict(p)

        price = _to_float(d.get("price") or d.get("tuition_cost_rub_year"), 0.0)
        budget_places = _to_float(d.get("budget_places") or d.get("budgetPlaces"), 0.0)
        paid_places = _to_float(d.get("paid_places") or d.get("paidPlaces"), 0.0)
        total_places = budget_places + paid_places
        budget_ratio = (budget_places / total_places) if total_places > 0 else 0.0
        price_log = float(np.log1p(max(price, 0.0)))

        row = {
            "city": _norm_text(d.get("city")),
            "level": _norm_text(d.get("level")),
            "duration": _to_float(d.get("duration"), 0.0),
            "university_name": _norm_text(d.get("university_name") or d.get("universityName")),
            "price": price,
            "price_log": price_log,
            "budget_places": budget_places,
            "paid_places": paid_places,
            "total_places": total_places,
            "budget_ratio": budget_ratio,
        }

        if with_target:
            row["budget_passing_score"] = _to_float(
                d.get("budget_passing_score") or d.get("budgetPassingScore"),
                0.0,
            )

        data.append(row)

    return pd.DataFrame(data)


def _encode_categorical_features(
    df: pd.DataFrame, categorical_cols: List[str]
) -> Tuple[pd.DataFrame, Dict[str, LabelEncoder]]:
    df = df.copy()
    encoders: Dict[str, LabelEncoder] = {}

    for col in categorical_cols:
        df[col] = df[col].fillna("unknown").astype(str).replace("", "unknown")
        le = _fit_label_encoder_with_unknown(df[col])
        df[f"{col}_encoded"] = le.transform(df[col])
        encoders[col] = le

    return df, encoders


def _prepare_regression_data(programs: List[Any]) -> Tuple[pd.DataFrame, np.ndarray, Dict[str, LabelEncoder]]:
    """
    Признаки для регрессии:
    - city, level, university_name (категориальные)
    - duration, price, price_log, budget_places, paid_places, total_places, budget_ratio (числовые)

    Целевая переменная:
    - budget_passing_score
    """
    df = _build_feature_dataframe(programs, with_target=True)

    df = df[df["budget_passing_score"] > 0].copy()

    if len(df) < 30:
        raise ValueError(
            f"Недостаточно данных для обучения модели: только {len(df)} программ с проходным баллом"
        )

    categorical_cols = ["city", "level", "university_name"]
    df, encoders = _encode_categorical_features(df, categorical_cols)

    feature_cols = [
        "price",
        "price_log",
        "budget_places",
        "paid_places",
        "total_places",
        "budget_ratio",
        "duration",
        "city_encoded",
        "level_encoded",
        "university_name_encoded",
    ]

    X = df[feature_cols]
    y = df["budget_passing_score"].values

    return X, y, encoders


def _build_regression_input(req: PredictPassingScoreRequest, encoders: Dict[str, LabelEncoder]) -> pd.DataFrame:
    price = _to_float(getattr(req, "price", None), 0.0)
    budget_places = _to_float(getattr(req, "budget_places", None), 0.0)
    paid_places = _to_float(getattr(req, "paid_places", None), 0.0)
    total_places = budget_places + paid_places
    budget_ratio = (budget_places / total_places) if total_places > 0 else 0.0
    price_log = float(np.log1p(max(price, 0.0)))

    city_encoded = _safe_encode(encoders["city"], getattr(req, "city", None) or "unknown")
    level_encoded = _safe_encode(encoders["level"], getattr(req, "level", None) or "unknown")
    university_encoded = _safe_encode(
        encoders["university_name"],
        getattr(req, "university_name", None) or "unknown",
    )

    return pd.DataFrame(
        [
            {
                "price": price,
                "price_log": price_log,
                "budget_places": budget_places,
                "paid_places": paid_places,
                "total_places": total_places,
                "budget_ratio": budget_ratio,
                "duration": _to_float(getattr(req, "duration", None), 0.0),
                "city_encoded": city_encoded,
                "level_encoded": level_encoded,
                "university_name_encoded": university_encoded,
            }
        ]
    )


# ===== НОВАЯ РЕГРЕССИЯ ПРОХОДНОГО БАЛЛА =====

def predict_passing_score_from_programs(
    programs: List[Any],
    req: PredictPassingScoreRequest,
) -> PredictPassingScoreResponse:
    """
    Регрессия проходного балла по признакам текущего датасета:
    - город, уровень образования, вуз (категории)
    - длительность, стоимость (и её логарифм),
    - количество бюджетных/платных мест, суммарные места, доля бюджета.
    """
    try:
        X, y, encoders = _prepare_regression_data(programs)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        model = RandomForestRegressor(
            n_estimators=500,
            max_depth=None,
            min_samples_leaf=3,
            max_features="sqrt",
            random_state=42,
            n_jobs=-1,
        )
        model.fit(X_train, y_train)

        y_pred_test = model.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred_test)
        r2 = r2_score(y_test, y_pred_test)

        X_new = _build_regression_input(req, encoders)
        predicted_score = float(model.predict(X_new)[0])

        predicted_score = max(0.0, min(310.0, predicted_score))

        return PredictPassingScoreResponse(
            predicted_score=round(predicted_score, 1),
            model_name="RandomForestRegressor",
            confidence_interval=f"± {round(mae, 1)} баллов",
            model_metrics={
                "mae": round(mae, 2),
                "r2_score": round(r2, 3),
                "train_size": len(X_train),
                "test_size": len(X_test),
                "features": list(X.columns),
            },
            details={
                "interpretation": (
                    "Прогноз построен по текущему датасету программ с учётом города, уровня, вуза, "
                    "длительности, стоимости, числа бюджетных/платных мест, общей ёмкости и доли бюджета. "
                    f"Модель обучена на {len(X_train)} программах. "
                    f"Средняя ошибка на тестовой выборке: {round(mae, 1)} баллов. "
                    f"R² = {round(r2, 3)}. "
                    "Результат следует рассматривать как ориентировочную оценку по аналогичным программам."
                )
            },
        )

    except Exception as e:
        return PredictPassingScoreResponse(
            predicted_score=0.0,
            model_name="error",
            confidence_interval=None,
            model_metrics=None,
            details={"error": str(e)},
        )


# ===== ML-КЛАССИФИКАЦИЯ КОНКУРЕНТОСПОСОБНОСТИ =====

MODEL_DIR = Path(__file__).resolve().parent / "saved_models"
MODEL_PATH = MODEL_DIR / "competitiveness_rf_model.joblib"
META_PATH = MODEL_DIR / "competitiveness_meta.joblib"

try:
    _competitiveness_model = joblib.load(MODEL_PATH)
    _competitiveness_meta: Dict[str, Any] = joblib.load(META_PATH)

    _category_names: Dict[int, str] = _competitiveness_meta.get(
        "category_names",
        {0: "Доступная", 1: "Стандартная", 2: "Высококонкурентная"},
    )

    # class_profile уже в формате {class_id: {metric: value}}
    _class_profile: Dict[int, Dict[str, float]] = _competitiveness_meta.get("class_profile", {})

    # топ-3 городов по каждому классу
    _top_cities_by_class: Dict[int, List[str]] = _competitiveness_meta.get("top_cities_by_class", {})

    _clf_loaded_ok = True
except Exception as e:
    _competitiveness_model = None
    _competitiveness_meta = {"load_error": str(e)}
    _category_names = {0: "Доступная", 1: "Стандартная", 2: "Высококонкурентная"}
    _class_profile = {}
    _top_cities_by_class = {}
    _clf_loaded_ok = False


def _build_classification_input(req: ClassifyCompetitivenessRequest) -> pd.DataFrame:
    """
    Формируем признаки в том же формате, что использовался при обучении train_competitiveness_model.py.
    """
    faculty = _norm_text(getattr(req, "faculty", None))
    level = _norm_text(getattr(req, "level", None))
    university_name = _norm_text(getattr(req, "university_name", None))
    city = _norm_text(getattr(req, "city", None))
    study_format = _norm_text(getattr(req, "study_format", None))
    language = _norm_text(getattr(req, "language", None))
    accreditation = _norm_text(getattr(req, "accreditation", None))

    budget_places = _to_float(getattr(req, "budget_places", None), 0.0)
    paid_places = _to_float(getattr(req, "paid_places", None), 0.0)
    total_places = budget_places + paid_places
    budget_ratio = (budget_places / total_places) if total_places > 0 else 0.0

    tuition_cost = _to_float(getattr(req, "price", None), 0.0)
    tuition_log = float(np.log1p(max(tuition_cost, 0.0)))

    # пользователь может явно ввести проходной балл
    budget_passing_score = _to_float(getattr(req, "budget_passing_score", None), 0.0)
    paid_min_score = _to_float(getattr(req, "paid_min_score", None), 0.0)
    duration = _to_float(getattr(req, "duration", None), 0.0)

    paid_min_score_missing = 1 if paid_min_score <= 0 else 0
    budget_score_missing = 1 if budget_passing_score <= 0 else 0

    row = {
        "faculty": faculty,
        "level": level,
        "university_name": university_name,
        "city": city,
        "study_format": study_format,
        "language": language,
        "accreditation": accreditation,
        "budget_places": budget_places,
        "paid_places": paid_places,
        "total_places": total_places,
        "budget_ratio": budget_ratio,
        "tuition_cost_rub_year": tuition_cost,
        "tuition_log": tuition_log,
        "budget_passing_score": budget_passing_score,
        "paid_min_score": paid_min_score,
        "duration": duration,
        "paid_min_score_missing": paid_min_score_missing,
        "budget_score_missing": budget_score_missing,
    }

    return pd.DataFrame([row])


def _get_class_profile_for_id(class_id: int) -> Dict[str, float]:
    """
    Берём профиль класса из meta["class_profile"], формат: {class_id: {metric: value}}.
    """
    return _class_profile.get(class_id, {})


def classify_competitiveness_from_programs(
    programs: List[Any],
    req: ClassifyCompetitivenessRequest,
) -> ClassifyCompetitivenessResponse:
    try:
        if not _clf_loaded_ok or _competitiveness_model is None:
            return ClassifyCompetitivenessResponse(
                category="Ошибка",
                probabilities={},
                model_name="competitiveness_model_not_loaded",
                accuracy=None,
                model_metrics={
                    "model_path": str(MODEL_PATH),
                    "meta_path": str(META_PATH),
                    "model_exists": MODEL_PATH.exists(),
                    "meta_exists": META_PATH.exists(),
                },
                details={
                    "error": (
                        "Модель конкурентоспособности не загружена. "
                        f"Причина: {_competitiveness_meta.get('load_error', 'unknown')}"
                    )
                },
            )

        # 1. Формируем вход для модели
        X_new = _build_classification_input(req)

        expected_cat = _competitiveness_meta.get("categorical_cols", [])
        expected_num = _competitiveness_meta.get("numeric_cols", [])
        expected_cols = expected_cat + expected_num

        missing_cols = [c for c in expected_cols if c not in X_new.columns]
        extra_cols = [c for c in X_new.columns if c not in expected_cols]

        if missing_cols:
            return ClassifyCompetitivenessResponse(
                category="Ошибка",
                probabilities={},
                model_name="input_columns_missing",
                accuracy=None,
                model_metrics={
                    "expected_columns": expected_cols,
                    "received_columns": list(X_new.columns),
                    "missing_columns": missing_cols,
                    "extra_columns": extra_cols,
                },
                details={
                    "error": f"Во входных данных отсутствуют колонки: {missing_cols}"
                },
            )

        X_new = X_new[expected_cols]

        # 2. Предсказание класса и вероятностей
        class_id = int(_competitiveness_model.predict(X_new)[0])
        proba = _competitiveness_model.predict_proba(X_new)[0]

        category = _category_names.get(class_id, "Не определено")

        probabilities: Dict[str, float] = {}
        for cls, p in zip(_competitiveness_model.classes_, proba):
            cls_int = int(cls)
            class_name = _category_names.get(cls_int, str(cls_int))
            probabilities[class_name] = round(float(p) * 100, 1)

        # 3. Метрики из train-скрипта + перевод accuracy/f1 в проценты
        metrics = _competitiveness_meta.get("metrics", {})
        accuracy_percent = round(float(metrics.get("accuracy", 0.0)) * 100.0, 1)
        f1_percent = round(float(metrics.get("f1_macro", 0.0)) * 100.0, 1)

        # 4. Характеристики класса из meta["class_profile"]
        class_profile = _get_class_profile_for_id(class_id)

        score_mean = class_profile.get("budget_passing_score")
        price_mean = class_profile.get("tuition_cost_rub_year")
        budget_places_mean = class_profile.get("budget_places")
        paid_places_mean = class_profile.get("paid_places")
        total_places_mean = class_profile.get("total_places")
        budget_ratio_mean = (
            class_profile.get("budget_ratio") * 100.0
            if class_profile.get("budget_ratio") is not None
            else None
        )
        duration_mean = class_profile.get("duration")

        top_cities = _top_cities_by_class.get(class_id, [])

        # 5. Интерпретация категории
        interpretation_parts: List[str] = []

        # 5.1 Общая формулировка категории
        interpretation_parts.append(
            f"Программа отнесена к категории «{category}»."
        )

        if category == "Высококонкурентная":
            interpretation_parts.append(
                "Программы этой категории, как правило, отличаются высоким конкурсом и более строгими требованиями к абитуриентам."
            )
        elif category == "Стандартная":
            interpretation_parts.append(
                "Программы этой категории, как правило, имеют умеренный или выше среднего уровень конкурса и сбалансированные условия поступления."
            )
        elif category == "Доступная":
            interpretation_parts.append(
                "Программы этой категории, как правило, имеют более мягкие условия поступления и ниже уровень конкуренции."
            )

        # 5.2 Цифровые характеристики класса
        stats_parts: List[str] = []

        if score_mean is not None:
            stats_parts.append(
                f"Средний проходной балл по программам этой категории — около {round(score_mean, 1)}."
            )

        if price_mean is not None:
            stats_parts.append(
                f"Средняя стоимость обучения — примерно {int(round(price_mean))} ₽ в год."
            )

        if (
            budget_places_mean is not None
            and paid_places_mean is not None
            and total_places_mean is not None
            and budget_ratio_mean is not None
        ):
            stats_parts.append(
                f"В среднем на программу приходится около {int(round(budget_places_mean))} бюджетных и "
                f"{int(round(paid_places_mean))} платных мест "
                f"(доля бюджета — около {round(budget_ratio_mean, 1)}%)."
            )

        if duration_mean is not None and duration_mean > 0:
            stats_parts.append(
                f"Cредняя длительность обучения — около {round(duration_mean, 1)} лет"
            )

        if stats_parts:
            interpretation_parts.append(" ".join(stats_parts) + ".")

        # 5.3 Города
        if top_cities:
            interpretation_parts.append(
                "Чаще всего такие программы представлены в городах: "
                + ", ".join(top_cities)
                + "."
            )

        # 5.4 Контекст по текущему запросу
        city_str = str(X_new["city"].iloc[0] or "").strip() or "город не указан"
        level_str = str(X_new["level"].iloc[0] or "").strip() or "уровень не указан"
        university_name = str(X_new["university_name"].iloc[0] or "").strip() or "Вуз не указан"

        interpretation_text = " ".join(interpretation_parts)

        return ClassifyCompetitivenessResponse(
            category=category,
            probabilities=probabilities,
            model_name="RandomForestClassifier",
            accuracy=accuracy_percent,
            model_metrics={
                "accuracy": accuracy_percent,
                "f1_macro": f1_percent,
                "train_size": metrics.get("train_size"),
                "test_size": metrics.get("test_size"),
                "expected_columns": expected_cols,
                "received_columns": list(X_new.columns),
                "class_profile": class_profile,
                "top_cities_by_class": _top_cities_by_class,
            },
            details={"interpretation": interpretation_text},
        )

    except Exception as e:
        return ClassifyCompetitivenessResponse(
            category="Ошибка",
            probabilities={},
            model_name="error",
            accuracy=None,
            model_metrics={
                "model_path": str(MODEL_PATH),
                "meta_path": str(META_PATH),
                "model_exists": MODEL_PATH.exists(),
                "meta_exists": META_PATH.exists(),
            },
            details={"error": repr(e)},
        )