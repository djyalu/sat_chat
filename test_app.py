"""간단한 테스트용 FastAPI 서버"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List
from datetime import datetime

app = FastAPI(title="SatChat Test API", version="0.1.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SatChat API 테스트 서버", "status": "running"}

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
    return [
        {
            "id": 1,
            "lat": 34.5,
            "lng": 126.8,
            "type": "플라스틱",
            "confidence": 0.92,
            "time": "2시간 전",
            "size": "large"
        },
        {
            "id": 2,
            "lat": 35.2,
            "lng": 129.1,
            "type": "어망",
            "confidence": 0.85,
            "time": "5시간 전",
            "size": "medium"
        }
    ]

@app.get("/api/v1/statistics")
async def get_statistics():
    return {
        "total_detections": 142,
        "active_alerts": 7,
        "monitored_area": 25000,
        "detection_rate": 89.3
    }

@app.get("/api/v1/alerts")
async def get_alerts():
    return [
        {
            "id": 1,
            "type": "critical",
            "title": "대규모 폐기물 집적 탐지",
            "description": "서해 인천 해역에서 대규모 플라스틱 폐기물 집적이 탐지되었습니다.",
            "location": "서해 인천 해역",
            "time": "10분 전",
            "status": "active"
        }
    ]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)