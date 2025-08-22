"""Satellite data collection tasks"""

import logging
from typing import List, Dict, Any

from celery import shared_task

from satchat.services.satellite.sentinel import Sentinel2Service

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def collect_all_areas(
    self,
    days_back: int = 3,
    max_cloud: float = 20
) -> Dict[str, Any]:
    """Collect satellite data for all Korean sea areas"""
    try:
        logger.info(f"Starting satellite data collection for all areas")
        
        sentinel_service = Sentinel2Service()
        
        # Run collection
        stats = await sentinel_service.automated_collection(
            areas=["west_sea", "south_sea", "east_sea"],
            days_back=days_back,
            max_cloud=max_cloud
        )
        
        logger.info(f"Collection completed: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in satellite collection task: {e}")
        raise self.retry(exc=e, countdown=300)  # Retry after 5 minutes


@shared_task(bind=True, max_retries=3)
def collect_specific_area(
    self,
    area: str,
    days_back: int = 3,
    max_cloud: float = 20
) -> Dict[str, Any]:
    """Collect satellite data for specific area"""
    try:
        logger.info(f"Starting satellite data collection for {area}")
        
        sentinel_service = Sentinel2Service()
        
        # Run collection
        stats = await sentinel_service.automated_collection(
            areas=[area],
            days_back=days_back,
            max_cloud=max_cloud
        )
        
        logger.info(f"Collection completed for {area}: {stats}")
        return stats
        
    except Exception as e:
        logger.error(f"Error in satellite collection task for {area}: {e}")
        raise self.retry(exc=e, countdown=300)


@shared_task
def download_satellite_image(product_id: str, product_info: Dict[str, Any]) -> bool:
    """Download specific satellite image"""
    try:
        logger.info(f"Downloading satellite image {product_id}")
        
        sentinel_service = Sentinel2Service()
        success, path = await sentinel_service.download_product(
            product_id,
            product_info
        )
        
        if success:
            logger.info(f"Successfully downloaded {product_id} to {path}")
        else:
            logger.error(f"Failed to download {product_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error downloading satellite image {product_id}: {e}")
        return False