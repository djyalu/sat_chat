from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Create FastAPI app
app = FastAPI(
    title="SatChat API",
    description="Marine Debris Monitoring System",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "SatChat API",
        "timestamp": datetime.now().isoformat(),
        "port": os.getenv("PORT", "8000")
    }

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SatChat"}

@app.get("/region/{region_name}")
def get_region(region_name: str):
    """Get region information"""
    regions = {
        "west_sea": {"name": "West Sea", "status": "monitoring"},
        "south_sea": {"name": "South Sea", "status": "monitoring"},
        "east_sea": {"name": "East Sea", "status": "monitoring"}
    }
    return regions.get(region_name, {"error": "Region not found"})

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
