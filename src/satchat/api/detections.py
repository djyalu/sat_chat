"""Debris detection endpoints"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from geoalchemy2.functions import ST_DWithin, ST_MakePoint

from satchat.core.database import get_async_db
from satchat.models.database import DebrisDetection, User, DebrisType
from satchat.models.schemas import (
    DebrisDetectionResponse,
    DebrisDetectionCreate,
    DebrisDetectionUpdate,
    PaginatedResponse,
    DebrisStatistics
)
from satchat.api.auth import get_current_active_user

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_detections(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    debris_type: Optional[DebrisType] = None,
    min_confidence: float = Query(0.0, ge=0.0, le=1.0),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    is_verified: Optional[bool] = None,
    image_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse:
    """List debris detections with filtering and pagination"""
    
    # Build query
    query = select(DebrisDetection)
    
    # Apply filters
    filters = []
    if debris_type:
        filters.append(DebrisDetection.debris_type == debris_type)
    if min_confidence > 0:
        filters.append(DebrisDetection.confidence >= min_confidence)
    if date_from:
        filters.append(DebrisDetection.created_at >= date_from)
    if date_to:
        filters.append(DebrisDetection.created_at <= date_to)
    if is_verified is not None:
        filters.append(DebrisDetection.is_verified == is_verified)
    if image_id:
        filters.append(DebrisDetection.image_id == image_id)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    query = query.order_by(DebrisDetection.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    detections = result.scalars().all()
    
    return PaginatedResponse(
        items=[DebrisDetectionResponse.model_validate(d) for d in detections],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/nearby")
async def get_nearby_detections(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(10, ge=0.1, le=100),
    debris_type: Optional[DebrisType] = None,
    min_confidence: float = Query(0.5, ge=0.0, le=1.0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> List[DebrisDetectionResponse]:
    """Get debris detections near a specific location"""
    
    # Build spatial query
    point = ST_MakePoint(lon, lat, 4326)
    radius_meters = radius_km * 1000
    
    query = select(DebrisDetection).where(
        ST_DWithin(
            DebrisDetection.geometry,
            point,
            radius_meters
        )
    )
    
    # Apply additional filters
    if debris_type:
        query = query.where(DebrisDetection.debris_type == debris_type)
    if min_confidence > 0:
        query = query.where(DebrisDetection.confidence >= min_confidence)
    
    # Limit results
    query = query.limit(limit)
    
    # Execute query
    result = await db.execute(query)
    detections = result.scalars().all()
    
    return [DebrisDetectionResponse.model_validate(d) for d in detections]


@router.get("/statistics", response_model=DebrisStatistics)
async def get_statistics(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> DebrisStatistics:
    """Get debris detection statistics"""
    
    # Build base query
    query = select(DebrisDetection)
    
    # Apply date filters
    if date_from:
        query = query.where(DebrisDetection.created_at >= date_from)
    if date_to:
        query = query.where(DebrisDetection.created_at <= date_to)
    
    # Get all detections
    result = await db.execute(query)
    detections = result.scalars().all()
    
    # Calculate statistics
    total_detections = len(detections)
    
    # Group by type
    by_type = {}
    by_severity = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    total_area = 0.0
    confidence_sum = 0.0
    
    for detection in detections:
        # Count by type
        debris_type = detection.debris_type.value
        by_type[debris_type] = by_type.get(debris_type, 0) + 1
        
        # Count by severity (based on confidence)
        if detection.confidence < 0.3:
            by_severity["low"] += 1
        elif detection.confidence < 0.6:
            by_severity["medium"] += 1
        elif detection.confidence < 0.9:
            by_severity["high"] += 1
        else:
            by_severity["critical"] += 1
        
        # Sum area and confidence
        if detection.area_m2:
            total_area += detection.area_m2
        confidence_sum += detection.confidence
    
    # Calculate average confidence
    avg_confidence = confidence_sum / total_detections if total_detections > 0 else 0
    
    return DebrisStatistics(
        total_detections=total_detections,
        by_type=by_type,
        by_severity=by_severity,
        average_confidence=avg_confidence,
        total_area_m2=total_area,
        date_range={
            "start": date_from or datetime.min,
            "end": date_to or datetime.now()
        }
    )


@router.get("/{detection_id}", response_model=DebrisDetectionResponse)
async def get_detection(
    detection_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> DebrisDetection:
    """Get specific debris detection by ID"""
    
    result = await db.execute(
        select(DebrisDetection).where(DebrisDetection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    return detection


@router.post("/", response_model=DebrisDetectionResponse, status_code=status.HTTP_201_CREATED)
async def create_detection(
    detection_data: DebrisDetectionCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> DebrisDetection:
    """Create new debris detection"""
    
    # Check user role
    if current_user.role not in ["admin", "operator", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Create detection
    detection = DebrisDetection(**detection_data.model_dump())
    
    db.add(detection)
    await db.commit()
    await db.refresh(detection)
    
    return detection


@router.patch("/{detection_id}/verify", response_model=DebrisDetectionResponse)
async def verify_detection(
    detection_id: UUID,
    verification_data: DebrisDetectionUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> DebrisDetection:
    """Verify or update debris detection"""
    
    # Check user role
    if current_user.role not in ["admin", "operator", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get detection
    result = await db.execute(
        select(DebrisDetection).where(DebrisDetection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Update verification fields
    if verification_data.is_verified is not None:
        detection.is_verified = verification_data.is_verified
        detection.verified_by = current_user.username
        detection.verified_at = datetime.utcnow()
    
    if verification_data.verification_notes:
        detection.verification_notes = verification_data.verification_notes
    
    detection.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(detection)
    
    return detection


@router.delete("/{detection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_detection(
    detection_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete debris detection"""
    
    # Check user role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete detections"
        )
    
    # Get detection
    result = await db.execute(
        select(DebrisDetection).where(DebrisDetection.id == detection_id)
    )
    detection = result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Delete detection
    await db.delete(detection)
    await db.commit()