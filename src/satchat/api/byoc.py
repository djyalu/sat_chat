"""BYOC (Bring Your Own COG) API endpoints for custom satellite data management"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from uuid import UUID
import numpy as np

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from satchat.core.database import get_async_db
from satchat.models.database import User, SatelliteImage
from satchat.api.auth import get_current_active_user
from satchat.services.satellite.byoc import BYOCService

router = APIRouter()


@router.get("/collection/info")
async def get_collection_info(
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get BYOC collection information"""
    
    return {
        "collection_id": "3bea22f5-2445-4a19-ba88-ced6571aef09",
        "collection_name": "Korea Sea",
        "type": "BYOC",
        "s3_bucket": "aaron_sat",
        "s3_region": "us-west-2 (Oregon)",
        "organization_id": "WS_5a8204bc-452c-454f-b068-b65ee4822073",
        "description": "Marine debris monitoring data for Korean waters",
        "created_by": "Telefix",
        "contact": "go41@naver.com"
    }


@router.get("/collections")
async def list_collections(
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """List all BYOC collections"""
    
    byoc_service = BYOCService()
    
    try:
        collections = await byoc_service.list_collections()
        return collections
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list collections: {str(e)}"
        )


@router.post("/ingest")
async def ingest_processed_data(
    background_tasks: BackgroundTasks,
    bbox: List[float] = Query(..., description="Bounding box [min_lon, min_lat, max_lon, max_lat]"),
    sensing_time: datetime = Query(..., description="Image acquisition time"),
    image_id: Optional[UUID] = Query(None, description="Source image ID"),
    has_debris: bool = Query(False, description="Whether debris was detected"),
    confidence: float = Query(0.0, ge=0.0, le=1.0, description="Detection confidence"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Ingest processed data into BYOC collection"""
    
    # Check permissions
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Validate bbox
    if len(bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bbox must have 4 values: [min_lon, min_lat, max_lon, max_lat]"
        )
    
    # Schedule ingestion task
    background_tasks.add_task(
        ingest_to_byoc,
        bbox=tuple(bbox),
        sensing_time=sensing_time,
        image_id=str(image_id) if image_id else None,
        has_debris=has_debris,
        confidence=confidence
    )
    
    return {
        "message": "Data ingestion scheduled",
        "collection_id": "3bea22f5-2445-4a19-ba88-ced6571aef09",
        "bbox": bbox,
        "sensing_time": sensing_time.isoformat(),
        "status": "processing"
    }


@router.get("/query")
async def query_byoc_data(
    bbox: List[float] = Query(None, description="Bounding box [min_lon, min_lat, max_lon, max_lat]"),
    start_date: datetime = Query(..., description="Start date"),
    end_date: datetime = Query(None, description="End date"),
    max_cloud: float = Query(100, ge=0, le=100, description="Max cloud coverage"),
    current_user: User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """Query BYOC collection for tiles"""
    
    # Set defaults
    if not end_date:
        end_date = datetime.utcnow()
    
    if not bbox:
        # Default to all Korean waters
        bbox = [124.0, 32.0, 132.0, 39.0]
    
    # Validate bbox
    if len(bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bbox must have 4 values"
        )
    
    byoc_service = BYOCService()
    
    try:
        tiles = await byoc_service.query_collection(
            bbox=tuple(bbox),
            time_range=(start_date, end_date),
            max_cloud_coverage=max_cloud
        )
        
        return tiles
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/upload-cog")
async def upload_cog_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sensing_time: datetime = Query(..., description="Image acquisition time"),
    bbox: List[float] = Query(..., description="Bounding box [min_lon, min_lat, max_lon, max_lat]"),
    debris_detected: bool = Query(False, description="Whether debris was detected"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Upload COG file directly to BYOC collection"""
    
    # Check permissions
    if current_user.role not in ["admin", "operator"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and operators can upload data"
        )
    
    # Validate file type
    if not file.filename.lower().endswith(('.tif', '.tiff')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only GeoTIFF files are supported"
        )
    
    # Validate bbox
    if len(bbox) != 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Bbox must have 4 values"
        )
    
    # Read file content
    content = await file.read()
    
    # Schedule upload task
    background_tasks.add_task(
        upload_cog_to_byoc,
        file_content=content,
        filename=file.filename,
        bbox=tuple(bbox),
        sensing_time=sensing_time,
        debris_detected=debris_detected
    )
    
    return {
        "message": "COG upload scheduled",
        "filename": file.filename,
        "collection_id": "3bea22f5-2445-4a19-ba88-ced6571aef09",
        "bbox": bbox,
        "sensing_time": sensing_time.isoformat(),
        "status": "uploading"
    }


@router.get("/visualize/{tile_id}")
async def visualize_tile(
    tile_id: str,
    width: int = Query(512, ge=256, le=2048, description="Output width"),
    height: int = Query(512, ge=256, le=2048, description="Output height"),
    format: str = Query("png", description="Output format (png or tiff)"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Generate visualization URL for BYOC tile"""
    
    byoc_service = BYOCService()
    
    # Get collection ID
    collection_id = "3bea22f5-2445-4a19-ba88-ced6571aef09"
    
    # Create visualization request
    evalscript = byoc_service.create_byoc_evalscript()
    
    # Generate Process API request
    process_request = {
        "input": {
            "bounds": {
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                }
            },
            "data": [{
                "type": collection_id,
                "dataFilter": {
                    "tileId": tile_id
                }
            }]
        },
        "output": {
            "width": width,
            "height": height,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": f"image/{format}"
                }
            }]
        },
        "evalscript": evalscript
    }
    
    return {
        "tile_id": tile_id,
        "collection_id": collection_id,
        "visualization_config": process_request,
        "description": "Use this configuration with Sentinel Hub Process API to visualize the tile"
    }


@router.get("/statistics")
async def get_byoc_statistics(
    days_back: int = Query(30, ge=1, le=365, description="Days to analyze"),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Get statistics for BYOC collection"""
    
    byoc_service = BYOCService()
    
    # Calculate time range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Query all tiles in time range
    tiles = await byoc_service.query_collection(
        bbox=(124.0, 32.0, 132.0, 39.0),  # All Korean waters
        time_range=(start_date, end_date),
        max_cloud_coverage=100
    )
    
    # Calculate statistics
    total_tiles = len(tiles)
    debris_tiles = sum(1 for t in tiles if t.get('properties', {}).get('debris_detected'))
    
    # Group by date
    tiles_by_date = {}
    for tile in tiles:
        date = tile.get('properties', {}).get('datetime', '').split('T')[0]
        if date:
            tiles_by_date[date] = tiles_by_date.get(date, 0) + 1
    
    return {
        "collection_id": "3bea22f5-2445-4a19-ba88-ced6571aef09",
        "time_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "statistics": {
            "total_tiles": total_tiles,
            "debris_detections": debris_tiles,
            "detection_rate": debris_tiles / total_tiles if total_tiles > 0 else 0,
            "tiles_by_date": tiles_by_date,
            "average_tiles_per_day": total_tiles / days_back if days_back > 0 else 0
        }
    }


# Background task functions
async def ingest_to_byoc(
    bbox: tuple,
    sensing_time: datetime,
    image_id: Optional[str],
    has_debris: bool,
    confidence: float
):
    """Background task to ingest data to BYOC"""
    byoc_service = BYOCService()
    
    # Create dummy data for demonstration
    # In production, this would process actual satellite imagery
    height, width = 512, 512
    image_array = np.random.randint(0, 255, (3, height, width), dtype=np.uint8)
    
    if has_debris:
        debris_mask = np.random.randint(0, 2, (height, width), dtype=np.uint8) * 255
    else:
        debris_mask = None
    
    metadata = {
        "source_image_id": image_id,
        "debris_detected": has_debris,
        "confidence": confidence,
        "processing_timestamp": datetime.utcnow().isoformat()
    }
    
    await byoc_service.ingest_processed_image(
        image_array=image_array,
        bbox=bbox,
        sensing_time=sensing_time,
        debris_mask=debris_mask,
        metadata=metadata
    )


async def upload_cog_to_byoc(
    file_content: bytes,
    filename: str,
    bbox: tuple,
    sensing_time: datetime,
    debris_detected: bool
):
    """Background task to upload COG file to BYOC"""
    byoc_service = BYOCService()
    
    # Generate S3 key
    date_str = sensing_time.strftime("%Y/%m/%d")
    s3_key = f"korea_sea/{date_str}/{filename}"
    
    # Upload to S3
    await byoc_service.upload_to_s3(
        cog_data=file_content,
        s3_key=s3_key,
        metadata={
            "filename": filename,
            "debris_detected": str(debris_detected),
            "upload_time": datetime.utcnow().isoformat()
        }
    )
    
    # Create tile in BYOC
    coverage_geometry = {
        "type": "Polygon",
        "coordinates": [[
            [bbox[0], bbox[1]],
            [bbox[2], bbox[1]],
            [bbox[2], bbox[3]],
            [bbox[0], bbox[3]],
            [bbox[0], bbox[1]]
        ]]
    }
    
    await byoc_service.create_tile(
        collection_id="3bea22f5-2445-4a19-ba88-ced6571aef09",
        tile_path=s3_key,
        sensing_time=sensing_time,
        coverage_geometry=coverage_geometry,
        additional_data={
            "original_filename": filename,
            "debris_detected": debris_detected
        }
    )