from fastapi import APIRouter

from src.api.routes import alerts, files

api_router = APIRouter()
api_router.include_router(files.router)
api_router.include_router(alerts.router)
