from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score,
    f1_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Путь до CSV с датасетом
DATA_PATH = Path("Data/Dataset_kursach-List1.csv")

# Куда сохранять модель и метаданные
MODEL_DIR = Path("backend/app/ml/saved_models")
MODEL_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = MODEL_DIR / "competitiveness_rf_model.joblib"
META_PATH = MODEL_DIR / "competitiveness_meta.joblib"
CLUSTERED_DATA_PATH = MODEL_DIR / "programs_with_competitiveness.csv"


def _norm_text(value) -> str:
    if value is None:
        return "unknown"
    text = str(value).strip()
    return text if text else "unknown"


def _to_float(value, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def load_dataset(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)

    expected_cols = [
        "id",
        "program_code",
        "name",
        "faculty",
        "level",
        "university_name",
        "city",
        "budget_places",
        "paid_places",
        "tuition_cost_rub_year",
        "budget_passing_score",
        "paid_min_score",
        "duration",
        "study_format",
        "language",
        "accreditation",
    ]

    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        raise ValueError(f"В датасете отсутствуют колонки: {missing}")

    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    text_cols = [
        "program_code",
        "name",
        "faculty",
        "level",
        "university_name",
        "city",
        "study_format",
        "language",
        "accreditation",
    ]
    for col in text_cols:
        df[col] = df[col].apply(_norm_text)

    numeric_cols = [
        "budget_places",
        "paid_places",
        "tuition_cost_rub_year",
        "budget_passing_score",
        "paid_min_score",
        "duration",
    ]
    for col in numeric_cols:
        df[col] = df[col].apply(_to_float)

    # производные признаки
    df["total_places"] = df["budget_places"] + df["paid_places"]
    df["budget_ratio"] = np.where(
        df["total_places"] > 0,
        df["budget_places"] / df["total_places"],
        0.0,
    )
    df["tuition_log"] = np.log1p(np.maximum(df["tuition_cost_rub_year"], 0))
    df["paid_min_score_missing"] = (df["paid_min_score"] <= 0).astype(int)
    df["budget_score_missing"] = (df["budget_passing_score"] <= 0).astype(int)

    return df


def get_feature_lists() -> Tuple[List[str], List[str]]:
    categorical_cols = [
        "faculty",
        "level",
        "university_name",
        "city",
        "study_format",
        "language",
        "accreditation",
    ]

    numeric_cols = [
        "budget_places",
        "paid_places",
        "total_places",
        "budget_ratio",
        "tuition_cost_rub_year",
        "tuition_log",
        "budget_passing_score",
        "paid_min_score",
        "duration",
        "paid_min_score_missing",
        "budget_score_missing",
    ]

    return categorical_cols, numeric_cols


def build_preprocessor(
    categorical_cols: List[str],
    numeric_cols: List[str],
) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "cat",
                Pipeline(
                    steps=[
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="constant",
                                fill_value="unknown",
                            ),
                        ),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_cols,
            ),
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_cols,
            ),
        ]
    )


def _build_cluster_profiles(df: pd.DataFrame) -> pd.DataFrame:
    """
    Строим сводные характеристики по сырым кластерам:
    - средний проходной балл
    - средняя стоимость
    - среднее количество мест (бюджет / платные / всего)
    - средняя доля бюджетных мест
    - средняя длительность
    """
    cluster_profile = (
        df.groupby("cluster_raw")[
            [
                "budget_passing_score",
                "tuition_cost_rub_year",
                "budget_places",
                "paid_places",
                "total_places",
                "budget_ratio",
                "duration",
            ]
        ]
        .mean()
        .round(2)
    )

    return cluster_profile


def _build_class_profiles(
    df: pd.DataFrame,
    cluster_to_class: Dict[int, int],
) -> pd.DataFrame:
    """
    Пересчёт профилей уже по классам конкурентоспособности (0/1/2),
    чтобы потом писать интерпретацию по категории, а не по raw‑кластеру.
    """
    df_tmp = df.copy()
    df_tmp["competitiveness_class"] = df_tmp["cluster_raw"].map(cluster_to_class)

    class_profile = (
        df_tmp.groupby("competitiveness_class")[
            [
                "budget_passing_score",
                "tuition_cost_rub_year",
                "budget_places",
                "paid_places",
                "total_places",
                "budget_ratio",
                "duration",
            ]
        ]
        .mean()
        .round(2)
    )

    return class_profile


def _get_top_cities_by_cluster(
    df: pd.DataFrame,
    top_n: int = 3,
) -> Dict[int, List[str]]:
    """
    Топ-N городов по количеству программ в каждом raw‑кластере.
    Используем именно сырые ID кластеров, потом смапим их на классы.
    """
    work_df = df.copy()
    work_df["city"] = work_df["city"].fillna("unknown").astype(str).str.strip()
    work_df = work_df[work_df["city"] != ""]

    result: Dict[int, List[str]] = {}

    for cluster_id, group in work_df.groupby("cluster_raw"):
        top_cities = (
            group["city"]
            .value_counts()
            .head(top_n)
            .index
            .tolist()
        )
        result[int(cluster_id)] = top_cities

    return result


def _map_top_cities_to_classes(
    cluster_to_class: Dict[int, int],
    top_cities_by_cluster: Dict[int, List[str]],
) -> Dict[int, List[str]]:
    """
    Переводим топы городов с raw‑кластеров на уровни конкурентоспособности (0/1/2).
    Если несколько raw‑кластеров сходятся в один класс — объединяем и берём top‑3.
    """
    tmp: Dict[int, List[str]] = {}

    for raw_cluster, cls in cluster_to_class.items():
        cities = top_cities_by_cluster.get(raw_cluster, [])
        if not cities:
            continue

        if cls not in tmp:
            tmp[cls] = []
        tmp[cls].extend(cities)

    # агрегируем и берём top‑3 по каждому классу
    result: Dict[int, List[str]] = {}
    for cls, cities in tmp.items():
        s = pd.Series(cities)
        top = s.value_counts().head(3).index.tolist()
        result[cls] = top

    return result


def cluster_programs(
    df: pd.DataFrame,
    categorical_cols: List[str],
    numeric_cols: List[str],
) -> Tuple[pd.DataFrame, Dict[int, int], pd.DataFrame, pd.DataFrame, Dict[int, List[str]]]:
    """
    Кластеризация программ + расчёт:
    - summary по сырым кластерам (для ранжирования)
    - профили по конкурентоспособности (class_profile)
    - топ‑3 города по классам
    """
    clustering_features = [
        "city",
        "university_name",
        "level",
        "study_format",
        "language",
        "budget_places",
        "paid_places",
        "total_places",
        "budget_ratio",
        "tuition_cost_rub_year",
        "tuition_log",
        "budget_passing_score",
        "paid_min_score",
        "duration",
    ]

    cluster_cat_cols = [c for c in categorical_cols if c in clustering_features]
    cluster_num_cols = [c for c in numeric_cols if c in clustering_features]

    preprocessor = build_preprocessor(cluster_cat_cols, cluster_num_cols)
    X_cluster = preprocessor.fit_transform(df[cluster_cat_cols + cluster_num_cols])

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)

    df = df.copy()
    df["cluster_raw"] = kmeans.fit_predict(X_cluster)

    # summary по сырым кластерам (для ранжирования)
    cluster_raw_summary = (
        df.groupby("cluster_raw")[
            [
                "budget_passing_score",
                "paid_min_score",
                "tuition_cost_rub_year",
                "total_places",
                "budget_ratio",
            ]
        ]
        .mean()
        .round(2)
    )

    # ранжирование кластеров по "конкурентности"
    ranking = (
        cluster_raw_summary["budget_passing_score"].fillna(0) * 0.45
        + cluster_raw_summary["paid_min_score"].fillna(0) * 0.15
        + (
            cluster_raw_summary["tuition_cost_rub_year"].fillna(0)
            / max(cluster_raw_summary["tuition_cost_rub_year"].max(), 1)
        )
        * 100
        * 0.15
        + (1 - cluster_raw_summary["budget_ratio"].fillna(0)) * 100 * 0.15
        + (
            1
            - cluster_raw_summary["total_places"].fillna(0)
            / max(cluster_raw_summary["total_places"].max(), 1)
        )
        * 100
        * 0.10
    )

    ordered_clusters = ranking.sort_values().index.tolist()

    # маппинг сырых кластеров в классы конкурентоспособности
    cluster_to_class: Dict[int, int] = {
        ordered_clusters[0]: 0,  # Доступная
        ordered_clusters[1]: 1,  # Стандартная
        ordered_clusters[2]: 2,  # Высококонкурентная
    }

    df["competitiveness_class"] = df["cluster_raw"].map(cluster_to_class)

    # профили по сырым кластерам и по классам (для интерпретации)
    cluster_profile_raw = _build_cluster_profiles(df)
    class_profile = _build_class_profiles(df, cluster_to_class)

    # топ‑3 городов по сырым кластерам и по классам
    top_cities_by_cluster = _get_top_cities_by_cluster(df, top_n=3)
    top_cities_by_class = _map_top_cities_to_classes(
        cluster_to_class, top_cities_by_cluster
    )

    return df, cluster_to_class, cluster_profile_raw, class_profile, top_cities_by_class


def train_classifier(
    df: pd.DataFrame,
    categorical_cols: List[str],
    numeric_cols: List[str],
) -> Tuple[Pipeline, Dict[str, float], np.ndarray]:
    X = df[categorical_cols + numeric_cols]
    y = df["competitiveness_class"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    preprocessor = build_preprocessor(categorical_cols, numeric_cols)

    clf = RandomForestClassifier(
        n_estimators=500,
        max_depth=None,
        min_samples_leaf=3,
        max_features="sqrt",
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", clf),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro")), 4),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
    }

    print("=== Classification report ===")
    print(classification_report(y_test, y_pred, digits=4))
    print("=== Confusion matrix ===")
    print(confusion_matrix(y_test, y_pred))
    print("=== Metrics ===")
    print(metrics)

    return pipeline, metrics, y_pred


def main():
    print(f"Загрузка датасета из: {DATA_PATH}")
    df = load_dataset(DATA_PATH)
    df = build_features(df)

    categorical_cols, numeric_cols = get_feature_lists()

    print("Кластеризация программ...")
    (
        clustered_df,
        cluster_to_class,
        cluster_raw_summary,
        class_profile,
        top_cities_by_class,
    ) = cluster_programs(df, categorical_cols, numeric_cols)

    print("=== Cluster raw summary (по cluster_raw) ===")
    print(cluster_raw_summary)

    print("=== Class profile (по competitiveness_class) ===")
    print(class_profile)

    print("=== Top-3 города по классам ===")
    print(top_cities_by_class)

    # Приводим class_profile к формату {class_id: {metric: value, ...}}
    class_profile_dict: Dict[int, Dict[str, float]] = {}
    for class_id, row in class_profile.iterrows():
        class_profile_dict[int(class_id)] = row.to_dict()

    print("=== Class profile dict (для meta) ===")
    print(class_profile_dict)

    print("Обучение RandomForestClassifier...")
    model, metrics, _ = train_classifier(
        clustered_df, categorical_cols, numeric_cols
    )

    category_names = {
        0: "Доступная",
        1: "Стандартная",
        2: "Высококонкурентная",
    }

    meta = {
        "categorical_cols": categorical_cols,
        "numeric_cols": numeric_cols,
        "cluster_to_class": cluster_to_class,
        "category_names": category_names,
        "metrics": metrics,
        # характеристики классов для интерпретации
        "class_profile": class_profile_dict,
        "top_cities_by_class": top_cities_by_class,
    }

    joblib.dump(model, MODEL_PATH)
    joblib.dump(meta, META_PATH)
    clustered_df.to_csv(CLUSTERED_DATA_PATH, index=False)

    print(f"Модель сохранена: {MODEL_PATH}")
    print(f"Метаданные сохранены: {META_PATH}")
    print(
        f"Датасет с competitiveness_class сохранен: {CLUSTERED_DATA_PATH}"
    )


if __name__ == "__main__":
    main()