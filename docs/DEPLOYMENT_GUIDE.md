# 🚀 SatChat 배포 및 운영 가이드

## 배포 개요

SatChat은 **Client-Heavy Architecture**를 기반으로 한 이중 배포 구조입니다:
- **클라이언트 앱**: GitHub Pages (CDN)
- **프록시 API**: Render (서버)

## 🏗️ 배포 아키텍처

### Production Environment
```
┌─────────────────────────────────────────┐
│        GitHub Pages (Client)           │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │     PWA     │  │   Static Assets │   │
│  │ Pure JS AI  │  │   CSS/JS/Images │   │
│  │   Engine    │  │  Satellite Tiles │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
                    │
                    ▼ (API Calls)
┌─────────────────────────────────────────┐
│         Render (Proxy API)              │
│                                         │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   FastAPI   │  │   CORS Handler  │   │
│  │   Proxy     │  │   Health Check  │   │
│  │   <20MB     │  │   Metadata      │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## 🌐 클라이언트 배포 (GitHub Pages)

### 자동 배포 설정

#### 1. GitHub Pages 설정
```yaml
# .github/workflows/deploy-pages.yml
name: Deploy to GitHub Pages

on:
  push:
    branches: [ main ]
    paths: 
      - 'client/**'
      - 'docs/**'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    permissions:
      contents: read
      pages: write
      id-token: write
      
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        
      - name: Setup Pages
        uses: actions/configure-pages@v4
        
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: '.'
          
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v3
```

#### 2. 프로젝트 설정
1. **Repository Settings** → **Pages**
2. **Source**: GitHub Actions
3. **Custom Domain** (선택사항): `satchat.yourdomain.com`
4. **Enforce HTTPS**: 체크

### 수동 배포
```bash
# 1. 프로젝트 클론
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat

# 2. GitHub Pages 활성화 확인
# Repository → Settings → Pages → Source: GitHub Actions

# 3. 배포 트리거
git add .
git commit -m "Deploy client app"
git push origin main
```

### 배포 URL
- **Production**: https://djyalu.github.io/sat_chat/
- **API Proxy**: https://satchat-client-proxy.onrender.com

## 🖥️ 서버 배포 (Render)

### Render 서비스 설정

#### 1. render.yaml 구성
```yaml
services:
  - type: web
    name: satchat-client-proxy
    env: python
    buildCommand: pip install -r requirements-minimal.txt
    startCommand: python minimal_proxy_api.py
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: ENVIRONMENT
        value: "production"
      - key: DEBUG
        value: "false"
```

#### 2. 의존성 파일
```
# requirements-minimal.txt
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
```

### 자동 배포 설정

#### GitHub Integration
1. **Render Dashboard** → **New Web Service**
2. **Connect Repository**: `https://github.com/djyalu/sat_chat`
3. **Settings**:
   - **Build Command**: `pip install -r requirements-minimal.txt`
   - **Start Command**: `python minimal_proxy_api.py`
   - **Auto-Deploy**: Yes

#### 환경 변수 설정
```bash
# Render Dashboard → Environment
PYTHON_VERSION=3.11
ENVIRONMENT=production
DEBUG=false
PORT=10000  # Render 자동 할당
```

### 수동 배포
```bash
# 1. 로컬 테스트
cd sat_chat
python3 minimal_proxy_api.py

# 2. 배포 확인
curl http://localhost:8000/health

# 3. Git 푸시로 자동 배포
git add minimal_proxy_api.py render.yaml
git commit -m "Update proxy API"
git push origin main
```

## 🔧 개발 환경 설정

### 로컬 개발 환경

#### 1. 전체 스택 로컬 실행
```bash
# 프로젝트 클론
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat

# Python 환경 설정
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements-minimal.txt

# API 서버 시작
python3 minimal_proxy_api.py &

# 클라이언트 서버 시작 (선택사항)
python3 -m http.server 8080

# 테스트
curl http://localhost:8000/health  # API
open http://localhost:8080         # Client
```

#### 2. 개발용 스크립트
```bash
#!/bin/bash
# dev-start.sh

echo "🚀 SatChat Development Environment"

# API 서버 시작
echo "Starting API proxy..."
python3 minimal_proxy_api.py &
API_PID=$!

# 클라이언트 서버 시작
echo "Starting client server..."
python3 -m http.server 8080 &
CLIENT_PID=$!

echo "✅ Development servers started"
echo "📡 API: http://localhost:8000"
echo "🌐 Client: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop all servers"

# 종료 처리
trap "kill $API_PID $CLIENT_PID; echo '\n🛑 Development servers stopped'" EXIT
wait
```

### Docker 개발 환경

#### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 최소 의존성 설치
COPY requirements-minimal.txt .
RUN pip install --no-cache-dir -r requirements-minimal.txt

# 앱 복사
COPY minimal_proxy_api.py .
COPY client/ ./client/

# 포트 노출
EXPOSE 8000

# 서버 시작
CMD ["python", "minimal_proxy_api.py"]
```

#### Docker Compose
```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  satchat-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - ENVIRONMENT=development
    volumes:
      - .:/app
    command: python minimal_proxy_api.py
    
  satchat-client:
    image: nginx:alpine
    ports:
      - "8080:80"
    volumes:
      - ./client:/usr/share/nginx/html
```

```bash
# 개발 환경 시작
docker-compose -f docker-compose.dev.yml up -d

# 로그 확인
docker-compose logs -f satchat-api
```

## 🛰️ 위성 이미지 시스템 배포

### Esri World Imagery 통합 설정

#### 클라이언트 측 설정
```javascript
// docs/index.html 내부 설정
const satelliteConfig = {
    // Esri World Imagery 서비스 URL
    tileUrl: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    
    // 성능 최적화 설정
    maxZoom: 18,
    tileSize: 256,
    attribution: "Tiles © Esri — Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community",
    
    // 한국 연안 최적화
    center: [35.2, 128.6],
    initialZoom: 8,
    bounds: [[33.0, 124.0], [39.0, 132.0]] // 한국 연안 경계
};
```

#### Interactive Map 레이어 배포 확인
```bash
#!/bin/bash
# verify-satellite-layers.sh

echo "🛰️ Verifying satellite imagery deployment..."

# 1. 기본 위성 이미지 로드 테스트
curl -I "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/8/108/95" \
  -H "User-Agent: SatChat/2.0" \
  -H "Referer: https://djyalu.github.io/sat_chat/"

# 2. Leaflet.js 로드 확인
curl -I "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"

# 3. 클라이언트 맵 초기화 테스트
echo "Testing map initialization..."
curl -s "https://djyalu.github.io/sat_chat/" | grep -q "Interactive Analysis Map" && \
  echo "✅ Interactive Map found" || echo "❌ Interactive Map not found"

echo "🗺️ Satellite imagery deployment verification complete"
```

### AI 분석 엔진 배포 검증

#### TensorFlow.js 제거 확인
```bash
#!/bin/bash
# verify-ai-engine.sh

echo "🤖 Verifying AI analysis engine deployment..."

CLIENT_URL="https://djyalu.github.io/sat_chat/"

# 1. TensorFlow.js 참조가 제거되었는지 확인
echo "Checking for TensorFlow.js references..."
if curl -s "$CLIENT_URL" | grep -q "tensorflow"; then
    echo "❌ TensorFlow.js references still found"
    exit 1
else
    echo "✅ TensorFlow.js successfully removed"
fi

# 2. Pure JS AI 엔진 존재 확인
echo "Checking for Pure JS AI engine..."
if curl -s "$CLIENT_URL" | grep -q "ultimateAnalysis"; then
    echo "✅ Pure JS AI engine found"
else
    echo "❌ Pure JS AI engine not found"
    exit 1
fi

# 3. 스택 오버플로 방지 시스템 확인
echo "Checking stack overflow protection..."
if curl -s "$CLIENT_URL" | grep -q "globalProcessingLock"; then
    echo "✅ Stack overflow protection active"
else
    echo "❌ Stack overflow protection not found"
    exit 1
fi

echo "🛡️ AI analysis engine deployment verification complete"
```

### 배포 후 테스트 스위트

#### 전체 시스템 테스트
```javascript
// test-deployment.js
// 브라우저 콘솔에서 실행

async function testSatChatDeployment() {
    console.log('🧪 Starting SatChat deployment test...');
    
    const tests = [];
    
    // 1. 맵 초기화 테스트
    tests.push({
        name: 'Map Initialization',
        test: () => !!window.map && window.mapInitialized,
        expected: true
    });
    
    // 2. AI 분석 엔진 테스트
    tests.push({
        name: 'AI Analysis Engine',
        test: () => typeof window.ultimateAnalysis === 'function',
        expected: true
    });
    
    // 3. 레이어 전환 테스트
    tests.push({
        name: 'Layer Switching',
        test: () => typeof window.changeMapLayer === 'function',
        expected: true
    });
    
    // 4. 스택 오버플로 방지 테스트
    tests.push({
        name: 'Stack Overflow Protection',
        test: () => typeof window.globalProcessingLock !== 'undefined',
        expected: true
    });
    
    // 5. 위성 이미지 레이어 테스트
    tests.push({
        name: 'Satellite Imagery',
        test: () => {
            changeMapLayer('rgb');
            return window.currentTileLayer && 
                   window.currentTileLayer._url.includes('World_Imagery');
        },
        expected: true
    });
    
    // 테스트 실행
    let passed = 0;
    let failed = 0;
    
    for (const test of tests) {
        try {
            const result = test.test();
            if (result === test.expected) {
                console.log(`✅ ${test.name}: PASSED`);
                passed++;
            } else {
                console.log(`❌ ${test.name}: FAILED (got ${result}, expected ${test.expected})`);
                failed++;
            }
        } catch (error) {
            console.log(`❌ ${test.name}: ERROR - ${error.message}`);
            failed++;
        }
    }
    
    console.log(`\n📊 Test Results: ${passed} passed, ${failed} failed`);
    return { passed, failed, total: tests.length };
}

// 테스트 실행
testSatChatDeployment();
```

### 성능 모니터링

#### 위성 타일 로딩 성능
```javascript
// performance-monitor.js
class SatelliteTilePerformanceMonitor {
    constructor() {
        this.metrics = {
            tileLoadTimes: [],
            failedTiles: 0,
            totalTiles: 0
        };
    }
    
    startMonitoring() {
        // Leaflet 이벤트 리스너 추가
        if (window.map) {
            window.map.on('tileloadstart', (e) => {
                e.tile._startTime = performance.now();
                this.metrics.totalTiles++;
            });
            
            window.map.on('tileload', (e) => {
                const loadTime = performance.now() - e.tile._startTime;
                this.metrics.tileLoadTimes.push(loadTime);
                
                if (loadTime > 2000) {
                    console.warn(`Slow tile load: ${loadTime}ms`);
                }
            });
            
            window.map.on('tileerror', (e) => {
                this.metrics.failedTiles++;
                console.error('Tile load failed:', e);
            });
        }
    }
    
    getMetrics() {
        const avgLoadTime = this.metrics.tileLoadTimes.reduce((a, b) => a + b, 0) / 
                           this.metrics.tileLoadTimes.length;
        
        return {
            averageLoadTime: avgLoadTime,
            totalTiles: this.metrics.totalTiles,
            failedTiles: this.metrics.failedTiles,
            successRate: ((this.metrics.totalTiles - this.metrics.failedTiles) / 
                         this.metrics.totalTiles * 100).toFixed(2) + '%'
        };
    }
}

// 모니터링 시작
const tileMonitor = new SatelliteTilePerformanceMonitor();
tileMonitor.startMonitoring();

// 5분 후 성능 보고서
setTimeout(() => {
    console.log('🛰️ Satellite Tile Performance Report:', tileMonitor.getMetrics());
}, 300000);
```

## 📊 모니터링 및 운영

### 헬스체크

#### 기본 모니터링
```bash
#!/bin/bash
# health-check.sh

API_URL="https://satchat-client-proxy.onrender.com"
CLIENT_URL="https://djyalu.github.io/sat_chat"

echo "🔍 SatChat Health Check $(date)"

# API 헬스체크
echo "Checking API..."
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")

if [ "$API_STATUS" = "200" ]; then
    echo "✅ API: Healthy"
else
    echo "❌ API: Unhealthy (HTTP $API_STATUS)"
fi

# 클라이언트 헬스체크
echo "Checking Client..."
CLIENT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$CLIENT_URL")

if [ "$CLIENT_STATUS" = "200" ]; then
    echo "✅ Client: Healthy"
else
    echo "❌ Client: Unhealthy (HTTP $CLIENT_STATUS)"
fi
```

#### 고급 모니터링 스크립트
```python
#!/usr/bin/env python3
"""
SatChat Advanced Monitoring Script
"""

import requests
import json
import time
from datetime import datetime

def check_api_performance():
    """API 성능 테스트"""
    api_url = "https://satchat-client-proxy.onrender.com"
    
    tests = [
        {"endpoint": "/health", "expected_time": 50},
        {"endpoint": "/regions", "expected_time": 100},
        {"endpoint": "/region/west_sea", "expected_time": 100}
    ]
    
    results = []
    
    for test in tests:
        start_time = time.time()
        try:
            response = requests.get(f"{api_url}{test['endpoint']}", timeout=5)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000  # ms
            
            results.append({
                "endpoint": test["endpoint"],
                "status": response.status_code,
                "response_time": response_time,
                "expected_time": test["expected_time"],
                "performance": "✅" if response_time < test["expected_time"] else "⚠️"
            })
            
        except Exception as e:
            results.append({
                "endpoint": test["endpoint"],
                "status": "ERROR",
                "error": str(e),
                "performance": "❌"
            })
    
    return results

def generate_report():
    """모니터링 리포트 생성"""
    print(f"🔍 SatChat Monitoring Report - {datetime.now()}")
    print("=" * 50)
    
    results = check_api_performance()
    
    for result in results:
        print(f"{result['performance']} {result['endpoint']}")
        if 'response_time' in result:
            print(f"   Response: {result['response_time']:.0f}ms (target: <{result['expected_time']}ms)")
        if 'error' in result:
            print(f"   Error: {result['error']}")
        print()

if __name__ == "__main__":
    generate_report()
```

### 로그 관리

#### Render 로그 확인
```bash
# Render CLI 설치
npm install -g @render/cli

# 로그인
render login

# 서비스 로그 확인
render logs satchat-client-proxy

# 실시간 로그
render logs satchat-client-proxy --tail
```

#### 로그 레벨 설정
```python
# minimal_proxy_api.py의 로깅 설정
import logging

# Production: WARNING 이상만
# Development: INFO 이상
LOG_LEVEL = "WARNING" if os.getenv("ENVIRONMENT") == "production" else "INFO"
logging.basicConfig(level=LOG_LEVEL)
```

### 성능 최적화

#### Render 최적화 설정
```yaml
# render.yaml 최적화
services:
  - type: web
    name: satchat-client-proxy
    env: python
    plan: starter  # Free tier
    buildCommand: pip install --no-cache-dir -r requirements-minimal.txt
    startCommand: python minimal_proxy_api.py
    healthCheckPath: /health
    envVars:
      - key: PYTHON_VERSION
        value: "3.11"
      - key: ENVIRONMENT
        value: "production"
      - key: WEB_CONCURRENCY
        value: "1"  # Single worker for minimal memory
```

#### 클라이언트 최적화
```html
<!-- index.html 최적화 -->
<head>
    <!-- Preload critical resources -->
    <link rel="preload" href="/css/main.css" as="style">
    <link rel="preload" href="/js/main.js" as="script">
    
    <!-- Service Worker 등록 -->
    <script>
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
    </script>
</head>
```

## 🔒 보안 및 백업

### 보안 체크리스트

#### API 보안
- [ ] HTTPS 강제 적용
- [ ] CORS 적절히 설정
- [ ] Rate limiting 구현 (필요시)
- [ ] 입력 데이터 검증
- [ ] 오류 정보 최소화

#### 클라이언트 보안
- [ ] Content Security Policy 설정
- [ ] HTTPS 강제 적용
- [ ] XSS 방지 코드 적용
- [ ] 민감 데이터 로컬 저장 방지

### 백업 전략

#### 코드 백업
```bash
# 자동 백업 스크립트
#!/bin/bash

BACKUP_DIR="/backup/satchat"
DATE=$(date +%Y%m%d_%H%M%S)

# Git 저장소 백업
git clone https://github.com/djyalu/sat_chat.git "$BACKUP_DIR/git_$DATE"

# 설정 파일 백업
cp render.yaml "$BACKUP_DIR/render_$DATE.yaml"
cp requirements-minimal.txt "$BACKUP_DIR/requirements_$DATE.txt"

echo "Backup completed: $BACKUP_DIR"
```

## 🚨 장애 복구

### 일반적인 문제 해결

#### API 서버 다운
1. **확인**: `curl https://satchat-client-proxy.onrender.com/health`
2. **Render 로그 확인**: `render logs satchat-client-proxy`
3. **재배포**: Git 푸시로 자동 재배포
4. **수동 재시작**: Render 대시보드에서 재시작

#### 클라이언트 접근 불가
1. **GitHub Pages 상태 확인**: GitHub Status 페이지
2. **DNS 확인**: `nslookup djyalu.github.io`
3. **캐시 초기화**: 브라우저 캐시 및 CDN 캐시 초기화
4. **재배포**: `git push origin main`

#### 완전 장애 시 복구 절차
```bash
# 1. 긴급 복구 스크립트
#!/bin/bash

echo "🚨 Emergency Recovery Mode"

# API 헬스체크
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "https://satchat-client-proxy.onrender.com/health")

if [ "$API_STATUS" != "200" ]; then
    echo "⚠️ API Down - Starting recovery"
    # 재배포 트리거
    git add .
    git commit -m "Emergency redeployment"
    git push origin main
fi

# 클라이언트 체크 및 복구 로직...
```

## 📈 확장 계획

### 트래픽 증가 대응
1. **CDN 최적화**: GitHub Pages는 자동 글로벌 CDN
2. **API 확장**: Render에서 상위 플랜으로 업그레이드
3. **캐싱 전략**: 클라이언트 사이드 캐싱 강화
4. **Load Balancing**: 필요시 다중 API 인스턴스

### 비용 최적화
- **현재**: GitHub Pages (무료) + Render Free Tier
- **예상 비용**: 월 $7 (Render Starter Plan)
- **확장**: 필요에 따라 점진적 업그레이드

---

*이 가이드는 SatChat의 안정적인 운영을 위한 포괄적인 배포 및 운영 정보를 제공합니다.*