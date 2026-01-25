from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.program import Program


class ProgramsService:
    def __init__(self, db: Session):
        self.db = db

    def list_programs(
        self,
        city: str | None,
        price_min: int | None,
        price_max: int | None,
        is_budget: bool | None,
        level: str | None,
    ) -> list[Program]:
        stmt = select(Program)

        if city:
            stmt = stmt.where(Program.city == city)

        if level:
            # В CSV у тебя educationallevel числом/строкой; в ТЗ "enum bachelor/master". [file:1][file:2]
            # Пока делаем простое "как есть": сравнение строки.
            stmt = stmt.where(Program.educationallevel == level)

        if price_min is not None:
            stmt = stmt.where(Program.tuitionfee.is_not(None)).where(Program.tuitionfee >= price_min)

        if price_max is not None:
            stmt = stmt.where(Program.tuitionfee.is_not(None)).where(Program.tuitionfee <= price_max)

        if is_budget is True:
            stmt = stmt.where(Program.budgetplaces.is_not(None)).where(Program.budgetplaces > 0)
        elif is_budget is False:
            # "не бюджет" = нет бюджетных мест или 0
            stmt = stmt.where((Program.budgetplaces.is_(None)) | (Program.budgetplaces == 0))

        stmt = stmt.order_by(Program.id.asc())

        return list(self.db.scalars(stmt).all())

    def get_program(self, program_id: int) -> Program | None:
        stmt = select(Program).where(Program.id == program_id)
        return self.db.scalars(stmt).first()
