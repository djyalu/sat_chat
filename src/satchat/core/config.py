"""SatChat 시스템 설정 관리"""

from typing import List, Optional, Dict, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, PostgresDsn, RedisDsn
from functools import lru_cache
import os
from pathlib import Path


class Settings(BaseSettings):
    """SatChat 중앙 설정 클래스"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 기본 설정
    app_name: str = "SatChat"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # API 설정
    api_prefix: str = "/api/v1"
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # 데이터베이스 설정
    database_url: PostgresDsn = Field(
        default="postgresql://satchat:password@localhost:5432/satchat",
        env="DATABASE_URL"
    )
    database_pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    database_max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    
    # Redis 설정
    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # 보안 설정
    secret_key: SecretStr = Field(
        default="your-secret-key-change-this-in-production",
        env="SECRET_KEY"
    )
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=60, env="JWT_EXPIRATION_MINUTES")
    
    # 위성 데이터 API 설정
    sentinel_user: Optional[str] = Field(default=None, env="SENTINEL_USER")
    sentinel_password: Optional[SecretStr] = Field(default=None, env="SENTINEL_PASSWORD")
    sentinel_api_url: str = Field(
        default="https://scihub.copernicus.eu/dhus",
        env="SENTINEL_API_URL"
    )
    
    # Sentinel Hub API 설정
    sentinel_hub_client_id: Optional[str] = Field(default=None, env="SENTINEL_HUB_CLIENT_ID")
    sentinel_hub_client_secret: Optional[SecretStr] = Field(default=None, env="SENTINEL_HUB_CLIENT_SECRET")
    sentinel_hub_instance_id: Optional[str] = Field(default=None, env="SENTINEL_HUB_INSTANCE_ID")
    sentinel_hub_organization_id: str = Field(
        default="WS_5a8204bc-452c-454f-b068-b65ee4822073",
        env="SENTINEL_HUB_ORGANIZATION_ID"
    )
    
    kompsat_api_key: Optional[SecretStr] = Field(default=None, env="KOMPSAT_API_KEY")
    kompsat_api_url: str = Field(
        default="https://ksatdb.kari.re.kr/api",
        env="KOMPSAT_API_URL"
    )
    
    planet_api_key: Optional[SecretStr] = Field(default=None, env="PLANET_API_KEY")
    
    # 저장소 설정
    s3_endpoint: str = Field(default="http://localhost:9000", env="S3_ENDPOINT")
    s3_access_key: SecretStr = Field(default="minioadmin", env="S3_ACCESS_KEY")
    s3_secret_key: SecretStr = Field(default="minioadmin", env="S3_SECRET_KEY")
    s3_bucket_raw: str = Field(default="satchat-raw", env="S3_BUCKET_RAW")
    s3_bucket_processed: str = Field(default="satchat-processed", env="S3_BUCKET_PROCESSED")
    s3_region: str = Field(default="us-east-1", env="S3_REGION")
    
    # ML 모델 설정
    model_path: Path = Field(default=Path("data/models"), env="MODEL_PATH")
    model_device: str = Field(default="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu", env="MODEL_DEVICE")
    model_batch_size: int = Field(default=8, env="MODEL_BATCH_SIZE")
    model_confidence_threshold: float = Field(default=0.5, env="MODEL_CONFIDENCE_THRESHOLD")
    
    # 처리 설정
    max_workers: int = Field(default=4, env="MAX_WORKERS")
    task_timeout: int = Field(default=3600, env="TASK_TIMEOUT")  # seconds
    image_tile_size: int = Field(default=512, env="IMAGE_TILE_SIZE")
    
    # 모니터링 설정
    monitoring_interval: int = Field(default=60, env="MONITORING_INTERVAL")  # seconds
    alert_webhook_url: Optional[str] = Field(default=None, env="ALERT_WEBHOOK_URL")
    
    # 한국 해역 특화 설정
    korea_bbox: Dict[str, List[float]] = Field(
        default={
            "west_sea": [124.0, 33.0, 127.0, 39.0],  # 서해
            "south_sea": [126.0, 32.0, 130.0, 35.0],  # 남해
            "east_sea": [128.0, 35.0, 132.0, 38.5],  # 동해
        },
        env="KOREA_BBOX"
    )
    
    # 로깅 설정
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}",
        env="LOG_FORMAT"
    )
    
    @property
    def database_url_sync(self) -> str:
        """SQLAlchemy 동기 URL"""
        return str(self.database_url)
    
    @property
    def database_url_async(self) -> str:
        """SQLAlchemy 비동기 URL"""
        return self.database_url_sync.replace("postgresql://", "postgresql+asyncpg://")
    
    @property
    def redis_url_str(self) -> str:
        """Redis URL 문자열"""
        return str(self.redis_url)
    
    @property
    def is_production(self) -> bool:
        """Production 환경 여부"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Development 환경 여부"""
        return self.environment == "development"


@lru_cache()
def get_settings() -> Settings:
    """Settings 싱글톤 인스턴스 반환"""
    return Settings()


settings = get_settings()