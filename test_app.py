"""간단한 테스트용 FastAPI 서버 - Advanced Detection 포함"""

import sys
import os
import asyncio
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import advanced detection modules
try:
    from src.satchat.sentinel_hub_advanced import SentinelHubAdvanced, DetectionConfig
    from src.satchat.debris_detection_pipeline import MarineDebrisDetectionPipeline
    ADVANCED_DETECTION = True
    print("✅ Advanced detection modules loaded")
except ImportError:
    ADVANCED_DETECTION = False
    print("ℹ️ Advanced detection modules not available, using enhanced mock data")

app = FastAPI(title="SatChat Test API - Advanced", version="0.2.0")

# CORS 설정 - Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize advanced detection if available
detection_pipeline = None
if ADVANCED_DETECTION:
    # Use dummy credentials for testing
    sentinel_client = SentinelHubAdvanced("test_client_id", "test_client_secret")
    detection_pipeline = MarineDebrisDetectionPipeline(sentinel_client)

@app.get("/")
async def root():
    """API 상태 및 GitHub Actions 데이터 수집 정보"""
    # Check if we have GitHub Actions data
    github_data_exists = os.path.exists("data/dashboard/dashboard.json")
    last_github_update = None
    
    if github_data_exists:
        try:
            with open("data/dashboard/dashboard.json", 'r', encoding='utf-8') as f:
                dashboard = json.load(f)
                last_github_update = dashboard.get('last_update')
        except:
            pass
    
    return {
        "message": "SatChat API 테스트 서버",
        "status": "running",
        "version": "0.2.0",
        "features": {
            "advanced_detection": ADVANCED_DETECTION,
            "github_actions_data": github_data_exists,
            "last_github_update": last_github_update,
            "spectral_analysis": True,
            "real_time_monitoring": True
        }
    }

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/api/v1/auth/login")
async def login(credentials: Dict[str, str]):
    return {
        "access_token": "test_token_12345",
        "token_type": "bearer",
        "user": {
            "id": 1,
            "email": credentials.get("email", "user@test.com"),
            "name": "테스트 사용자",
            "role": "admin"
        }
    }

@app.get("/api/v1/detections")
async def get_detections():
    """Get marine debris detections with advanced spectral analysis"""
    
    if ADVANCED_DETECTION and detection_pipeline:
        # Run actual detection cycle
        try:
            detections = await detection_pipeline.run_detection_cycle('all')
            return [
                {
                    "id": d.id,
                    "latitude": d.location['latitude'],
                    "longitude": d.location['longitude'],
                    "debris_type": d.debris_type,
                    "confidence": d.ml_confidence,
                    "detection_time": d.timestamp.isoformat(),
                    "patch_size": d.patch_size,
                    "priority": d.priority,
                    "region": d.region,
                    "spectral_indices": d.spectral_indices,
                    "verification_status": d.verification_status
                }
                for d in detections[:10]  # Return latest 10 detections
            ]
        except Exception as e:
            print(f"Detection error: {e}")
            # Fall back to enhanced mock data
    
    # Enhanced mock data based on research
    return [
        {
            "id": "west_sea_20241122_0001",
            "latitude": 36.5,
            "longitude": 126.2,
            "debris_type": "플라스틱 (Plastic)",
            "confidence": 0.92,
            "detection_time": datetime.now().isoformat(),
            "patch_size": 450.5,  # m²
            "priority": "high",
            "region": "서해",
            "spectral_indices": {
                "fdi": 0.035,  # Floating Debris Index
                "ndvi": 0.08,
                "ndwi": 0.42,
                "fai": 0.028
            },
            "verification_status": "unverified"
        },
        {
            "id": "south_sea_20241122_0002",
            "latitude": 34.8,
            "longitude": 128.3,
            "debris_type": "어망/로프 (Fishing nets/Ropes)",
            "confidence": 0.85,
            "detection_time": datetime.now().isoformat(),
            "patch_size": 280.0,
            "priority": "high",
            "region": "남해",
            "spectral_indices": {
                "fdi": 0.025,
                "ndvi": 0.15,
                "ndwi": 0.38,
                "fai": 0.022
            },
            "verification_status": "unverified"
        },
        {
            "id": "east_sea_20241122_0003",
            "latitude": 37.2,
            "longitude": 129.8,
            "debris_type": "혼합 폐기물 (Mixed debris)",
            "confidence": 0.78,
            "detection_time": datetime.now().isoformat(),
            "patch_size": 120.5,
            "priority": "medium",
            "region": "동해",
            "spectral_indices": {
                "fdi": 0.018,
                "ndvi": 0.22,
                "ndwi": 0.35,
                "fai": 0.015
            },
            "verification_status": "unverified"
        }
    ]

@app.get("/api/v1/statistics")
async def get_statistics():
    """Get enhanced statistics with spectral analysis metrics"""
    
    if ADVANCED_DETECTION and detection_pipeline:
        # Get actual metrics from pipeline
        metrics = detection_pipeline.get_performance_metrics()
        stats = detection_pipeline.sentinel.get_detection_statistics(
            [d.to_dict() for d in detection_pipeline.detection_history]
        )
        
        return {
            "total_detections": metrics['total_detections'],
            "active_alerts": metrics['alerts_generated'],
            "monitored_area": 25000,  # km²
            "detection_rate": metrics.get('detection_rate', 0) * 100,
            "average_processing_time": metrics.get('average_processing_time', 0),
            "by_debris_type": stats.get('by_type', {}),
            "by_region": stats.get('by_region', {}),
            "by_priority": stats.get('by_priority', {}),
            "total_debris_area": stats.get('total_area', 0),
            "average_confidence": stats.get('average_confidence', 0),
            "spectral_indices_performance": {
                "fdi_detections": "35%",  # Primary indicator
                "ndwi_accuracy": "92%",
                "multi_index_validation": "87%"
            }
        }
    
    # Enhanced mock statistics
    return {
        "total_detections": 142,
        "active_alerts": 7,
        "monitored_area": 25000,  # km²
        "detection_rate": 89.3,  # %
        "average_processing_time": 2.5,  # seconds
        "by_debris_type": {
            "플라스틱 (Plastic)": 64,
            "어망/로프 (Fishing nets/Ropes)": 43,
            "혼합 폐기물 (Mixed debris)": 35
        },
        "by_region": {
            "서해": 58,
            "남해": 52,
            "동해": 32
        },
        "by_priority": {
            "critical": 5,
            "high": 12,
            "medium": 35,
            "low": 90
        },
        "total_debris_area": 45600,  # m²
        "average_confidence": 0.82,
        "spectral_indices_performance": {
            "fdi_detections": "35%",
            "ndwi_accuracy": "92%",
            "multi_index_validation": "87%"
        }
    }

@app.get("/api/v1/alerts")
async def get_alerts():
    """Get alerts with priority based on spectral analysis"""
    
    if ADVANCED_DETECTION and detection_pipeline:
        # Return actual alerts from pipeline
        return detection_pipeline.alert_queue[:10]  # Latest 10 alerts
    
    # Enhanced mock alerts based on research
    return [
        {
            "id": "ALERT_west_sea_20241122_0001",
            "priority": "critical",
            "title": "CRITICAL: 대규모 플라스틱 집적 탐지",
            "message": "서해 충남 연안 (36.5°N, 126.2°E)에서 450m² 규모의 플라스틱 폐기물이 탐지되었습니다. FDI 지수 0.035 (임계값 초과). 신뢰도: 92%",
            "created_at": datetime.now().isoformat(),
            "detection_id": "west_sea_20241122_0001",
            "action_required": "즉각적인 정화 작업 필요. 해양 당국에 연락 요망.",
            "spectral_alert": {
                "fdi_exceeded": True,
                "confidence_level": "high",
                "verification_needed": False
            }
        },
        {
            "id": "ALERT_south_sea_20241122_0002",
            "priority": "high",
            "title": "HIGH: 어망 위험 탐지",
            "message": "남해 거제도 인근 (34.8°N, 128.3°E)에서 280m² 규모의 폐어망이 탐지되었습니다. 선박 항행 위험. 신뢰도: 85%",
            "created_at": datetime.now().isoformat(),
            "detection_id": "south_sea_20241122_0002",
            "action_required": "어망 위험 - 지역 어선 및 해경에 통보 필요.",
            "spectral_alert": {
                "fdi_exceeded": True,
                "confidence_level": "high",
                "verification_needed": True
            }
        },
        {
            "id": "ALERT_east_sea_20241122_0003",
            "priority": "medium",
            "title": "MEDIUM: 혼합 폐기물 감지",
            "message": "동해 강원 연안 (37.2°N, 129.8°E)에서 120m² 규모의 혼합 폐기물이 탐지되었습니다. 신뢰도: 78%",
            "created_at": datetime.now().isoformat(),
            "detection_id": "east_sea_20241122_0003",
            "action_required": "모니터링 및 다음 정기 정화 일정에 포함.",
            "spectral_alert": {
                "fdi_exceeded": False,
                "confidence_level": "medium",
                "verification_needed": True
            }
        }
    ]

@app.get("/api/v1/spectral-analysis")
async def get_spectral_analysis():
    """Get detailed spectral analysis for detection validation"""
    return {
        "analysis_method": "Multi-spectral Index Analysis",
        "indices_used": [
            {
                "name": "FDI",
                "full_name": "Floating Debris Index",
                "description": "Primary indicator for plastic detection",
                "threshold": 0.02,
                "importance": "35%",
                "formula": "NIR - (RED + (NIR_narrow - RED) * (833 - 665) / (865 - 665))"
            },
            {
                "name": "NDWI",
                "full_name": "Normalized Difference Water Index",
                "description": "Water body identification",
                "threshold": 0.3,
                "importance": "25%",
                "formula": "(GREEN - NIR) / (GREEN + NIR)"
            },
            {
                "name": "NDVI",
                "full_name": "Normalized Difference Vegetation Index",
                "description": "Distinguish debris from vegetation",
                "threshold": -0.1,
                "importance": "20%",
                "formula": "(NIR - RED) / (NIR + RED)"
            },
            {
                "name": "FAI",
                "full_name": "Floating Algae Index",
                "description": "Distinguish algae from plastic",
                "threshold": 0.01,
                "importance": "10%",
                "formula": "NIR - (RED + (SWIR1 - RED) * (833 - 665) / (1610 - 665))"
            }
        ],
        "validation_metrics": {
            "precision": 0.87,
            "recall": 0.82,
            "f1_score": 0.84,
            "false_positive_rate": 0.13
        },
        "optimal_conditions": {
            "cloud_coverage": "< 20%",
            "sun_angle": "30-60°",
            "wind_speed": "< 10 m/s",
            "wave_height": "< 2m"
        }
    }

@app.get("/api/v1/regions")
async def get_regions():
    """Get monitored regions with priority zones"""
    return {
        "regions": [
            {
                "id": "west_sea",
                "name": "서해 (West Sea)",
                "bbox": [124.0, 33.0, 127.0, 39.0],
                "priority_zones": [
                    {
                        "name": "충남 연안",
                        "bbox": [125.5, 36.5, 126.5, 37.5],
                        "risk_level": "high",
                        "monitoring_frequency": "daily"
                    },
                    {
                        "name": "경기만",
                        "bbox": [126.0, 37.0, 127.0, 38.0],
                        "risk_level": "critical",
                        "monitoring_frequency": "twice daily"
                    }
                ],
                "current_detections": 58,
                "avg_debris_size": 320.5
            },
            {
                "id": "south_sea",
                "name": "남해 (South Sea)",
                "bbox": [126.0, 32.0, 130.0, 35.0],
                "priority_zones": [
                    {
                        "name": "부산 연안",
                        "bbox": [127.5, 34.0, 128.5, 35.0],
                        "risk_level": "high",
                        "monitoring_frequency": "daily"
                    },
                    {
                        "name": "거제도 주변",
                        "bbox": [128.0, 33.5, 129.0, 34.5],
                        "risk_level": "medium",
                        "monitoring_frequency": "every 2 days"
                    }
                ],
                "current_detections": 52,
                "avg_debris_size": 280.0
            },
            {
                "id": "east_sea",
                "name": "동해 (East Sea)",
                "bbox": [128.0, 35.0, 132.0, 38.5],
                "priority_zones": [
                    {
                        "name": "울산 연안",
                        "bbox": [129.0, 35.5, 130.0, 36.5],
                        "risk_level": "medium",
                        "monitoring_frequency": "every 2 days"
                    },
                    {
                        "name": "강원 연안",
                        "bbox": [129.5, 37.0, 130.5, 38.0],
                        "risk_level": "low",
                        "monitoring_frequency": "weekly"
                    }
                ],
                "current_detections": 32,
                "avg_debris_size": 150.0
            }
        ],
        "total_monitored_area": 25000,  # km²
        "update_frequency": "6 hours"
    }

@app.get("/api/v1/performance")
async def get_performance():
    """Get system performance metrics"""
    if ADVANCED_DETECTION and detection_pipeline:
        return detection_pipeline.get_performance_metrics()
    
    return {
        "total_detections": 142,
        "detection_rate": 0.89,
        "average_processing_time": 2.5,
        "alerts_generated": 7,
        "regions_monitored": 3,
        "last_update": datetime.now().isoformat(),
        "system_health": "optimal",
        "api_response_time": 0.125,  # seconds
        "satellite_coverage": "95%",
        "data_freshness": "< 6 hours"
    }

@app.get("/api/v1/github-data")
async def get_github_data():
    """Get data collected by GitHub Actions"""
    dashboard_file = "data/dashboard/dashboard.json"
    
    if os.path.exists(dashboard_file):
        try:
            with open(dashboard_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            return {
                "error": "Failed to load GitHub Actions data",
                "message": str(e)
            }
    
    return {
        "message": "No GitHub Actions data available yet",
        "info": "Data will be available after GitHub Actions workflow runs",
        "schedule": "Every 6 hours",
        "manual_trigger": "Available via GitHub Actions UI"
    }

@app.get("/api/v1/github-data/realtime")
async def get_github_realtime():
    """Get real-time statistics from GitHub Actions data"""
    realtime_file = "data/dashboard/realtime.json"
    
    if os.path.exists(realtime_file):
        with open(realtime_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback to mock data
    return {
        "total_detections": 142,
        "active_alerts": 7,
        "monitored_area": 25000,
        "detection_rate": 89.3
    }

@app.get("/api/v1/github-data/map")
async def get_github_map_data():
    """Get map data from GitHub Actions"""
    map_file = "data/dashboard/map_data.json"
    
    if os.path.exists(map_file):
        with open(map_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback to mock data
    return await get_detections()

@app.get("/api/v1/github-data/hotspots")
async def get_github_hotspots():
    """Get hotspot areas from GitHub Actions analysis"""
    hotspots_file = "data/dashboard/hotspots.json"
    
    if os.path.exists(hotspots_file):
        with open(hotspots_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Fallback to mock hotspots
    return [
        {
            "center": {"lat": 36.5, "lon": 126.5},
            "detection_count": 8,
            "total_area": 1250.5,
            "average_confidence": 0.88,
            "region": "서해 - 충남 연안"
        },
        {
            "center": {"lat": 34.8, "lon": 128.3},
            "detection_count": 6,
            "total_area": 980.0,
            "average_confidence": 0.85,
            "region": "남해 - 부산 연안"
        }
    ]

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting SatChat Advanced Detection API Server...")
    print("📡 Sentinel Hub integration: " + ("Enabled" if ADVANCED_DETECTION else "Mock Mode"))
    print("🌊 Monitoring Korean waters with advanced spectral analysis")
    uvicorn.run(app, host="0.0.0.0", port=8000)