from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.core.exceptions import (
    TravelPlannerException,
    travel_planner_exception_handler,
    generic_exception_handler,
)
from app.api.routes import health, trips
from app.db.mongo import init_mongo, ensure_indexes, close_mongo

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    settings = get_settings()
    setup_logging(settings.app_env)
    logger.info("Starting Travel Planner API...")

    init_mongo()
    try:
        await ensure_indexes()
    except Exception:
        # Fail fast with a readable message instead of a driver traceback wall
        logger.error("Cannot reach MongoDB. Check MONGODB_URI in backend/.env and that the server is running.")
        raise

    logger.info("Travel Planner API is ready.")
    yield

    # --- Shutdown ---
    await close_mongo()
    logger.info("Shutting down Travel Planner API...")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Travel Planner API",
        description="Trip planning with Google Maps, MongoDB and a Gemini assistant",
        version="1.0.0",
        docs_url="/docs" if settings.app_env == "development" else None,
        redoc_url=None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(TravelPlannerException, travel_planner_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    app.include_router(trips.router, prefix="/trips", tags=["Trips"])
    app.include_router(health.router)

    return app


app = create_app()