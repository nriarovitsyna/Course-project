from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.program import Program


class ProgramsService:
    def __init__(self, db: Session):
        self.db = db

    def list_programs(
        self,
        city: str | None,
        price_min: float | None,
        price_max: float | None,
        is_budget: bool | None,
        level: str | None,
    ) -> list[Program]:
        stmt = select(Program)

        if city:
            stmt = stmt.where(Program.city == city)

        if level:
            stmt = stmt.where(Program.level == level)

        if price_min is not None:
            stmt = (
                stmt.where(Program.tuition_cost_rub_year.is_not(None))
                    .where(Program.tuition_cost_rub_year >= price_min)
            )

        if price_max is not None:
            stmt = (
                stmt.where(Program.tuition_cost_rub_year.is_not(None))
                    .where(Program.tuition_cost_rub_year <= price_max)
            )

        if is_budget is True:
            stmt = (
                stmt.where(Program.budget_places.is_not(None))
                    .where(Program.budget_places > 0)
            )
        elif is_budget is False:
            stmt = stmt.where(
                (Program.budget_places.is_(None)) | (Program.budget_places == 0)
            )

        stmt = stmt.order_by(Program.id.asc())
        return list(self.db.scalars(stmt).all())

    def get_program(self, program_id: int) -> Program | None:
        stmt = select(Program).where(Program.id == program_id)
        return self.db.scalars(stmt).first()