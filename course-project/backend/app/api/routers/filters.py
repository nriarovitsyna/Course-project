from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.filters import FiltersValuesOut
from app.services.filters_service import FiltersService

router = APIRouter()


@router.get("/values", response_model=FiltersValuesOut)
def get_filter_values(db: Session = Depends(get_db)):
    svc = FiltersService(db)
    return svc.get_values()
