"""Image processing tasks"""

import logging
from typing import List, Optional
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from satchat.core.database import SessionLocal
from satchat.models.database import SatelliteImage, ProcessingStatus
from satchat.services.processing import process_satellite_image

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_image(self, image_id: str) -> bool:
    """Process single satellite image"""
    try:
        logger.info(f"Starting processing for image {image_id}")
        
        # Process image
        success = await process_satellite_image(image_id)
        
        if success:
            logger.info(f"Successfully processed image {image_id}")
        else:
            logger.error(f"Failed to process image {image_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error processing image {image_id}: {e}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def process_pending_images(limit: int = 10) -> List[str]:
    """Process pending satellite images"""
    processed_ids = []
    
    try:
        with SessionLocal() as db:
            # Get pending images
            result = db.execute(
                select(SatelliteImage)
                .where(SatelliteImage.processing_status == ProcessingStatus.PENDING)
                .limit(limit)
            )
            pending_images = result.scalars().all()
            
            logger.info(f"Found {len(pending_images)} pending images")
            
            # Queue processing tasks
            for image in pending_images:
                process_image.delay(str(image.id))
                processed_ids.append(str(image.id))
                
                # Update status to processing
                image.processing_status = ProcessingStatus.PROCESSING
            
            db.commit()
            
        logger.info(f"Queued {len(processed_ids)} images for processing")
        return processed_ids
        
    except Exception as e:
        logger.error(f"Error processing pending images: {e}")
        return processed_ids


@shared_task
def reprocess_failed_images(limit: int = 5) -> List[str]:
    """Reprocess failed images"""
    reprocessed_ids = []
    
    try:
        with SessionLocal() as db:
            # Get failed images
            result = db.execute(
                select(SatelliteImage)
                .where(SatelliteImage.processing_status == ProcessingStatus.FAILED)
                .limit(limit)
            )
            failed_images = result.scalars().all()
            
            logger.info(f"Found {len(failed_images)} failed images")
            
            # Queue reprocessing tasks
            for image in failed_images:
                process_image.delay(str(image.id))
                reprocessed_ids.append(str(image.id))
                
                # Reset status to pending
                image.processing_status = ProcessingStatus.PENDING
            
            db.commit()
            
        logger.info(f"Queued {len(reprocessed_ids)} images for reprocessing")
        return reprocessed_ids
        
    except Exception as e:
        logger.error(f"Error reprocessing failed images: {e}")
        return reprocessed_ids