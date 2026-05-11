from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.schemas.analytics import Summary, Series, Point
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/summary", response_model=Summary)
def analytics_summary(
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_summary(
        db,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/programs-by-city", response_model=Series)
def programs_by_city(
    limit: int = 10,
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_programs_by_city(
        db,
        limit=limit,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/programs-by-faculty", response_model=Series)
def programs_by_faculty(
    limit: int = 10,
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_programs_by_faculty(
        db,
        limit=limit,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/budget-vs-paid", response_model=Series)
def budget_vs_paid(
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_budget_vs_paid(
        db,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )

@router.get("/price-buckets", response_model=Series)
def price_buckets(
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_price_buckets(
        db,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/price-vs-budget", response_model=list[Point])
def price_vs_budget(
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_price_vs_budget(
        db,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/avg-price-by-city", response_model=Series)
def avg_price_by_city(
    limit: int = 10,
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_avg_price_by_city(
        db,
        limit=limit,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )


@router.get("/level-format", response_model=Series)
def level_format(
    city: Optional[str] = None,
    faculty: Optional[str] = None,
    university_name: Optional[str] = None,
    level: Optional[str] = None,
    duration: Optional[str] = None,
    study_format: Optional[str] = None,
    accreditation: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    has_budget: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    return analytics_service.get_level_format_distribution(
        db,
        city=city,
        faculty=faculty,
        university_name=university_name,
        level=level,
        duration=duration,
        study_format=study_format,
        accreditation=accreditation,
        price_min=price_min,
        price_max=price_max,
        has_budget=has_budget,
    )