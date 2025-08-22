"""Monitoring area management endpoints"""

from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from geoalchemy2.functions import ST_Contains, ST_MakeEnvelope

from satchat.core.database import get_async_db
from satchat.models.database import MonitoringArea, User, DebrisDetection, SatelliteImage
from satchat.models.schemas import (
    MonitoringAreaResponse,
    MonitoringAreaCreate,
    MonitoringAreaUpdate,
    MonitoringReport,
    PaginatedResponse
)
from satchat.api.auth import get_current_active_user

router = APIRouter()


@router.get("/areas", response_model=List[MonitoringAreaResponse])
async def list_monitoring_areas(
    is_active: Optional[bool] = None,
    area_type: Optional[str] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> List[MonitoringArea]:
    """List all monitoring areas"""
    
    # Build query
    query = select(MonitoringArea)
    
    # Apply filters
    filters = []
    if is_active is not None:
        filters.append(MonitoringArea.is_active == is_active)
    if area_type:
        filters.append(MonitoringArea.area_type == area_type)
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(MonitoringArea.priority.desc())
    
    # Execute query
    result = await db.execute(query)
    areas = result.scalars().all()
    
    return areas


@router.get("/areas/{area_id}", response_model=MonitoringAreaResponse)
async def get_monitoring_area(
    area_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> MonitoringArea:
    """Get specific monitoring area"""
    
    result = await db.execute(
        select(MonitoringArea).where(MonitoringArea.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring area not found"
        )
    
    return area


@router.post("/areas", response_model=MonitoringAreaResponse, status_code=status.HTTP_201_CREATED)
async def create_monitoring_area(
    area_data: MonitoringAreaCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> MonitoringArea:
    """Create new monitoring area"""
    
    # Check user role
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Check if name already exists
    result = await db.execute(
        select(MonitoringArea).where(MonitoringArea.name == area_data.name)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Monitoring area with this name already exists"
        )
    
    # Create geometry from bbox
    bbox = area_data.bbox
    from geoalchemy2 import WKTElement
    geometry = WKTElement(
        f"POLYGON(({bbox['min_lon']} {bbox['min_lat']}, "
        f"{bbox['max_lon']} {bbox['min_lat']}, "
        f"{bbox['max_lon']} {bbox['max_lat']}, "
        f"{bbox['min_lon']} {bbox['max_lat']}, "
        f"{bbox['min_lon']} {bbox['min_lat']}))",
        srid=4326
    )
    
    # Create monitoring area
    area_dict = area_data.model_dump()
    area_dict['geometry'] = geometry
    area = MonitoringArea(**area_dict)
    
    db.add(area)
    await db.commit()
    await db.refresh(area)
    
    return area


@router.patch("/areas/{area_id}", response_model=MonitoringAreaResponse)
async def update_monitoring_area(
    area_id: UUID,
    update_data: MonitoringAreaUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> MonitoringArea:
    """Update monitoring area"""
    
    # Check user role
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get area
    result = await db.execute(
        select(MonitoringArea).where(MonitoringArea.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring area not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(area, field, value)
    
    area.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(area)
    
    return area


@router.delete("/areas/{area_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitoring_area(
    area_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete monitoring area"""
    
    # Check user role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete monitoring areas"
        )
    
    # Get area
    result = await db.execute(
        select(MonitoringArea).where(MonitoringArea.id == area_id)
    )
    area = result.scalar_one_or_none()
    
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring area not found"
        )
    
    # Delete area
    await db.delete(area)
    await db.commit()


@router.get("/areas/{area_id}/report", response_model=MonitoringReport)
async def get_monitoring_report(
    area_id: UUID,
    days_back: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> MonitoringReport:
    """Generate monitoring report for an area"""
    
    # Get area
    area_result = await db.execute(
        select(MonitoringArea).where(MonitoringArea.id == area_id)
    )
    area = area_result.scalar_one_or_none()
    
    if not area:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Monitoring area not found"
        )
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Get satellite images in area
    image_query = select(func.count(SatelliteImage.id)).where(
        and_(
            ST_Contains(area.geometry, SatelliteImage.geometry),
            SatelliteImage.acquisition_date >= start_date,
            SatelliteImage.acquisition_date <= end_date
        )
    )
    image_result = await db.execute(image_query)
    total_images = image_result.scalar() or 0
    
    # Get detections in area
    detection_query = select(DebrisDetection).where(
        and_(
            ST_Contains(area.geometry, DebrisDetection.geometry),
            DebrisDetection.created_at >= start_date,
            DebrisDetection.created_at <= end_date
        )
    )
    detection_result = await db.execute(detection_query)
    detections = detection_result.scalars().all()
    
    # Calculate debris summary
    debris_summary = {}
    total_area = 0.0
    
    for detection in detections:
        debris_type = detection.debris_type.value
        if debris_type not in debris_summary:
            debris_summary[debris_type] = {
                "count": 0,
                "total_area": 0.0,
                "avg_confidence": 0.0
            }
        
        debris_summary[debris_type]["count"] += 1
        if detection.area_m2:
            debris_summary[debris_type]["total_area"] += detection.area_m2
            total_area += detection.area_m2
    
    # Calculate average confidence
    for debris_type in debris_summary:
        type_detections = [d for d in detections if d.debris_type.value == debris_type]
        if type_detections:
            avg_conf = sum(d.confidence for d in type_detections) / len(type_detections)
            debris_summary[debris_type]["avg_confidence"] = avg_conf
    
    # Count alerts generated
    # This would require joining with alerts table
    alerts_generated = 0  # Placeholder
    
    # Calculate average processing time
    # This would require analyzing processing jobs
    avg_processing_time = 0.0  # Placeholder
    
    return MonitoringReport(
        area_id=area_id,
        area_name=area.name,
        period_start=start_date,
        period_end=end_date,
        total_images=total_images,
        total_detections=len(detections),
        debris_summary=debris_summary,
        alerts_generated=alerts_generated,
        average_processing_time=avg_processing_time
    )