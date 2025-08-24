#!/usr/bin/env python3
"""
🚀 SatChat Lite - Production Ready Lightweight Service
실제 배포를 위한 초경량 통합 서비스
"""

import asyncio
import os
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import logging

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 로깅 최소화
logging.getLogger("uvicorn").setLevel(logging.WARNING)

# ============================================================================
# Configuration
# ============================================================================

PORT = int(os.environ.get("PORT", 8000))
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")

# ============================================================================
# Lightweight App
# ============================================================================

app = FastAPI(
    title="SatChat Lite",
    version="1.0.0",
    description="Ultra-lightweight Marine Debris Monitoring System",
    docs_url="/docs" if DEBUG else None,
    redoc_url=None
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# 메모리 캐시
cache = {}

# ============================================================================
# Models
# ============================================================================

class AnalysisRequest(BaseModel):
    region: str
    analysis_type: Optional[str] = "basic"

class RegionData(BaseModel):
    region: str
    name: str
    bbox: List[float]
    risk_level: str
    avg_debris: float

# ============================================================================
# Korean Sea Regions Data
# ============================================================================

KOREA_REGIONS = {
    "west_sea": RegionData(
        region="west_sea",
        name="서해",
        bbox=[124.5, 35.5, 126.5, 37.5],
        risk_level="medium",
        avg_debris=0.35
    ),
    "south_sea": RegionData(
        region="south_sea", 
        name="남해",
        bbox=[126.0, 32.0, 130.0, 35.0],
        risk_level="high",
        avg_debris=0.65
    ),
    "east_sea": RegionData(
        region="east_sea",
        name="동해", 
        bbox=[128.0, 35.0, 132.0, 38.5],
        risk_level="low",
        avg_debris=0.15
    ),
    "busan_port": RegionData(
        region="busan_port",
        name="부산항",
        bbox=[129.0, 35.0, 129.2, 35.2], 
        risk_level="critical",
        avg_debris=0.85
    ),
    "incheon_port": RegionData(
        region="incheon_port",
        name="인천항",
        bbox=[126.5, 37.4, 126.7, 37.6],
        risk_level="high", 
        avg_debris=0.75
    )
}

# ============================================================================
# Main Dashboard HTML
# ============================================================================

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 SatChat Lite Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        .loading { animation: spin 1s linear infinite; }
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        #map { height: 400px; }
        .status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 8px; }
        .status-healthy { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-critical { background-color: #ef4444; }
    </style>
</head>
<body class="bg-gray-900 text-white">
    <div class="container mx-auto p-4">
        <!-- Header -->
        <header class="bg-gradient-to-r from-blue-800 to-green-800 rounded-lg p-6 mb-6">
            <h1 class="text-4xl font-bold mb-2">🚀 SatChat Lite</h1>
            <p class="text-gray-200 mb-2">Ultra-lightweight Marine Debris Monitoring</p>
            <div class="flex gap-4 text-sm">
                <span class="bg-green-600 px-3 py-1 rounded">⚡ Fast Response</span>
                <span class="bg-blue-600 px-3 py-1 rounded">💾 Memory Optimized</span>
                <span class="bg-purple-600 px-3 py-1 rounded">🚀 Cloud Ready</span>
            </div>
        </header>

        <!-- System Status -->
        <div class="bg-gray-800 rounded-lg p-4 mb-6">
            <h2 class="text-xl font-bold mb-4">📊 System Status</h2>
            <div class="grid grid-cols-2 md:grid-cols-4 gap-4" id="systemStatus">
                <div class="text-center">
                    <div class="status-dot status-healthy"></div>
                    <span class="text-sm">API Service</span>
                </div>
                <div class="text-center">
                    <div class="status-dot status-healthy"></div>
                    <span class="text-sm">Analysis Engine</span>
                </div>
                <div class="text-center">
                    <div class="status-dot status-healthy"></div>
                    <span class="text-sm">Memory Cache</span>
                </div>
                <div class="text-center">
                    <div class="status-dot status-healthy"></div>
                    <span class="text-sm">Lightweight Mode</span>
                </div>
            </div>
        </div>

        <!-- Region Analysis -->
        <div class="bg-gray-800 rounded-lg p-4 mb-6">
            <h2 class="text-xl font-bold mb-4">🌊 Region Analysis</h2>
            <div class="grid grid-cols-1 md:grid-cols-5 gap-3 mb-4">
                <button onclick="analyzeRegion('west_sea')" class="px-4 py-3 bg-blue-600 hover:bg-blue-700 rounded-lg transition">
                    🌊 서해<br><span class="text-xs">West Sea</span>
                </button>
                <button onclick="analyzeRegion('south_sea')" class="px-4 py-3 bg-green-600 hover:bg-green-700 rounded-lg transition">
                    🌊 남해<br><span class="text-xs">South Sea</span>
                </button>
                <button onclick="analyzeRegion('east_sea')" class="px-4 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg transition">
                    🌊 동해<br><span class="text-xs">East Sea</span>
                </button>
                <button onclick="analyzeRegion('busan_port')" class="px-4 py-3 bg-red-600 hover:bg-red-700 rounded-lg transition">
                    🚢 부산항<br><span class="text-xs">Busan Port</span>
                </button>
                <button onclick="analyzeRegion('incheon_port')" class="px-4 py-3 bg-yellow-600 hover:bg-yellow-700 rounded-lg transition">
                    🚢 인천항<br><span class="text-xs">Incheon Port</span>
                </button>
            </div>
            
            <!-- Analysis Results -->
            <div id="analysisResults" class="mt-4"></div>
        </div>

        <!-- Interactive Map -->
        <div class="bg-gray-800 rounded-lg p-4 mb-6">
            <h2 class="text-xl font-bold mb-4">🗺️ Interactive Map</h2>
            <div id="map"></div>
        </div>

        <!-- Performance Metrics -->
        <div class="bg-gray-800 rounded-lg p-4 mb-6">
            <h2 class="text-xl font-bold mb-4">⚡ Performance Metrics</h2>
            <div id="performanceMetrics" class="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div class="text-center">
                    <div class="text-2xl font-bold text-green-400" id="responseTime">--</div>
                    <div class="text-sm text-gray-400">Response Time (ms)</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-blue-400" id="memoryUsage">--</div>
                    <div class="text-sm text-gray-400">Memory Usage (MB)</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-purple-400" id="cacheItems">--</div>
                    <div class="text-sm text-gray-400">Cache Items</div>
                </div>
                <div class="text-center">
                    <div class="text-2xl font-bold text-yellow-400" id="uptime">--</div>
                    <div class="text-sm text-gray-400">Uptime (min)</div>
                </div>
            </div>
        </div>

        <!-- API Test -->
        <div class="bg-gray-800 rounded-lg p-4 mb-6">
            <h2 class="text-xl font-bold mb-4">🔧 API Test</h2>
            <div class="flex gap-2 mb-2">
                <button onclick="testAPI('/health')" class="px-4 py-2 bg-green-600 hover:bg-green-700 rounded">Health Check</button>
                <button onclick="testAPI('/api/regions')" class="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded">Regions</button>
                <button onclick="testAPI('/api/system')" class="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded">System Info</button>
            </div>
            <pre id="apiResults" class="bg-gray-900 p-3 rounded text-sm overflow-auto max-h-40"></pre>
        </div>
    </div>

    <script>
        // Initialize map
        const map = L.map('map').setView([36.5, 127.5], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);

        // Add region markers
        const regions = {
            west_sea: [36.5, 125.5],
            south_sea: [33.5, 128.0], 
            east_sea: [36.5, 129.5],
            busan_port: [35.1, 129.1],
            incheon_port: [37.5, 126.6]
        };

        Object.entries(regions).forEach(([key, coords]) => {
            L.marker(coords).addTo(map)
                .bindPopup(`<b>${key}</b><br>Click to analyze`)
                .on('click', () => analyzeRegion(key));
        });

        // Analysis function
        async function analyzeRegion(region) {
            const resultsDiv = document.getElementById('analysisResults');
            resultsDiv.innerHTML = `
                <div class="bg-gray-700 p-4 rounded">
                    <div class="flex items-center">
                        <div class="loading w-6 h-6 border-2 border-green-500 border-t-transparent rounded-full mr-3"></div>
                        <span>Analyzing ${region}...</span>
                    </div>
                </div>
            `;

            try {
                const startTime = performance.now();
                const response = await fetch('/api/analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({region: region, analysis_type: 'basic'})
                });
                const data = await response.json();
                const endTime = performance.now();
                
                document.getElementById('responseTime').textContent = Math.round(endTime - startTime);
                
                resultsDiv.innerHTML = `
                    <div class="bg-gray-700 p-4 rounded">
                        <h3 class="text-lg font-bold mb-2">📊 Analysis Results: ${data.region_name}</h3>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <span class="text-gray-400">Risk Level:</span>
                                <span class="font-bold text-${data.risk_level === 'critical' ? 'red' : data.risk_level === 'high' ? 'yellow' : 'green'}-400">${data.risk_level.toUpperCase()}</span>
                            </div>
                            <div>
                                <span class="text-gray-400">Debris Probability:</span>
                                <span class="font-bold">${(data.debris_probability * 100).toFixed(1)}%</span>
                            </div>
                            <div>
                                <span class="text-gray-400">Confidence:</span>
                                <span class="font-bold">${(data.confidence * 100).toFixed(1)}%</span>
                            </div>
                            <div>
                                <span class="text-gray-400">Processing Time:</span>
                                <span class="font-bold">${data.processing_time_ms}ms</span>
                            </div>
                        </div>
                    </div>
                `;
            } catch (error) {
                resultsDiv.innerHTML = `<div class="bg-red-700 p-4 rounded">Error: ${error.message}</div>`;
            }
        }

        // API Test function
        async function testAPI(endpoint) {
            try {
                const response = await fetch(endpoint);
                const data = await response.json();
                document.getElementById('apiResults').textContent = JSON.stringify(data, null, 2);
            } catch (error) {
                document.getElementById('apiResults').textContent = `Error: ${error.message}`;
            }
        }

        // Auto-refresh system metrics
        async function updateMetrics() {
            try {
                const response = await fetch('/api/system');
                const data = await response.json();
                document.getElementById('memoryUsage').textContent = data.memory_usage_mb || '--';
                document.getElementById('cacheItems').textContent = data.active_cache_items || '--';
                document.getElementById('uptime').textContent = data.uptime_minutes || '--';
            } catch (error) {
                console.error('Failed to update metrics:', error);
            }
        }

        // Update metrics every 30 seconds
        setInterval(updateMetrics, 30000);
        updateMetrics(); // Initial load

        // Load initial data
        window.onload = () => {
            console.log('🚀 SatChat Lite Dashboard Loaded');
            testAPI('/health');
        };
    </script>
</body>
</html>
"""

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """메인 대시보드"""
    return DASHBOARD_HTML

@app.get("/health")
async def health_check():
    """헬스체크"""
    return {
        "status": "healthy",
        "service": "SatChat Lite",
        "version": "1.0.0",
        "environment": ENVIRONMENT,
        "timestamp": datetime.now().isoformat(),
        "memory_optimized": True
    }

@app.get("/api/regions") 
async def get_regions():
    """지원 해역 목록"""
    return {
        "regions": [
            {
                "id": region_id,
                "name": region_data.name,
                "bbox": region_data.bbox,
                "risk_level": region_data.risk_level
            }
            for region_id, region_data in KOREA_REGIONS.items()
        ]
    }

@app.post("/api/analyze")
async def analyze_region(request: AnalysisRequest):
    """해역 분석 API"""
    start_time = time.time()
    
    if request.region not in KOREA_REGIONS:
        raise HTTPException(status_code=404, detail="Region not found")
    
    region_data = KOREA_REGIONS[request.region]
    
    # 캐시 확인
    cache_key = f"{request.region}_{request.analysis_type}"
    if cache_key in cache:
        cached_result = cache[cache_key]
        if time.time() - cached_result["cached_at"] < 300:  # 5분 캐시
            return cached_result["data"]
    
    # 기본 분석 수행
    await asyncio.sleep(0.05)  # 실제 처리 시뮬레이션
    
    processing_time = int((time.time() - start_time) * 1000)
    
    result = {
        "region": request.region,
        "region_name": region_data.name,
        "analysis_type": request.analysis_type,
        "bbox": region_data.bbox,
        "risk_level": region_data.risk_level,
        "debris_probability": region_data.avg_debris,
        "confidence": 0.85,
        "processing_time_ms": processing_time,
        "timestamp": datetime.now().isoformat(),
        "lite_mode": True
    }
    
    # 캐시에 저장
    cache[cache_key] = {
        "data": result,
        "cached_at": time.time()
    }
    
    return result

@app.get("/api/system")
async def system_info():
    """시스템 정보"""
    import psutil
    
    process = psutil.Process()
    memory_mb = process.memory_info().rss // 1024 // 1024
    
    return {
        "memory_usage_mb": memory_mb,
        "cpu_percent": process.cpu_percent(),
        "active_cache_items": len(cache),
        "uptime_minutes": int((time.time() - start_time) / 60) if 'start_time' in globals() else 0,
        "environment": ENVIRONMENT,
        "port": PORT
    }

# ============================================================================
# Startup
# ============================================================================

start_time = time.time()

if __name__ == "__main__":
    import uvicorn
    
    print(f"🚀 Starting SatChat Lite on port {PORT}")
    print(f"💾 Environment: {ENVIRONMENT}")
    print(f"🌐 Dashboard: http://localhost:{PORT}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=PORT,
        workers=1,
        access_log=False,
        log_level="warning"
    )