from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.routing import APIRoute
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.api.main import api_router
from app.api.routes.message import delete_expired_messages
from app.core.config import settings
from app.core.security import get_ip_address

scheduler = BackgroundScheduler()

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

limiter = Limiter(key_func=get_ip_address, default_limits=["100/minute"])
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model or other resources here
    try:
        scheduler.add_job(delete_expired_messages, 'interval', minutes=5)
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
origins = [str(origin).strip("/") for origin in settings.BACKEND_CORS_ORIGINS]
origins.append("null")
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

app.include_router(api_router, prefix=settings.API_V1_STR)
