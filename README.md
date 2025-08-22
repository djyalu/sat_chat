# SatChat - 해상 폐기물 모니터링 시스템

> 텔레픽스(Telefix)의 위성 데이터 기반 해상 폐기물 탐지 및 모니터링 솔루션

## 🌊 프로젝트 개요

SatChat은 위성 영상 데이터와 AI/ML 기술을 활용하여 해상 폐기물을 자동으로 탐지하고 모니터링하는 시스템입니다. 한국 해역의 특성에 최적화된 알고리즘을 통해 플라스틱, 기름, 어구 등 다양한 해양 폐기물을 실시간으로 추적합니다.

### 🎯 주요 기능

- **다중 위성 데이터 통합**: Sentinel-2, KOMPSAT, Landsat 등 다양한 위성 데이터 활용
- **AI 기반 폐기물 탐지**: 딥러닝 모델을 통한 자동 폐기물 식별 및 분류
- **실시간 모니터링**: 웹 대시보드를 통한 실시간 현황 파악
- **자동 알림 시스템**: 임계값 초과 시 자동 경보 발송
- **한국 해역 최적화**: 서해, 남해, 동해 각 해역의 특성에 맞춰 최적화

## 🛠️ 기술 스택

### Backend
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Database**: PostgreSQL + PostGIS
- **Cache**: Redis
- **Task Queue**: Celery
- **Storage**: MinIO (S3-compatible)

### AI/ML
- **Deep Learning**: PyTorch
- **Computer Vision**: OpenCV, scikit-image
- **Geospatial**: Rasterio, GeoPandas
- **Model**: YOLO, U-Net, Vision Transformer

### Infrastructure
- **Container**: Docker
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions

## 🚀 시작하기

### 사전 요구사항

- Python 3.11+
- PostgreSQL 14+ with PostGIS extension
- Redis 6+
- Docker & Docker Compose
- CUDA 11.8+ (GPU 사용 시)

### 설치 및 실행

1. **저장소 클론**
```bash
git clone https://github.com/telefix/satchat.git
cd satchat
```

2. **가상환경 설정**
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. **의존성 설치**
```bash
pip install poetry
poetry install
```

4. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 필요한 값 설정
```

5. **데이터베이스 초기화**
```bash
# PostgreSQL with PostGIS 실행
docker-compose up -d postgres redis minio

# 데이터베이스 마이그레이션
alembic upgrade head
```

6. **서버 실행**
```bash
# 개발 서버
uvicorn src.satchat.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker
celery -A src.satchat.worker worker --loglevel=info

# Celery Beat (Scheduler)
celery -A src.satchat.worker beat --loglevel=info
```

## 📁 프로젝트 구조

```
satchat/
├── src/
│   └── satchat/
│       ├── api/             # API 엔드포인트
│       ├── core/            # 핵심 설정 및 유틸리티
│       ├── data/            # 데이터 처리 모듈
│       ├── models/          # 데이터 모델
│       ├── services/        # 비즈니스 로직
│       ├── ml/              # ML 모델 및 추론
│       ├── processing/      # 이미지 처리
│       └── monitoring/      # 모니터링 및 알림
├── tests/                   # 테스트 코드
├── docs/                    # 문서
├── config/                  # 설정 파일
├── scripts/                 # 유틸리티 스크립트
├── notebooks/               # Jupyter 노트북
└── data/                    # 데이터 디렉토리
    ├── raw/                 # 원본 데이터
    ├── processed/           # 처리된 데이터
    └── models/              # 학습된 모델
```

## 🧪 개발

### 테스트 실행
```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=src/satchat

# 특정 테스트
pytest tests/unit/test_detection.py
```

### 코드 품질
```bash
# 포매팅
black src/ tests/

# Linting
ruff check src/ tests/

# Type checking
mypy src/
```

### API 문서

서버 실행 후:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔧 환경 설정

주요 환경 변수 (상세 내용은 `.env.example` 참조):

- `DATABASE_URL`: PostgreSQL 연결 URL
- `REDIS_URL`: Redis 연결 URL
- `S3_ENDPOINT`: S3/MinIO 엔드포인트
- `SENTINEL_USER/PASSWORD`: Sentinel Hub 인증
- `KOMPSAT_API_KEY`: KOMPSAT API 키
- `MODEL_DEVICE`: GPU 사용 여부 (cuda/cpu)

## 📝 라이센스

비공개 소프트웨어 - Telefix 소유

## 📧 문의

- Email: dev@telefix.co.kr
- Website: https://telefix.co.kr

---

© 2024 Telefix. All rights reserved.