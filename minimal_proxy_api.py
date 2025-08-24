#!/usr/bin/env python3
"""
SatChat Ultra-Minimal API Proxy - 20MB RAM Target
Client-side processing with minimal server footprint
"""

import os
import json
from datetime import datetime
from typing import Dict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(
    title="SatChat Minimal Proxy",
    version="3.0.0",
    description="Ultra-lightweight proxy for client-side AI processing"
)

# Minimal CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Minimal region data (no processing, just metadata)
KOREA_REGIONS = {
    "west_sea": {"name": "서해", "bbox": [124.5, 35.5, 126.5, 37.5]},
    "south_sea": {"name": "남해", "bbox": [128.4, 34.6, 128.8, 35.0]},
    "east_sea": {"name": "동해", "bbox": [129.0, 35.5, 130.0, 36.5]},
    "busan_port": {"name": "부산항", "bbox": [129.0, 35.0, 129.2, 35.2]},
    "incheon_port": {"name": "인천항", "bbox": [126.5, 37.4, 126.7, 37.6]}
}

@app.get("/")
async def root():
    return {
        "service": "SatChat Ultra-Minimal Proxy",
        "version": "3.0.0",
        "status": "operational",
        "processing": "client-side",
        "features": {
            "tensorflow_js": True,
            "offline_capable": True,
            "memory_footprint": "ultra-low",
            "client_ai": True
        },
        "regions": list(KOREA_REGIONS.keys())
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "memory_mode": "ultra-minimal"
    }

@app.get("/regions")
async def get_regions():
    """Return available regions for client processing"""
    return {
        "regions": KOREA_REGIONS,
        "processing_note": "Analysis performed client-side with TensorFlow.js",
        "capabilities": ["multi-index", "ml-detection", "offline-first"]
    }

@app.get("/region/{region_name}")
async def get_region_metadata(region_name: str):
    """Return region metadata only - processing done client-side"""
    
    if region_name not in KOREA_REGIONS:
        raise HTTPException(status_code=404, detail="Region not found")
    
    region_info = KOREA_REGIONS[region_name]
    
    return {
        "region": region_name,
        "region_name": region_info["name"],
        "bbox": region_info["bbox"],
        "timestamp": datetime.now().isoformat(),
        "processing_mode": "client-side",
        "instructions": {
            "analysis": "Use client-side TensorFlow.js processor",
            "indices": ["FDI", "NDWI", "MCI", "FAI", "Turbidity"],
            "ml_detection": "CNN-based debris classification",
            "offline_capable": True
        },
        "data_source": "Client-Generated Synthetic + TensorFlow.js",
        "api_role": "metadata_provider_only"
    }

@app.post("/auth/validate")
async def validate_token():
    """Minimal auth validation"""
    return {"valid": True, "client_processing": True}

@app.get("/system/minimal")
async def system_info():
    """Ultra-minimal system information"""
    return {
        "mode": "client-ai-proxy",
        "ram_target": "20MB",
        "processing": "offloaded_to_client",
        "tensorflow_js": "enabled",
        "offline_first": True
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting SatChat Ultra-Minimal Proxy...")
    print("💻 Client-side AI Processing + TensorFlow.js")
    print("📱 Progressive Web App + Offline-First")
    print("⚡ Memory Target: <20MB RAM")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)