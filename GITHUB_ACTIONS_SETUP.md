# 🤖 GitHub Actions를 통한 Sentinel Hub 자동 데이터 수집

## 📋 Overview

GitHub Actions를 사용하여 매 6시간마다 자동으로 Sentinel Hub에서 해양 폐기물 데이터를 수집하고 시스템에 표시합니다.

## 🚀 주요 기능

### 자동 데이터 수집
- **주기**: 매 6시간 (00:00, 06:00, 12:00, 18:00 UTC)
- **지역**: 서해, 남해, 동해 전체 모니터링
- **우선 지역**: 충남 연안, 경기만, 부산 연안 등 집중 감시

### 데이터 처리
- 분광 지수 분석 (FDI, NDWI, NDVI)
- 머신러닝 기반 필터링
- 핫스팟 지역 자동 식별
- 트렌드 분석 및 예측

### 알림 시스템
- Critical/High 우선순위 알림 자동 발송
- Discord/Slack 웹훅 지원
- 실시간 대시보드 업데이트

## 🔧 설정 방법

### 1. GitHub Secrets 설정

GitHub 저장소의 Settings → Secrets and variables → Actions에서 다음 시크릿 추가:

```yaml
# 필수 시크릿
SENTINEL_CLIENT_ID: "your-sentinel-hub-client-id"
SENTINEL_CLIENT_SECRET: "your-sentinel-hub-client-secret"

# 선택적 알림 설정
DISCORD_WEBHOOK: "https://discord.com/api/webhooks/..."
SLACK_WEBHOOK: "https://hooks.slack.com/services/..."
```

### 2. Sentinel Hub 계정 설정

1. [Sentinel Hub Dashboard](https://apps.sentinel-hub.com/dashboard/) 접속
2. OAuth 클라이언트 생성
3. Client ID와 Secret 복사
4. GitHub Secrets에 추가

### 3. 워크플로우 활성화

```bash
# GitHub Actions 워크플로우 확인
cat .github/workflows/sentinel-hub-data-fetch.yml

# 수동 실행 테스트
gh workflow run sentinel-hub-data-fetch.yml
```

## 📊 데이터 구조

### 수집되는 데이터

```json
{
  "timestamp": "2024-11-22T12:00:00Z",
  "detections": [
    {
      "id": "west_sea_20241122_0001",
      "latitude": 36.5,
      "longitude": 126.2,
      "debris_type": "플라스틱 (Plastic)",
      "confidence": 0.92,
      "patch_size": 450.5,
      "priority": "high",
      "spectral_indices": {
        "fdi": 0.035,
        "ndvi": 0.08,
        "ndwi": 0.42
      }
    }
  ],
  "statistics": {
    "total_detections": 142,
    "by_region": {...},
    "by_type": {...},
    "average_confidence": 0.82
  },
  "alerts": [...]
}
```

### 저장 위치

```
data/
├── detections/        # 탐지 데이터
│   └── detections_YYYYMMDD_HHMMSS.json
├── statistics/        # 통계 데이터
│   └── stats_YYYYMMDD_HHMMSS.json
├── alerts/           # 알림 데이터
│   └── alerts_YYYYMMDD_HHMMSS.json
├── dashboard/        # 대시보드용 처리된 데이터
│   ├── dashboard.json
│   ├── realtime.json
│   ├── map_data.json
│   └── hotspots.json
└── latest.json       # 최신 종합 데이터
```

## 🌐 API 엔드포인트

### GitHub Actions 데이터 조회

```python
# 전체 대시보드 데이터
GET /api/v1/github-data

# 실시간 통계
GET /api/v1/github-data/realtime

# 지도 데이터
GET /api/v1/github-data/map

# 핫스팟 지역
GET /api/v1/github-data/hotspots
```

### 프론트엔드 통합

```javascript
// React 컴포넌트에서 사용
useEffect(() => {
    // GitHub Actions 데이터 확인
    fetch('http://localhost:8000/api/v1/github-data')
        .then(res => res.json())
        .then(data => {
            if (data.last_update) {
                // GitHub Actions 데이터 사용
                setDetections(data.map_data);
                setAlerts(data.alerts);
                setStatistics(data.realtime);
            } else {
                // 폴백: 기본 API 사용
                fetch('http://localhost:8000/api/v1/detections')
                    .then(res => res.json())
                    .then(setDetections);
            }
        });
}, []);
```

## 📈 모니터링

### GitHub Actions 실행 상태

- **Actions 탭**: 워크플로우 실행 이력 확인
- **실행 로그**: 각 단계별 상세 로그
- **아티팩트**: 수집된 데이터 다운로드 가능 (30일 보관)

### 실행 통계

```yaml
# 최근 실행 상태 확인
gh run list --workflow=sentinel-hub-data-fetch.yml

# 특정 실행 로그 보기
gh run view <run-id>

# 아티팩트 다운로드
gh run download <run-id>
```

## 🔍 트러블슈팅

### 워크플로우 실패 시

1. **Secrets 확인**: SENTINEL_CLIENT_ID, SENTINEL_CLIENT_SECRET 설정 확인
2. **권한 확인**: GitHub Actions가 저장소에 쓰기 권한 있는지 확인
3. **API 한도**: Sentinel Hub API 사용량 확인

### 데이터가 표시되지 않을 때

1. **파일 경로 확인**: `data/dashboard/` 디렉토리 존재 여부
2. **API 상태 확인**: `GET /` 엔드포인트에서 `github_actions_data` 확인
3. **최근 실행 시간**: `last_github_update` 필드 확인

## 📅 스케줄 커스터마이징

`.github/workflows/sentinel-hub-data-fetch.yml` 파일에서 cron 표현식 수정:

```yaml
on:
  schedule:
    # 매 3시간마다
    - cron: '0 */3 * * *'
    
    # 매일 오전 9시 (KST)
    - cron: '0 0 * * *'  # UTC 00:00 = KST 09:00
    
    # 평일만 (월-금)
    - cron: '0 */6 * * 1-5'
```

## 🚨 알림 설정

### Discord 웹훅

1. Discord 서버 설정 → 연동 → 웹후크
2. 새 웹훅 생성
3. URL 복사 → GitHub Secret 추가

### Slack 웹훅

1. Slack App 생성
2. Incoming Webhooks 활성화
3. Webhook URL 생성
4. GitHub Secret 추가

## 📊 대시보드 통합

실시간 대시보드는 GitHub Actions 데이터를 자동으로 표시:

1. **자동 갱신**: 6시간마다 새 데이터 로드
2. **폴백 지원**: GitHub 데이터 없을 시 로컬 데이터 사용
3. **캐싱**: 성능 최적화를 위한 데이터 캐싱

## 🔗 관련 파일

- `.github/workflows/sentinel-hub-data-fetch.yml` - 워크플로우 정의
- `scripts/fetch_sentinel_data.py` - 데이터 수집 스크립트
- `scripts/process_detections.py` - 데이터 처리 스크립트
- `scripts/update_dashboard.py` - 대시보드 업데이트
- `test_app.py` - API 서버 (GitHub 데이터 제공)

## 💡 활용 예시

### 1. 긴급 대응 시스템
- Critical 알림 시 자동으로 관계 기관 통보
- 정화 작업 우선순위 결정

### 2. 트렌드 분석
- 계절별 폐기물 증감 패턴 파악
- 예측 모델 학습 데이터 축적

### 3. 성과 측정
- 정화 작업 전후 비교
- 정책 효과성 평가

---

*GitHub Actions를 통해 24/7 자동 모니터링이 가능합니다!* 🌊🛰️