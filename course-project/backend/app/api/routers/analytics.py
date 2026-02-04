from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import AnalyticsDashboardOut
from app.services.analytics_service import AnalyticsService

router = APIRouter()


@router.get("/dashboard", response_model=AnalyticsDashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    svc = AnalyticsService(db)
    return svc.build_dashboard()