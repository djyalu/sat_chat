"""SatChat API 스키마 (Pydantic 모델)"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator
from pydantic.types import conint, confloat


# Enums (database.py와 동일)
class DebrisType(str, Enum):
    PLASTIC = "plastic"
    OIL = "oil"
    FISHING_GEAR = "fishing_gear"
    ORGANIC = "organic"
    METAL = "metal"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Base Schemas
class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        json_encoders={datetime: lambda v: v.isoformat()}
    )


# Satellite Image Schemas
class SatelliteImageBase(BaseSchema):
    """Satellite image base schema"""
    satellite_name: str = Field(..., description="Satellite name (e.g., Sentinel-2, KOMPSAT)")
    product_id: str = Field(..., description="Unique product identifier")
    acquisition_date: datetime = Field(..., description="Image acquisition date")
    center_lat: float = Field(..., ge=-90, le=90)
    center_lon: float = Field(..., ge=-180, le=180)
    cloud_coverage: Optional[float] = Field(None, ge=0, le=100)
    resolution: Optional[float] = Field(None, gt=0)


class SatelliteImageCreate(SatelliteImageBase):
    """Schema for creating satellite image"""
    bbox: Optional[Dict[str, float]] = None
    bands: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class SatelliteImageUpdate(BaseSchema):
    """Schema for updating satellite image"""
    processing_status: Optional[ProcessingStatus] = None
    processed_data_path: Optional[str] = None
    processing_error: Optional[str] = None


class SatelliteImageResponse(SatelliteImageBase):
    """Schema for satellite image response"""
    id: UUID
    processing_status: ProcessingStatus
    raw_data_path: Optional[str]
    processed_data_path: Optional[str]
    thumbnail_path: Optional[str]
    created_at: datetime
    updated_at: datetime


# Debris Detection Schemas
class DebrisDetectionBase(BaseSchema):
    """Debris detection base schema"""
    debris_type: DebrisType
    confidence: confloat(ge=0, le=1) = Field(..., description="Detection confidence (0-1)")
    center_lat: float = Field(..., ge=-90, le=90)
    center_lon: float = Field(..., ge=-180, le=180)
    area_m2: Optional[float] = Field(None, gt=0, description="Estimated area in square meters")


class DebrisDetectionCreate(DebrisDetectionBase):
    """Schema for creating debris detection"""
    image_id: UUID
    bbox_pixel: Optional[Dict[str, int]] = None
    spectral_indices: Optional[Dict[str, float]] = None
    features: Optional[Dict[str, Any]] = None
    detection_model: str = Field(..., description="Model name/version used for detection")


class DebrisDetectionUpdate(BaseSchema):
    """Schema for updating debris detection"""
    is_verified: Optional[bool] = None
    verified_by: Optional[str] = None
    verification_notes: Optional[str] = None


class DebrisDetectionResponse(DebrisDetectionBase):
    """Schema for debris detection response"""
    id: UUID
    image_id: UUID
    is_verified: bool
    verified_by: Optional[str]
    verified_at: Optional[datetime]
    detection_model: str
    created_at: datetime
    updated_at: datetime


# Alert Schemas
class AlertBase(BaseSchema):
    """Alert base schema"""
    severity: AlertSeverity
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    location_name: Optional[str] = Field(None, max_length=255)


class AlertCreate(AlertBase):
    """Schema for creating alert"""
    detection_id: UUID
    coordinates: Optional[Dict[str, float]] = None


class AlertUpdate(BaseSchema):
    """Schema for updating alert"""
    is_acknowledged: Optional[bool] = None
    acknowledged_by: Optional[str] = None
    response_notes: Optional[str] = None


class AlertResponse(AlertBase):
    """Schema for alert response"""
    id: UUID
    detection_id: UUID
    is_sent: bool
    sent_at: Optional[datetime]
    is_acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Monitoring Area Schemas
class MonitoringAreaBase(BaseSchema):
    """Monitoring area base schema"""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    area_type: Optional[str] = Field(None, max_length=50)
    is_active: bool = True
    priority: conint(ge=1, le=10) = 1
    monitoring_frequency: conint(gt=0) = 24  # hours


class MonitoringAreaCreate(MonitoringAreaBase):
    """Schema for creating monitoring area"""
    bbox: Dict[str, float] = Field(..., description="Bounding box coordinates")
    alert_thresholds: Optional[Dict[str, float]] = None
    responsible_org: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class MonitoringAreaUpdate(BaseSchema):
    """Schema for updating monitoring area"""
    is_active: Optional[bool] = None
    priority: Optional[conint(ge=1, le=10)] = None
    monitoring_frequency: Optional[conint(gt=0)] = None
    alert_thresholds: Optional[Dict[str, float]] = None


class MonitoringAreaResponse(MonitoringAreaBase):
    """Schema for monitoring area response"""
    id: UUID
    bbox: Dict[str, float]
    responsible_org: Optional[str]
    contact_email: Optional[str]
    created_at: datetime
    updated_at: datetime


# Processing Job Schemas
class ProcessingJobBase(BaseSchema):
    """Processing job base schema"""
    job_type: str = Field(..., max_length=50)
    job_status: ProcessingStatus = ProcessingStatus.PENDING
    target_type: Optional[str] = Field(None, max_length=50)
    target_id: Optional[UUID] = None


class ProcessingJobCreate(ProcessingJobBase):
    """Schema for creating processing job"""
    parameters: Optional[Dict[str, Any]] = None
    max_retries: int = 3


class ProcessingJobUpdate(BaseSchema):
    """Schema for updating processing job"""
    job_status: Optional[ProcessingStatus] = None
    progress: Optional[conint(ge=0, le=100)] = None
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class ProcessingJobResponse(ProcessingJobBase):
    """Schema for processing job response"""
    id: UUID
    worker_id: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: int
    current_step: Optional[str]
    retry_count: int
    created_at: datetime
    updated_at: datetime


# User Schemas
class UserBase(BaseSchema):
    """User base schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating user"""
    password: str = Field(..., min_length=8)
    role: str = "viewer"


class UserUpdate(BaseSchema):
    """Schema for updating user"""
    full_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime


# Authentication Schemas
class Token(BaseSchema):
    """JWT token schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseSchema):
    """Token data schema"""
    user_id: UUID
    username: str
    role: str
    exp: datetime


class LoginRequest(BaseSchema):
    """Login request schema"""
    username: str
    password: str


# Statistics & Analytics Schemas
class DebrisStatistics(BaseSchema):
    """Debris statistics schema"""
    total_detections: int
    by_type: Dict[str, int]
    by_severity: Dict[str, int]
    average_confidence: float
    total_area_m2: float
    date_range: Dict[str, datetime]


class MonitoringReport(BaseSchema):
    """Monitoring report schema"""
    area_id: UUID
    area_name: str
    period_start: datetime
    period_end: datetime
    total_images: int
    total_detections: int
    debris_summary: Dict[str, Any]
    alerts_generated: int
    average_processing_time: float


# Search & Filter Schemas  
class SearchFilters(BaseSchema):
    """Search filters schema"""
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    bbox: Optional[Dict[str, float]] = None
    debris_types: Optional[List[DebrisType]] = None
    min_confidence: Optional[confloat(ge=0, le=1)] = None
    satellite_names: Optional[List[str]] = None
    is_verified: Optional[bool] = None


class PaginationParams(BaseSchema):
    """Pagination parameters schema"""
    page: conint(ge=1) = 1
    page_size: conint(ge=1, le=100) = 20
    sort_by: Optional[str] = "created_at"
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseSchema):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int