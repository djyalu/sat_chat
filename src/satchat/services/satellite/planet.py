"""Planet Labs API integration for high-resolution satellite imagery"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import aiohttp
import json

from satchat.core.config import settings

logger = logging.getLogger(__name__)


class PlanetService:
    """Planet Labs API service for high-resolution satellite imagery"""
    
    def __init__(self):
        """Initialize Planet service"""
        self.api_key = settings.planet_api_key.get_secret_value() if settings.planet_api_key else None
        self.base_url = "https://api.planet.com"
        self.data_api_url = f"{self.base_url}/data/v1"
        self.orders_api_url = f"{self.base_url}/compute/ops/orders/v2"
        self.stats_api_url = f"{self.base_url}/data/v1/stats"
        
        if not self.api_key:
            logger.warning("Planet API key not configured")
    
    def get_headers(self) -> Dict[str, str]:
        """Get API headers with authentication"""
        return {
            "Authorization": f"api-key {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def search_scenes(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        item_types: List[str] = None,
        max_cloud_cover: float = 0.2,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search for Planet scenes
        
        Args:
            bbox: Bounding box [west, south, east, north]
            start_date: Start date for search
            end_date: End date for search
            item_types: List of item types (e.g., ['PSScene', 'SkySatCollect'])
            max_cloud_cover: Maximum cloud cover (0-1)
            limit: Maximum number of results
        
        Returns:
            List of scene metadata
        """
        
        if not self.api_key:
            raise ValueError("Planet API key not configured")
        
        if item_types is None:
            item_types = ["PSScene"]  # PlanetScope scenes by default
        
        # Build search filter
        search_filter = {
            "type": "AndFilter",
            "config": [
                {
                    "type": "GeometryFilter",
                    "field_name": "geometry",
                    "config": {
                        "type": "Polygon",
                        "coordinates": [[
                            [bbox[0], bbox[1]],  # SW
                            [bbox[2], bbox[1]],  # SE
                            [bbox[2], bbox[3]],  # NE
                            [bbox[0], bbox[3]],  # NW
                            [bbox[0], bbox[1]]   # Close polygon
                        ]]
                    }
                },
                {
                    "type": "DateRangeFilter",
                    "field_name": "acquired",
                    "config": {
                        "gte": start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "lte": end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    }
                },
                {
                    "type": "RangeFilter",
                    "field_name": "cloud_cover",
                    "config": {
                        "lte": max_cloud_cover
                    }
                },
                {
                    "type": "AssetFilter",
                    "config": ["ortho_analytic_4b"]  # 4-band analytical ortho
                }
            ]
        }
        
        # Create search request
        search_request = {
            "item_types": item_types,
            "filter": search_filter,
            "limit": limit
        }
        
        # Quick search endpoint
        url = f"{self.data_api_url}/quick-search"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=search_request,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    features = data.get("features", [])
                    logger.info(f"Found {len(features)} Planet scenes")
                    return features
                else:
                    error = await response.text()
                    logger.error(f"Planet search error: {error}")
                    raise Exception(f"Planet API search failed: {error}")
    
    async def get_scene_metadata(
        self,
        item_type: str,
        item_id: str
    ) -> Dict[str, Any]:
        """Get detailed metadata for a specific scene
        
        Args:
            item_type: Type of item (e.g., 'PSScene')
            item_id: Scene ID
        
        Returns:
            Scene metadata
        """
        
        url = f"{self.data_api_url}/item-types/{item_type}/items/{item_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get scene metadata: {error}")
    
    async def create_order(
        self,
        scene_ids: List[str],
        item_type: str = "PSScene",
        product_bundle: str = "analytic_sr_udm2",
        delivery: Dict[str, Any] = None
    ) -> str:
        """Create an order for downloading scenes
        
        Args:
            scene_ids: List of scene IDs to order
            item_type: Type of items
            product_bundle: Product bundle to order
            delivery: Delivery configuration
        
        Returns:
            Order ID
        """
        
        if not delivery:
            # Default to S3 delivery
            delivery = {
                "aws_s3": {
                    "bucket": settings.s3_bucket_raw,
                    "aws_region": settings.s3_region,
                    "aws_access_key_id": settings.s3_access_key.get_secret_value(),
                    "aws_secret_access_key": settings.s3_secret_key.get_secret_value(),
                    "path_prefix": "planet/"
                }
            }
        
        # Create order request
        order_request = {
            "name": f"SatChat Order {datetime.utcnow().isoformat()}",
            "products": [
                {
                    "item_ids": scene_ids,
                    "item_type": item_type,
                    "product_bundle": product_bundle
                }
            ],
            "delivery": delivery
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.orders_api_url,
                json=order_request,
                headers=self.get_headers()
            ) as response:
                if response.status in [200, 202]:
                    order_data = await response.json()
                    order_id = order_data.get("id")
                    logger.info(f"Created Planet order: {order_id}")
                    return order_id
                else:
                    error = await response.text()
                    raise Exception(f"Failed to create order: {error}")
    
    async def get_order_status(
        self,
        order_id: str
    ) -> Dict[str, Any]:
        """Get status of an order
        
        Args:
            order_id: Order ID
        
        Returns:
            Order status information
        """
        
        url = f"{self.orders_api_url}/{order_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get order status: {error}")
    
    async def get_statistics(
        self,
        bbox: List[float],
        start_date: datetime,
        end_date: datetime,
        item_types: List[str] = None,
        interval: str = "day"
    ) -> Dict[str, Any]:
        """Get statistics for an area and time range
        
        Args:
            bbox: Bounding box
            start_date: Start date
            end_date: End date
            item_types: Item types to include
            interval: Aggregation interval ('day', 'week', 'month')
        
        Returns:
            Statistics data
        """
        
        if item_types is None:
            item_types = ["PSScene"]
        
        # Build statistics request
        stats_request = {
            "interval": interval,
            "item_types": item_types,
            "filter": {
                "type": "AndFilter",
                "config": [
                    {
                        "type": "GeometryFilter",
                        "field_name": "geometry",
                        "config": {
                            "type": "Polygon",
                            "coordinates": [[
                                [bbox[0], bbox[1]],
                                [bbox[2], bbox[1]],
                                [bbox[2], bbox[3]],
                                [bbox[0], bbox[3]],
                                [bbox[0], bbox[1]]
                            ]]
                        }
                    },
                    {
                        "type": "DateRangeFilter",
                        "field_name": "acquired",
                        "config": {
                            "gte": start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                            "lte": end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                        }
                    }
                ]
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.stats_api_url,
                json=stats_request,
                headers=self.get_headers()
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error = await response.text()
                    raise Exception(f"Failed to get statistics: {error}")
    
    async def process_korean_waters_hires(
        self,
        days_back: int = 7,
        max_cloud_cover: float = 0.1
    ) -> Dict[str, Any]:
        """Process Korean waters with high-resolution Planet imagery
        
        Args:
            days_back: Days to look back
            max_cloud_cover: Maximum cloud cover (0-1)
        
        Returns:
            Processing results
        """
        
        results = {}
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days_back)
        
        for area_name, bbox in settings.korea_bbox.items():
            logger.info(f"Processing {area_name} with Planet imagery")
            
            try:
                # Search for scenes
                scenes = await self.search_scenes(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    max_cloud_cover=max_cloud_cover,
                    limit=10  # Limit to reduce costs
                )
                
                # Get statistics
                stats = await self.get_statistics(
                    bbox=bbox,
                    start_date=start_date,
                    end_date=end_date,
                    interval="day"
                )
                
                results[area_name] = {
                    "scenes_found": len(scenes),
                    "statistics": stats,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Log scene information
                if scenes:
                    latest_scene = scenes[0]
                    logger.info(
                        f"{area_name}: Found scene {latest_scene['id']} "
                        f"from {latest_scene['properties']['acquired']}"
                    )
                
            except Exception as e:
                logger.error(f"Error processing {area_name} with Planet: {e}")
                results[area_name] = {"error": str(e)}
        
        return results