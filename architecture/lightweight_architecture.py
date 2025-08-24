#!/usr/bin/env python3
"""
🚀 SatChat 경량화 아키텍처 - 인프라 부하 회피 설계
Ultra-lightweight design for resource-constrained environments
"""

import asyncio
import os
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
from functools import lru_cache
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
import httpx

# ============================================================================
# 1. 극도로 경량화된 Core Service
# ============================================================================

class LightweightConfig:
    """리소스 최적화 설정"""
    # 메모리 사용량 제한
    MAX_MEMORY_MB = 100
    MAX_WORKERS = 1
    LAZY_LOADING = True
    
    # 외부 의존성 최소화
    USE_EXTERNAL_DB = False  # SQLite 대신
    USE_EXTERNAL_CACHE = False  # 메모리 캐시 대신
    USE_EXTERNAL_QUEUE = False  # 직접 처리 대신
    
    # API 제한
    MAX_CONCURRENT_REQUESTS = 5
    REQUEST_TIMEOUT = 10
    
    # 기능 단계별 로딩
    ENABLE_ML_PROCESSING = os.getenv("ENABLE_ML", "false").lower() == "true"
    ENABLE_HEAVY_ANALYSIS = os.getenv("ENABLE_HEAVY", "false").lower() == "true"

# ============================================================================
# 2. 지연 로딩 (Lazy Loading) 시스템
# ============================================================================

class LazyLoader:
    """지연 로딩으로 메모리 사용량 최적화"""
    
    def __init__(self):
        self._ml_model = None
        self._image_processor = None
        self._heavy_dependencies = None
    
    @property 
    def ml_model(self):
        """ML 모델은 실제 사용시에만 로드"""
        if self._ml_model is None and LightweightConfig.ENABLE_ML_PROCESSING:
            try:
                # 경량화된 모델만 로드
                import numpy as np
                self._ml_model = self._load_lightweight_model()
            except ImportError:
                self._ml_model = None
        return self._ml_model
    
    def _load_lightweight_model(self):
        """10MB 이하 경량 모델 로드"""
        # 실제 모델 대신 규칙 기반 처리
        return {
            "type": "rule_based",
            "fdi_threshold": 0.05,
            "ndwi_threshold": 0.3,
            "confidence_base": 0.7
        }

# 글로벌 지연 로더
lazy_loader = LazyLoader()

# ============================================================================
# 3. 메모리 효율적 데이터 저장
# ============================================================================

class MemoryOptimizedStorage:
    """메모리 최적화된 임시 저장소"""
    
    def __init__(self, max_items=100):
        self.cache = {}
        self.max_items = max_items
        self.access_count = {}
    
    def set(self, key: str, value: Any, ttl: int = 300):
        """LRU 기반 캐시 저장"""
        if len(self.cache) >= self.max_items:
            # 가장 적게 사용된 항목 제거
            lru_key = min(self.access_count, key=self.access_count.get)
            del self.cache[lru_key]
            del self.access_count[lru_key]
        
        self.cache[key] = {
            "value": value,
            "expires": asyncio.get_event_loop().time() + ttl
        }
        self.access_count[key] = 0
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key not in self.cache:
            return None
            
        item = self.cache[key]
        if asyncio.get_event_loop().time() > item["expires"]:
            del self.cache[key]
            del self.access_count[key]
            return None
        
        self.access_count[key] += 1
        return item["value"]

# 글로벌 저장소
storage = MemoryOptimizedStorage()

# ============================================================================
# 4. 극경량 FastAPI 앱
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """최소한의 리소스로 빠른 시작"""
    print("🚀 SatChat Lightweight Service Starting...")
    print(f"💾 Memory limit: {LightweightConfig.MAX_MEMORY_MB}MB")
    print(f"⚡ ML Processing: {LightweightConfig.ENABLE_ML_PROCESSING}")
    
    # 필수 리소스만 초기화
    if LightweightConfig.LAZY_LOADING:
        print("🔄 Lazy loading enabled - services load on demand")
    
    yield
    
    print("🛑 Shutting down gracefully...")

# 극경량 앱 생성
app = FastAPI(
    title="SatChat Lightweight",
    version="1.0.0-lite",
    description="Resource-optimized marine debris monitoring",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("DEBUG") == "true" else None
)

# CORS 설정 (최소한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ============================================================================
# 5. 핵심 API 엔드포인트 (경량화)
# ============================================================================

class RegionRequest(BaseModel):
    region: str
    analysis_type: Optional[str] = "basic"

@app.get("/health")
async def health_check():
    """최소 헬스체크"""
    return {
        "status": "healthy",
        "memory_usage": f"{LightweightConfig.MAX_MEMORY_MB}MB",
        "ml_enabled": LightweightConfig.ENABLE_ML_PROCESSING,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/")
async def root():
    """정적 대시보드 서빙"""
    dashboard_html = """
    <!DOCTYPE html>
    <html><head><title>SatChat Lite</title>
    <script src="https://cdn.tailwindcss.com"></script></head>
    <body class="bg-gray-900 text-white p-8">
    <h1 class="text-3xl font-bold mb-4">🚀 SatChat Lightweight</h1>
    <div class="bg-gray-800 p-4 rounded">
        <p>Ultra-lightweight marine debris monitoring system</p>
        <button onclick="testAPI()" class="bg-blue-500 px-4 py-2 rounded mt-2">Test Analysis</button>
        <div id="result" class="mt-4"></div>
    </div>
    <script>
    async function testAPI() {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({region: 'west_sea', analysis_type: 'basic'})
        });
        const data = await response.json();
        document.getElementById('result').innerHTML = JSON.stringify(data, null, 2);
    }
    </script>
    </body></html>
    """
    return HTMLResponse(dashboard_html)

@app.post("/api/analyze")
async def lightweight_analysis(
    request: RegionRequest, 
    background_tasks: BackgroundTasks
):
    """경량화된 해역 분석"""
    
    # 캐시 확인
    cache_key = f"{request.region}_{request.analysis_type}"
    cached_result = storage.get(cache_key)
    if cached_result:
        return cached_result
    
    # 기본 분석 (매우 빠름)
    if request.analysis_type == "basic":
        result = await basic_analysis(request.region)
    elif request.analysis_type == "advanced" and LightweightConfig.ENABLE_ML_PROCESSING:
        # 백그라운드에서 처리
        background_tasks.add_task(advanced_analysis_task, request.region)
        result = {
            "status": "processing",
            "region": request.region,
            "analysis_id": f"adv_{cache_key}",
            "estimated_completion": "30 seconds"
        }
    else:
        result = {"error": "Analysis type not available in lite mode"}
    
    # 캐시에 저장
    storage.set(cache_key, result, ttl=300)
    return result

async def basic_analysis(region: str) -> Dict[str, Any]:
    """초경량 기본 분석 (1초 이내)"""
    
    # 한국 해역 기본 정보
    regions_info = {
        "west_sea": {"name": "서해", "risk_level": "medium", "avg_debris": 0.3},
        "south_sea": {"name": "남해", "risk_level": "high", "avg_debris": 0.7}, 
        "east_sea": {"name": "동해", "risk_level": "low", "avg_debris": 0.1}
    }
    
    region_data = regions_info.get(region, {"name": "Unknown", "risk_level": "unknown", "avg_debris": 0})
    
    # 시뮬레이션된 기본 분석
    return {
        "region": region,
        "region_name": region_data["name"],
        "analysis_type": "basic",
        "risk_level": region_data["risk_level"],
        "debris_probability": region_data["avg_debris"],
        "confidence": 0.85,
        "processing_time_ms": 50,
        "timestamp": asyncio.get_event_loop().time()
    }

async def advanced_analysis_task(region: str):
    """고급 분석 백그라운드 태스크"""
    # 시뮬레이션된 고급 처리
    await asyncio.sleep(2)  # 실제로는 ML 처리
    
    result = {
        "region": region,
        "analysis_type": "advanced",
        "ml_confidence": 0.92,
        "detected_objects": ["plastic_debris", "oil_spill"],
        "coordinates": [[35.5, 126.5], [35.6, 126.6]],
        "processing_time_ms": 2000,
        "timestamp": asyncio.get_event_loop().time()
    }
    
    # 결과 저장
    storage.set(f"adv_{region}_advanced", result, ttl=600)

@app.get("/api/status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    """분석 상태 확인"""
    result = storage.get(analysis_id)
    if result:
        return result
    else:
        return {"status": "not_found", "analysis_id": analysis_id}

# ============================================================================
# 6. 리소스 모니터링
# ============================================================================

@app.get("/api/system")
async def system_info():
    """시스템 리소스 상태"""
    import psutil
    import sys
    
    return {
        "memory_usage_mb": psutil.Process().memory_info().rss // 1024 // 1024,
        "cpu_percent": psutil.Process().cpu_percent(),
        "python_version": sys.version,
        "active_cache_items": len(storage.cache),
        "ml_loaded": lazy_loader._ml_model is not None
    }

# ============================================================================
# 7. 서버 실행
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    
    # 경량화 설정
    uvicorn.run(
        app,
        host="0.0.0.0", 
        port=port,
        workers=1,  # 단일 워커
        loop="asyncio",
        access_log=False,  # 로그 최소화
        log_level="warning"  # 로그 레벨 최소화
    )