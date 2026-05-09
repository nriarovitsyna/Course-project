from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.ml import (
    RecommendationRequest,
    RecommendationResponse,
    SmartSearchRequest,
    SmartSearchResponse,
    ClusterRequest,
    ClusterResponse,
    PredictionRequest,
    PredictionResponse,
    PredictPassingScoreRequest,
    PredictPassingScoreResponse,
    ClassifyCompetitivenessRequest,
    ClassifyCompetitivenessResponse,
    TextAnalysisRequest,
    TextAnalysisResponse,
    CompareRequest,
    CompareResponse,
    ExplainRequest,
    ExplainResponse,
)
from app.services.ml_service import ml_service


router = APIRouter(tags=["ml"])


@router.post("/recommend", response_model=RecommendationResponse)
def recommend(req: RecommendationRequest, db: Session = Depends(get_db)):
    return ml_service.recommend(db, req)


@router.post("/smart-search", response_model=SmartSearchResponse)
def smart_search(req: SmartSearchRequest, db: Session = Depends(get_db)):
    return ml_service.smart_search(db, req)


@router.post("/cluster", response_model=ClusterResponse)
def cluster(req: ClusterRequest, db: Session = Depends(get_db)):
    return ml_service.cluster_programs(db, req)


@router.post("/predict-price", response_model=PredictionResponse)
def predict_price(req: PredictionRequest, db: Session = Depends(get_db)):
    return ml_service.predict_price(db, req)


@router.post("/predict-popularity", response_model=PredictionResponse)
def predict_popularity(req: PredictionRequest, db: Session = Depends(get_db)):
    return ml_service.predict_popularity(db, req)


@router.post("/predict-passing-score", response_model=PredictPassingScoreResponse)
def predict_passing_score(
    req: PredictPassingScoreRequest,
    db: Session = Depends(get_db)
):
    return ml_service.predict_passing_score(db, req)


@router.post("/classify-competitiveness", response_model=ClassifyCompetitivenessResponse)
def classify_competitiveness(
    req: ClassifyCompetitivenessRequest,
    db: Session = Depends(get_db)
):
    return ml_service.classify_competitiveness(db, req)


@router.post("/analyze-text", response_model=TextAnalysisResponse)
def analyze_text(req: TextAnalysisRequest):
    return ml_service.analyze_text(req)


@router.post("/compare", response_model=CompareResponse)
def compare(req: CompareRequest, db: Session = Depends(get_db)):
    return ml_service.compare_programs(db, req)


@router.post("/explain", response_model=ExplainResponse)
def explain(req: ExplainRequest, db: Session = Depends(get_db)):
    return ml_service.explain_result(db, req)