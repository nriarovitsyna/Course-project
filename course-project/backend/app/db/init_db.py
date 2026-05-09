from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.program import Program
from app.services.import_service import ImportService


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    if not settings.AUTO_IMPORT_ON_STARTUP:
        return

    db: Session = SessionLocal()
    try:
        has_any = db.execute(select(Program.id).limit(1)).first() is not None
        if not has_any:
            ImportService(db).import_csv(settings.DATASET_PATH)
    finally:
        db.close()