# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SatChat is a marine debris monitoring system developed by Telefix (텔레픽스) that uses satellite imagery and AI/ML to detect and track ocean waste. The system is optimized for Korean waters (West Sea, South Sea, East Sea) and integrates multiple satellite data sources including Sentinel-2 and KOMPSAT.

## Key Technologies

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL with PostGIS extension for geospatial data
- **Cache**: Redis for session management and task queuing
- **Storage**: MinIO (S3-compatible object storage)
- **ML Framework**: PyTorch for deep learning models
- **Image Processing**: OpenCV, Rasterio, scikit-image
- **Task Queue**: Celery for async processing
- **Python Version**: 3.11+

## Project Structure

```
sat_chat/
├── src/satchat/
│   ├── api/             # API endpoints (FastAPI routers)
│   ├── core/            # Core configuration and database setup
│   │   ├── config.py    # Settings management (Pydantic)
│   │   └── database.py  # Database connections
│   ├── models/          # Data models
│   │   ├── database.py  # SQLAlchemy ORM models
│   │   └── schemas.py   # Pydantic API schemas
│   ├── services/        # Business logic
│   │   ├── satellite/   # Satellite data collection
│   │   └── storage.py   # S3/MinIO operations
│   ├── ml/              # Machine learning models
│   ├── processing/      # Image processing pipelines
│   ├── monitoring/      # Monitoring and alerts
│   └── main.py          # FastAPI application entry point
├── tests/               # Test files
├── config/              # Configuration files
├── scripts/             # Utility scripts
├── pyproject.toml       # Poetry dependency management
├── .env.example         # Environment variables template
└── README.md            # Project documentation
```

## Common Development Commands

### Environment Setup
```bash
# Install Poetry (if not installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell

# Copy environment variables
cp .env.example .env
# Edit .env with actual values
```

### Database Operations
```bash
# Start PostgreSQL and Redis with Docker
docker-compose up -d postgres redis minio

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "Description"
```

### Running the Application
```bash
# Development server with hot reload
uvicorn src.satchat.main:app --reload --host 0.0.0.0 --port 8000

# Production server
gunicorn src.satchat.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Run Celery worker (for async tasks)
celery -A src.satchat.worker worker --loglevel=info

# Run Celery beat (for scheduled tasks)
celery -A src.satchat.worker beat --loglevel=info
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/satchat --cov-report=html

# Run specific test file
pytest tests/unit/test_detection.py

# Run tests in parallel
pytest -n auto
```

### Code Quality
```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with MyPy
mypy src/

# Run all quality checks
pre-commit run --all-files
```

## Architecture Overview

### Core Components

1. **Data Collection Layer**
   - `services/satellite/`: Integrates with satellite APIs (Sentinel, KOMPSAT)
   - Automated data collection with configurable schedules
   - Handles authentication and rate limiting

2. **Processing Pipeline**
   - `processing/`: Image preprocessing (atmospheric correction, cloud masking)
   - `ml/`: Deep learning models for debris detection (YOLO, U-Net)
   - Async processing using Celery workers

3. **API Layer**
   - FastAPI-based REST API
   - JWT authentication
   - WebSocket support for real-time updates
   - Automatic API documentation (Swagger/ReDoc)

4. **Storage Architecture**
   - PostgreSQL: Metadata, user data, detection results
   - PostGIS: Geospatial queries and indexing
   - MinIO/S3: Raw and processed satellite images
   - Redis: Cache and task queue

### Key Database Models

- `SatelliteImage`: Satellite image metadata and processing status
- `DebrisDetection`: Detection results with confidence scores
- `Alert`: Alert notifications for critical detections
- `MonitoringArea`: Defined areas for regular monitoring
- `ProcessingJob`: Async job tracking
- `User`: User authentication and permissions

### API Endpoints Structure

- `/api/v1/auth/`: Authentication (login, refresh, logout)
- `/api/v1/images/`: Satellite image management
- `/api/v1/detections/`: Debris detection results
- `/api/v1/alerts/`: Alert management
- `/api/v1/monitoring/`: Monitoring area configuration
- `/health/`: Health check endpoints
- `/metrics/`: Prometheus metrics (production only)

## Environment Variables

Key environment variables (see `.env.example` for full list):

- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `S3_ENDPOINT`: MinIO/S3 endpoint
- `SENTINEL_USER/PASSWORD`: Sentinel Hub credentials
- `KOMPSAT_API_KEY`: KOMPSAT satellite API key
- `SECRET_KEY`: JWT signing key (must be secure in production)
- `MODEL_DEVICE`: `cuda` for GPU or `cpu`

## Korean Sea Areas Configuration

The system is configured for three main Korean sea areas:

- **West Sea (서해)**: `[124.0, 33.0, 127.0, 39.0]` - High turbidity
- **South Sea (남해)**: `[126.0, 32.0, 130.0, 35.0]` - Optimal optical conditions
- **East Sea (동해)**: `[128.0, 35.0, 132.0, 38.5]` - Deep water, high resolution

## Development Best Practices

1. **Async/Await**: Use async functions for I/O operations
2. **Type Hints**: Always include type hints for better code clarity
3. **Error Handling**: Use structured error responses with proper HTTP status codes
4. **Logging**: Use loguru for structured logging
5. **Testing**: Write tests for all new features (aim for >80% coverage)
6. **Documentation**: Update API docs and docstrings for all public functions
7. **Security**: Never commit secrets, use environment variables
8. **Database**: Use migrations for all schema changes

## Troubleshooting

### Common Issues

1. **Database connection errors**: Check PostgreSQL is running and credentials are correct
2. **S3/MinIO errors**: Ensure MinIO is running and buckets are created
3. **Import errors**: Run `poetry install` to ensure all dependencies are installed
4. **Migration errors**: Check database is accessible and migrations are up to date
5. **Celery not processing**: Ensure Redis is running and worker is started

### Useful Debug Commands

```bash
# Check PostgreSQL connection
psql $DATABASE_URL -c "SELECT 1"

# Check Redis connection
redis-cli ping

# List MinIO buckets
mc ls minio/

# View Celery tasks
celery -A src.satchat.worker inspect active

# Check API health
curl http://localhost:8000/health
```## 체크포인트 1 - 2025-08-22 20:38
- 내용: Complete SatChat marine debris monitoring system with full UI and local testing environment
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 9c9e29f3

## 체크포인트 2 - 2025-08-22 22:51
- 내용: Complete eo-learn marine debris detection and land cover classification systems with fixed band indices and working workflows
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 501baaf4

## 체크포인트 3 - 2025-08-22 23:47
- 내용: All marine debris detection systems fully tested and operational - ready for production deployment
- 상태: 활성
- Git 브랜치: main
- Git 커밋: dae2f313

## 체크포인트 4 - 2025-08-22 23:49
- 내용: Enhanced Sentinel API with realistic ocean data fallback and improved error handling
- 상태: 활성
- Git 브랜치: main
- Git 커밋: e32137fb

## 체크포인트 5 - 2025-08-22 23:56
- 내용: Complete GitHub Pages deployment with React dashboard, monitoring system, and automated CI/CD pipeline
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 91f1d966

## 체크포인트 6 - 2025-08-23 00:31
- 내용: Integrated SatChat Multi-Analysis Dashboard with enhanced marine debris monitoring components - unified dashboard accessible at port 5555 with multi-index analysis (FDI, NDWI, MCI, turbidity), ML-based segmentation, interactive maps, field validation system, and dual API support
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 8a5398c9

## 체크포인트 7 - 2025-08-23 01:01
- 내용: Complete Render deployment configuration for SatChat production hosting - configured Python dependencies, deployment scripts, CORS settings, dynamic port binding, and production-first API detection for seamless transition between local development and cloud deployment
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 60dc8308

## 체크포인트 8 - 2025-08-24 01:01
- 내용: Render 배포 완료 설정 - 502 에러 문제 해결 대기 중
- 상태: 활성
- Git 브랜치: main
- Git 커밋: d6e07083

## 체크포인트 9 - 2025-08-24 11:58
- 내용: 프로젝트 구조 대정리 완료 - 체계적 파일 정리 및 재구성
- 상태: 완료
- Git 브랜치: main
- Git 커밋: 2c5de752

## 체크포인트 10 - 2025-08-24 12:32
- 내용: 완전 자동 배포 시스템 구축 - GitHub-Render 통합 CI/CD 파이프라인
- 상태: 완료
- Git 브랜치: main
- Git 커밋: 2826d5d
- 주요 기능:
  - 자동 배포 스크립트 (deploy.sh, auto_deploy.py)
  - GitHub Actions 워크플로우 (.github/workflows/deploy-render.yml)
  - 배포 상태 모니터링 (monitor_deployment.py)
  - Git push = Render 자동 배포 트리거
  - /ccsave 명령 시 자동 Render 배포 지원
  - Poetry 오류 수정 및 pip 기반 배포 설정

## 체크포인트 11 - 2025-08-24 12:56
- 내용: Render 배포 이슈 해결 - Python 3.11 설정 및 데모 모드 추가
- 상태: 완료
- Git 브랜치: main
- Git 커밋: 58914d8
- 주요 수정사항:
  - Python 3.11.6 런타임 명시 (runtime.txt, .python-version)
  - requirements.txt 의존성 버전 고정
  - render.yaml uvicorn 직접 실행 설정
  - Sentinel Hub 자격 증명 없이도 데모 모드 작동
  - health_check.py 배포 모니터링 도구 추가
  - 로컬 테스트 완료 (정상 작동)
  - Render 환경 변수 설정 대기 중

## 체크포인트 12 - 2025-08-24 13:25
- 내용: Poetry 자동 감지 문제 해결 및 Render 배포 최종 수정
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 5f1735f
- 주요 수정사항:
  - pyproject.toml 더미 파일 생성 (Poetry 오류 방지)
  - render.yaml pip 명시적 사용 설정
  - PORT 환경변수 기본값 설정 (10000)
  - 배포 자동화 완전 구현
  - /ccsave 명령 시 자동 Render 배포

## 체크포인트 13 - 2025-08-25 00:27
- 내용: Client-Heavy 아키텍처 완전 구현 및 일관성 정리 - TensorFlow.js PWA + Ultra-Minimal Proxy
- 상태: 활성
- Git 브랜치: main
- Git 커밋: 121c83e1

