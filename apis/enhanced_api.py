#!/usr/bin/env python3
"""Enhanced Marine Debris Monitoring API - Multi-Index Integration"""

import os
import io
import base64
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from PIL import Image
from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import asyncio

# Enhanced components
from src.satchat.processing.multi_index_analyzer import MultiIndexAnalyzer
from src.satchat.ml.marine_segmentation import MarineSegmentationML
from src.satchat.services.tile_service import TileService
from src.satchat.services.batch_processor import BatchProcessor, ValidationLevel
from src.satchat.validation.field_validation import FieldValidationSystem, FieldObservation, ConfidenceLevel

# Original Sentinel integration
from sentinelhub import (
    SHConfig, CRS, BBox, DataCollection,
    SentinelHubRequest, MimeType
)

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enhanced SatChat Marine Debris Monitoring API", 
    version="2.0.0",
    description="Multi-index satellite imagery analysis for marine debris detection"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enhanced components initialization
analyzer = MultiIndexAnalyzer()
ml_segmentation = MarineSegmentationML()
tile_service = TileService()
batch_processor = BatchProcessor()
validation_system = FieldValidationSystem()

# Korea regions (enhanced with more locations)
KOREA_REGIONS = {
    "west_sea": {
        "name": "서해 (인천 근해)",
        "bbox": [124.5, 35.5, 126.5, 37.5],
        "priority": "high"
    },
    "south_sea": {
        "name": "남해 (거제도 근해)", 
        "bbox": [128.4, 34.6, 128.8, 35.0],
        "priority": "critical"
    },
    "east_sea": {
        "name": "동해 (울산 근해)",
        "bbox": [129.0, 35.5, 130.0, 36.5],
        "priority": "medium"
    },
    "busan_port": {
        "name": "부산항 일대",
        "bbox": [129.0, 35.0, 129.2, 35.2],
        "priority": "critical"
    },
    "incheon_port": {
        "name": "인천항 일대", 
        "bbox": [126.5, 37.4, 126.7, 37.6],
        "priority": "high"
    }
}

# Pydantic models
class AnalysisRequest(BaseModel):
    region: str
    analysis_types: List[str] = ["fdi", "ndwi", "mci", "debris_ml"]
    validation_level: str = "medium"
    include_tiles: bool = False

class BatchJobRequest(BaseModel):
    name: str
    regions: List[str]
    time_range_days: int = 7
    analysis_types: List[str] = ["fdi", "ndwi", "mci", "debris_ml"]
    priority: int = 5

class FieldObservationRequest(BaseModel):
    location: List[float]  # [lat, lon]
    debris_present: bool
    debris_density: str
    debris_types: List[str]
    observer: str
    confidence: str

def get_sentinel_config():
    """Get Sentinel Hub configuration"""
    config = SHConfig()
    config.sh_client_id = os.getenv('SENTINEL_HUB_CLIENT_ID')
    config.sh_client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET')
    config.sh_base_url = 'https://services.sentinel-hub.com'
    config.sh_token_url = 'https://services.sentinel-hub.com/oauth/token'
    return config

def get_enhanced_sentinel_data(region_name: str) -> np.ndarray:
    """Get enhanced Sentinel-2 data with all required bands"""
    
    if region_name not in KOREA_REGIONS:
        raise ValueError(f"Unknown region: {region_name}")
    
    region = KOREA_REGIONS[region_name]
    config = get_sentinel_config()
    
    bbox = BBox(bbox=region['bbox'], crs=CRS.WGS84)
    time_interval = (datetime.now() - timedelta(days=14), datetime.now())
    
    # Enhanced evalscript for multi-index analysis
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12", "SCL"]
            }],
            output: [{
                id: "default",
                bands: 12,
                sampleType: "FLOAT32"
            }]
        };
    }
    
    function evaluatePixel(sample) {
        // Cloud masking
        if (sample.SCL == 3 || sample.SCL == 9 || sample.SCL == 8) {
            return [0,0,0,0,0,0,0,0,0,0,0,0];
        }
        
        return [
            sample.B01,  // Coastal aerosol
            sample.B02,  // Blue
            sample.B03,  // Green  
            sample.B04,  // Red
            sample.B05,  // Red Edge 1
            sample.B06,  // Red Edge 2
            sample.B07,  // Red Edge 3
            sample.B08,  // NIR
            sample.B8A,  // NIR narrow
            sample.B09,  // Water vapour
            sample.B11,  // SWIR 1
            sample.B12   // SWIR 2
        ];
    }
    """
    
    request = SentinelHubRequest(
        evalscript=evalscript,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=0.3
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=bbox,
        size=[512, 512],
        config=config
    )
    
    logger.info(f"📡 Downloading enhanced 12-band Sentinel-2 data for {region_name}...")
    data = request.get_data()
    
    if not data or len(data) == 0:
        raise ValueError("No data received from Sentinel Hub")
    
    enhanced_data = data[0]
    logger.info(f"✅ Received enhanced data: {enhanced_data.shape}, {enhanced_data.dtype}")
    
    return enhanced_data

def array_to_base64(arr: np.ndarray) -> str:
    """Convert NumPy array to Base64 image"""
    if arr.max() <= 1.0:
        arr = (arr * 255).astype(np.uint8)
    else:
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode()

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "service": "Enhanced SatChat Marine Debris Monitoring API",
        "version": "2.0.0",
        "status": "operational",
        "capabilities": {
            "multi_index_analysis": ["FDI", "NDWI", "NDVI", "MCI", "FAI", "Turbidity"],
            "ml_segmentation": "MARIDA-based classification",
            "tile_service": "OGC/XYZ compliant",
            "batch_processing": "Large-scale monitoring",
            "field_validation": "Ground truth integration"
        },
        "regions": list(KOREA_REGIONS.keys()),
        "endpoints": {
            "analysis": "/region/{region_name}",
            "enhanced_analysis": "/enhanced/region/{region_name}",
            "tiles": "/tiles/{layer}/{z}/{x}/{y}.png",
            "batch_jobs": "/batch/jobs",
            "field_observations": "/field/observations",
            "validation": "/validation/checklist"
        }
    }

@app.get("/enhanced/region/{region_name}")
async def get_enhanced_region_data(
    region_name: str,
    analysis_types: List[str] = Query(default=["fdi", "ndwi", "mci", "debris_ml"]),
    validation_level: str = Query(default="medium"),
    include_tiles: bool = Query(default=False)
):
    """Enhanced region analysis with multi-index processing"""
    
    try:
        # Get enhanced satellite data
        sentinel_data = get_enhanced_sentinel_data(region_name)
        
        # Multi-index analysis
        logger.info("🔬 Running multi-index analysis...")
        indices = analyzer.calculate_multi_indices(sentinel_data)
        
        # ML-based segmentation
        ml_results = {}
        if "debris_ml" in analysis_types and ml_segmentation.is_trained:
            logger.info("🤖 Running ML segmentation...")
            segmentation, confidence = ml_segmentation.predict_segmentation(sentinel_data, indices)
            ml_results = ml_segmentation.analyze_marine_debris(segmentation, confidence)
        
        # Prepare analysis results
        analysis_data = {}
        
        for analysis_type in analysis_types:
            if analysis_type in indices:
                index_data = indices[analysis_type]
                analysis_data[analysis_type] = {
                    'mean': float(np.mean(index_data)),
                    'std': float(np.std(index_data)),
                    'min': float(np.min(index_data)),
                    'max': float(np.max(index_data)),
                    'percentile_95': float(np.percentile(index_data, 95))
                }
                
                # Add specific analysis for debris detection
                if analysis_type == 'fdi':
                    debris_mask = index_data > 0.1
                    analysis_data[analysis_type].update({
                        'debris_area_km2': float(np.sum(debris_mask) * 0.01),
                        'debris_percentage': float(np.sum(debris_mask) / index_data.size * 100),
                        'high_confidence_debris': float(np.sum(index_data > 0.2) * 0.01)
                    })
                    
                elif analysis_type == 'ndwi':
                    water_mask = index_data > 0
                    analysis_data[analysis_type].update({
                        'water_area_km2': float(np.sum(water_mask) * 0.01),
                        'water_percentage': float(np.sum(water_mask) / index_data.size * 100)
                    })
        
        # Add ML results
        if ml_results:
            analysis_data['debris_ml'] = ml_results
        
        # Field validation
        logger.info("✅ Running field validation...")
        mission_data = {
            'id': f"{region_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'region': KOREA_REGIONS[region_name],
            'analysis_data': analysis_data,
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'satellite': 'Sentinel-2 L2A',
                'bands_used': 12,
                'spatial_resolution': '10m'
            }
        }
        
        validation_level_enum = {
            'low': ValidationLevel.LOW,
            'medium': ValidationLevel.MEDIUM, 
            'high': ValidationLevel.HIGH,
            'critical': ValidationLevel.CRITICAL
        }.get(validation_level, ValidationLevel.MEDIUM)
        
        validation_checklist = await validation_system.run_validation_checklist(
            mission_data, validation_level_enum
        )
        
        # Generate visualizations
        visualizations = {}
        for analysis_type in analysis_types:
            if analysis_type in indices:
                vis_array = analyzer.create_visualization(indices[analysis_type], analysis_type)
                visualizations[f"image_{analysis_type}"] = array_to_base64(vis_array)
        
        # RGB image
        if sentinel_data.shape[2] >= 4:
            rgb_array = np.stack([
                sentinel_data[..., 3],  # Red (B04)
                sentinel_data[..., 2],  # Green (B03) 
                sentinel_data[..., 1]   # Blue (B02)
            ], axis=-1)
            # Normalize
            rgb_normalized = np.clip(rgb_array / 3000 * 255, 0, 255).astype(np.uint8)
            visualizations["image_rgb"] = array_to_base64(rgb_normalized)
        
        # Prepare final response
        result = {
            "region": region_name,
            "region_name": KOREA_REGIONS[region_name]["name"],
            "timestamp": datetime.now().isoformat(),
            "bbox": KOREA_REGIONS[region_name]["bbox"],
            
            # Enhanced analysis data
            "analysis_data": analysis_data,
            "analysis_types": analysis_types,
            
            # Validation results
            "validation": {
                "level": validation_level,
                "overall_confidence": validation_checklist.overall_confidence,
                "checks_passed": len(validation_checklist.checks_completed),
                "checks_failed": len(validation_checklist.checks_failed),
                "recommendations": validation_checklist.recommendations
            },
            
            # Visualizations
            **visualizations,
            
            # Summary statistics
            "summary": {
                "total_analysis_area_km2": 25 * 25,  # Approximate area
                "processing_time": "Enhanced multi-index analysis",
                "confidence_score": validation_checklist.overall_confidence,
                "data_source": "Sentinel-2 L2A Enhanced (12-band)"
            }
        }
        
        # Add tile URLs if requested
        if include_tiles:
            base_url = "http://localhost:8003/tiles"  # Tile server port
            result["tile_urls"] = {
                analysis_type: f"{base_url}/{analysis_type}/{{z}}/{{x}}/{{y}}.png"
                for analysis_type in analysis_types
            }
        
        logger.info(f"📊 Enhanced Analysis Complete: {len(analysis_types)} indices, confidence: {validation_checklist.overall_confidence:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Enhanced analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Enhanced analysis failed: {str(e)}")

@app.get("/tiles/{layer}/{z}/{x}/{y}.png")
async def get_tile(layer: str, z: int, x: int, y: int):
    """Get map tile for specific layer"""
    
    try:
        tile_data = tile_service.get_tile(layer, z, x, y)
        
        if tile_data is None:
            raise HTTPException(status_code=404, detail="Tile not found")
        
        return Response(content=tile_data, media_type="image/png")
        
    except Exception as e:
        logger.error(f"Tile service error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tiles/{layer}/metadata.json")
async def get_tile_metadata(layer: str):
    """Get tile layer metadata"""
    
    try:
        metadata = tile_service.get_tile_metadata(layer)
        return metadata
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch/jobs")
async def create_batch_job(job_request: BatchJobRequest, background_tasks: BackgroundTasks):
    """Create batch processing job"""
    
    try:
        # Convert region names to region data
        regions_data = []
        for region_name in job_request.regions:
            if region_name in KOREA_REGIONS:
                region_data = KOREA_REGIONS[region_name].copy()
                region_data['id'] = region_name
                regions_data.append(region_data)
        
        # Create time range
        end_time = datetime.now()
        start_time = end_time - timedelta(days=job_request.time_range_days)
        time_range = (start_time.isoformat(), end_time.isoformat())
        
        # Create batch job
        job_id = batch_processor.create_job(
            name=job_request.name,
            regions=regions_data,
            time_range=time_range,
            analysis_types=job_request.analysis_types,
            priority=job_request.priority
        )
        
        return {
            "job_id": job_id,
            "status": "created",
            "message": f"Batch job created with {len(regions_data)} regions",
            "estimated_processing_time_minutes": len(regions_data) * 2
        }
        
    except Exception as e:
        logger.error(f"Batch job creation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/batch/jobs/{job_id}")
async def get_batch_job_status(job_id: str):
    """Get batch job status"""
    
    job_status = batch_processor.get_job_status(job_id)
    
    if job_status is None:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status

@app.get("/batch/jobs")
async def list_batch_jobs(status: Optional[str] = None):
    """List batch jobs"""
    
    status_filter = None
    if status:
        from src.satchat.services.batch_processor import JobStatus
        status_filter = JobStatus(status)
    
    jobs = batch_processor.list_jobs(status_filter)
    
    return {
        "jobs": jobs,
        "total_jobs": len(jobs),
        "system_stats": batch_processor.get_system_stats()
    }

@app.post("/field/observations")
async def add_field_observation(obs_request: FieldObservationRequest):
    """Add field observation"""
    
    try:
        # Convert confidence string to enum
        confidence_mapping = {
            'very_low': ConfidenceLevel.VERY_LOW,
            'low': ConfidenceLevel.LOW,
            'medium': ConfidenceLevel.MEDIUM,
            'high': ConfidenceLevel.HIGH,
            'very_high': ConfidenceLevel.VERY_HIGH
        }
        
        confidence_level = confidence_mapping.get(obs_request.confidence.lower(), ConfidenceLevel.MEDIUM)
        
        # Create field observation
        observation = FieldObservation(
            id=f"obs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            location=tuple(obs_request.location),
            timestamp=datetime.now().isoformat(),
            observation_type="manual",
            debris_present=obs_request.debris_present,
            debris_density=obs_request.debris_density,
            debris_types=obs_request.debris_types,
            photos=[],
            observer=obs_request.observer,
            weather_conditions={},
            confidence=confidence_level
        )
        
        validation_system.add_field_observation(observation)
        
        return {
            "observation_id": observation.id,
            "status": "added",
            "message": "Field observation added successfully"
        }
        
    except Exception as e:
        logger.error(f"Field observation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/field/observations")
async def list_field_observations():
    """List field observations"""
    
    observations = []
    for obs in validation_system.field_observations.values():
        observations.append({
            'id': obs.id,
            'location': obs.location,
            'timestamp': obs.timestamp,
            'debris_present': obs.debris_present,
            'debris_density': obs.debris_density,
            'observer': obs.observer,
            'confidence': obs.confidence.name
        })
    
    return {
        "observations": observations,
        "total_observations": len(observations)
    }

@app.post("/validation/checklist")
async def run_validation_checklist(
    mission_id: str,
    region: str,
    validation_level: str = "medium"
):
    """Run validation checklist for mission"""
    
    try:
        if region not in KOREA_REGIONS:
            raise HTTPException(status_code=400, detail="Invalid region")
        
        # Get recent analysis data (simplified)
        mission_data = {
            'id': mission_id,
            'region': KOREA_REGIONS[region],
            'analysis_data': {},  # Would be populated with actual analysis
            'metadata': {
                'timestamp': datetime.now().isoformat(),
                'region': region
            }
        }
        
        validation_level_enum = {
            'low': ValidationLevel.LOW,
            'medium': ValidationLevel.MEDIUM,
            'high': ValidationLevel.HIGH,
            'critical': ValidationLevel.CRITICAL
        }.get(validation_level, ValidationLevel.MEDIUM)
        
        checklist = await validation_system.run_validation_checklist(
            mission_data, validation_level_enum
        )
        
        return {
            "mission_id": mission_id,
            "validation_level": validation_level,
            "overall_confidence": checklist.overall_confidence,
            "checks_completed": checklist.checks_completed,
            "checks_failed": checklist.checks_failed,
            "recommendations": checklist.recommendations,
            "timestamp": checklist.timestamp
        }
        
    except Exception as e:
        logger.error(f"Validation checklist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/system/status")
async def get_system_status():
    """Get overall system status"""
    
    return {
        "api_version": "2.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "multi_index_analyzer": "operational",
            "ml_segmentation": "trained" if ml_segmentation.is_trained else "untrained",
            "tile_service": "operational",
            "batch_processor": "operational",
            "validation_system": "operational"
        },
        "statistics": {
            "regions_available": len(KOREA_REGIONS),
            "field_observations": len(validation_system.field_observations),
            "active_batch_jobs": len(batch_processor.active_jobs),
            "batch_processor_stats": batch_processor.get_system_stats()
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }

# Start background tasks
@app.on_event("startup")
async def startup_event():
    """Initialize background tasks"""
    logger.info("🚀 Starting Enhanced SatChat API v2.0.0")
    
    # Start batch processor (would normally be in separate process)
    # asyncio.create_task(batch_processor.start_processing())
    
    logger.info("✅ Enhanced API initialized successfully")

if __name__ == "__main__":
    import uvicorn
    print("🛰️ Starting Enhanced SatChat API v2.0.0...")
    print("🔬 Multi-index analysis with ML segmentation")
    print("🗺️ Tile service and batch processing enabled")
    print("✅ Field validation and operational checklists active")
    uvicorn.run(app, host="0.0.0.0", port=8003)