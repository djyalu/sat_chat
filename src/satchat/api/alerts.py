"""Alert management endpoints"""

from typing import List, Optional
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from satchat.core.database import get_async_db
from satchat.models.database import Alert, User, AlertSeverity, DebrisDetection
from satchat.models.schemas import (
    AlertResponse,
    AlertCreate,
    AlertUpdate,
    PaginatedResponse
)
from satchat.api.auth import get_current_active_user
from satchat.services.notification import send_alert_notification

router = APIRouter()


@router.get("/", response_model=PaginatedResponse)
async def list_alerts(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    severity: Optional[AlertSeverity] = None,
    is_acknowledged: Optional[bool] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> PaginatedResponse:
    """List alerts with filtering and pagination"""
    
    # Build query
    query = select(Alert)
    
    # Apply filters
    filters = []
    if severity:
        filters.append(Alert.severity == severity)
    if is_acknowledged is not None:
        filters.append(Alert.is_acknowledged == is_acknowledged)
    if date_from:
        filters.append(Alert.created_at >= date_from)
    if date_to:
        filters.append(Alert.created_at <= date_to)
    
    if filters:
        query = query.where(and_(*filters))
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Apply pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)
    query = query.order_by(Alert.severity.desc(), Alert.created_at.desc())
    
    # Execute query
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return PaginatedResponse(
        items=[AlertResponse.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=(total + page_size - 1) // page_size
    )


@router.get("/active", response_model=List[AlertResponse])
async def get_active_alerts(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> List[Alert]:
    """Get active (unacknowledged) alerts"""
    
    query = select(Alert).where(
        Alert.is_acknowledged == False
    ).order_by(
        Alert.severity.desc(),
        Alert.created_at.desc()
    ).limit(limit)
    
    result = await db.execute(query)
    alerts = result.scalars().all()
    
    return alerts


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> Alert:
    """Get specific alert by ID"""
    
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    return alert


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
async def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> Alert:
    """Create new alert"""
    
    # Check user role
    if current_user.role not in ["admin", "operator", "analyst"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Verify detection exists
    detection_result = await db.execute(
        select(DebrisDetection).where(DebrisDetection.id == alert_data.detection_id)
    )
    detection = detection_result.scalar_one_or_none()
    
    if not detection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection not found"
        )
    
    # Create alert
    alert = Alert(**alert_data.model_dump())
    
    db.add(alert)
    await db.commit()
    await db.refresh(alert)
    
    # Schedule notification
    if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
        background_tasks.add_task(
            send_alert_notification,
            alert_id=str(alert.id)
        )
    
    return alert


@router.patch("/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(
    alert_id: UUID,
    update_data: AlertUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> Alert:
    """Acknowledge an alert"""
    
    # Get alert
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Update acknowledgment
    if update_data.is_acknowledged:
        alert.is_acknowledged = True
        alert.acknowledged_by = current_user.username
        alert.acknowledged_at = datetime.utcnow()
    
    if update_data.response_notes:
        alert.response_notes = update_data.response_notes
    
    alert.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(alert)
    
    return alert


@router.post("/{alert_id}/resend", status_code=status.HTTP_202_ACCEPTED)
async def resend_alert(
    alert_id: UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Resend alert notification"""
    
    # Check user role
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get alert
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Schedule notification
    background_tasks.add_task(
        send_alert_notification,
        alert_id=str(alert_id)
    )
    
    return {
        "message": "Alert notification scheduled",
        "alert_id": str(alert_id)
    }


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
) -> None:
    """Delete alert"""
    
    # Check user role
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete alerts"
        )
    
    # Get alert
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = result.scalar_one_or_none()
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    
    # Delete alert
    await db.delete(alert)
    await db.commit()