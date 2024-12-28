from fastapi import APIRouter

# from .routes import message
from app.api.routes import message, location
api_router = APIRouter()
api_router.include_router(message.router, prefix="/message", tags=["message"])
api_router.include_router(location.router, prefix="/location", tags=["location"])
