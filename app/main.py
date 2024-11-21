from contextlib import asynccontextmanager
from datetime import datetime, UTC

from fastapi import FastAPI, Request
from fastapi.routing import APIRoute

from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.main import api_router

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.api.routes.message import delete_expired_messages
from app.core.config import settings

scheduler = BackgroundScheduler()

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

limiter = Limiter(key_func=get_remote_address, default_limits=["10/minute"])
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model or other resources here
    try:
        scheduler.add_job(delete_expired_messages, 'interval', minutes=1)
        scheduler.start()
        yield
    finally:
        # Clean up the ML models and release the resources
        scheduler.shutdown()

app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key="Thisisthebesticando")

app.include_router(api_router, prefix=settings.API_V1_STR)
