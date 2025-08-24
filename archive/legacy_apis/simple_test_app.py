#!/usr/bin/env python3
"""
Minimal FastAPI app for Render deployment testing
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="SatChat Test API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "success",
        "message": "SatChat Test API is running!",
        "port": os.getenv("PORT", "unknown"),
        "python_version": "3.11.6"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SatChat Test API"
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)