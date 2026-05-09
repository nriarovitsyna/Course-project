from typing import List, Any, Dict, Optional
from collections import Counter

from app.ml.features import program_to_dict

try:
    import numpy as np
    import pandas as pd

    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.compose import ColumnTransformer
    from sklearn.decomposition import PCA
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import silhouette_score, calinski_harabasz_score, davies_bouldin_score
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import OneHotEncoder, StandardScaler
except Exception:
    np = None
    pd = None
    KMeans = None
    AgglomerativeClustering = None
    ColumnTransformer = None
    PCA = None
    SimpleImputer = None
    silhouette_score = None
    calinski_harabasz_score = None
    davies_bouldin_score = None
    Pipeline = None
    OneHotEncoder = None
    StandardScaler = None


ALLOWED_FEATURES = {
    "name": "categorical",
    "price": "numeric",
    "city": "categorical",
    "budget_passing_score": "numeric",
    "level": "categorical",
    "budget_places": "numeric",
    "study_format": "categorical",
    "duration": "numeric",
}


DEFAULT_FEATURES = [
    "name",
    "price",
    "city",
    "budget_passing_score",
    "level",
]


ALLOWED_ALGORITHMS = {"kmeans", "agglomerative"}


FEATURE_LABELS = {
    "name": "Название программы",
    "price": "Стоимость обучения",
    "city": "Город",
    "budget_passing_score": "Проходной балл",
    "level": "Уровень образования",
    "budget_places": "Количество бюджетных мест",
    "study_format": "Форма обучения",
    "duration": "Продолжительность",
}


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_program(program: Dict[str, Any]) -> Dict[str, Any]:
    price = program.get("price")
    if price is None:
        price = program.get("tuition_cost_rub_year") or program.get("tuitionCostRubYear")

    return {
        "id": program.get("id"),
        "name": program.get("name"),
        "university_name": program.get("university_name") or program.get("universityName"),
        "city": program.get("city"),
        "faculty": program.get("faculty"),
        "level": program.get("level"),
        "study_format": program.get("study_format") or program.get("studyFormat"),
        "price": _to_float(price),
        "has_budget": 1 if (program.get("has_budget") if "has_budget" in program else program.get("hasBudget")) else 0,
        "description": program.get("description"),
        "duration": _to_float(program.get("duration")),
        "language": program.get("language"),
        "accreditation": program.get("accreditation"),
        "budget_places": _to_float(program.get("budget_places") or program.get("budgetPlaces")),
        "paid_places": _to_float(program.get("paid_places") or program.get("paidPlaces")),
        "budget_passing_score": _to_float(program.get("budget_passing_score") or program.get("budgetPassingScore")),
    }


def _validate_features(features: Optional[List[str]]) -> List[str]:
    if not features:
        return DEFAULT_FEATURES.copy()

    cleaned = []
    for f in features:
        if f in ALLOWED_FEATURES and f not in cleaned:
            cleaned.append(f)

    return cleaned if cleaned else DEFAULT_FEATURES.copy()


def _validate_algorithm(algorithm: Optional[str]) -> str:
    algo = (algorithm or "kmeans").strip().lower()
    return algo if algo in ALLOWED_ALGORITHMS else "kmeans"


def _build_dataframe(programs: List[Any], features: List[str]):
    items = [_normalize_program(program_to_dict(p)) for p in programs]
    rows = []

    for item in items:
        row = {
            "id": item["id"],
            "name": item["name"] or f"program_{item['id']}",
            "university_name": item.get("university_name"),
        }
        for feature in features:
            row[feature] = item.get(feature)
        rows.append(row)

    df = pd.DataFrame(rows)
    return items, df


def _build_preprocessor(features: List[str]):
    numeric_features = [f for f in features if ALLOWED_FEATURES[f] == "numeric"]
    categorical_features = [f for f in features if ALLOWED_FEATURES[f] == "categorical"]

    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, numeric_features),
            ("cat", categorical_transformer, categorical_features),
        ],
        remainder="drop"
    )

    return preprocessor, numeric_features, categorical_features


def _safe_round(value, digits=3):
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except Exception:
        return None


def _mode_or_none(values: List[Any]):
    vals = [v for v in values if v not in (None, "", "nan")]
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


def _cluster_description(cluster_id: int, cluster_df):
    city_mode = _mode_or_none(cluster_df["city"].tolist()) if "city" in cluster_df.columns else None
    level_mode = _mode_or_none(cluster_df["level"].tolist()) if "level" in cluster_df.columns else None
    study_format_mode = _mode_or_none(cluster_df["study_format"].tolist()) if "study_format" in cluster_df.columns else None

    mean_price = _safe_round(cluster_df["price"].dropna().mean(), 0) if "price" in cluster_df.columns else None
    mean_score = _safe_round(cluster_df["budget_passing_score"].dropna().mean(), 1) if "budget_passing_score" in cluster_df.columns else None
    mean_budget_places = _safe_round(cluster_df["budget_places"].dropna().mean(), 1) if "budget_places" in cluster_df.columns else None
    mean_duration = _safe_round(cluster_df["duration"].dropna().mean(), 1) if "duration" in cluster_df.columns else None

    parts = [f"Кластер {cluster_id + 1}:"]

    if level_mode:
        parts.append(f"преимущественно программы уровня «{level_mode}»")
    if city_mode:
        parts.append(f"чаще всего в городе «{city_mode}»")
    if study_format_mode:
        parts.append(f"с формой обучения «{study_format_mode}»")
    if mean_price is not None:
        parts.append(f"со средней стоимостью около {int(mean_price):,} руб.".replace(",", " "))
    if mean_score is not None:
        parts.append(f"и средним проходным баллом около {mean_score}")
    if mean_budget_places is not None:
        parts.append(f"при среднем числе бюджетных мест около {mean_budget_places}")
    if mean_duration is not None:
        parts.append(f"и средней продолжительности около {mean_duration} лет")

    return ", ".join(parts) + "."


def _build_model(algorithm: str, n_clusters: int):
    if algorithm == "agglomerative":
        return AgglomerativeClustering(n_clusters=n_clusters)
    return KMeans(n_clusters=n_clusters, random_state=42, n_init=10)


def _available_feature_options() -> List[Dict[str, str]]:
    return [
        {"key": key, "label": FEATURE_LABELS.get(key, key), "type": ALLOWED_FEATURES[key]}
        for key in ALLOWED_FEATURES.keys()
    ]


def cluster_programs(
    programs: List[Any],
    n_clusters: int = 3,
    features: Optional[List[str]] = None,
    algorithm: str = "kmeans",
) -> Dict[str, Any]:
    """
    Полный кластерный анализ образовательных программ:
    - выбор признаков пользователем;
    - выбор алгоритма кластеризации (kmeans или agglomerative);
    - кодирование категориальных признаков;
    - метрики качества;
    - агрегированные описания кластеров;
    - 2D-координаты для визуализации.
    """
    if np is None or pd is None or KMeans is None or AgglomerativeClustering is None:
        return {
            "items": [],
            "cluster_count": 0,
            "algorithm": algorithm,
            "available_algorithms": sorted(ALLOWED_ALGORITHMS),
            "available_features": _available_feature_options(),
            "features_used": [],
            "metrics": {
                "silhouette_score": None,
                "calinski_harabasz_score": None,
                "davies_bouldin_score": None,
            },
            "clusters": [],
            "points": [],
            "message": "sklearn/pandas/numpy недоступны",
        }

    items_raw = [program_to_dict(p) for p in programs]
    algorithm = _validate_algorithm(algorithm)

    if not items_raw:
        return {
            "items": [],
            "cluster_count": 0,
            "algorithm": algorithm,
            "available_algorithms": sorted(ALLOWED_ALGORITHMS),
            "available_features": _available_feature_options(),
            "features_used": [],
            "metrics": {
                "silhouette_score": None,
                "calinski_harabasz_score": None,
                "davies_bouldin_score": None,
            },
            "clusters": [],
            "points": [],
            "message": "Нет данных для кластеризации",
        }

    features_used = _validate_features(features)
    n_clusters = max(2, min(int(n_clusters or 3), 10))

    normalized_items, df = _build_dataframe(programs, features_used)

    if len(df) < n_clusters:
        n_clusters = max(2, min(len(df), 2))

    if len(df) < 2:
        return {
            "items": [],
            "cluster_count": 0,
            "algorithm": algorithm,
            "available_algorithms": sorted(ALLOWED_ALGORITHMS),
            "available_features": _available_feature_options(),
            "features_used": features_used,
            "metrics": {
                "silhouette_score": None,
                "calinski_harabasz_score": None,
                "davies_bouldin_score": None,
            },
            "clusters": [],
            "points": [],
            "message": "Недостаточно программ для кластеризации",
        }

    preprocessor, numeric_features, categorical_features = _build_preprocessor(features_used)
    X = preprocessor.fit_transform(df[features_used])

    if hasattr(X, "toarray"):
        X_dense = X.toarray()
    else:
        X_dense = np.asarray(X)

    model = _build_model(algorithm, n_clusters)
    labels = model.fit_predict(X_dense)

    silhouette = None
    ch_score = None
    db_score = None

    unique_labels = np.unique(labels)
    if len(unique_labels) >= 2 and len(df) > len(unique_labels):
        try:
            silhouette = float(silhouette_score(X_dense, labels))
        except Exception:
            silhouette = None
        try:
            ch_score = float(calinski_harabasz_score(X_dense, labels))
        except Exception:
            ch_score = None
        try:
            db_score = float(davies_bouldin_score(X_dense, labels))
        except Exception:
            db_score = None

    if X_dense.shape[1] > 2:
        reducer = PCA(n_components=2, random_state=42)
        coords = reducer.fit_transform(X_dense)
    elif X_dense.shape[1] == 2:
        coords = X_dense
    else:
        coords = np.column_stack([X_dense[:, 0], np.zeros(len(X_dense))])

    df_result = df.copy()
    df_result["cluster_id"] = labels
    df_result["x"] = coords[:, 0]
    df_result["y"] = coords[:, 1]

    items = []
    points = []
    clusters = []

    for _, row in df_result.iterrows():
        item = {
            "program_id": int(row["id"]),
            "program_name": row["name"],
            "university_name": row["university_name"] if "university_name" in row and pd.notna(row["university_name"]) else None,
            "city": row["city"] if "city" in row and pd.notna(row["city"]) else None,
            "cluster_id": int(row["cluster_id"]),
        }
        items.append(item)

        points.append({
            "program_id": int(row["id"]),
            "program_name": row["name"],
            "cluster_id": int(row["cluster_id"]),
            "x": float(row["x"]),
            "y": float(row["y"]),
        })

    for cluster_id in sorted(df_result["cluster_id"].unique()):
        cluster_df = df_result[df_result["cluster_id"] == cluster_id]

        stat = {
            "cluster_id": int(cluster_id),
            "size": int(len(cluster_df)),
            "description": _cluster_description(int(cluster_id), cluster_df),
            "stats": {
                "price_mean": _safe_round(cluster_df["price"].dropna().mean(), 2) if "price" in cluster_df.columns else None,
                "price_median": _safe_round(cluster_df["price"].dropna().median(), 2) if "price" in cluster_df.columns else None,
                "budget_passing_score_mean": _safe_round(cluster_df["budget_passing_score"].dropna().mean(), 2) if "budget_passing_score" in cluster_df.columns else None,
                "budget_passing_score_median": _safe_round(cluster_df["budget_passing_score"].dropna().median(), 2) if "budget_passing_score" in cluster_df.columns else None,
                "budget_places_mean": _safe_round(cluster_df["budget_places"].dropna().mean(), 2) if "budget_places" in cluster_df.columns else None,
                "budget_places_median": _safe_round(cluster_df["budget_places"].dropna().median(), 2) if "budget_places" in cluster_df.columns else None,
                "duration_mean": _safe_round(cluster_df["duration"].dropna().mean(), 2) if "duration" in cluster_df.columns else None,
                "duration_median": _safe_round(cluster_df["duration"].dropna().median(), 2) if "duration" in cluster_df.columns else None,
                "city_mode": _mode_or_none(cluster_df["city"].tolist()) if "city" in cluster_df.columns else None,
                "level_mode": _mode_or_none(cluster_df["level"].tolist()) if "level" in cluster_df.columns else None,
                "study_format_mode": _mode_or_none(cluster_df["study_format"].tolist()) if "study_format" in cluster_df.columns else None,
                "name_mode": _mode_or_none(cluster_df["name"].tolist()) if "name" in cluster_df.columns else None,
            }
        }
        clusters.append(stat)

    return {
        "items": items,
        "cluster_count": int(n_clusters),
        "algorithm": algorithm,
        "available_algorithms": sorted(ALLOWED_ALGORITHMS),
        "available_features": _available_feature_options(),
        "features_used": features_used,
        "metrics": {
            "silhouette_score": _safe_round(silhouette, 4),
            "calinski_harabasz_score": _safe_round(ch_score, 4),
            "davies_bouldin_score": _safe_round(db_score, 4),
        },
        "clusters": clusters,
        "points": points,
        "message": None,
    }