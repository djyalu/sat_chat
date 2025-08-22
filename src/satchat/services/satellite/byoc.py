"""Sentinel Hub BYOC (Bring Your Own COG) integration for custom satellite data"""

import logging
import json
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import aiohttp

import boto3
from botocore.exceptions import ClientError
import rasterio
from rasterio.io import MemoryFile
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np

from satchat.core.config import settings
from satchat.services.satellite.sentinel_hub import SentinelHubService

logger = logging.getLogger(__name__)


class BYOCService(SentinelHubService):
    """BYOC service for managing custom satellite data in Sentinel Hub"""
    
    def __init__(self):
        """Initialize BYOC service"""
        super().__init__()
        self.byoc_url = f"{self.base_url}/api/v1/byoc"
        self.collection_name = "Korea Sea"
        self.collection_type = "BYOC"
        self.s3_bucket = "aaron_sat"
        self.s3_region = "us-west-2"  # Oregon
        self.collection_id = None
        
        # Initialize S3 client for Oregon region
        self.s3_client = boto3.client(
            's3',
            region_name=self.s3_region,
            aws_access_key_id=settings.s3_access_key.get_secret_value(),
            aws_secret_access_key=settings.s3_secret_key.get_secret_value()
        )
    
    async def create_collection(self) -> str:
        """Create BYOC collection for Korea Sea"""
        
        token = await self.get_access_token()
        
        collection_data = {
            "name": self.collection_name,
            "s3Bucket": self.s3_bucket,
            "awsRegion": self.s3_region,
            "additionalData": {
                "description": "Marine debris monitoring data for Korean waters",
                "organization": "Telefix",
                "created": datetime.utcnow().isoformat(),
                "contact": "go41@naver.com"
            }
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.byoc_url}/collections",
                json=collection_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    self.collection_id = result.get('id')
                    logger.info(f"Created BYOC collection: {self.collection_id}")
                    return self.collection_id
                else:
                    error = await response.text()
                    logger.error(f"Failed to create collection: {error}")
                    raise Exception(f"Collection creation failed: {error}")
    
    async def get_or_create_collection(self) -> str:
        """Get existing collection or create new one"""
        
        # First, try to get existing collection
        collections = await self.list_collections()
        
        for collection in collections:
            if collection.get('name') == self.collection_name:
                self.collection_id = collection.get('id')
                logger.info(f"Found existing collection: {self.collection_id}")
                return self.collection_id
        
        # Create new collection if not found
        return await self.create_collection()
    
    async def list_collections(self) -> List[Dict[str, Any]]:
        """List all BYOC collections"""
        
        token = await self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.byoc_url}/collections",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('data', [])
                else:
                    error = await response.text()
                    logger.error(f"Failed to list collections: {error}")
                    return []
    
    async def create_tile(
        self,
        collection_id: str,
        tile_path: str,
        sensing_time: datetime,
        coverage_geometry: Dict[str, Any],
        additional_data: Dict[str, Any] = None
    ) -> str:
        """Create a tile in BYOC collection"""
        
        token = await self.get_access_token()
        
        tile_data = {
            "path": tile_path,
            "sensingTime": sensing_time.strftime("%Y-%m-%dT%H:%M:%S"),
            "coverageGeometry": coverage_geometry,
            "ingestionInfo": {
                "ingestionTime": datetime.utcnow().isoformat(),
                "source": "SatChat Processing Pipeline"
            }
        }
        
        if additional_data:
            tile_data["additionalData"] = additional_data
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.byoc_url}/collections/{collection_id}/tiles",
                json=tile_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    tile_id = result.get('id')
                    logger.info(f"Created tile: {tile_id}")
                    return tile_id
                else:
                    error = await response.text()
                    logger.error(f"Failed to create tile: {error}")
                    raise Exception(f"Tile creation failed: {error}")
    
    def prepare_cog(
        self,
        image_array: np.ndarray,
        transform: Any,
        crs: str = 'EPSG:4326',
        bands: int = 3
    ) -> bytes:
        """Prepare Cloud Optimized GeoTIFF from numpy array"""
        
        profile = {
            'driver': 'GTiff',
            'dtype': image_array.dtype,
            'width': image_array.shape[2],
            'height': image_array.shape[1],
            'count': bands,
            'crs': crs,
            'transform': transform,
            'compress': 'deflate',
            'tiled': True,
            'blockxsize': 512,
            'blockysize': 512,
            'interleave': 'band',
            'COPY_SRC_OVERVIEWS': 'YES',
            'COMPRESS_OVERVIEW': 'DEFLATE'
        }
        
        # Create COG in memory
        with MemoryFile() as memfile:
            with memfile.open(**profile) as dst:
                for i in range(bands):
                    dst.write(image_array[i], i + 1)
                
                # Add overviews for COG
                factors = [2, 4, 8, 16]
                dst.build_overviews(factors, Resampling.average)
                dst.update_tags(ns='rio_overview', resampling='average')
            
            return memfile.read()
    
    async def upload_to_s3(
        self,
        cog_data: bytes,
        s3_key: str,
        metadata: Dict[str, str] = None
    ) -> str:
        """Upload COG to S3 bucket"""
        
        try:
            extra_args = {
                'ContentType': 'image/tiff',
                'CacheControl': 'max-age=31536000'
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=s3_key,
                Body=cog_data,
                **extra_args
            )
            
            s3_url = f"s3://{self.s3_bucket}/{s3_key}"
            logger.info(f"Uploaded COG to {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"S3 upload failed: {e}")
            raise
    
    async def ingest_processed_image(
        self,
        image_array: np.ndarray,
        bbox: Tuple[float, float, float, float],
        sensing_time: datetime,
        debris_mask: np.ndarray = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ingest processed image into BYOC collection
        
        Args:
            image_array: Processed image array (bands, height, width)
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            sensing_time: Image acquisition time
            debris_mask: Optional debris detection mask
            metadata: Additional metadata
        
        Returns:
            Ingestion result with tile ID and S3 path
        """
        
        # Ensure collection exists
        collection_id = await self.get_or_create_collection()
        
        # Generate unique tile ID
        tile_id = hashlib.md5(
            f"{sensing_time.isoformat()}_{bbox}".encode()
        ).hexdigest()[:12]
        
        # Prepare S3 key
        date_str = sensing_time.strftime("%Y/%m/%d")
        s3_key = f"korea_sea/{date_str}/{tile_id}.tif"
        
        # Calculate transform
        from rasterio.transform import from_bounds
        transform = from_bounds(
            bbox[0], bbox[1], bbox[2], bbox[3],
            image_array.shape[2], image_array.shape[1]
        )
        
        # Prepare COG
        cog_data = self.prepare_cog(
            image_array,
            transform,
            bands=image_array.shape[0]
        )
        
        # Upload to S3
        s3_url = await self.upload_to_s3(
            cog_data,
            s3_key,
            metadata={
                'collection': self.collection_name,
                'sensing_time': sensing_time.isoformat(),
                'debris_detected': str(debris_mask is not None)
            }
        )
        
        # If debris mask exists, upload it too
        debris_s3_url = None
        if debris_mask is not None:
            debris_key = f"korea_sea/{date_str}/{tile_id}_debris.tif"
            debris_cog = self.prepare_cog(
                debris_mask[np.newaxis, :, :],
                transform,
                bands=1
            )
            debris_s3_url = await self.upload_to_s3(
                debris_cog,
                debris_key,
                metadata={'type': 'debris_mask'}
            )
        
        # Create coverage geometry
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
        
        # Create tile in BYOC
        tile_id = await self.create_tile(
            collection_id=collection_id,
            tile_path=s3_key,
            sensing_time=sensing_time,
            coverage_geometry=coverage_geometry,
            additional_data={
                **metadata,
                'debris_mask_path': debris_key if debris_mask is not None else None,
                'processed_by': 'SatChat',
                'processing_time': datetime.utcnow().isoformat()
            }
        )
        
        return {
            'collection_id': collection_id,
            'tile_id': tile_id,
            's3_url': s3_url,
            'debris_mask_url': debris_s3_url,
            'bbox': bbox,
            'sensing_time': sensing_time.isoformat()
        }
    
    async def query_collection(
        self,
        bbox: Tuple[float, float, float, float],
        time_range: Tuple[datetime, datetime],
        max_cloud_coverage: float = 100
    ) -> List[Dict[str, Any]]:
        """Query BYOC collection for tiles
        
        Args:
            bbox: Bounding box
            time_range: Time range (start, end)
            max_cloud_coverage: Maximum cloud coverage
        
        Returns:
            List of matching tiles
        """
        
        collection_id = await self.get_or_create_collection()
        token = await self.get_access_token()
        
        query_params = {
            "bbox": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}",
            "datetime": f"{time_range[0].isoformat()}/{time_range[1].isoformat()}",
            "maxCloudCoverage": max_cloud_coverage
        }
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.byoc_url}/collections/{collection_id}/tiles",
                params=query_params,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('features', [])
                else:
                    error = await response.text()
                    logger.error(f"Query failed: {error}")
                    return []
    
    def create_byoc_evalscript(self) -> str:
        """Create evalscript for BYOC data visualization and analysis"""
        
        return """
        //VERSION=3
        // BYOC Marine Debris Detection Script
        
        function setup() {
            return {
                input: ["B01", "B02", "B03", "B04", "dataMask"],
                output: [
                    {
                        id: "default",
                        bands: 3,
                        sampleType: "AUTO"
                    },
                    {
                        id: "debris_highlight",
                        bands: 4,
                        sampleType: "AUTO"
                    },
                    {
                        id: "indices",
                        bands: 2,
                        sampleType: "FLOAT32"
                    }
                ]
            };
        }
        
        function evaluatePixel(sample) {
            // Basic RGB visualization
            let rgb = [sample.B03, sample.B02, sample.B01];
            
            // Calculate custom indices if NIR band available
            let ndvi = 0;
            let debris_index = 0;
            
            if (sample.B04) {
                // NDVI calculation
                ndvi = (sample.B04 - sample.B03) / (sample.B04 + sample.B03 + 0.001);
                
                // Custom debris index
                debris_index = (sample.B04 - sample.B02) / (sample.B04 + sample.B02 + 0.001);
            }
            
            // Highlight potential debris
            let highlight = rgb;
            if (debris_index > 0.1) {
                highlight = [1, 0.2, 0.2];  // Red highlight
            }
            
            return {
                default: rgb,
                debris_highlight: [...highlight, sample.dataMask],
                indices: [ndvi, debris_index]
            };
        }
        """