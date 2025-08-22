"""SatChat FastAPI Application"""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from loguru import logger

from satchat.core.config import settings
from satchat.core.database import init_async_db, check_async_db_connection
from satchat.api import health, auth, images, detections, alerts, monitoring

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Configure loguru
logger.add(
    "logs/satchat.log",
    rotation="1 day",
    retention="30 days",
    level=settings.log_level,
    format=settings.log_format
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Initialize database
    await init_async_db()
    
    # Check database connection
    db_connected = await check_async_db_connection()
    if not db_connected:
        logger.error("Failed to connect to database")
    else:
        logger.info("Database connection established")
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="해상 폐기물 모니터링 시스템 API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add trusted host middleware
if settings.is_production:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.telefix.co.kr", "localhost"]
    )

# Add Prometheus metrics
if settings.is_production:
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# Root endpoint
@app.get("/")
async def root() -> Dict[str, Any]:
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "environment": settings.environment
    }


# Include API routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(
    auth.router,
    prefix=f"{settings.api_prefix}/auth",
    tags=["authentication"]
)
app.include_router(
    images.router,
    prefix=f"{settings.api_prefix}/images",
    tags=["satellite-images"]
)
app.include_router(
    detections.router,
    prefix=f"{settings.api_prefix}/detections",
    tags=["debris-detections"]
)
app.include_router(
    alerts.router,
    prefix=f"{settings.api_prefix}/alerts",
    tags=["alerts"]
)
app.include_router(
    monitoring.router,
    prefix=f"{settings.api_prefix}/monitoring",
    tags=["monitoring"]
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )