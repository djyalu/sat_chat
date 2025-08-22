"""Sentinel Hub API endpoints for advanced processing"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from satchat.core.database import get_async_db
from satchat.models.database import User
from satchat.api.auth import get_current_active_user
from satchat.services.satellite.sentinel_hub import SentinelHubService

router = APIRouter()


@router.post("/process/marine-debris")
async def process_marine_debris(
    background_tasks: BackgroundTasks,
    bbox: List[float] = Query(..., description="Bounding box [min_lon, min_lat, max_lon, max_lat]"),
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(None, description="End date (default: now)"),
    resolution: int = Query(10, ge=10, le=100, description="Resolution in meters"),
    max_cloud: float = Query(20, ge=0, le=100, description="Max cloud coverage %"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Process area for marine debris detection using Sentinel Hub"""
    
    # Check user permissions
    if current_user.role not in ["admin", "operator", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Validate bbox
    if len(bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bbox must have 4 values: [min_lon, min_lat, max_lon, max_lat]"
        )
    
    # Set end date if not provided
    if not end_date:
        end_date = datetime.utcnow()
    
    # Schedule processing task
    background_tasks.add_task(
        process_sentinel_hub_area,
        bbox=tuple(bbox),
        time_range=(start_date, end_date),
        resolution=resolution,
        max_cloud_coverage=max_cloud
    )
    
    return {
        "message": "Marine debris processing task scheduled",
        "bbox": bbox,
        "time_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "resolution": resolution,
        "max_cloud_coverage": max_cloud
    }


@router.get("/statistics/marine-debris")
async def get_marine_debris_statistics(
    area: str = Query(..., description="Korean sea area: west_sea, south_sea, or east_sea"),
    days_back: int = Query(7, ge=1, le=90, description="Days to analyze"),
    aggregation: str = Query("P1D", description="Aggregation interval (P1D=daily, P1W=weekly)"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get statistical analysis of marine debris for Korean waters"""
    
    # Validate area
    valid_areas = ["west_sea", "south_sea", "east_sea"]
    if area not in valid_areas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid area. Must be one of: {valid_areas}"
        )
    
    # Initialize service
    sentinel_hub = SentinelHubService()
    
    # Get area bbox
    from satchat.core.config import settings
    bbox = settings.korea_bbox[area]
    
    # Calculate time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Create polygon from bbox
    from shapely.geometry import box
    area_polygon = box(*bbox)
    
    try:
        # Get statistics
        stats = await sentinel_hub.get_statistics(
            geometry=area_polygon,
            time_range=(start_date, end_date),
            aggregation_interval=aggregation
        )
        
        return {
            "area": area,
            "bbox": bbox,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "statistics": stats
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}"
        )


@router.post("/batch/create")
async def create_batch_job(
    areas: List[str] = Query(["west_sea", "south_sea", "east_sea"], description="Areas to process"),
    days_back: int = Query(7, ge=1, le=90, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Create batch processing job for large-scale marine debris analysis"""
    
    # Check user permissions
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and operators can create batch jobs"
        )
    
    # Validate areas
    valid_areas = ["west_sea", "south_sea", "east_sea"]
    invalid = [a for a in areas if a not in valid_areas]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid areas: {invalid}"
        )
    
    # Initialize service
    sentinel_hub = SentinelHubService()
    
    # Calculate time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Prepare area configurations
    from satchat.core.config import settings
    area_configs = [
        {"name": area, "bbox": settings.korea_bbox[area]}
        for area in areas
    ]
    
    try:
        # Create batch job
        job_id = await sentinel_hub.create_batch_job(
            areas=area_configs,
            time_range=(start_date, end_date)
        )
        
        return {
            "job_id": job_id,
            "status": "created",
            "areas": areas,
            "time_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create batch job: {str(e)}"
        )


@router.get("/batch/{job_id}/status")
async def get_batch_job_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get status of batch processing job"""
    
    # Initialize service
    sentinel_hub = SentinelHubService()
    
    try:
        # Get job status
        status = await sentinel_hub.monitor_batch_job(job_id)
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get job status: {str(e)}"
        )


@router.post("/process/korean-waters")
async def process_all_korean_waters(
    background_tasks: BackgroundTasks,
    days_back: int = Query(7, ge=1, le=30, description="Days to analyze"),
    resolution: int = Query(10, ge=10, le=100, description="Resolution in meters"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Process all Korean water areas for marine debris"""
    
    # Check user permissions
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and operators can trigger full processing"
        )
    
    # Schedule processing task
    background_tasks.add_task(
        process_korean_waters_task,
        days_back=days_back,
        resolution=resolution
    )
    
    return {
        "message": "Korean waters processing task scheduled",
        "areas": ["west_sea", "south_sea", "east_sea"],
        "days_back": days_back,
        "resolution": resolution
    }


# Background task functions
async def process_sentinel_hub_area(
    bbox: tuple,
    time_range: tuple,
    resolution: int,
    max_cloud_coverage: float
):
    """Background task to process area with Sentinel Hub"""
    sentinel_hub = SentinelHubService()
    await sentinel_hub.process_area(
        bbox=bbox,
        time_range=time_range,
        resolution=resolution,
        max_cloud_coverage=max_cloud_coverage
    )


async def process_korean_waters_task(
    days_back: int,
    resolution: int
):
    """Background task to process all Korean waters"""
    sentinel_hub = SentinelHubService()
    await sentinel_hub.process_korean_waters(
        days_back=days_back,
        resolution=resolution
    )