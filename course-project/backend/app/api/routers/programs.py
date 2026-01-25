from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.program import ProgramOut, ProgramsListOut
from app.services.programs_service import ProgramsService

router = APIRouter()


@router.get("", response_model=ProgramsListOut)
def list_programs(
    city: str | None = Query(default=None),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    is_budget: bool | None = Query(default=None),
    level: str | None = Query(default=None, description="bachelor|master"),
    db: Session = Depends(get_db),
):
    svc = ProgramsService(db)
    items = svc.list_programs(
        city=city,
        price_min=price_min,
        price_max=price_max,
        is_budget=is_budget,
        level=level,
    )
    return {"items": items, "total": len(items)}


@router.get("/{program_id}", response_model=ProgramOut)
def get_program(program_id: int, db: Session = Depends(get_db)):
    svc = ProgramsService(db)
    program = svc.get_program(program_id)
    if program is None:
        raise HTTPException(status_code=404, detail="Program not found")  # 404 по ТЗ [file:1]
    return program
