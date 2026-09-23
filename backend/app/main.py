"""FastAPI Application Entry Point for Explainable AI Fraud & Risk Detection System."""

from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.api.v1.endpoints.health import router as health_router

logger = logging.getLogger("fraudlens.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context for startup and shutdown events."""
    # 1. Startup tasks: ensure database tables & default accounts exist
    from backend.app.core.init_db import init_db
    from backend.app.core.database import SessionLocal
    db = SessionLocal()
    try:
        init_db(db)
    except Exception as e:
        logger.error("Error initializing database tables: %s", e)
    finally:
        db.close()

    # 2. Pre-warm ML Prediction Service into memory to eliminate cold start latency
    try:
        from backend.app.services.prediction_service import FraudPredictionService
        service = FraudPredictionService.get_instance()
        if service.is_ready:
            logger.info("ML FraudPredictionService pre-warmed successfully (Model: %s)", service.model_name)
    except Exception as e:
        logger.warning("Could not pre-warm ML model at startup: %s", e)

    yield
    # Shutdown tasks


def create_application() -> FastAPI:
    """Factory function to build and configure the FastAPI application."""
    application = FastAPI(
        title=settings.APP_NAME,
        description="FraudLens AI — Explainable AI-Based Financial Fraud & Risk Detection System API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # GZip Response Compression (Compress payloads > 1KB for faster network transfer)
    application.add_middleware(GZipMiddleware, minimum_size=1000)

    # CORS Configuration
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Top-level /api/health endpoint
    application.include_router(health_router, prefix="/api")

    # API v1 versioned endpoints
    application.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @application.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.APP_NAME,
            "version": "0.1.0",
            "environment": settings.APP_ENV,
            "docs": "/docs",
            "health": "/api/health",
        }

    return application


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.app.main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=settings.DEBUG,
    )
