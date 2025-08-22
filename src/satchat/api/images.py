"""Satellite image management endpoints"""

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from geoalchemy2.functions import ST_Intersects, ST_MakeEnvelope

from satchat.core.database import get_async_db
from satchat.models.database import SatelliteImage, User, ProcessingStatus
from satchat.models.schemas import (
    SatelliteImageResponse,
    SatelliteImageCreate,
    SatelliteImageUpdate,
    PaginatedResponse,
    SearchFilters
)
from satchat.api.auth import get_current_active_user
from satchat.services.satellite.sentinel import Sentinel2Service
from satchat.services.processing import process_satellite_image

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_images(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    satellite_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    processing_status: Optional[ProcessingStatus] = None,
    bbox: Optional[str] = None,  # "min_lon,min_lat,max_lon,max_lat"
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse:
    """List satellite images with filtering and pagination"""
    
    # Build query
    query = select(SatelliteImage)
    
    # Apply filters
    filters = []
    if satellite_name:
        filters.append(SatelliteImage.satellite_name == satellite_name)
    if date_from:
        filters.append(SatelliteImage.acquisition_date >= date_from)
    if date_to:
        filters.append(SatelliteImage.acquisition_date <= date_to)
    if processing_status:
        filters.append(SatelliteImage.processing_status == processing_status)
    
    # Spatial filter
    if bbox:
        try:
            coords = [float(x) for x in bbox.split(",")]
            if len(coords) == 4:
                filters.append(
                    ST_Intersects(
                        SatelliteImage.geometry,
                        ST_MakeEnvelope(*coords, 4326)
                    )
                )
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid bbox format. Use: min_lon,min_lat,max_lon,max_lat"
            )
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    query = query.order_by(SatelliteImage.acquisition_date.desc())
    
    # Execute query
    result = await db.execute(query)
    images = result.scalars().all()
    
    return PaginatedResponse(
        items=[SatelliteImageResponse.model_validate(img) for img in images],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/{image_id}", response_model=SatelliteImageResponse)
async def get_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> SatelliteImage:
    """Get specific satellite image by ID"""
    
    result = await db.execute(
        select(SatelliteImage).where(SatelliteImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    return image


@router.post("/collect", status_code=status.HTTP_202_ACCEPTED)
async def trigger_collection(
    background_tasks: BackgroundTasks,
    areas: List[str] = Query(["west_sea", "south_sea", "east_sea"]),
    days_back: int = Query(3, ge=1, le=30),
    max_cloud_coverage: float = Query(20, ge=0, le=100),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Trigger satellite data collection for Korean sea areas"""
    
    # Check user role
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Validate areas
    valid_areas = ["west_sea", "south_sea", "east_sea"]
    invalid_areas = [a for a in areas if a not in valid_areas]
    if invalid_areas:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid areas: {invalid_areas}. Valid options: {valid_areas}"
        )
    
    # Schedule collection task
    background_tasks.add_task(
        collect_satellite_data,
        areas=areas,
        days_back=days_back,
        max_cloud_coverage=max_cloud_coverage
    )
    
    return {
        "message": "Collection task scheduled",
        "areas": areas,
        "days_back": days_back,
        "max_cloud_coverage": max_cloud_coverage
    }


@router.post("/{image_id}/process", status_code=status.HTTP_202_ACCEPTED)
async def trigger_processing(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Trigger processing for a satellite image"""
    
    # Get image
    result = await db.execute(
        select(SatelliteImage).where(SatelliteImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Check if already processing
    if image.processing_status in [ProcessingStatus.DOWNLOADING, ProcessingStatus.PROCESSING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image is already being processed"
        )
    
    # Update status
    image.processing_status = ProcessingStatus.PROCESSING
    image.processing_started_at = datetime.utcnow()
    await db.commit()
    
    # Schedule processing task
    background_tasks.add_task(
        process_satellite_image,
        image_id=str(image_id)
    )
    
    return {
        "message": "Processing task scheduled",
        "image_id": str(image_id),
        "status": "processing"
    }


@router.patch("/{image_id}", response_model=SatelliteImageResponse)
async def update_image(
    image_id: UUID,
    update_data: SatelliteImageUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> SatelliteImage:
    """Update satellite image metadata"""
    
    # Check user role
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get image
    result = await db.execute(
        select(SatelliteImage).where(SatelliteImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(image, field, value)
    
    image.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(image)
    
    return image


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete satellite image"""
    
    # Check user role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete images"
        )
    
    # Get image
    result = await db.execute(
        select(SatelliteImage).where(SatelliteImage.id == image_id)
    )
    image = result.scalar_one_or_none()
    
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found"
        )
    
    # Delete image
    await db.delete(image)
    await db.commit()


# Background task functions
async def collect_satellite_data(
    areas: List[str],
    days_back: int,
    max_cloud_coverage: float
):
    """Background task to collect satellite data"""
    sentinel_service = Sentinel2Service()
    await sentinel_service.automated_collection(
        areas=areas,
        days_back=days_back,
        max_cloud=max_cloud_coverage
    )