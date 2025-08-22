"""SatChat 데이터베이스 모델"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import uuid4
from enum import Enum

from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, JSON, Text,
    ForeignKey, Index, UniqueConstraint, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from geoalchemy2 import Geometry

Base = declarative_base()


class DebrisType(str, Enum):
    """폐기물 유형 열거형"""
    PLASTIC = "plastic"
    OIL = "oil"
    FISHING_GEAR = "fishing_gear"
    ORGANIC = "organic"
    METAL = "metal"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """처리 상태 열거형"""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AlertSeverity(str, Enum):
    """알림 심각도 열거형"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SatelliteImage(Base):
    """위성 이미지 메타데이터 테이블"""
    __tablename__ = "satellite_images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 위성 정보
    satellite_name = Column(String(50), nullable=False)  # Sentinel-2, KOMPSAT 등
    product_id = Column(String(255), unique=True, nullable=False)
    acquisition_date = Column(DateTime(timezone=True), nullable=False)
    
    # 위치 정보
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    bbox = Column(JSONB)  # {"min_lat": 0, "max_lat": 0, "min_lon": 0, "max_lon": 0}
    
    # 이미지 정보
    cloud_coverage = Column(Float)  # 0-100 %
    resolution = Column(Float)  # meters per pixel
    bands = Column(ARRAY(String))  # ['B02', 'B03', 'B04', ...]
    file_size = Column(Integer)  # bytes
    
    # 저장 정보
    raw_data_path = Column(String(500))
    processed_data_path = Column(String(500))
    thumbnail_path = Column(String(500))
    
    # 처리 정보
    processing_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    processing_error = Column(Text)
    
    # 메타데이터
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    detections = relationship("DebrisDetection", back_populates="image", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_satellite_images_acquisition_date', 'acquisition_date'),
        Index('idx_satellite_images_geometry', 'geometry', postgresql_using='gist'),
        Index('idx_satellite_images_processing_status', 'processing_status'),
    )


class DebrisDetection(Base):
    """폐기물 탐지 결과 테이블"""
    __tablename__ = "debris_detections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 이미지 참조
    image_id = Column(UUID(as_uuid=True), ForeignKey('satellite_images.id'), nullable=False)
    
    # 탐지 정보
    debris_type = Column(SQLEnum(DebrisType), nullable=False)
    confidence = Column(Float, nullable=False)  # 0-1
    
    # 위치 정보
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    area_m2 = Column(Float)  # 추정 면적 (제곱미터)
    
    # 바운딩 박스 (이미지 좌표)
    bbox_pixel = Column(JSONB)  # {"x": 0, "y": 0, "width": 100, "height": 100}
    
    # 특징
    spectral_indices = Column(JSONB)  # {"ndvi": 0.5, "fai": 0.3, ...}
    features = Column(JSONB)  # ML 모델 특징
    
    # 검증
    is_verified = Column(Boolean, default=False)
    verified_by = Column(String(100))
    verified_at = Column(DateTime(timezone=True))
    verification_notes = Column(Text)
    
    # 메타데이터
    detection_model = Column(String(100))  # 사용된 모델 이름/버전
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    image = relationship("SatelliteImage", back_populates="detections")
    alerts = relationship("Alert", back_populates="detection", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_debris_detections_image_id', 'image_id'),
        Index('idx_debris_detections_debris_type', 'debris_type'),
        Index('idx_debris_detections_confidence', 'confidence'),
        Index('idx_debris_detections_geometry', 'geometry', postgresql_using='gist'),
        Index('idx_debris_detections_created_at', 'created_at'),
    )


class Alert(Base):
    """알림 테이블"""
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 탐지 참조
    detection_id = Column(UUID(as_uuid=True), ForeignKey('debris_detections.id'), nullable=False)
    
    # 알림 정보
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    # 위치 정보
    location_name = Column(String(255))  # 예: "서해 태안 앞바다"
    coordinates = Column(JSONB)  # {"lat": 36.5, "lon": 126.3}
    
    # 알림 상태
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime(timezone=True))
    sent_to = Column(ARRAY(String))  # 수신자 목록
    
    # 응답
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(String(100))
    acknowledged_at = Column(DateTime(timezone=True))
    response_notes = Column(Text)
    
    # 메타데이터
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    detection = relationship("DebrisDetection", back_populates="alerts")
    
    __table_args__ = (
        Index('idx_alerts_detection_id', 'detection_id'),
        Index('idx_alerts_severity', 'severity'),
        Index('idx_alerts_created_at', 'created_at'),
    )


class MonitoringArea(Base):
    """모니터링 구역 테이블"""
    __tablename__ = "monitoring_areas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 구역 정보
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    area_type = Column(String(50))  # 'west_sea', 'south_sea', 'east_sea', 'custom'
    
    # 위치 정보
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False)
    bbox = Column(JSONB)  # 바운딩 박스
    
    # 모니터링 설정
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=1)  # 1-10, 높을수록 우선순위 높음
    monitoring_frequency = Column(Integer, default=24)  # hours
    
    # 임계값 설정
    alert_thresholds = Column(JSONB)  # {"plastic": 0.7, "oil": 0.8, ...}
    
    # 담당자 정보
    responsible_org = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    
    # 메타데이터
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_monitoring_areas_geometry', 'geometry', postgresql_using='gist'),
        Index('idx_monitoring_areas_is_active', 'is_active'),
        Index('idx_monitoring_areas_priority', 'priority'),
    )


class ProcessingJob(Base):
    """처리 작업 테이블"""
    __tablename__ = "processing_jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 작업 정보
    job_type = Column(String(50), nullable=False)  # 'download', 'preprocess', 'detection', 'postprocess'
    job_status = Column(SQLEnum(ProcessingStatus), default=ProcessingStatus.PENDING)
    
    # 대상 정보
    target_type = Column(String(50))  # 'image', 'area', 'batch'
    target_id = Column(UUID(as_uuid=True))
    
    # 실행 정보
    worker_id = Column(String(100))
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    
    # 진행 상황
    progress = Column(Integer, default=0)  # 0-100 %
    current_step = Column(String(255))
    total_steps = Column(Integer)
    
    # 결과
    result = Column(JSONB)
    error_message = Column(Text)
    error_traceback = Column(Text)
    
    # 재시도
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 메타데이터
    parameters = Column(JSONB)
    metadata = Column(JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_processing_jobs_job_status', 'job_status'),
        Index('idx_processing_jobs_job_type', 'job_type'),
        Index('idx_processing_jobs_created_at', 'created_at'),
    )


class User(Base):
    """사용자 테이블"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # 인증 정보
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # 프로필
    full_name = Column(String(255))
    organization = Column(String(255))
    department = Column(String(255))
    phone = Column(String(50))
    
    # 권한
    role = Column(String(50), default="viewer")  # 'admin', 'operator', 'analyst', 'viewer'
    permissions = Column(JSONB)
    
    # 상태
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_login_at = Column(DateTime(timezone=True))
    
    # 설정
    preferences = Column(JSONB)  # 사용자 설정
    notification_settings = Column(JSONB)  # 알림 설정
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_username', 'username'),
        Index('idx_users_role', 'role'),
    )