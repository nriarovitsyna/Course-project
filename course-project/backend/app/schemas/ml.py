from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


# ===== КОРОТКОЕ ОПИСАНИЕ ПРОГРАММЫ (используется в рекомендациях и smart search) =====

class ProgramShort(BaseModel):
    id: int
    name: str
    university_name: Optional[str] = None
    city: Optional[str] = None
    faculty: Optional[str] = None
    level: Optional[str] = None
    study_format: Optional[str] = None
    price: Optional[float] = None
    has_budget: Optional[bool] = None
    score: Optional[float] = None
    explanation: Optional[str] = None


# ===== РЕКОМЕНДАЦИИ (ручной запрос) =====

class RecommendationRequest(BaseModel):
    query: Optional[str] = None

    city: Optional[str] = None
    faculty: Optional[str] = None
    university_name: Optional[str] = None
    level: Optional[str] = None
    study_format: Optional[str] = None
    language: Optional[str] = None
    accreditation: Optional[str] = None
    has_budget: Optional[bool] = None

    price_min: Optional[float] = None
    price_max: Optional[float] = None
    min_score: Optional[float] = None
    duration_min: Optional[float] = None
    duration_max: Optional[float] = None

    compatibility_threshold: float = 0.0
    limit: int = 1000


class RecommendationResponse(BaseModel):
    items: List[ProgramShort]
    total: int


# ===== SMART SEARCH (естественный язык) =====

class SmartSearchRequest(BaseModel):
    query: str
    compatibility_threshold: float = 0.0
    limit: int = 1000


class SmartSearchResponse(BaseModel):
    items: List[ProgramShort]
    total: int


# ===== КЛАСТЕРНЫЙ АНАЛИЗ =====

class ClusterRequest(BaseModel):
    """
    Запрос на кластеризацию:
    - features: признаки из нового списка;
    - n_clusters: количество кластеров;
    - algorithm: 'kmeans' или 'agglomerative'.
    """
    features: List[str] = Field(default_factory=lambda: [
        "name",
        "price",
        "city",
        "budget_passing_score",
        "level",
        "budget_places",
        "study_format",
        "duration",
    ])
    n_clusters: int = Field(default=3, ge=2, le=10)
    algorithm: Literal["kmeans", "agglomerative"] = "kmeans"


class ClusterFeatureOption(BaseModel):
    key: str
    label: str
    type: str


class ClusterItem(BaseModel):
    program_id: int
    program_name: str
    university_name: Optional[str] = None
    city: Optional[str] = None
    cluster_id: int


class ClusterMetrics(BaseModel):
    silhouette_score: Optional[float] = None
    calinski_harabasz_score: Optional[float] = None
    davies_bouldin_score: Optional[float] = None


class ClusterStats(BaseModel):
    price_mean: Optional[float] = None
    price_median: Optional[float] = None
    budget_passing_score_mean: Optional[float] = None
    budget_passing_score_median: Optional[float] = None
    budget_places_mean: Optional[float] = None
    budget_places_median: Optional[float] = None

    duration_mean: Optional[float] = None
    duration_median: Optional[float] = None

    city_mode: Optional[str] = None
    level_mode: Optional[str] = None
    study_format_mode: Optional[str] = None
    name_mode: Optional[str] = None


class ClusterSummary(BaseModel):
    cluster_id: int
    size: int
    description: str
    stats: ClusterStats


class ClusterPoint(BaseModel):
    program_id: int
    program_name: str
    cluster_id: int
    x: float
    y: float


class ClusterResponse(BaseModel):
    items: List[ClusterItem] = Field(default_factory=list)
    cluster_count: int = 0
    algorithm: str = "kmeans"
    available_algorithms: List[str] = Field(default_factory=list)
    available_features: List[ClusterFeatureOption] = Field(default_factory=list)
    features_used: List[str] = Field(default_factory=list)
    metrics: ClusterMetrics
    clusters: List[ClusterSummary] = Field(default_factory=list)
    points: List[ClusterPoint] = Field(default_factory=list)
    message: Optional[str] = None


# ===== ОБЩИЙ PREDICTION (если где-то используется) =====

class PredictionRequest(BaseModel):
    city: Optional[str] = None
    faculty: Optional[str] = None
    level: Optional[str] = None
    study_format: Optional[str] = None
    has_budget: Optional[bool] = None
    description: Optional[str] = None


class PredictionResponse(BaseModel):
    value: float
    model_name: str
    details: Optional[Dict[str, Any]] = None


# ===== НОВЫЕ СХЕМЫ ДЛЯ ML-ПРЕДСКАЗАНИЙ (проходной балл и конкурентоспособность) =====

class PredictPassingScoreRequest(BaseModel):
    city: Optional[str] = None
    level: Optional[str] = None
    duration: Optional[float] = None
    university_name: Optional[str] = None
    price: Optional[float] = None
    budget_places: Optional[int] = None
    paid_places: Optional[int] = None


class PredictPassingScoreResponse(BaseModel):
    predicted_score: float
    model_name: str
    confidence_interval: Optional[str] = None
    model_metrics: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None


class ClassifyCompetitivenessRequest(BaseModel):
    city: Optional[str] = None
    faculty: Optional[str] = None
    level: Optional[str] = None
    study_format: Optional[str] = None
    language: Optional[str] = None
    accreditation: Optional[str] = None
    duration: Optional[float] = None
    university_name: Optional[str] = None
    price: Optional[float] = None
    budget_places: Optional[int] = None
    paid_places: Optional[int] = None
    budget_passing_score: Optional[float] = None
    paid_min_score: Optional[float] = None


class ClassifyCompetitivenessResponse(BaseModel):
    category: str
    probabilities: Dict[str, float] = Field(default_factory=dict)
    model_name: str
    accuracy: Optional[float] = None
    model_metrics: Optional[Dict[str, Any]] = None
    details: Optional[Dict[str, Any]] = None

# ===== РАЗБОР ТЕКСТА ЗАПРОСА =====

class TextAnalysisRequest(BaseModel):
    text: str


class TextAnalysisResponse(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    detected_names: List[str] = Field(default_factory=list)
    detected_cities: List[str] = Field(default_factory=list)
    detected_faculties: List[str] = Field(default_factory=list)
    detected_universities: List[str] = Field(default_factory=list)
    detected_levels: List[str] = Field(default_factory=list)
    detected_budget: Optional[bool] = None
    detected_languages: List[str] = Field(default_factory=list)
    detected_accreditations: List[str] = Field(default_factory=list)
    detected_study_formats: List[str] = Field(default_factory=list)

    detected_duration_min: Optional[float] = None
    detected_duration_max: Optional[float] = None
    detected_price_min: Optional[float] = None
    detected_price_max: Optional[float] = None

    detected_budget_score_min: Optional[float] = None
    detected_budget_score_max: Optional[float] = None
    detected_paid_score_min: Optional[float] = None
    detected_paid_score_max: Optional[float] = None

    detected_budget_places_min: Optional[float] = None
    detected_budget_places_max: Optional[float] = None
    detected_paid_places_min: Optional[float] = None
    detected_paid_places_max: Optional[float] = None

    normalized_query: str


# ===== СРАВНЕНИЕ ПРОГРАММ =====

class CompareRequest(BaseModel):
    program_ids: List[int] = Field(..., min_items=2, max_items=10)


class CompareRow(BaseModel):
    criterion: str
    values: Dict[str, Any]


class CompareResponse(BaseModel):
    rows: List[CompareRow]


# ===== ОБЪЯСНЕНИЕ РЕКОМЕНДАЦИЙ =====

class ExplainRequest(BaseModel):
    program_id: int
    query: Optional[str] = None


class ExplainResponse(BaseModel):
    program_id: int
    explanation: str
    factors: Dict[str, Any]
    match_score: Optional[float] = None