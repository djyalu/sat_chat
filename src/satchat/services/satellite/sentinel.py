"""Sentinel-2 위성 데이터 수집 서비스"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import asyncio
import aiohttp

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
import geopandas as gpd
from shapely.geometry import box, Polygon
import pandas as pd

from satchat.core.config import settings
from satchat.models.database import SatelliteImage, ProcessingStatus
from satchat.models.schemas import SatelliteImageCreate
from satchat.services.storage import S3Service
from satchat.core.database import get_async_db

logger = logging.getLogger(__name__)


class Sentinel2Service:
    """Sentinel-2 위성 데이터 수집 및 관리 서비스"""
    
    def __init__(self):
        """Initialize Sentinel-2 service"""
        self.api = None
        if settings.sentinel_user and settings.sentinel_password:
            self.api = SentinelAPI(
                settings.sentinel_user,
                settings.sentinel_password.get_secret_value(),
                settings.sentinel_api_url
            )
        self.s3_service = S3Service()
        self.download_path = Path("data/downloads/sentinel2")
        self.download_path.mkdir(parents=True, exist_ok=True)
    
    def search_products(
        self,
        area_of_interest: Polygon,
        start_date: datetime,
        end_date: datetime,
        max_cloud_coverage: float = 20,
        product_type: str = "S2MSI2A",  # Level-2A (Bottom of Atmosphere)
        limit: int = 100
    ) -> pd.DataFrame:
        """
        Search Sentinel-2 products for given parameters
        
        Args:
            area_of_interest: Polygon defining the search area
            start_date: Start date for search
            end_date: End date for search
            max_cloud_coverage: Maximum cloud coverage percentage
            product_type: Sentinel-2 product type
            limit: Maximum number of results
        
        Returns:
            DataFrame with product information
        """
        if not self.api:
            raise ValueError("Sentinel API not configured. Check credentials.")
        
        # Convert polygon to WKT format
        footprint = area_of_interest.wkt
        
        # Search products
        products = self.api.query(
            footprint,
            date=(start_date, end_date),
            platformname="Sentinel-2",
            producttype=product_type,
            cloudcoverpercentage=(0, max_cloud_coverage),
            limit=limit
        )
        
        # Convert to DataFrame
        products_df = self.api.to_dataframe(products)
        
        if not products_df.empty:
            # Sort by cloud coverage and date
            products_df = products_df.sort_values(
                ["cloudcoverpercentage", "ingestiondate"],
                ascending=[True, False]
            )
            
            logger.info(f"Found {len(products_df)} Sentinel-2 products")
        else:
            logger.warning("No Sentinel-2 products found for given criteria")
        
        return products_df
    
    def search_korea_seas(
        self,
        sea_area: str,
        days_back: int = 7,
        max_cloud_coverage: float = 20
    ) -> pd.DataFrame:
        """
        Search Sentinel-2 products for Korean sea areas
        
        Args:
            sea_area: One of 'west_sea', 'south_sea', 'east_sea'
            days_back: Number of days to search back
            max_cloud_coverage: Maximum cloud coverage
        
        Returns:
            DataFrame with product information
        """
        # Get bbox for the sea area
        bbox_coords = settings.korea_bbox.get(sea_area)
        if not bbox_coords:
            raise ValueError(f"Unknown sea area: {sea_area}")
        
        # Create polygon from bbox
        min_lon, min_lat, max_lon, max_lat = bbox_coords
        area_polygon = box(min_lon, min_lat, max_lon, max_lat)
        
        # Set date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Searching Sentinel-2 for {sea_area} from {start_date} to {end_date}")
        
        return self.search_products(
            area_of_interest=area_polygon,
            start_date=start_date,
            end_date=end_date,
            max_cloud_coverage=max_cloud_coverage
        )
    
    async def download_product(
        self,
        product_id: str,
        product_info: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Download a Sentinel-2 product
        
        Args:
            product_id: Product UUID
            product_info: Product metadata
        
        Returns:
            Tuple of (success, local_path)
        """
        if not self.api:
            return False, None
        
        try:
            # Check if already downloaded
            local_file = self.download_path / f"{product_info['title']}.zip"
            if local_file.exists():
                logger.info(f"Product {product_info['title']} already downloaded")
                return True, str(local_file)
            
            # Download product
            logger.info(f"Downloading {product_info['title']}...")
            self.api.download(
                product_id,
                directory_path=str(self.download_path),
                checksum=True
            )
            
            logger.info(f"Successfully downloaded {product_info['title']}")
            return True, str(local_file)
            
        except Exception as e:
            logger.error(f"Error downloading product {product_id}: {e}")
            return False, None
    
    async def process_and_store(
        self,
        product_id: str,
        product_info: Dict[str, Any],
        local_path: str
    ) -> Optional[SatelliteImage]:
        """
        Process downloaded product and store in database
        
        Args:
            product_id: Product UUID
            product_info: Product metadata
            local_path: Local file path
        
        Returns:
            SatelliteImage instance or None
        """
        try:
            # Upload to S3
            s3_key = f"sentinel2/{product_info['title']}.zip"
            s3_url = await self.s3_service.upload_file(
                local_path,
                settings.s3_bucket_raw,
                s3_key
            )
            
            # Parse geometry
            footprint = product_info.get('footprint', '')
            if footprint:
                from shapely import wkt
                geometry = wkt.loads(footprint)
                centroid = geometry.centroid
                bounds = geometry.bounds
            else:
                centroid = None
                bounds = None
            
            # Create database entry
            image_data = SatelliteImageCreate(
                satellite_name="Sentinel-2",
                product_id=product_info['title'],
                acquisition_date=product_info['datatakesensingstart'],
                center_lat=centroid.y if centroid else 0,
                center_lon=centroid.x if centroid else 0,
                cloud_coverage=product_info.get('cloudcoverpercentage', 0),
                resolution=10.0,  # Sentinel-2 resolution in meters
                bbox={
                    "min_lat": bounds[1] if bounds else 0,
                    "min_lon": bounds[0] if bounds else 0,
                    "max_lat": bounds[3] if bounds else 0,
                    "max_lon": bounds[2] if bounds else 0
                } if bounds else None,
                bands=["B02", "B03", "B04", "B08"],  # RGB + NIR
                metadata={
                    "product_type": product_info.get('producttype'),
                    "orbit_number": product_info.get('orbitnumber'),
                    "relative_orbit": product_info.get('relativeorbitnumber'),
                    "processing_level": product_info.get('processinglevel'),
                    "platform": product_info.get('platformname'),
                    "size": product_info.get('size')
                }
            )
            
            # Store in database
            async with get_async_db() as db:
                image = SatelliteImage(
                    **image_data.model_dump(),
                    raw_data_path=s3_url,
                    processing_status=ProcessingStatus.PENDING
                )
                db.add(image)
                await db.commit()
                await db.refresh(image)
                
                logger.info(f"Stored image {image.product_id} in database")
                return image
                
        except Exception as e:
            logger.error(f"Error processing product {product_id}: {e}")
            return None
    
    async def automated_collection(
        self,
        areas: List[str] = None,
        days_back: int = 3,
        max_cloud: float = 15
    ) -> Dict[str, Any]:
        """
        Automated collection for Korean sea areas
        
        Args:
            areas: List of sea areas to collect
            days_back: Days to look back
            max_cloud: Maximum cloud coverage
        
        Returns:
            Collection statistics
        """
        if areas is None:
            areas = ["west_sea", "south_sea", "east_sea"]
        
        stats = {
            "total_found": 0,
            "total_downloaded": 0,
            "total_stored": 0,
            "errors": [],
            "by_area": {}
        }
        
        for area in areas:
            logger.info(f"Collecting data for {area}")
            area_stats = {
                "found": 0,
                "downloaded": 0,
                "stored": 0
            }
            
            try:
                # Search products
                products_df = self.search_korea_seas(
                    sea_area=area,
                    days_back=days_back,
                    max_cloud_coverage=max_cloud
                )
                
                area_stats["found"] = len(products_df)
                stats["total_found"] += len(products_df)
                
                # Process top products
                for idx, (product_id, product_info) in enumerate(products_df.head(5).iterrows()):
                    # Download
                    success, local_path = await self.download_product(
                        product_id,
                        product_info.to_dict()
                    )
                    
                    if success and local_path:
                        area_stats["downloaded"] += 1
                        stats["total_downloaded"] += 1
                        
                        # Store
                        image = await self.process_and_store(
                            product_id,
                            product_info.to_dict(),
                            local_path
                        )
                        
                        if image:
                            area_stats["stored"] += 1
                            stats["total_stored"] += 1
                
            except Exception as e:
                error_msg = f"Error collecting {area}: {str(e)}"
                logger.error(error_msg)
                stats["errors"].append(error_msg)
            
            stats["by_area"][area] = area_stats
        
        logger.info(f"Collection complete: {stats}")
        return stats
    
    def get_quicklook_url(self, product_id: str) -> Optional[str]:
        """
        Get quicklook (preview) URL for a product
        
        Args:
            product_id: Product UUID
        
        Returns:
            Quicklook URL or None
        """
        if not self.api:
            return None
        
        try:
            # Get product info
            product_info = self.api.get_product_odata(product_id)
            return product_info.get('quicklook_url')
        except Exception as e:
            logger.error(f"Error getting quicklook URL: {e}")
            return None