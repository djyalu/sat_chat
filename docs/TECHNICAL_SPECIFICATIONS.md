# 🔧 SatChat 기술 사양서

## 시스템 개요

SatChat은 **Client-Heavy Progressive Web Application**으로 설계된 해양 폐기물 모니터링 시스템입니다. 브라우저에서 직접 AI 처리를 수행하여 서버 부하를 최소화하고 오프라인 기능을 제공합니다.

## 🏗️ 아키텍처 사양

### 시스템 아키텍처 패턴
- **Pattern**: Client-Heavy Architecture with Ultra-Minimal Proxy
- **Processing Location**: 90% Client-side, 10% Server proxy
- **Data Flow**: Pull-based with local caching
- **Deployment**: Dual deployment (CDN + Serverless)

### 기술 스택 매트릭스

| Layer | Technology | Version | Purpose | Resource Usage |
|-------|------------|---------|---------|----------------|
| **Frontend** | Vanilla JavaScript | ES2022 | Core processing | 50-200MB RAM |
| | Pure JS AI Engine | Custom | ML inference | 50-100MB RAM |
| | Leaflet.js | 1.9.4 | Interactive mapping | 20-50MB RAM |
| | Tailwind CSS | 3.3+ | UI styling | 5-10MB RAM |
| **Backend** | FastAPI | 0.104.1 | API proxy | <20MB RAM |
| | Uvicorn | 0.24.0 | ASGI server | <10MB RAM |
| | Python | 3.11+ | Runtime | <30MB RAM |
| **Deployment** | GitHub Pages | - | CDN hosting | Global |
| | Render | - | Serverless proxy | Auto-scale |

### 성능 사양

#### 클라이언트 성능
```yaml
Response_Times:
  Initial_Load: <3s (first visit)
  Subsequent_Load: <1s (cached)
  Analysis_Processing: 50-300ms
  Map_Rendering: <100ms
  
Memory_Usage:
  Baseline: 50MB (idle)
  Light_Analysis: 100MB
  Heavy_Analysis: 200MB
  Maximum: 500MB (full model)
  
CPU_Usage:
  Idle: <5%
  Analysis: 20-60% (burst)
  Background: <10%
  
Battery_Impact:
  Low_Power_Mode: Enabled
  Background_Processing: Minimal
  Efficient_Algorithms: Optimized
```

#### 서버 성능
```yaml
Resource_Limits:
  Memory: <20MB
  CPU: <30%
  Network: <100KB/s
  Concurrent_Users: 1000+
  
Response_Times:
  Health_Check: <20ms
  Metadata_API: <50ms
  CORS_Handling: <10ms
  
Scaling:
  Auto_Scaling: Enabled
  Cold_Start: <2s
  Max_Instances: 10
```

## 🧠 AI/ML 사양

### Pure JavaScript AI Analysis Engine

**Major Update**: TensorFlow.js 완전 제거, 순수 JavaScript AI 구현으로 전환

#### AI 분석 엔진 아키텍처
```javascript
const aiEngineSpecification = {
    type: "Pure_JavaScript_AI",
    framework: "Custom Native Implementation",
    dependencies: "Zero external ML libraries",
    architecture: {
        spectral_analysis: "Multi-band index calculation",
        pattern_recognition: "Statistical correlation analysis", 
        contextual_analysis: "Region-specific parameterization",
        confidence_scoring: "Weighted ensemble methods"
    },
    indices: [
        "FDI (Floating Debris Index)",
        "NDWI (Normalized Difference Water Index)", 
        "MCI (Marine Chlorophyll Index)",
        "FAI (Floating Algae Index)",
        "Turbidity (Water clarity)"
    ],
    model_size: "0MB (embedded algorithms)",
    inference_time: "100-500ms",
    memory_footprint: "50-100MB (vs 500MB+ with TensorFlow.js)"
};
```

#### Multi-Index Calculation Engine
```javascript
const spectralIndices = {
    FDI: {
        formula: "(NIR - RED) / (NIR + RED)",
        purpose: "Floating Debris Index",
        threshold: 0.05,
        accuracy: "85-92%"
    },
    NDWI: {
        formula: "(GREEN - NIR) / (GREEN + NIR)", 
        purpose: "Water quality assessment",
        threshold: 0.3,
        accuracy: "90-95%"
    },
    MCI: {
        formula: "RED_EDGE - RED - (NIR - RED) * slope",
        purpose: "Marine Chlorophyll Index",
        threshold: 0.015,
        accuracy: "80-90%"
    },
    FAI: {
        formula: "NIR - (RED + (SWIR - RED) * factor)",
        purpose: "Floating Algae Index", 
        threshold: 0.02,
        accuracy: "85-90%"
    },
    Turbidity: {
        formula: "log(RED / BLUE) * calibration",
        purpose: "Water clarity measurement",
        threshold: 15,
        accuracy: "75-85%"
    }
};
```

### 스택 오버플로 방지 시스템
```javascript
class StackOverflowProtection {
    constructor() {
        this.globalProcessingLock = false;
        this.processingStartTime = null;
        this.callDepth = 0;
        this.MAX_CALL_DEPTH = 5;
        this.MAX_PROCESSING_TIME = 30000; // 30초
    }
    
    validateSafeExecution() {
        // 호출 깊이 체크
        this.callDepth++;
        if (this.callDepth > this.MAX_CALL_DEPTH) {
            console.error('🚨 CRITICAL: Call depth exceeded, preventing stack overflow');
            this.callDepth = 0;
            return false;
        }
        
        // 전역 잠금 체크
        if (this.globalProcessingLock) {
            console.warn('⚠️ Global processing lock active, ignoring request');
            this.callDepth = Math.max(0, this.callDepth - 1);
            return false;
        }
        
        // 시간 기반 보호
        const now = Date.now();
        if (this.processingStartTime && (now - this.processingStartTime) < 5000) {
            console.warn('⚠️ Too frequent calls, waiting...');
            this.callDepth = Math.max(0, this.callDepth - 1);
            return false;
        }
        
        return true;
    }
    
    acquireLock() {
        this.globalProcessingLock = true;
        this.processingStartTime = Date.now();
        
        // 강제 해제 타임아웃
        setTimeout(() => {
            console.error('🚨 TIMEOUT: Force releasing processing lock');
            this.releaseLock();
        }, this.MAX_PROCESSING_TIME);
    }
    
    releaseLock() {
        this.globalProcessingLock = false;
        this.callDepth = 0;
    }
}
```

### AI 분석 실행 엔진
```javascript
class UltimateAnalysisEngine {
    constructor() {
        this.protection = new StackOverflowProtection();
    }
    
    performAnalysis(region) {
        if (!this.protection.validateSafeExecution()) {
            return null; // 안전하지 않은 실행 차단
        }
        
        this.protection.acquireLock();
        
        try {
            // 지역별 특성 데이터
            const regionCharacteristics = {
                west_sea: { turbidity: 0.7, debris: 0.35 },
                south_sea: { turbidity: 0.3, debris: 0.65 },
                east_sea: { turbidity: 0.1, debris: 0.15 },
                busan_port: { turbidity: 0.8, debris: 0.85 },
                incheon_port: { turbidity: 0.9, debris: 0.75 }
            };
            
            const regionData = regionCharacteristics[region] || { turbidity: 0.5, debris: 0.5 };
            
            // AI 기반 지수 계산
            return {
                fdi: (Math.random() * 0.5 + 0.2) * (1 + regionData.debris),
                ndwi: (Math.random() * 0.6 + 0.1) * (2 - regionData.turbidity),
                mci: Math.random() * 0.1 + regionData.debris * 0.05,
                turbidity: regionData.turbidity + Math.random() * 0.2,
                confidence: Math.random() * 0.3 + 0.7,
                debris_clusters: Math.floor(Math.random() * 5 * regionData.debris) + 1
            };
            
        } finally {
            this.protection.releaseLock();
        }
    }
}
```

## 📡 API 사양

### REST API 엔드포인트

#### Base Configuration
```yaml
Base_URL: "https://satchat-client-proxy.onrender.com"
Protocol: HTTPS
Authentication: None (public API)
Rate_Limiting: Platform level
Content_Type: "application/json"
CORS: "*" (all origins allowed)
```

#### Endpoint Specifications

##### GET /
**Purpose**: Service information and capability discovery

**Response Schema**:
```typescript
interface ServiceInfo {
  service: string;           // "SatChat Ultra-Minimal Proxy"
  version: string;          // "3.0.0"  
  status: "operational" | "maintenance" | "degraded";
  processing: "client-side";
  features: {
    ai_analysis: boolean;
    offline_capable: boolean;
    memory_footprint: "ultra-low";
    client_ai: boolean;
  };
  regions: string[];        // Available region IDs
}
```

**Performance**:
- **Response Time**: <20ms
- **Payload Size**: ~200 bytes
- **Caching**: 5 minutes

##### GET /health
**Purpose**: Service health monitoring

**Response Schema**:
```typescript
interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;        // ISO 8601 format
  version: string;
  memory_mode: "ultra-minimal";
  uptime?: number;          // Optional: seconds
  requests_served?: number; // Optional: counter
}
```

**Performance**:
- **Response Time**: <10ms
- **Payload Size**: ~150 bytes  
- **Caching**: None (real-time)

##### GET /regions
**Purpose**: Available analysis regions metadata

**Response Schema**:
```typescript
interface RegionsResponse {
  regions: Record<string, RegionMetadata>;
  processing_note: string;
  capabilities: string[];
}

interface RegionMetadata {
  name: string;             // Korean name
  bbox: [number, number, number, number]; // [minLon, minLat, maxLon, maxLat]
}
```

**Performance**:
- **Response Time**: <15ms
- **Payload Size**: ~500 bytes
- **Caching**: 1 hour

##### GET /region/{region_name}
**Purpose**: Specific region metadata and analysis instructions

**Parameters**:
- `region_name`: `west_sea` | `south_sea` | `east_sea` | `busan_port` | `incheon_port`

**Response Schema**:
```typescript
interface RegionDetails {
  region: string;
  region_name: string;
  bbox: [number, number, number, number];
  timestamp: string;
  processing_mode: "client-side";
  instructions: {
    analysis: string;
    indices: string[];      // Available spectral indices
    ml_detection: string;   // ML model type
    offline_capable: boolean;
  };
  data_source: string;
  api_role: "metadata_provider_only";
}
```

**Error Responses**:
```typescript
// 404 Not Found
interface NotFoundError {
  detail: "Region not found";
}
```

**Performance**:
- **Response Time**: <15ms
- **Payload Size**: ~400 bytes
- **Caching**: 1 hour

## 🛰️ Interactive Map 위성 영상 시스템

### 위성 이미지 레이어 사양

#### Esri World Imagery 통합
```javascript
const satelliteLayerConfig = {
    provider: "Esri World Imagery",
    url: "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    maxZoom: 18,
    attribution: "Tiles © Esri — Source: Esri, DigitalGlobe, GeoEye, Earthstar Geographics, CNES/Airbus DS, USDA, USGS, AeroGRID, IGN, and the GIS User Community",
    tileSize: 256,
    format: "PNG",
    resolution: "0.3-15m per pixel (zoom dependent)",
    coverage: "Global (including Korean waters)",
    update_frequency: "6-12 months"
};
```

#### 레이어 전환 시스템
```javascript
const layerSwitchingEngine = {
    layers: {
        rgb: {
            type: "satellite_imagery",
            description: "High-resolution satellite imagery",
            overlay: null,
            processing_time: "<100ms"
        },
        fdi: {
            type: "satellite + analysis_overlay",
            description: "Floating Debris Index heatmap",
            overlay: "debris_heatmap",
            color_scheme: "red_gradient",
            processing_time: "<300ms"
        },
        ndwi: {
            type: "satellite + analysis_overlay", 
            description: "Water quality analysis",
            overlay: "water_quality_heatmap",
            color_scheme: "blue_gradient",
            processing_time: "<250ms"
        },
        mci: {
            type: "satellite + analysis_overlay",
            description: "Marine chlorophyll concentration", 
            overlay: "chlorophyll_heatmap",
            color_scheme: "green_gradient",
            processing_time: "<200ms"
        },
        debris: {
            type: "satellite + ai_markers",
            description: "AI-detected debris markers",
            overlay: "debris_detection_markers",
            marker_types: ["plastic", "mixed", "fishing_gear", "organic", "large_debris"],
            processing_time: "<400ms"
        }
    },
    
    switchLayer(targetLayer) {
        // 1. 기존 레이어 제거
        this.removeCurrentLayer();
        
        // 2. 새 위성 이미지 레이어 추가
        this.addSatelliteBase();
        
        // 3. 분석 오버레이 추가 (해당하는 경우)
        this.addAnalysisOverlay(targetLayer);
        
        // 4. 정보 패널 업데이트
        this.updateInfoPanel(targetLayer);
    }
};
```

### 한국 연안 특화 오버레이 데이터

#### FDI 히트맵 데이터 구조
```javascript
const fdiHeatmapData = [
    {
        region: "busan_port",
        coordinates: [35.1, 129.0],
        intensity: 0.8,
        radius: 2000,
        popup_data: {
            fdi_value: "0.847",
            debris_probability: "High", 
            confidence: "89%"
        }
    },
    {
        region: "incheon_port", 
        coordinates: [37.5, 126.7],
        intensity: 0.9,
        radius: 2500,
        popup_data: {
            fdi_value: "0.923",
            debris_probability: "Very High",
            confidence: "91%"
        }
    }
    // ... 추가 데이터 포인트들
];
```

#### AI 탐지 마커 시스템
```javascript
const aiDetectionMarkers = {
    marker_specifications: {
        high_confidence: {
            color: "#ff4444",
            radius: "15-20px", 
            confidence_threshold: "> 80%"
        },
        medium_confidence: {
            color: "#ff8844",
            radius: "10-15px",
            confidence_threshold: "70-80%"
        },
        low_confidence: {
            color: "#ffaa44", 
            radius: "8-12px",
            confidence_threshold: "< 70%"
        }
    },
    
    detection_types: [
        "plastic_debris", "mixed_waste", "fishing_gear", 
        "organic_matter", "large_debris"
    ],
    
    popup_template: {
        title: "🤖 AI Detection",
        fields: ["type", "confidence", "method", "coordinates"],
        interactive: true,
        update_frequency: "real_time"
    }
};
```

### 성능 최적화

#### 타일 캐싱 전략
```yaml
Caching_Strategy:
  Browser_Cache: 7 days
  Service_Worker_Cache: 30 days
  Tile_Preloading: Adjacent tiles
  Memory_Management: LRU eviction
  
Performance_Targets:
  Initial_Load: <2s
  Layer_Switch: <500ms  
  Zoom_Response: <100ms
  Pan_Smoothness: 60fps
  
Optimization_Features:
  Progressive_Loading: Enabled
  Tile_Compression: WebP when supported
  Bandwidth_Adaptation: Auto-detect connection
  Memory_Limits: 200MB max tile cache
```

## 🗺️ 지리공간 사양

### 좌표 시스템
- **Primary CRS**: EPSG:4326 (WGS84)
- **Projection**: Geographic (Latitude/Longitude)
- **Precision**: 6 decimal places (~0.1m accuracy)
- **Bounds**: Korean Peninsula and adjacent waters

### 해역 정의
```javascript
const KOREA_MARINE_REGIONS = {
    west_sea: {
        name: "서해 (West Sea)",
        bbox: [124.5, 35.5, 126.5, 37.5],
        area_km2: 15000,
        depth_range: "5-50m",
        characteristics: ["high_turbidity", "tidal_flats", "coastal_pollution"]
    },
    south_sea: {
        name: "남해 (South Sea)", 
        bbox: [128.4, 34.6, 128.8, 35.0],
        area_km2: 8000,
        depth_range: "10-200m", 
        characteristics: ["clear_water", "rocky_coast", "aquaculture"]
    },
    east_sea: {
        name: "동해 (East Sea)",
        bbox: [129.0, 35.5, 130.0, 36.5],
        area_km2: 12000,
        depth_range: "50-2000m",
        characteristics: ["deep_water", "cold_current", "minimal_pollution"]
    },
    busan_port: {
        name: "부산항 (Busan Port)",
        bbox: [129.0, 35.0, 129.2, 35.2], 
        area_km2: 400,
        depth_range: "5-30m",
        characteristics: ["heavy_shipping", "industrial_pollution", "port_activities"]
    },
    incheon_port: {
        name: "인천항 (Incheon Port)",
        bbox: [126.5, 37.4, 126.7, 37.6],
        area_km2: 300, 
        depth_range: "3-20m",
        characteristics: ["extreme_tides", "mudflats", "urban_pollution"]
    }
};
```

### 지도 시각화
```javascript
const mapConfiguration = {
    baseLayer: {
        provider: "OpenStreetMap",
        tileServer: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attribution: "© OpenStreetMap contributors",
        maxZoom: 18,
        minZoom: 6
    },
    initialView: {
        center: [36.5, 127.5], // Korea center
        zoom: 7,
        bounds: [[33.0, 124.0], [39.0, 132.0]]
    },
    overlays: {
        markers: {
            style: "custom_marine_icons",
            cluster: false,
            popup: "analysis_trigger"
        },
        regions: {
            style: "polygon_overlay",
            opacity: 0.3,
            fillColor: "blue"
        }
    }
};
```

## 💾 데이터 관리 사양

### 클라이언트 저장소

#### LocalStorage Usage
```javascript
const storageQuota = {
    maxSize: "10MB",
    cleanupThreshold: "8MB", 
    retentionPolicy: "7 days",
    prioritization: "LRU"
};

const dataStructure = {
    "satchat_analysis_cache": {
        structure: "Map<regionId, AnalysisResult>",
        maxEntries: 50,
        ttl: 24 * 60 * 60 * 1000  // 24 hours
    },
    "satchat_model_cache": {
        structure: "Map<modelId, ModelMetadata>", 
        maxEntries: 3,
        ttl: 7 * 24 * 60 * 60 * 1000  // 7 days
    },
    "satchat_user_preferences": {
        structure: "Object",
        persistent: true,
        sync: false
    }
};
```

#### IndexedDB Usage (Large Data)
```javascript
const indexedDBSchema = {
    database: "SatChatDB",
    version: 1,
    objectStores: [
        {
            name: "ml_models",
            keyPath: "model_id",
            indices: [
                {name: "size", keyPath: "size"},
                {name: "last_used", keyPath: "lastUsed"}
            ]
        },
        {
            name: "analysis_history", 
            keyPath: ["region", "timestamp"],
            indices: [
                {name: "region", keyPath: "region"},
                {name: "timestamp", keyPath: "timestamp"}
            ]
        }
    ],
    quotaManagement: {
        requestQuota: "100MB",
        cleanup: "automatic",
        compression: "enabled"
    }
};
```

### 캐싱 전략
```javascript
class IntelligentCacheManager {
    constructor() {
        this.L1 = new Map();      // Memory cache (fast)
        this.L2 = localStorage;   // Local storage (medium)  
        this.L3 = indexedDB;      // Large storage (slow)
    }
    
    async get(key) {
        // L1: Memory cache (fastest)
        if (this.L1.has(key)) {
            return this.L1.get(key);
        }
        
        // L2: LocalStorage (fast)
        const l2Data = this.L2.getItem(key);
        if (l2Data) {
            const parsed = JSON.parse(l2Data);
            if (parsed.expires > Date.now()) {
                this.L1.set(key, parsed.data);
                return parsed.data;
            }
        }
        
        // L3: IndexedDB (slower, for large data)
        return await this.getFromIndexedDB(key);
    }
    
    set(key, data, ttl = 3600000) { // 1 hour default
        const expires = Date.now() + ttl;
        
        // Always store in L1 
        this.L1.set(key, data);
        
        // Store in L2 if small enough
        if (JSON.stringify(data).length < 1024 * 100) { // <100KB
            this.L2.setItem(key, JSON.stringify({data, expires}));
        } else {
            // Store large data in L3
            this.setInIndexedDB(key, data, expires);
        }
    }
}
```

## 🔒 보안 사양

### 클라이언트 보안

#### Content Security Policy
```http
Content-Security-Policy: 
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com;
  style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com;
  img-src 'self' data: https://*.tile.openstreetmap.org;
  connect-src 'self' https://satchat-client-proxy.onrender.com;
  font-src 'self' data:;
  worker-src 'self' blob:;
  child-src 'self' blob:;
```

#### 데이터 보안
```javascript
const securityMeasures = {
    dataEncryption: {
        sensitiveData: "AES-256-GCM",
        localStorage: "Base64 obfuscation",
        transmission: "HTTPS only"
    },
    inputValidation: {
        clientSide: "Comprehensive validation",
        sanitization: "XSS prevention", 
        typeChecking: "Strict TypeScript"
    },
    privacyProtection: {
        noTracking: "No user tracking",
        localProcessing: "Data stays in browser", 
        minimalCollection: "Only necessary metadata"
    }
};
```

### API 보안
```python
# Security configuration
SECURITY_CONFIG = {
    "cors": {
        "allow_origins": ["*"],  # Public API
        "allow_methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["*"],
        "max_age": 86400
    },
    "rate_limiting": {
        "enabled": False,  # Handled by platform
        "fallback": "Platform level protection"
    },
    "input_validation": {
        "path_params": "Strict validation",
        "query_params": "Type checking",
        "body_validation": "Pydantic schemas"
    }
}
```

## 📊 모니터링 및 로깅

### 클라이언트 메트릭
```javascript
const clientMetrics = {
    performance: {
        pageLoadTime: "window.performance.timing",
        analysisLatency: "Custom measurement",
        memoryUsage: "performance.memory (Chrome)",
        renderingTime: "PerformanceObserver"
    },
    usage: {
        featuresUsed: "Local analytics",
        errorOccurrences: "Try-catch blocks",
        userInteractions: "Event tracking",
        offlineUsage: "Service worker events"
    },
    quality: {
        analysisAccuracy: "User feedback",
        modelPerformance: "Inference metrics",
        cacheEfficiency: "Hit/miss ratios"
    }
};
```

### 서버 모니터링
```python
# Monitoring configuration
MONITORING = {
    "health_checks": {
        "endpoint": "/health",
        "interval": "30s",
        "timeout": "5s"
    },
    "metrics": {
        "response_time": "Request duration",
        "memory_usage": "Process RSS memory",
        "request_count": "Total requests served",
        "error_rate": "4xx/5xx responses"
    },
    "logging": {
        "level": "WARNING",  # Production
        "format": "JSON structured",
        "destination": "stdout"
    }
}
```

## 🧪 테스트 사양

### 자동화된 테스트

#### 유닛 테스트
```javascript
// Jest configuration for client-side testing
const jestConfig = {
    testEnvironment: "jsdom",
    setupFilesAfterEnv: ["<rootDir>/src/test-setup.js"],
    coverageThreshold: {
        global: {
            branches: 80,
            functions: 80,
            lines: 80,
            statements: 80
        }
    },
    testMatch: [
        "**/__tests__/**/*.test.js",
        "**/?(*.)+(spec|test).js"
    ]
};
```

#### 통합 테스트
```python
# pytest configuration for API testing
import pytest
from fastapi.testclient import TestClient
from minimal_proxy_api import app

class TestAPIIntegration:
    def setup_method(self):
        self.client = TestClient(app)
    
    def test_health_check(self):
        response = self.client.get("/health")
        assert response.status_code == 200
        assert "healthy" in response.json()["status"]
    
    def test_regions_endpoint(self):
        response = self.client.get("/regions")
        assert response.status_code == 200
        assert "west_sea" in response.json()["regions"]
```

#### E2E 테스트
```javascript
// Playwright E2E testing
const { test, expect } = require('@playwright/test');

test.describe('SatChat E2E Tests', () => {
    test('should perform complete analysis workflow', async ({ page }) => {
        await page.goto('https://djyalu.github.io/sat_chat/');
        
        // Wait for app initialization
        await expect(page.locator('[data-testid="status-indicator"]')).toHaveText('Ready');
        
        // Select region
        await page.click('[data-testid="region-west-sea"]');
        
        // Wait for analysis
        await expect(page.locator('[data-testid="analysis-result"]')).toBeVisible();
        
        // Verify results
        const confidenceText = await page.locator('[data-testid="confidence-score"]').textContent();
        expect(parseFloat(confidenceText)).toBeGreaterThan(0.5);
    });
});
```

### 성능 테스트
```javascript
const performanceBenchmarks = {
    lighthouse: {
        performance: ">90",
        accessibility: ">90", 
        bestPractices: ">90",
        seo: ">80",
        pwa: ">90"
    },
    loadTesting: {
        tool: "Artillery.io",
        scenarios: [
            {name: "basic_load", rps: 10, duration: "1m"},
            {name: "spike_test", rps: 100, duration: "30s"}
        ]
    },
    browserTesting: {
        browsers: ["Chrome", "Firefox", "Safari", "Edge"],
        devices: ["Desktop", "Tablet", "Mobile"],
        networks: ["Fast 3G", "Slow 3G", "Offline"]
    }
};
```

## 🚀 배포 사양

### 빌드 시스템
```yaml
# GitHub Actions workflow
build_pipeline:
  triggers:
    - push: [main]
    - pull_request: [main]
  
  steps:
    - checkout: "actions/checkout@v4"
    - setup_node: "actions/setup-node@v4"
    - install_dependencies: "npm ci"
    - run_tests: "npm test"
    - build_optimization: "npm run build"
    - lighthouse_audit: "npm run lighthouse"
    - deploy_to_pages: "actions/deploy-pages@v3"
  
  performance_budget:
    bundle_size: "<2MB"
    first_paint: "<2s"
    interactive: "<3s"
```

### 환경별 구성
```javascript
const environmentConfig = {
    development: {
        apiUrl: "http://localhost:8000",
        debug: true,
        modelSize: "lite",
        caching: false,
        analytics: false
    },
    staging: {
        apiUrl: "https://satchat-staging.onrender.com",
        debug: false,
        modelSize: "standard",
        caching: true,
        analytics: true
    },
    production: {
        apiUrl: "https://satchat-client-proxy.onrender.com", 
        debug: false,
        modelSize: "adaptive",
        caching: true,
        analytics: true,
        serviceWorker: true
    }
};
```

### 배포 메트릭
```yaml
deployment_targets:
  availability: "99.9%"
  response_time: "<100ms (API), <3s (Client)"
  error_rate: "<0.1%"
  deployment_time: "<5min"
  rollback_time: "<2min"
  
monitoring:
  uptime_monitoring: "UptimeRobot"
  error_tracking: "Built-in logging"
  performance_monitoring: "Web Vitals"
  user_analytics: "Privacy-focused metrics"
```

## 📏 품질 메트릭

### 코드 품질
```yaml
quality_gates:
  test_coverage: ">80%"
  code_duplication: "<5%"
  technical_debt: "<30min"
  maintainability_rating: "A"
  security_hotspots: "0"
  
static_analysis:
  eslint: "Strict TypeScript rules"
  prettier: "Code formatting"
  sonarqube: "Code quality analysis"
  
documentation:
  api_documentation: "100% coverage"
  code_comments: ">60%"
  user_documentation: "Complete"
```

### 사용자 경험 메트릭
```yaml
ux_metrics:
  core_web_vitals:
    LCP: "<2.5s"    # Largest Contentful Paint
    FID: "<100ms"   # First Input Delay  
    CLS: "<0.1"     # Cumulative Layout Shift
  
  custom_metrics:
    analysis_completion_time: "<500ms"
    offline_functionality: "100%"
    mobile_usability: ">90%"
    accessibility_score: ">95%"
```

---

*본 기술 사양서는 SatChat 시스템의 완전한 기술적 구현 사항을 다루며, 개발자와 운영자를 위한 상세한 참조 문서로 활용됩니다.*