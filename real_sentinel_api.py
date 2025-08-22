#!/usr/bin/env python3
"""실제 Sentinel Hub 데이터만 사용하는 간단한 API"""

import os
import io
import base64
import numpy as np
from datetime import datetime, timedelta
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Sentinel Hub imports
from sentinelhub import (
    SHConfig, CRS, BBox, DataCollection,
    SentinelHubRequest, MimeType
)

# 환경 변수 로드
load_dotenv()

app = FastAPI(title="SatChat Real Sentinel API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 한국 해역 정의
KOREA_REGIONS = {
    "west_sea": {
        "name": "서해",
        "bbox": [124.5, 35.5, 126.5, 37.5],  # 인천 근해
    },
    "south_sea": {
        "name": "남해", 
        "bbox": [128.4, 34.6, 128.8, 35.0],  # 거제도 근해
    },
    "east_sea": {
        "name": "동해",
        "bbox": [129.0, 35.5, 130.0, 36.5],  # 울산 근해
    }
}

def get_sentinel_config():
    """Sentinel Hub 설정"""
    config = SHConfig()
    config.sh_client_id = os.getenv('SENTINEL_HUB_CLIENT_ID')
    config.sh_client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET')
    config.sh_base_url = 'https://services.sentinel-hub.com'
    config.sh_token_url = 'https://services.sentinel-hub.com/oauth/token'
    return config

def get_real_sentinel_data(region_name: str):
    """실제 Sentinel-2 데이터 가져오기"""
    
    if region_name not in KOREA_REGIONS:
        raise ValueError(f"Unknown region: {region_name}")
    
    region = KOREA_REGIONS[region_name]
    config = get_sentinel_config()
    
    # BBox 생성
    bbox = BBox(bbox=region['bbox'], crs=CRS.WGS84)
    
    # 최근 14일 데이터
    time_interval = (datetime.now() - timedelta(days=14), datetime.now())
    
    # 해양 플라스틱 탐지 evalscript
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "B08", "B11", "SCL"]
            }],
            output: [{
                id: "default", 
                bands: 4
            }]
        };
    }
    
    function evaluatePixel(sample) {
        // 구름 제거
        if (sample.SCL == 3 || sample.SCL == 9) {
            return [0, 0, 0, 0];
        }
        
        // 정규화
        let blue = sample.B02 / 10000;
        let green = sample.B03 / 10000;
        let red = sample.B04 / 10000;
        let nir = sample.B08 / 10000;
        let swir = sample.B11 / 10000;
        
        // NDWI (물 탐지)
        let ndwi = (green - nir) / (green + nir + 0.001);
        
        // FDI (부유 물질 탐지)  
        let fdi = nir - red - 0.5 * (swir - red);
        
        // 플라스틱 가능성
        let plastic = 0;
        if (ndwi > 0 && fdi > 0.01) {
            plastic = Math.min(fdi * 20, 1);
        }
        
        // RGB 강화 + 플라스틱 점수
        return [red * 3, green * 3, blue * 3, plastic];
    }
    """
    
    # Sentinel-2 요청
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=0.3  # 구름 30% 이하
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=[512, 512],
        config=config
    )
    
    # 데이터 다운로드
    print(f"📡 Downloading real Sentinel-2 data for {region_name}...")
    data = request.get_data()
    
    if not data or len(data) == 0:
        raise ValueError("No data received from Sentinel Hub")
    
    image_data = data[0]
    print(f"✅ Received: {image_data.shape}, {image_data.dtype}")
    
    return image_data

def process_sentinel_image(image_data: np.ndarray):
    """Sentinel 이미지 처리"""
    
    # RGB와 플라스틱 레이어 분리
    if image_data.shape[2] >= 4:
        rgb = image_data[:, :, :3].astype(np.float32)
        plastic = image_data[:, :, 3].astype(np.float32)
    else:
        rgb = image_data.astype(np.float32)
        plastic = np.zeros((image_data.shape[0], image_data.shape[1]), dtype=np.float32)
    
    # RGB 정규화 및 대비 향상
    rgb = np.clip(rgb / 255.0, 0, 1)
    
    # 플라스틱 통계
    plastic_pixels = np.sum(plastic > 0.3)
    total_pixels = plastic.size
    plastic_percentage = plastic_pixels / total_pixels
    
    # 핫스팟 탐지
    hotspots = []
    if plastic_pixels > 0:
        # 간단한 핫스팟 탐지
        y_coords, x_coords = np.where(plastic > 0.5)
        if len(x_coords) > 0:
            # 클러스터링 (간단버전)
            for i in range(min(10, len(x_coords))):  # 최대 10개
                hotspots.append({
                    "lat": float(35.0 + (y_coords[i] / 512) * 1.0),  # 대략적 좌표
                    "lon": float(128.0 + (x_coords[i] / 512) * 1.0),
                    "intensity": float(plastic[y_coords[i], x_coords[i]]),
                    "pixel_count": 1
                })
    
    return rgb, plastic, plastic_percentage, hotspots

def array_to_base64(arr: np.ndarray) -> str:
    """NumPy 배열을 Base64 이미지로 변환"""
    # 0-1 범위를 0-255로 변환
    if arr.max() <= 1.0:
        arr = (arr * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

@app.get("/")
async def root():
    return {
        "service": "SatChat Real Sentinel API",
        "status": "operational",
        "data_source": "Sentinel-2 L2A (Real)",
        "regions": list(KOREA_REGIONS.keys())
    }

@app.get("/region/{region_name}")
async def get_region_data(region_name: str):
    """실제 Sentinel 데이터 반환"""
    
    try:
        # 실제 데이터 다운로드
        image_data = get_real_sentinel_data(region_name)
        
        # 이미지 처리
        rgb, plastic, plastic_percentage, hotspots = process_sentinel_image(image_data)
        
        # 히트맵 생성
        from matplotlib import cm
        heatmap_colored = cm.hot(plastic)[:, :, :3]  # RGB만
        
        # Base64 변환
        rgb_base64 = array_to_base64(rgb)
        heatmap_base64 = array_to_base64(heatmap_colored)
        
        result = {
            "region": region_name,
            "region_name": KOREA_REGIONS[region_name]["name"],
            "timestamp": datetime.now().isoformat(),
            "bbox": KOREA_REGIONS[region_name]["bbox"],
            "image_rgb": rgb_base64,
            "heatmap": heatmap_base64,
            "plastic_percentage": float(plastic_percentage),
            "plastic_area_km2": float(plastic_percentage * 1000),  # 대략적
            "hotspots": hotspots,
            "confidence": float(np.mean(plastic[plastic > 0.3])) if hotspots else 0.0,
            "data_source": "Sentinel-2 L2A (Real)"
        }
        
        print(f"📊 Results: {plastic_percentage*100:.2f}% plastic, {len(hotspots)} hotspots")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching satellite data: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    print("🛰️ Starting Real Sentinel API...")
    print("📡 Using only actual Sentinel-2 satellite data")
    uvicorn.run(app, host="0.0.0.0", port=8002)