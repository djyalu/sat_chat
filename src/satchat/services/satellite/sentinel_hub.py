"""Sentinel Hub API integration for advanced satellite data processing"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import json
import asyncio
import aiohttp
from pathlib import Path

import numpy as np
from shapely.geometry import Polygon, box
import geopandas as gpd

from satchat.core.config import settings
from satchat.models.database import SatelliteImage, ProcessingStatus
from satchat.services.storage import S3Service

logger = logging.getLogger(__name__)


class SentinelHubService:
    """Sentinel Hub API service for advanced satellite data processing"""
    
    def __init__(self):
        """Initialize Sentinel Hub service"""
        self.client_id = settings.sentinel_hub_client_id
        self.client_secret = settings.sentinel_hub_client_secret
        self.instance_id = settings.sentinel_hub_instance_id
        self.base_url = "https://services.sentinel-hub.com"
        self.oauth_url = "https://services.sentinel-hub.com/oauth/token"
        self.process_url = f"{self.base_url}/api/v1/process"
        self.statistical_url = f"{self.base_url}/api/v1/statistics"
        self.batch_url = f"{self.base_url}/api/v1/batch/process"
        
        self.access_token = None
        self.token_expires_at = None
        self.s3_service = S3Service()
    
    async def get_access_token(self) -> str:
        """Get or refresh Sentinel Hub access token"""
        if self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token
        
        # Request new token
        async with aiohttp.ClientSession() as session:
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret.get_secret_value()
            }
            
            async with session.post(self.oauth_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    expires_in = token_data.get('expires_in', 3600)
                    self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 60)
                    logger.info("Successfully obtained Sentinel Hub access token")
                    return self.access_token
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get access token: {error}")
    
    def create_evalscript_marine_debris(self) -> str:
        """Create evalscript for marine debris detection"""
        return """
        //VERSION=3
        // Marine Debris Detection Script for Sentinel-2
        // Optimized for Korean Waters
        
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL"],
                    units: "DN"
                }],
                output: [
                    {
                        id: "default",
                        bands: 4,
                        sampleType: "UINT8"
                    },
                    {
                        id: "debris_mask",
                        bands: 1,
                        sampleType: "UINT8"
                    },
                    {
                        id: "indices",
                        bands: 3,
                        sampleType: "FLOAT32"
                    }
                ]
            };
        }
        
        function evaluatePixel(sample) {
            // Normalize bands
            let B02 = sample.B02 / 10000;  // Blue
            let B03 = sample.B03 / 10000;  // Green
            let B04 = sample.B04 / 10000;  // Red
            let B08 = sample.B08 / 10000;  // NIR
            let B11 = sample.B11 / 10000;  // SWIR1
            let B12 = sample.B12 / 10000;  // SWIR2
            
            // Scene classification
            let SCL = sample.SCL;
            
            // Skip clouds, cloud shadows, and land
            if (SCL == 3 || SCL == 8 || SCL == 9 || SCL == 10 || SCL == 11) {
                return {
                    default: [0, 0, 0, 0],
                    debris_mask: [0],
                    indices: [0, 0, 0]
                };
            }
            
            // Calculate indices for marine debris detection
            
            // 1. Floating Algae Index (FAI) - detects floating materials
            let FAI = B08 - (B04 + (B12 - B04) * ((865 - 665) / (2190 - 665)));
            
            // 2. Normalized Difference Water Index (NDWI)
            let NDWI = (B03 - B08) / (B03 + B08 + 0.001);
            
            // 3. Plastic Index (PI) - experimental index for plastic detection
            // Based on spectral signature of plastics in NIR and SWIR
            let PI = (B08 - B04) / (B08 + B04 + 0.001) * (B11 / B12);
            
            // 4. Floating Debris Index (FDI) - custom for marine debris
            let FDI = FAI * 2 + PI;
            
            // Debris detection thresholds (tuned for Korean waters)
            let is_debris = 0;
            
            // High confidence debris
            if (FDI > 0.05 && FAI > 0.02 && NDWI < 0.3) {
                is_debris = 255;  // Definite debris
            }
            // Medium confidence debris
            else if (FDI > 0.03 && FAI > 0.01) {
                is_debris = 170;  // Probable debris
            }
            // Low confidence debris
            else if (FDI > 0.01 || (PI > 0.1 && NDWI < 0.5)) {
                is_debris = 85;   // Possible debris
            }
            
            // Enhanced visualization for debris
            let visualization = [B04, B03, B02];
            if (is_debris > 0) {
                // Highlight debris in red
                visualization[0] = Math.min(B04 * 3 + 0.3, 1);
                visualization[1] = B03 * 0.5;
                visualization[2] = B02 * 0.5;
            }
            
            return {
                default: [
                    visualization[0] * 255,
                    visualization[1] * 255,
                    visualization[2] * 255,
                    255
                ],
                debris_mask: [is_debris],
                indices: [FAI, NDWI, FDI]
            };
        }
        """
    
    async def process_area(
        self,
        bbox: Tuple[float, float, float, float],
        time_range: Tuple[datetime, datetime],
        resolution: int = 10,
        max_cloud_coverage: float = 20
    ) -> Dict[str, Any]:
        """Process area using Sentinel Hub Process API"""
        
        token = await self.get_access_token()
        
        # Create request payload
        request = {
            "input": {
                "bounds": {
                    "bbox": list(bbox),
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": time_range[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "to": time_range[1].strftime("%Y-%m-%dT%H:%M:%SZ")
                        },
                        "maxCloudCoverage": max_cloud_coverage
                    }
                }]
            },
            "output": {
                "width": 512,
                "height": 512,
                "responses": [
                    {
                        "identifier": "default",
                        "format": {
                            "type": "image/png"
                        }
                    },
                    {
                        "identifier": "debris_mask",
                        "format": {
                            "type": "image/tiff"
                        }
                    }
                ]
            },
            "evalscript": self.create_evalscript_marine_debris()
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.process_url,
                json=request,
                headers=headers
            ) as response:
                if response.status == 200:
                    # Process multipart response
                    result = await self._process_multipart_response(response)
                    logger.info(f"Successfully processed area with bbox {bbox}")
                    return result
                else:
                    error = await response.text()
                    logger.error(f"Process API error: {error}")
                    raise Exception(f"Process API failed: {error}")
    
    async def get_statistics(
        self,
        geometry: Polygon,
        time_range: Tuple[datetime, datetime],
        aggregation_interval: str = "P1D",  # Daily
        resolution: int = 100
    ) -> Dict[str, Any]:
        """Get statistical analysis for marine debris using Statistical API"""
        
        token = await self.get_access_token()
        
        # Convert polygon to GeoJSON
        from shapely.geometry import mapping
        geojson = mapping(geometry)
        
        request = {
            "input": {
                "bounds": {
                    "geometry": geojson,
                    "properties": {
                        "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                    }
                },
                "data": [{
                    "type": "sentinel-2-l2a",
                    "dataFilter": {
                        "timeRange": {
                            "from": time_range[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                            "to": time_range[1].strftime("%Y-%m-%dT%H:%M:%SZ")
                        }
                    }
                }]
            },
            "aggregation": {
                "timeRange": {
                    "from": time_range[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "to": time_range[1].strftime("%Y-%m-%dT%H:%M:%SZ")
                },
                "aggregationInterval": {
                    "of": aggregation_interval
                },
                "evalscript": """
                    //VERSION=3
                    function setup() {
                        return {
                            input: [{
                                bands: ["B02", "B03", "B04", "B08", "B11", "B12", "SCL", "dataMask"],
                                units: "DN"
                            }],
                            output: [
                                {
                                    id: "debris_statistics",
                                    bands: 3,
                                    sampleType: "FLOAT32"
                                },
                                {
                                    id: "water_quality",
                                    bands: 2,
                                    sampleType: "FLOAT32"
                                }
                            ]
                        };
                    }
                    
                    function evaluatePixel(samples, scenes) {
                        // Calculate statistics for marine debris
                        let debris_count = 0;
                        let fai_sum = 0;
                        let ndwi_sum = 0;
                        let valid_pixels = 0;
                        
                        for (let i = 0; i < samples.length; i++) {
                            if (samples[i].dataMask && samples[i].SCL == 6) {  // Water pixels only
                                let B03 = samples[i].B03 / 10000;
                                let B04 = samples[i].B04 / 10000;
                                let B08 = samples[i].B08 / 10000;
                                let B12 = samples[i].B12 / 10000;
                                
                                // FAI calculation
                                let FAI = B08 - (B04 + (B12 - B04) * 0.5);
                                let NDWI = (B03 - B08) / (B03 + B08 + 0.001);
                                
                                if (FAI > 0.02) debris_count++;
                                fai_sum += FAI;
                                ndwi_sum += NDWI;
                                valid_pixels++;
                            }
                        }
                        
                        return {
                            debris_statistics: [
                                debris_count,
                                valid_pixels > 0 ? fai_sum / valid_pixels : 0,
                                valid_pixels > 0 ? debris_count / valid_pixels : 0
                            ],
                            water_quality: [
                                valid_pixels > 0 ? ndwi_sum / valid_pixels : 0,
                                valid_pixels
                            ]
                        };
                    }
                """,
                "resx": resolution,
                "resy": resolution
            },
            "calculations": {
                "default": {
                    "histograms": {
                        "default": {
                            "nBins": 20,
                            "lowEdge": 0,
                            "highEdge": 1
                        }
                    },
                    "statistics": {
                        "default": {
                            "percentiles": {
                                "k": [25, 50, 75, 90, 95]
                            }
                        }
                    }
                }
            }
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.statistical_url,
                json=request,
                headers=headers
            ) as response:
                if response.status == 200:
                    stats = await response.json()
                    logger.info(f"Successfully retrieved statistics for area")
                    return self._process_statistics(stats)
                else:
                    error = await response.text()
                    logger.error(f"Statistical API error: {error}")
                    raise Exception(f"Statistical API failed: {error}")
    
    async def create_batch_job(
        self,
        areas: List[Dict[str, Any]],
        time_range: Tuple[datetime, datetime],
        output_bucket: str = None
    ) -> str:
        """Create batch processing job for large-scale analysis"""
        
        token = await self.get_access_token()
        
        if not output_bucket:
            output_bucket = settings.s3_bucket_processed
        
        request = {
            "processRequest": {
                "input": {
                    "bounds": {
                        "properties": {
                            "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                        }
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": time_range[0].strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "to": time_range[1].strftime("%Y-%m-%dT%H:%M:%SZ")
                            },
                            "maxCloudCoverage": 20
                        }
                    }]
                },
                "output": {
                    "defaultTileSize": 2048,
                    "cogOutput": True,
                    "responses": [
                        {
                            "identifier": "debris_analysis",
                            "format": {
                                "type": "image/tiff"
                            }
                        }
                    ]
                },
                "evalscript": self.create_evalscript_marine_debris()
            },
            "tilingGrid": {
                "id": 0,
                "resolution": 10
            },
            "output": {
                "s3": {
                    "url": f"s3://{output_bucket}/batch/",
                    "accessKey": settings.s3_access_key.get_secret_value(),
                    "secretAccessKey": settings.s3_secret_key.get_secret_value(),
                    "region": settings.s3_region
                }
            },
            "description": "Marine debris detection batch processing for Korean waters"
        }
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.batch_url,
                json=request,
                headers=headers
            ) as response:
                if response.status == 201:
                    job_data = await response.json()
                    job_id = job_data['id']
                    logger.info(f"Created batch job with ID: {job_id}")
                    return job_id
                else:
                    error = await response.text()
                    logger.error(f"Batch API error: {error}")
                    raise Exception(f"Batch job creation failed: {error}")
    
    async def monitor_batch_job(self, job_id: str) -> Dict[str, Any]:
        """Monitor batch processing job status"""
        
        token = await self.get_access_token()
        
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.batch_url}/{job_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get batch job status: {error}")
    
    async def _process_multipart_response(self, response) -> Dict[str, Any]:
        """Process multipart response from Process API"""
        # This would parse the multipart response and extract images
        # For now, returning placeholder
        return {
            "visualization": None,
            "debris_mask": None,
            "metadata": {}
        }
    
    def _process_statistics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Process statistics response into meaningful metrics"""
        
        processed_stats = {
            "debris_detection": {},
            "water_quality": {},
            "temporal_analysis": []
        }
        
        if "data" in stats:
            for entry in stats["data"]:
                date = entry.get("interval", {}).get("from")
                
                # Extract debris statistics
                debris_stats = entry.get("outputs", {}).get("debris_statistics", {})
                if debris_stats:
                    bands = debris_stats.get("bands", {})
                    processed_stats["temporal_analysis"].append({
                        "date": date,
                        "debris_pixels": bands.get("B0", {}).get("stats", {}).get("mean", 0),
                        "fai_mean": bands.get("B1", {}).get("stats", {}).get("mean", 0),
                        "debris_ratio": bands.get("B2", {}).get("stats", {}).get("mean", 0)
                    })
        
        return processed_stats
    
    async def process_korean_waters(
        self,
        days_back: int = 7,
        resolution: int = 10
    ) -> Dict[str, Any]:
        """Process all Korean water areas for marine debris"""
        
        results = {}
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        time_range = (start_date, end_date)
        
        # Process each Korean sea area
        for area_name, bbox in settings.korea_bbox.items():
            logger.info(f"Processing {area_name}")
            
            try:
                # Process imagery
                imagery_result = await self.process_area(
                    bbox=tuple(bbox),
                    time_range=time_range,
                    resolution=resolution
                )
                
                # Get statistics
                area_polygon = box(*bbox)
                stats_result = await self.get_statistics(
                    geometry=area_polygon,
                    time_range=time_range
                )
                
                results[area_name] = {
                    "imagery": imagery_result,
                    "statistics": stats_result,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error processing {area_name}: {e}")
                results[area_name] = {"error": str(e)}
        
        return results