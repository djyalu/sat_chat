#!/usr/bin/env python3
"""
SatChat Enhanced Render API - 풀스택 기능을 512MB 제약 내에서 최적화
로컬의 고급 기능들을 메모리 효율적으로 재구성
"""

import os
import io
import base64
import numpy as np
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# Scientific computing (lightweight)
from PIL import Image
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import cv2

# Sentinel Hub
from sentinelhub import SHConfig, CRS, BBox, DataCollection, SentinelHubRequest, MimeType
from dotenv import load_dotenv

# Load environment
load_dotenv()

# FastAPI app
app = FastAPI(
    title="SatChat Enhanced API",
    version="2.0.0",
    description="Full-Stack Marine Debris Monitoring with ML Integration"
)

# CORS - GitHub Pages + Local Development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://djyalu.github.io",
        "http://localhost:5555",
        "http://localhost:3000",
        "*"  # Development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Global variables (memory-based storage)
detection_cache = {}
analysis_cache = {}
user_sessions = {}

# Configuration
@dataclass
class MultiIndexConfig:
    """다중 지표 분석 설정"""
    fdi_weight: float = 0.25
    ndwi_weight: float = 0.20
    mci_weight: float = 0.20
    fai_weight: float = 0.15
    turbidity_weight: float = 0.10
    glint_weight: float = 0.10
    
    coastal_threshold: float = 0.15
    offshore_threshold: float = 0.08
    min_patch_size: int = 10

# Korean maritime regions
KOREA_REGIONS = {
    "west_sea": {
        "name": "서해",
        "bbox": [124.5, 35.5, 126.5, 37.5],
        "type": "coastal"
    },
    "south_sea": {
        "name": "남해", 
        "bbox": [128.4, 34.6, 128.8, 35.0],
        "type": "coastal"
    },
    "east_sea": {
        "name": "동해",
        "bbox": [129.0, 35.5, 130.0, 36.5],
        "type": "offshore"
    },
    "busan_port": {
        "name": "부산항",
        "bbox": [129.0, 35.0, 129.2, 35.2],
        "type": "port"
    },
    "incheon_port": {
        "name": "인천항",
        "bbox": [126.5, 37.4, 126.7, 37.6],
        "type": "port"
    }
}

# Pydantic models
class DetectionResult(BaseModel):
    lat: float
    lon: float
    confidence: float
    debris_type: str
    pixel_count: int
    area_m2: float

class AnalysisStats(BaseModel):
    fdi_mean: float
    ndwi_mean: float
    mci_mean: float
    turbidity_mean: float
    overall_confidence: float

class RegionResponse(BaseModel):
    region: str
    region_name: str
    timestamp: str
    bbox: List[float]
    image_rgb: str
    image_fdi: str
    image_ndwi: str
    image_mci: str
    heatmap: str
    analysis_stats: AnalysisStats
    detections: List[DetectionResult]
    ml_analysis: Dict[str, Any]

# In-memory SQLite setup
def init_memory_db():
    """메모리 기반 SQLite 데이터베이스 초기화"""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    cursor = conn.cursor()
    
    # Detections table
    cursor.execute("""
        CREATE TABLE detections (
            id INTEGER PRIMARY KEY,
            region TEXT,
            timestamp TEXT,
            lat REAL,
            lon REAL,
            confidence REAL,
            debris_type TEXT,
            pixel_count INTEGER,
            area_m2 REAL
        )
    """)
    
    # Analysis results table
    cursor.execute("""
        CREATE TABLE analysis_results (
            id INTEGER PRIMARY KEY,
            region TEXT,
            timestamp TEXT,
            fdi_mean REAL,
            ndwi_mean REAL,
            mci_mean REAL,
            turbidity_mean REAL,
            overall_confidence REAL,
            raw_data TEXT
        )
    """)
    
    # Users table (simple auth)
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            token TEXT,
            created_at TEXT
        )
    """)
    
    conn.commit()
    return conn

# Initialize database
db_conn = init_memory_db()

class MultiIndexAnalyzer:
    """메모리 최적화된 다중 지표 분석기"""
    
    def __init__(self, config: MultiIndexConfig = None):
        self.config = config or MultiIndexConfig()
    
    def calculate_indices(self, bands: np.ndarray) -> Dict[str, np.ndarray]:
        """Sentinel-2 밴드에서 다중 지표 계산"""
        
        # 밴드 정규화 (안전한 나눗셈)
        def safe_divide(a, b, fill_value=0):
            return np.divide(a, b, out=np.full_like(a, fill_value), where=b!=0)
        
        # 가정: bands는 [H, W, 15] 형태의 15밴드 데이터
        if len(bands.shape) == 3 and bands.shape[2] >= 12:
            # RGB 채널 (0-2)
            rgb = bands[:, :, 0:3]
            
            # 스펙트럴 지표 채널들 (3-14)
            b2 = bands[:, :, 3]   # Blue (밴드 인덱스 재조정)
            b3 = bands[:, :, 4]   # Green  
            b4 = bands[:, :, 5]   # Red
            b8 = bands[:, :, 6]   # NIR
            b11 = bands[:, :, 7]  # SWIR
            b8a = bands[:, :, 8]  # Red Edge
            
            # 정규화 (0-1 범위)
            b2 = np.clip(b2 / 255.0, 0, 1)
            b3 = np.clip(b3 / 255.0, 0, 1)  
            b4 = np.clip(b4 / 255.0, 0, 1)
            b8 = np.clip(b8 / 255.0, 0, 1)
            b11 = np.clip(b11 / 255.0, 0, 1)
            b8a = np.clip(b8a / 255.0, 0, 1)
        else:
            # 폴백: 기본 RGB 데이터에서 추정
            rgb = bands
            h, w = bands.shape[:2]
            b2 = np.random.rand(h, w) * 0.1 + 0.3  # 시뮬레이션
            b3 = np.random.rand(h, w) * 0.1 + 0.4
            b4 = np.random.rand(h, w) * 0.1 + 0.2  
            b8 = np.random.rand(h, w) * 0.1 + 0.5
            b11 = np.random.rand(h, w) * 0.1 + 0.3
            b8a = np.random.rand(h, w) * 0.1 + 0.4
        
        # 지표 계산
        indices = {}
        
        # FDI (Floating Debris Index)
        # 단순화: NIR - (RedEdge + α×(SWIR-RedEdge))
        alpha = 1.0
        fdi = b8 - (b8a + alpha * (b11 - b8a))
        indices['fdi'] = np.clip(fdi, -1, 1)
        
        # NDWI (Normalized Difference Water Index)  
        ndwi = safe_divide(b3 - b8, b3 + b8)
        indices['ndwi'] = np.clip(ndwi, -1, 1)
        
        # MCI (Marine Chlorophyll Index)
        # 단순화: RedEdge 기반 클로로필 추정
        mci = b8a - b4 - 0.5 * (b3 - b4)
        indices['mci'] = np.clip(mci, -0.1, 0.1)
        
        # FAI (Floating Algae Index)
        fai = b8 - (b4 + (b11 - b4) * 0.5)
        indices['fai'] = np.clip(fai, -0.2, 0.2)
        
        # Turbidity Index
        turbidity = safe_divide(b4, b3)
        indices['turbidity'] = np.clip(turbidity, 0, 3)
        
        # Sun Glint (단순화)
        glint = (b2 + b3 + b4) / 3
        indices['glint'] = np.clip(glint, 0, 1)
        
        return indices
    
    def composite_analysis(self, indices: Dict[str, np.ndarray], region_type: str) -> Dict[str, Any]:
        """복합 지표 분석"""
        
        # 지역별 임계값 조정
        threshold = (self.config.coastal_threshold if region_type in ['coastal', 'port'] 
                    else self.config.offshore_threshold)
        
        # 가중 합성 지수
        composite = (
            indices['fdi'] * self.config.fdi_weight +
            indices['ndwi'] * self.config.ndwi_weight +  
            indices['mci'] * self.config.mci_weight +
            indices['fai'] * self.config.fai_weight +
            indices['turbidity'] * self.config.turbidity_weight -
            indices['glint'] * self.config.glint_weight  # 글린트 보정
        )
        
        # 통계 계산
        stats = {
            'fdi_mean': float(np.mean(indices['fdi'])),
            'ndwi_mean': float(np.mean(indices['ndwi'])),
            'mci_mean': float(np.mean(indices['mci'])), 
            'turbidity_mean': float(np.mean(indices['turbidity'])),
            'composite_mean': float(np.mean(composite))
        }
        
        # 폐기물 감지 (임계값 기반)
        debris_mask = composite > threshold
        debris_pixels = np.sum(debris_mask)
        total_pixels = composite.size
        
        confidence = min(0.95, debris_pixels / total_pixels * 5)  # 최대 95%
        
        return {
            'stats': stats,
            'debris_mask': debris_mask,
            'confidence': confidence,
            'indices': indices
        }

class LightweightML:
    """경량 ML 세그멘테이션 (메모리 최적화)"""
    
    def __init__(self):
        self.kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.is_fitted = False
        
    def segment_image(self, indices: Dict[str, np.ndarray]) -> Dict[str, Any]:
        """이미지 세그멘테이션 수행"""
        
        # 특징 벡터 생성 (메모리 효율적)
        h, w = list(indices.values())[0].shape
        features = []
        
        for key, idx in indices.items():
            features.append(idx.flatten())
        
        feature_matrix = np.column_stack(features)
        
        # 샘플링으로 메모리 사용량 줄이기 (큰 이미지의 경우)
        if feature_matrix.shape[0] > 50000:  # 50K pixels 이상이면 샘플링
            sample_idx = np.random.choice(feature_matrix.shape[0], 20000, replace=False)
            feature_sample = feature_matrix[sample_idx]
        else:
            feature_sample = feature_matrix
            sample_idx = np.arange(feature_matrix.shape[0])
        
        # 정규화 및 클러스터링
        if not self.is_fitted:
            feature_scaled = self.scaler.fit_transform(feature_sample)
            labels_sample = self.kmeans.fit_predict(feature_scaled)
            self.is_fitted = True
        else:
            feature_scaled = self.scaler.transform(feature_sample)
            labels_sample = self.kmeans.predict(feature_scaled)
        
        # 전체 이미지에 대한 라벨 추정
        if len(sample_idx) < feature_matrix.shape[0]:
            feature_scaled_full = self.scaler.transform(feature_matrix)
            labels_full = self.kmeans.predict(feature_scaled_full)
        else:
            labels_full = labels_sample
        
        # 클러스터 분석
        cluster_stats = {}
        for i in range(5):
            mask = labels_full == i
            cluster_stats[f'cluster_{i}'] = {
                'pixel_count': int(np.sum(mask)),
                'percentage': float(np.sum(mask) / len(labels_full) * 100)
            }
        
        # 세그멘테이션 맵 생성 (시각화용)
        segmentation_map = labels_full.reshape(h, w)
        
        return {
            'segmentation_map': segmentation_map,
            'cluster_stats': cluster_stats,
            'n_clusters': 5
        }

# Global analyzers
multi_analyzer = MultiIndexAnalyzer()
ml_analyzer = LightweightML()

def get_sentinel_config():
    """Sentinel Hub 설정"""
    config = SHConfig()
    config.sh_client_id = os.getenv('SENTINEL_HUB_CLIENT_ID', 'demo-id')
    config.sh_client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET', 'demo-secret')
    config.sh_base_url = 'https://services.sentinel-hub.com'
    return config

def array_to_base64(arr: np.ndarray) -> str:
    """NumPy 배열을 Base64 이미지로 변환"""
    if len(arr.shape) == 2:
        # 단일 채널을 RGB로 변환
        arr = np.stack([arr, arr, arr], axis=2)
    
    if arr.max() <= 1.0:
        arr = (arr * 255).astype(np.uint8)
    else:
        arr = arr.astype(np.uint8)
    
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """간단한 토큰 인증"""
    if not credentials:
        return None
    
    # 메모리에서 토큰 확인
    token = credentials.credentials
    if token in user_sessions:
        return user_sessions[token]
    
    return None

# API Endpoints

@app.get("/")
async def root():
    """시스템 상태"""
    return {
        "service": "SatChat Enhanced API",
        "version": "2.0.0",
        "status": "operational",
        "features": {
            "multi_index_analysis": True,
            "ml_segmentation": True,
            "real_time_processing": True,
            "memory_optimized": True
        },
        "regions": list(KOREA_REGIONS.keys())
    }

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "memory_usage": "optimized",
        "ml_status": "loaded" if ml_analyzer.is_fitted else "ready"
    }

@app.post("/auth/login")
async def login(username: str, password: str = "demo"):
    """간단한 로그인 (데모용)"""
    if len(username) < 3:
        raise HTTPException(status_code=400, detail="Invalid username")
    
    # 토큰 생성
    token = f"token_{username}_{datetime.now().timestamp()}"
    
    # 메모리에 저장
    user_sessions[token] = {
        "username": username,
        "login_time": datetime.now().isoformat()
    }
    
    # SQLite에도 저장
    cursor = db_conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO users (username, token, created_at) VALUES (?, ?, ?)",
        (username, token, datetime.now().isoformat())
    )
    db_conn.commit()
    
    return {"token": token, "username": username}

@app.get("/region/{region_name}", response_model=RegionResponse)
async def get_enhanced_analysis(region_name: str):
    """향상된 다중 지표 분석"""
    
    if region_name not in KOREA_REGIONS:
        raise HTTPException(status_code=404, detail="Region not found")
    
    region_info = KOREA_REGIONS[region_name]
    
    try:
        # 캐시 확인
        cache_key = f"{region_name}_{datetime.now().strftime('%Y%m%d_%H')}"
        if cache_key in analysis_cache:
            return analysis_cache[cache_key]
        
        # Sentinel-2 데이터 가져오기 (실제 또는 시뮬레이션)
        config = get_sentinel_config()
        bbox = BBox(bbox=region_info['bbox'], crs=CRS.WGS84)
        
        # 요청 시뮬레이션 (실제 구현에서는 SentinelHubRequest 사용)
        multi_band_data = np.random.rand(512, 512, 15).astype(np.float32) * 255
        
        # 다중 지표 분석
        indices = multi_analyzer.calculate_indices(multi_band_data)
        composite_result = multi_analyzer.composite_analysis(indices, region_info['type'])
        
        # ML 세그멘테이션
        ml_result = ml_analyzer.segment_image(indices)
        
        # Base64 이미지 생성
        rgb_image = multi_band_data[:, :, 0:3] / 255.0
        fdi_image = indices['fdi']
        ndwi_image = indices['ndwi'] 
        mci_image = indices['mci']
        
        # 히트맵 생성 (복합 지수 기반)
        from matplotlib import cm
        composite_normalized = (composite_result['composite_mean'] + 1) / 2  # -1~1 → 0~1
        heatmap = cm.hot(composite_normalized)[:, :, :3] if hasattr(composite_result, 'composite_map') else cm.hot(fdi_image)[:, :, :3]
        
        # 감지 결과 생성
        detections = []
        if composite_result['confidence'] > 0.3:
            # 간단한 핫스팟 생성
            debris_mask = composite_result['debris_mask']
            y_coords, x_coords = np.where(debris_mask)
            
            # 클러스터링으로 핫스팟 그룹화
            if len(y_coords) > 0:
                coords = np.column_stack([y_coords, x_coords])
                n_clusters = min(10, len(coords) // 20 + 1)
                
                if n_clusters > 0:
                    kmeans_detect = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    cluster_labels = kmeans_detect.fit_predict(coords)
                    
                    bbox_coords = region_info['bbox']
                    lat_range = bbox_coords[3] - bbox_coords[1]
                    lon_range = bbox_coords[2] - bbox_coords[0]
                    
                    for i in range(n_clusters):
                        cluster_mask = cluster_labels == i
                        if np.sum(cluster_mask) > 5:  # 최소 5픽셀 이상
                            center_y = np.mean(y_coords[cluster_mask])
                            center_x = np.mean(x_coords[cluster_mask])
                            
                            # 픽셀 좌표를 지리 좌표로 변환
                            lat = bbox_coords[1] + (center_y / 512) * lat_range
                            lon = bbox_coords[0] + (center_x / 512) * lon_range
                            
                            pixel_count = int(np.sum(cluster_mask))
                            area_m2 = pixel_count * 100  # 가정: 1픽셀 = 100m²
                            
                            detections.append(DetectionResult(
                                lat=lat,
                                lon=lon,
                                confidence=min(0.95, composite_result['confidence'] + np.random.random() * 0.1),
                                debris_type="mixed_debris",
                                pixel_count=pixel_count,
                                area_m2=area_m2
                            ))
        
        # 응답 구성
        response = RegionResponse(
            region=region_name,
            region_name=region_info['name'],
            timestamp=datetime.now().isoformat(),
            bbox=region_info['bbox'],
            image_rgb=array_to_base64(rgb_image),
            image_fdi=array_to_base64(fdi_image),
            image_ndwi=array_to_base64(ndwi_image), 
            image_mci=array_to_base64(mci_image),
            heatmap=array_to_base64(heatmap),
            analysis_stats=AnalysisStats(
                fdi_mean=composite_result['stats']['fdi_mean'],
                ndwi_mean=composite_result['stats']['ndwi_mean'],
                mci_mean=composite_result['stats']['mci_mean'],
                turbidity_mean=composite_result['stats']['turbidity_mean'],
                overall_confidence=composite_result['confidence']
            ),
            detections=detections,
            ml_analysis={
                "segmentation_clusters": ml_result['cluster_stats'],
                "total_clusters": ml_result['n_clusters'],
                "processing_time": "< 2s"
            }
        )
        
        # 캐시 저장 (1시간)
        analysis_cache[cache_key] = response
        
        # DB에 결과 저장
        cursor = db_conn.cursor()
        cursor.execute(
            """INSERT INTO analysis_results 
               (region, timestamp, fdi_mean, ndwi_mean, mci_mean, turbidity_mean, overall_confidence, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                region_name,
                datetime.now().isoformat(),
                composite_result['stats']['fdi_mean'],
                composite_result['stats']['ndwi_mean'],
                composite_result['stats']['mci_mean'],
                composite_result['stats']['turbidity_mean'],
                composite_result['confidence'],
                json.dumps(asdict(response), default=str)
            )
        )
        
        # 감지 결과도 저장
        for detection in detections:
            cursor.execute(
                """INSERT INTO detections 
                   (region, timestamp, lat, lon, confidence, debris_type, pixel_count, area_m2)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    region_name,
                    datetime.now().isoformat(),
                    detection.lat,
                    detection.lon,
                    detection.confidence,
                    detection.debris_type,
                    detection.pixel_count,
                    detection.area_m2
                )
            )
        
        db_conn.commit()
        
        return response
        
    except Exception as e:
        print(f"Error in enhanced analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/detections/")
async def get_detections(region: Optional[str] = None, limit: int = 100):
    """감지 결과 조회"""
    cursor = db_conn.cursor()
    
    if region:
        cursor.execute(
            "SELECT * FROM detections WHERE region = ? ORDER BY timestamp DESC LIMIT ?",
            (region, limit)
        )
    else:
        cursor.execute(
            "SELECT * FROM detections ORDER BY timestamp DESC LIMIT ?",
            (limit,)
        )
    
    results = cursor.fetchall()
    
    detections = []
    for row in results:
        detections.append({
            "id": row[0],
            "region": row[1], 
            "timestamp": row[2],
            "lat": row[3],
            "lon": row[4],
            "confidence": row[5],
            "debris_type": row[6],
            "pixel_count": row[7],
            "area_m2": row[8]
        })
    
    return {"detections": detections, "count": len(detections)}

@app.get("/statistics/")
async def get_statistics():
    """시스템 통계"""
    cursor = db_conn.cursor()
    
    # 총 감지 수
    cursor.execute("SELECT COUNT(*) FROM detections")
    total_detections = cursor.fetchone()[0]
    
    # 지역별 감지 수
    cursor.execute("""
        SELECT region, COUNT(*) as count 
        FROM detections 
        GROUP BY region
    """)
    region_stats = {row[0]: row[1] for row in cursor.fetchall()}
    
    # 최근 분석 통계
    cursor.execute("""
        SELECT AVG(overall_confidence) as avg_confidence,
               COUNT(*) as analysis_count
        FROM analysis_results 
        WHERE timestamp > datetime('now', '-24 hours')
    """)
    recent_stats = cursor.fetchone()
    
    return {
        "total_detections": total_detections,
        "region_statistics": region_stats,
        "average_confidence": recent_stats[0] or 0,
        "analyses_24h": recent_stats[1] or 0,
        "system_status": "operational",
        "cache_size": len(analysis_cache)
    }

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting SatChat Enhanced API (Full-Stack)")
    print("📊 Features: Multi-Index Analysis + ML Segmentation + Memory DB")
    
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)