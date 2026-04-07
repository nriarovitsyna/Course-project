from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.program import Program
from app.schemas.analytics import Summary, Series


def apply_common_filters(
    query,
    city: str | None = None,
    faculty: str | None = None,
    university_name: str | None = None,
    level: str | None = None,
    duration: str | None = None,
    study_format: str | None = None,
    accreditation: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    has_budget: bool | None = None,
):
    if city:
        query = query.filter(Program.city == city)
    if faculty:
        query = query.filter(Program.faculty == faculty)
    if university_name:
        query = query.filter(Program.university_name == university_name)
    if level:
        query = query.filter(Program.level == level)
    if duration:
        query = query.filter(Program.duration == duration)
    if study_format:
        query = query.filter(Program.study_format == study_format)
    if accreditation:
        query = query.filter(Program.accreditation == accreditation)
    if price_min is not None:
        query = query.filter(Program.tuition_cost_rub_year >= price_min)
    if price_max is not None:
        query = query.filter(Program.tuition_cost_rub_year <= price_max)
    if has_budget is not None:
        if has_budget:
            query = query.filter((Program.budget_places != None) & (Program.budget_places > 0))
        else:
            query = query.filter((Program.budget_places == None) | (Program.budget_places == 0))
    return query


# summary 

def get_summary(db: Session, **filters) -> Summary:
    base = db.query(Program)
    base = apply_common_filters(base, **filters)

    total = base.count()

    price_q = apply_common_filters(
        db.query(
            func.avg(Program.tuition_cost_rub_year),
            func.min(Program.tuition_cost_rub_year),
            func.max(Program.tuition_cost_rub_year),
        ),
        **filters,
    ).one()
    avg_price, min_price, max_price = price_q

    budget_q = apply_common_filters(
        db.query(func.count()).filter(
            (Program.budget_places != None) & (Program.budget_places > 0)
        ),
        **filters,
    )
    budget_programs = budget_q.scalar() or 0

    budget_share = None
    if total > 0:
        budget_share = budget_programs / total

    return Summary(
        total_programs=total,
        avg_price=avg_price,
        min_price=min_price,
        max_price=max_price,
        budget_programs=budget_programs,
        budget_share=budget_share,
    )


# programs by city

def get_programs_by_city(db: Session, limit: int = 10, **filters) -> Series:
    q = db.query(
        Program.city,
        func.count().label("cnt"),
    )
    q = apply_common_filters(q, **filters)
    q = q.group_by(Program.city).order_by(func.count().desc())
    if limit:
        q = q.limit(limit)

    rows = q.all()
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    return Series(labels=labels, values=values)


# programs by faculty 

def get_programs_by_faculty(db: Session, limit: int = 10, **filters) -> Series:
    q = db.query(
        Program.faculty,
        func.count().label("cnt"),
    )
    q = apply_common_filters(q, **filters)
    q = q.group_by(Program.faculty).order_by(func.count().desc())
    if limit:
        q = q.limit(limit)

    rows = q.all()
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    return Series(labels=labels, values=values)


# budget vs paid

def get_budget_vs_paid(db: Session, **filters) -> Series:
    q = db.query(
        case(
            (
                (Program.budget_places != None) & (Program.budget_places > 0),
                "Есть бюджет",
            ),
            else_="Только платное",
        ).label("kind"),
        func.count().label("cnt"),
    )
    q = apply_common_filters(q, **filters)
    q = q.group_by("kind")

    rows = q.all()
    labels = [r[0] for r in rows]
    values = [r[1] for r in rows]
    return Series(labels=labels, values=values)