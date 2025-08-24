"""
Simple FastAPI app for Render deployment testing
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

app = FastAPI(title="SatChat Simple API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "service": "SatChat Simple API", 
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "environment": "production" if os.environ.get("PORT") else "development"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/test")
async def test():
    return {
        "message": "Test endpoint working",
        "port": os.environ.get("PORT", "8002"),
        "python_version": "3.13+"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    host = "0.0.0.0"
    print(f"🚀 Starting Simple App on {host}:{port}")
    uvicorn.run("simple_app:app", host=host, port=port, reload=False)