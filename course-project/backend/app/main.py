from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.api import api_router
from app.db.init_db import init_db

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.on_event("startup")
def on_startup() -> None:
    # Создаём таблицы и при необходимости делаем первичный импорт CSV -> Postgres.
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
