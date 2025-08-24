"""
Minimal FastAPI app for Render deployment
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI(title="SatChat API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "SatChat API",
        "status": "running",
        "message": "Deploy successful!"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}