from sqlalchemy.orm import Session

from app.schemas.ml import (
    RecommendationRequest,
    RecommendationResponse,
    ProgramShort,
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

from app.ml.rank import rank_programs
from app.ml.cluster import cluster_programs
from app.ml.predict import (
    predict_price_from_programs,
    predict_popularity_from_programs,
    predict_passing_score_from_programs,
    classify_competitiveness_from_programs,
)
from app.ml.text import analyze_text
from app.ml.compare import compare_programs
from app.ml.explain import explain_program

from app.models.program import Program


class MLService:
    def _base_query(self, db: Session):
        return db.query(Program)

    def recommend(self, db: Session, req: RecommendationRequest) -> RecommendationResponse:
        """
        Рекомендация по полям формы с ранжированием по score.
        """
        programs = self._base_query(db).all()

        query_data = {
            "query": req.query or "",
            "detected_cities": [req.city] if req.city else [],
            "detected_faculties": [req.faculty] if req.faculty else [],
            "detected_universities": [req.university_name] if req.university_name else [],
            "detected_levels": [req.level] if req.level else [],
            "detected_study_formats": [req.study_format] if req.study_format else [],
            "detected_languages": [req.language] if req.language else [],
            "detected_accreditations": [req.accreditation] if req.accreditation else [],
            "detected_budget": req.has_budget,
            "detected_price_min": req.price_min,
            "detected_price_max": req.price_max,
            "detected_min_score": req.min_score,
            "detected_duration_min": req.duration_min,
            "detected_duration_max": req.duration_max,
        }

        ranked = rank_programs(programs, query_data)

        threshold = req.compatibility_threshold or 0.0
        ranked = [item for item in ranked if (item.get("score") or 0.0) >= threshold]

        limited = ranked[: req.limit]
        items = [ProgramShort(**item) for item in limited]
        return RecommendationResponse(items=items, total=len(ranked))

    def smart_search(self, db: Session, req: SmartSearchRequest) -> SmartSearchResponse:
        """
        Умный поиск:
        text.py/analyze_text извлекает критерии из текста,
        rank.py ранжирует программы по этим критериям.
        """
        analysis = analyze_text(TextAnalysisRequest(text=req.query))
        programs = self._base_query(db).all()

        try:
            query_data = analysis.model_dump()
        except AttributeError:
            query_data = analysis.dict()

        query_data["query"] = req.query

        ranked = rank_programs(programs, query_data)

        threshold = req.compatibility_threshold or 0.0
        ranked = [item for item in ranked if (item.get("score") or 0.0) >= threshold]

        limited = ranked[: req.limit]
        items = [ProgramShort(**item) for item in limited]
        return SmartSearchResponse(items=items, total=len(ranked))

    def cluster_programs(self, db: Session, req: ClusterRequest) -> ClusterResponse:
        """
        Кластеризация образовательных программ по выбранным признакам.
        """
        programs = self._base_query(db).all()

        result = cluster_programs(
            programs=programs,
            n_clusters=req.n_clusters,
            features=req.features,
            algorithm=req.algorithm,
        )

        return ClusterResponse(**result)

    def predict_price(self, db: Session, req: PredictionRequest) -> PredictionResponse:
        programs = self._base_query(db).all()
        return predict_price_from_programs(programs, req)

    def predict_popularity(self, db: Session, req: PredictionRequest) -> PredictionResponse:
        programs = self._base_query(db).all()
        return predict_popularity_from_programs(programs, req)

    def predict_passing_score(
        self,
        db: Session,
        req: PredictPassingScoreRequest
    ) -> PredictPassingScoreResponse:
        """
        ML-регрессия: предсказание проходного балла программы.
        """
        programs = self._base_query(db).all()
        return predict_passing_score_from_programs(programs, req)

    def classify_competitiveness(
        self,
        db: Session,
        req: ClassifyCompetitivenessRequest
    ) -> ClassifyCompetitivenessResponse:
        """
        ML-классификация: определение конкурентоспособности программы.
        """
        programs = self._base_query(db).all()
        return classify_competitiveness_from_programs(programs, req)

    def analyze_text(self, req: TextAnalysisRequest) -> TextAnalysisResponse:
        return analyze_text(req)

    def compare_programs(self, db: Session, req: CompareRequest) -> CompareResponse:
        programs = self._base_query(db).filter(Program.id.in_(req.program_ids)).all()
        return compare_programs(programs)

    def explain_result(self, db: Session, req: ExplainRequest) -> ExplainResponse:
        program = self._base_query(db).filter(Program.id == req.program_id).first()
        if not program:
            return ExplainResponse(
                program_id=req.program_id,
                explanation="Программа не найдена",
                factors={},
                match_score=None,
            )

        analysis = analyze_text(TextAnalysisRequest(text=req.query or ""))
        try:
            query_data = analysis.model_dump()
        except AttributeError:
            query_data = analysis.dict()

        query_data["query"] = req.query or ""

        result = explain_program(program, query_data)
        return ExplainResponse(**result)


ml_service = MLService()