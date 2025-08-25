# 📡 SatChat API Reference

## API 개요

SatChat은 **Ultra-Minimal Proxy API**를 제공합니다. 대부분의 처리는 클라이언트에서 수행되며, API는 메타데이터 제공과 CORS 처리 역할만 담당합니다.

## Base URL

```
Production: https://satchat-client-proxy.onrender.com
Development: http://localhost:8000
```

## 🏗️ API 설계 원칙

### Client-Heavy Architecture
- **서버 역할**: 메타데이터 제공 + CORS 처리만
- **클라이언트 역할**: 모든 분석 및 ML 처리
- **데이터 흐름**: 서버 → 메타데이터 → 클라이언트 처리

### Resource Optimization
- **메모리 사용량**: <20MB
- **응답 시간**: <50ms
- **처리 방식**: 즉시 응답 (계산 없음)

## 📚 API 엔드포인트

### 1. Root Endpoint

#### `GET /`
서비스 기본 정보를 반환합니다.

**Request:**
```bash
curl https://satchat-client-proxy.onrender.com/
```

**Response:**
```json
{
  "service": "SatChat Ultra-Minimal Proxy",
  "version": "3.0.0",
  "status": "operational",
  "processing": "client-side",
  "features": {
    "ai_analysis": true,
    "offline_capable": true,
    "memory_footprint": "ultra-low",
    "client_ai": true
  },
  "regions": ["west_sea", "south_sea", "east_sea", "busan_port", "incheon_port"]
}
```

### 2. Health Check

#### `GET /health`
서비스 상태를 확인합니다.

**Request:**
```bash
curl https://satchat-client-proxy.onrender.com/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-08-24T15:30:00.123456",
  "version": "3.0.0",
  "memory_mode": "ultra-minimal"
}
```

**Status Codes:**
- `200`: 서비스 정상 작동
- `503`: 서비스 이용 불가

### 3. Regions API

#### `GET /regions`
지원하는 모든 해역 정보를 반환합니다.

**Request:**
```bash
curl https://satchat-client-proxy.onrender.com/regions
```

**Response:**
```json
{
  "regions": {
    "west_sea": {
      "name": "서해",
      "bbox": [124.5, 35.5, 126.5, 37.5]
    },
    "south_sea": {
      "name": "남해",
      "bbox": [128.4, 34.6, 128.8, 35.0]
    },
    "east_sea": {
      "name": "동해",
      "bbox": [129.0, 35.5, 130.0, 36.5]
    },
    "busan_port": {
      "name": "부산항",
      "bbox": [129.0, 35.0, 129.2, 35.2]
    },
    "incheon_port": {
      "name": "인천항",
      "bbox": [126.5, 37.4, 126.7, 37.6]
    }
  },
  "processing_note": "Analysis performed client-side with AI Analysis Engine",
  "capabilities": ["multi-index", "ml-detection", "offline-first"]
}
```

#### `GET /region/{region_name}`
특정 해역의 메타데이터를 반환합니다.

**Parameters:**
- `region_name` (path): 해역 식별자 (`west_sea`, `south_sea`, `east_sea`, `busan_port`, `incheon_port`)

**Request:**
```bash
curl https://satchat-client-proxy.onrender.com/region/west_sea
```

**Response:**
```json
{
  "region": "west_sea",
  "region_name": "서해",
  "bbox": [124.5, 35.5, 126.5, 37.5],
  "timestamp": "2025-08-24T15:30:00.123456",
  "processing_mode": "client-side",
  "instructions": {
    "analysis": "Use client-side AI Analysis Engine processor",
    "indices": ["FDI", "NDWI", "MCI", "FAI", "Turbidity"],
    "ml_detection": "CNN-based debris classification",
    "offline_capable": true
  },
  "data_source": "Client-Generated Synthetic + AI Analysis Engine",
  "api_role": "metadata_provider_only"
}
```

**Error Response (404):**
```json
{
  "detail": "Region not found"
}
```

### 4. Authentication

#### `POST /auth/validate`
클라이언트 토큰 유효성을 검증합니다.

**Request:**
```bash
curl -X POST https://satchat-client-proxy.onrender.com/auth/validate \
  -H "Content-Type: application/json"
```

**Response:**
```json
{
  "valid": true,
  "client_processing": true
}
```

## 🛠️ 클라이언트 통합

### JavaScript 사용 예시

#### 기본 API 호출
```javascript
class SatChatAPI {
    constructor(baseUrl = 'https://satchat-client-proxy.onrender.com') {
        this.baseUrl = baseUrl;
    }
    
    async getRegions() {
        const response = await fetch(`${this.baseUrl}/regions`);
        return await response.json();
    }
    
    async getRegionMetadata(regionName) {
        const response = await fetch(`${this.baseUrl}/region/${regionName}`);
        return await response.json();
    }
    
    async checkHealth() {
        const response = await fetch(`${this.baseUrl}/health`);
        return await response.json();
    }
}

// 사용 예시
const api = new SatChatAPI();

// 모든 해역 정보 가져오기
const regions = await api.getRegions();
console.log('Available regions:', regions.regions);

// 특정 해역 메타데이터 가져오기
const westSeaInfo = await api.getRegionMetadata('west_sea');
console.log('West Sea BBox:', westSeaInfo.bbox);
```

#### 오류 처리
```javascript
class SatChatAPI {
    async safeApiCall(url) {
        try {
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`API Error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('API Call Failed:', error);
            
            // 오프라인 모드로 전환
            return this.getOfflineData();
        }
    }
    
    getOfflineData() {
        return {
            offline: true,
            regions: {
                west_sea: { name: "서해", bbox: [124.5, 35.5, 126.5, 37.5] },
                // ... 오프라인 데이터
            }
        };
    }
}
```

### React 통합 예시
```jsx
import { useState, useEffect } from 'react';

function RegionSelector() {
    const [regions, setRegions] = useState({});
    const [loading, setLoading] = useState(true);
    
    useEffect(() => {
        fetch('https://satchat-client-proxy.onrender.com/regions')
            .then(res => res.json())
            .then(data => {
                setRegions(data.regions);
                setLoading(false);
            })
            .catch(error => {
                console.error('Failed to load regions:', error);
                setLoading(false);
            });
    }, []);
    
    if (loading) return <div>Loading regions...</div>;
    
    return (
        <div>
            <h3>Select Region</h3>
            {Object.entries(regions).map(([key, region]) => (
                <button 
                    key={key}
                    onClick={() => handleRegionSelect(key)}
                >
                    {region.name}
                </button>
            ))}
        </div>
    );
}
```

## 🤖 클라이언트 측 AI 분석 엔진

SatChat의 핵심은 **클라이언트에서 실행되는 AI 분석 엔진**입니다. TensorFlow.js를 제거하고 순수 JavaScript로 구현되었습니다.

### AI 분석 함수 사용법

#### 기본 분석 실행
```javascript
// 전역 AI 분석 함수 호출
window.ultimateAnalysis('west_sea');

// 또는 안전한 방식으로 호출
if (window.ultimateAnalysis) {
    window.ultimateAnalysis('busan_port');
}
```

#### 분석 결과 구조
```javascript
// 분석 완료 후 DOM에서 결과 추출
const results = {
    fdi: document.getElementById('fdiMean')?.textContent,
    ndwi: document.getElementById('ndwiMean')?.textContent,
    mci: document.getElementById('mciMean')?.textContent,
    turbidity: document.getElementById('turbidityMean')?.textContent,
    debrisClusters: document.getElementById('debrisClusters')?.textContent,
    confidence: document.getElementById('mlConfidence')?.textContent
};
```

#### Interactive Map 레이어 제어
```javascript
// 위성 이미지 레이어로 전환
changeMapLayer('rgb');

// FDI 분석 레이어로 전환
changeMapLayer('fdi');

// NDWI 수질 분석 레이어로 전환
changeMapLayer('ndwi');

// MCI 클로로필 분석 레이어로 전환
changeMapLayer('mci');

// AI 폐기물 탐지 레이어로 전환
changeMapLayer('debris');
```

### 스택 오버플로 방지 시스템

AI 분석 엔진은 강력한 보호 메커니즘을 포함합니다:

```javascript
// 글로벌 잠금 상태 확인
if (globalProcessingLock) {
    console.warn('⚠️ 분석이 이미 실행 중입니다');
    return;
}

// 호출 깊이 제한 (최대 5단계)
if (callDepth > MAX_CALL_DEPTH) {
    console.error('🚨 호출 깊이 초과, 스택 오버플로 방지');
    return;
}

// 시간 기반 보호 (5초 간격)
const now = Date.now();
if (processingStartTime && (now - processingStartTime) < 5000) {
    console.warn('⚠️ 너무 빠른 호출, 대기 중...');
    return;
}
```

### 분석 성능 모니터링

#### 분석 시간 측정
```javascript
// 분석 시작 시간 기록
const startTime = performance.now();

// 분석 실행
window.ultimateAnalysis('south_sea');

// 완료 시간 계산 (콘솔에서 확인)
// 일반적으로 100-500ms 소요
```

#### 메모리 사용량 확인
```javascript
// 메모리 정보 (Chrome DevTools에서 사용 가능)
if (performance.memory) {
    console.log('Used:', performance.memory.usedJSHeapSize);
    console.log('Total:', performance.memory.totalJSHeapSize);
    console.log('Limit:', performance.memory.jsHeapSizeLimit);
}
```

### 디버깅 도구

#### 맵 기능 전체 테스트
```javascript
// 브라우저 콘솔에서 실행
window.testMap();

// 또는 특정 레이어만 테스트
changeMapLayer('fdi');
console.log('FDI 레이어 테스트 완료');
```

#### 분석 상태 모니터링
```javascript
// 분석 상태 실시간 확인
setInterval(() => {
    console.log('Processing Lock:', globalProcessingLock);
    console.log('Call Depth:', callDepth);
    console.log('Map Initialized:', mapInitialized);
}, 1000);
```

### 오프라인 캐싱

클라이언트에서 분석 결과를 자동으로 캐시합니다:

```javascript
// 분석 결과 캐시 저장
window.cacheAnalysisResult('west_sea', analysisData);

// 캐시된 결과 확인
const cachedResult = localStorage.getItem('satchat_analysis_west_sea');
if (cachedResult) {
    const data = JSON.parse(cachedResult);
    console.log('Cached analysis:', data);
}
```

## 📊 성능 특성

### Response Times
| Endpoint | Expected Time | Max Time |
|----------|---------------|----------|
| `/` | <20ms | 50ms |
| `/health` | <10ms | 30ms |
| `/regions` | <15ms | 40ms |
| `/region/{id}` | <15ms | 40ms |

### Resource Usage
- **Memory**: <20MB
- **CPU**: <5% (idle)
- **Network**: Minimal (메타데이터만)
- **Scaling**: Auto-scaling enabled

## 🔧 개발자 도구

### API 테스트
```bash
# 모든 엔드포인트 테스트 스크립트
#!/bin/bash

BASE_URL="https://satchat-client-proxy.onrender.com"

echo "=== SatChat API Test ==="
echo "Testing Health Check..."
curl -s "$BASE_URL/health" | jq .status

echo -e "\nTesting Regions..."
curl -s "$BASE_URL/regions" | jq '.regions | keys'

echo -e "\nTesting Specific Region..."
curl -s "$BASE_URL/region/west_sea" | jq .region_name

echo -e "\nTesting Auth..."
curl -s -X POST "$BASE_URL/auth/validate" | jq .valid
```

### 개발 환경 설정
```bash
# 로컬 개발 서버 실행
python3 minimal_proxy_api.py

# API 테스트
curl http://localhost:8000/health
```

## 🚨 오류 코드

### HTTP Status Codes
- `200`: 성공
- `404`: 리소스 없음 (잘못된 region_name)
- `500`: 서버 내부 오류
- `503`: 서비스 이용 불가

### Error Response Format
```json
{
  "detail": "Error description",
  "error_code": "REGION_NOT_FOUND",
  "timestamp": "2025-08-24T15:30:00.123456"
}
```

## 🔒 보안 고려사항

### CORS 정책
- **모든 오리진 허용**: 퍼블릭 API 특성상 제한 없음
- **허용 메서드**: `GET`, `POST`, `OPTIONS`
- **허용 헤더**: 모든 헤더

### Rate Limiting
- **기본 제한**: 없음 (메타데이터만 제공)
- **남용 방지**: Render 플랫폼 수준에서 처리

## 🚀 마이그레이션 가이드

### v2.0 → v3.0 변경사항
- ✅ **Processing 모드**: 서버 처리 → 클라이언트 처리
- ✅ **응답 구조**: 분석 결과 → 메타데이터만
- ✅ **메모리 사용**: 100MB → 20MB
- ✅ **의존성**: 10+ 패키지 → 3 패키지

---

*이 API는 클라이언트 사이드 처리를 위한 최소한의 메타데이터만 제공하며, 실제 분석은 AI Analysis Engine를 통해 브라우저에서 수행됩니다.*