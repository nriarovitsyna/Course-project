from fastapi import APIRouter

from app.api.routers.programs import router as programs_router
from app.api.routers.filters import router as filters_router
from app.api.routers.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(programs_router, prefix="/programs")
api_router.include_router(filters_router, prefix="/filters")
api_router.include_router(analytics_router, prefix="/analytics")