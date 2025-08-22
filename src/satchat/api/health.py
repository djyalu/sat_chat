"""Health check endpoints"""

from typing import Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from satchat.core.database import get_async_db, check_async_db_connection
from satchat.core.config import settings
from satchat.services.storage import S3Service

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment
    }


@router.get("/ready", response_model=Dict[str, Any])
async def readiness_check(
    db: AsyncSession = Depends(get_async_db)
) -> Dict[str, Any]:
    """Readiness check including database connectivity"""
    
    # Check database
    db_status = await check_async_db_connection()
    
    # Check S3/MinIO
    s3_service = S3Service()
    try:
        s3_service.client.list_buckets()
        s3_status = True
    except Exception:
        s3_status = False
    
    all_ready = db_status and s3_status
    
    return {
        "ready": all_ready,
        "services": {
            "database": db_status,
            "storage": s3_status
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """Liveness check for container orchestration"""
    return {"status": "alive"}