#!/usr/bin/env python3
"""
Option A: Single Service 통합 아키텍처
프론트엔드를 FastAPI static files로 통합하는 방식
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
import os

# 통합 앱 구조
app = FastAPI(
    title="SatChat Fullstack Application",
    version="2.0.0",
    description="Integrated Frontend-Backend Marine Debris Monitoring System"
)

# 정적 파일 서빙 (CSS, JS, 이미지)
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")

# 템플릿 엔진 설정
templates = Jinja2Templates(directory="frontend/templates")

# API 라우터들 (기존 백엔드)
from src.satchat.api import (
    health, images, detections, alerts, monitoring, 
    sentinel_hub, byoc, ogc
)

# API 엔드포인트들
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(images.router, prefix="/api/v1/images", tags=["images"])
app.include_router(detections.router, prefix="/api/v1/detections", tags=["detections"])
app.include_router(alerts.router, prefix="/api/v1/alerts", tags=["alerts"])
app.include_router(monitoring.router, prefix="/api/v1/monitoring", tags=["monitoring"])
app.include_router(sentinel_hub.router, prefix="/api/v1/sentinel-hub", tags=["sentinel-hub"])
app.include_router(byoc.router, prefix="/api/v1/byoc", tags=["byoc"])
app.include_router(ogc.router, prefix="/api/v1/ogc", tags=["ogc"])

# 프론트엔드 라우팅
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """메인 대시보드"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "SatChat Marine Debris Monitoring",
        "api_base_url": "/api"
    })

@app.get("/analysis", response_class=HTMLResponse) 
async def analysis_page(request: Request):
    """Multi-Index 분석 페이지"""
    return templates.TemplateResponse("multi_analysis.html", {
        "request": request,
        "title": "Multi-Index Analysis",
        "api_base_url": "/api"
    })

@app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    """모니터링 페이지"""
    return templates.TemplateResponse("monitoring.html", {
        "request": request,
        "title": "Real-time Monitoring",
        "api_base_url": "/api"
    })

# SPA 라우팅 지원 (클라이언트 사이드 라우팅)
@app.get("/{path:path}")
async def spa_handler(request: Request, path: str):
    """SPA 경로를 index.html로 리디렉션"""
    if path.startswith("api/"):
        # API 경로는 404 반환
        return {"detail": "Not found"}
    
    # 프론트엔드 경로는 메인 앱으로
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "SatChat",
        "api_base_url": "/api"
    })

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)