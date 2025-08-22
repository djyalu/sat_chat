#!/usr/bin/env python3
"""Batch processing system for large-scale marine debris monitoring"""

import numpy as np
import asyncio
from typing import List, Dict, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import logging
import json
import os
from pathlib import Path
import time
from enum import Enum
import uuid

from ..processing.multi_index_analyzer import MultiIndexAnalyzer
from ..ml.marine_segmentation import MarineSegmentationML

logger = logging.getLogger(__name__)

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class BatchJob:
    """Batch processing job definition"""
    id: str
    name: str
    regions: List[Dict[str, Any]]
    time_range: Tuple[str, str]
    analysis_types: List[str]
    output_format: str
    priority: int = 5
    status: JobStatus = JobStatus.PENDING
    progress: float = 0.0
    created_at: str = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error_message: Optional[str] = None
    results_path: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class ProcessingResult:
    """Results from processing a single region"""
    region_id: str
    timestamp: str
    analysis_data: Dict[str, Any]
    metadata: Dict[str, Any]
    processing_time: float
    success: bool = True
    error: Optional[str] = None

class BatchProcessor:
    """Large-scale batch processing system for marine debris monitoring"""
    
    def __init__(self, max_workers: int = 4, results_dir: str = "batch_results"):
        self.analyzer = MultiIndexAnalyzer()
        self.ml_segmentation = MarineSegmentationML()
        
        self.max_workers = max_workers
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
        
        # Job management
        self.jobs: Dict[str, BatchJob] = {}
        self.job_queue = asyncio.Queue()
        self.active_jobs = set()
        
        # Processing pools
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers * 2)
        
        # Statistics
        self.stats = {
            'total_jobs': 0,
            'completed_jobs': 0,
            'failed_jobs': 0,
            'total_regions_processed': 0,
            'total_processing_time': 0.0,
            'start_time': datetime.now().isoformat()
        }
        
    def create_job(self, name: str, regions: List[Dict[str, Any]], 
                  time_range: Tuple[str, str], 
                  analysis_types: List[str] = None,
                  output_format: str = 'geojson',
                  priority: int = 5) -> str:
        """Create a new batch processing job"""
        
        if analysis_types is None:
            analysis_types = ['fdi', 'ndwi', 'mci', 'debris_ml']
        
        job_id = str(uuid.uuid4())
        
        job = BatchJob(
            id=job_id,
            name=name,
            regions=regions,
            time_range=time_range,
            analysis_types=analysis_types,
            output_format=output_format,
            priority=priority
        )
        
        self.jobs[job_id] = job
        self.stats['total_jobs'] += 1
        
        # Add to queue (async operation)
        asyncio.create_task(self.job_queue.put(job))
        
        logger.info(f"Created batch job {job_id}: {name} with {len(regions)} regions")
        
        return job_id
    
    async def process_job_queue(self):
        """Process jobs from the queue"""
        while True:
            try:
                # Get next job from queue
                job = await self.job_queue.get()
                
                if len(self.active_jobs) >= self.max_workers:
                    # Queue is full, wait
                    await asyncio.sleep(1)
                    await self.job_queue.put(job)  # Put back
                    continue
                
                # Start processing job
                self.active_jobs.add(job.id)
                asyncio.create_task(self._process_job(job))
                
            except Exception as e:
                logger.error(f"Error in job queue processing: {e}")
                await asyncio.sleep(5)
    
    async def _process_job(self, job: BatchJob):
        """Process a single batch job"""
        
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now().isoformat()
        
        try:
            logger.info(f"Starting job {job.id}: {job.name}")
            
            # Process regions in parallel
            results = await self._process_regions(job)
            
            # Aggregate and save results
            output_path = await self._save_results(job, results)
            
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            job.results_path = str(output_path)
            job.progress = 100.0
            
            self.stats['completed_jobs'] += 1
            self.stats['total_regions_processed'] += len(results)
            
            logger.info(f"Completed job {job.id}: processed {len(results)} regions")
            
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.now().isoformat()
            
            self.stats['failed_jobs'] += 1
            
            logger.error(f"Failed job {job.id}: {e}")
        
        finally:
            self.active_jobs.discard(job.id)
    
    async def _process_regions(self, job: BatchJob) -> List[ProcessingResult]:
        """Process all regions for a job in parallel"""
        
        results = []
        total_regions = len(job.regions)
        
        # Create processing tasks
        tasks = []
        for i, region in enumerate(job.regions):
            task = asyncio.create_task(
                self._process_single_region(
                    region, job.time_range, job.analysis_types, i, total_regions
                )
            )
            tasks.append(task)
        
        # Process with progress tracking
        completed = 0
        for task in asyncio.as_completed(tasks):
            try:
                result = await task
                results.append(result)
                completed += 1
                
                # Update progress
                job.progress = (completed / total_regions) * 100
                
                if completed % 10 == 0:  # Log every 10 completed
                    logger.info(f"Job {job.id}: {completed}/{total_regions} regions processed")
                    
            except Exception as e:
                logger.error(f"Error processing region in job {job.id}: {e}")
                # Create failed result
                failed_result = ProcessingResult(
                    region_id="unknown",
                    timestamp=datetime.now().isoformat(),
                    analysis_data={},
                    metadata={},
                    processing_time=0.0,
                    success=False,
                    error=str(e)
                )
                results.append(failed_result)
        
        return results
    
    async def _process_single_region(self, region: Dict[str, Any], 
                                   time_range: Tuple[str, str],
                                   analysis_types: List[str],
                                   region_idx: int, total_regions: int) -> ProcessingResult:
        """Process a single region asynchronously"""
        
        start_time = time.time()
        region_id = region.get('id', f"region_{region_idx}")
        
        try:
            # Get satellite data (would normally be from Sentinel Hub API)
            sentinel_data = await self._get_sentinel_data_async(region, time_range)
            
            if sentinel_data is None:
                raise ValueError("No satellite data available")
            
            # Run analysis in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            analysis_result = await loop.run_in_executor(
                self.thread_pool, 
                self._run_analysis, 
                sentinel_data, analysis_types
            )
            
            processing_time = time.time() - start_time
            self.stats['total_processing_time'] += processing_time
            
            # Create result
            result = ProcessingResult(
                region_id=region_id,
                timestamp=datetime.now().isoformat(),
                analysis_data=analysis_result,
                metadata={
                    'region': region,
                    'time_range': time_range,
                    'analysis_types': analysis_types,
                    'processing_time': processing_time
                },
                processing_time=processing_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(f"Error processing region {region_id}: {e}")
            
            return ProcessingResult(
                region_id=region_id,
                timestamp=datetime.now().isoformat(),
                analysis_data={},
                metadata={'region': region},
                processing_time=processing_time,
                success=False,
                error=str(e)
            )
    
    async def _get_sentinel_data_async(self, region: Dict[str, Any], 
                                     time_range: Tuple[str, str]) -> Optional[np.ndarray]:
        """Get Sentinel data asynchronously (simulated)"""
        
        # Simulate API call delay
        await asyncio.sleep(0.1)
        
        # TODO: Replace with actual Sentinel Hub API integration
        # For now, return synthetic data
        try:
            # Simulate different data availability
            import random
            if random.random() < 0.1:  # 10% failure rate
                return None
            
            # Create synthetic 15-band data
            h, w = 512, 512
            bands = 15
            
            # Simulate realistic satellite data values
            data = np.random.rand(h, w, bands) * 2000 + 500
            data = data.astype(np.float32)
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel data: {e}")
            return None
    
    def _run_analysis(self, sentinel_data: np.ndarray, 
                     analysis_types: List[str]) -> Dict[str, Any]:
        """Run analysis on satellite data (CPU-bound)"""
        
        results = {}
        
        try:
            # Calculate multi-indices
            if sentinel_data.shape[2] >= 12:  # Ensure we have enough bands
                indices = self.analyzer.calculate_multi_indices(sentinel_data)
            else:
                # Create minimal indices for limited band data
                indices = self._create_minimal_indices(sentinel_data)
            
            # Add requested analysis types
            if 'fdi' in analysis_types:
                results['fdi'] = {
                    'mean': float(np.mean(indices['fdi'])),
                    'max': float(np.max(indices['fdi'])),
                    'debris_area_km2': float(np.sum(indices['fdi'] > 0.1) * 0.01),  # 10m pixels
                    'debris_percentage': float(np.sum(indices['fdi'] > 0.1) / indices['fdi'].size * 100)
                }
            
            if 'ndwi' in analysis_types:
                water_mask = indices['ndwi'] > 0
                results['ndwi'] = {
                    'mean': float(np.mean(indices['ndwi'])),
                    'water_percentage': float(np.sum(water_mask) / indices['ndwi'].size * 100),
                    'water_area_km2': float(np.sum(water_mask) * 0.01)
                }
            
            if 'mci' in analysis_types:
                results['mci'] = {
                    'mean': float(np.mean(indices['mci'])),
                    'max': float(np.max(indices['mci'])),
                    'high_chlorophyll_percentage': float(np.sum(indices['mci'] > 0.01) / indices['mci'].size * 100)
                }
            
            if 'debris_ml' in analysis_types and self.ml_segmentation.is_trained:
                # ML-based segmentation
                segmentation, confidence = self.ml_segmentation.predict_segmentation(
                    sentinel_data, indices
                )
                
                debris_analysis = self.ml_segmentation.analyze_marine_debris(
                    segmentation, confidence
                )
                
                results['debris_ml'] = debris_analysis
            
            # Add processing metadata
            results['metadata'] = {
                'bands_available': int(sentinel_data.shape[2]),
                'spatial_resolution': '10m',
                'analysis_timestamp': datetime.now().isoformat(),
                'indices_calculated': list(indices.keys())
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {'error': str(e)}
    
    def _create_minimal_indices(self, sentinel_data: np.ndarray) -> Dict[str, np.ndarray]:
        """Create minimal indices for limited band data"""
        
        h, w = sentinel_data.shape[:2]
        
        # Create basic indices with available data
        indices = {}
        
        if sentinel_data.shape[2] >= 4:
            # Assume first 4 bands are Blue, Green, Red, NIR
            blue = sentinel_data[..., 0]
            green = sentinel_data[..., 1] 
            red = sentinel_data[..., 2]
            nir = sentinel_data[..., 3]
            
            # Basic NDWI and NDVI
            indices['ndwi'] = (green - nir) / (green + nir + 1e-10)
            indices['ndvi'] = (nir - red) / (nir + red + 1e-10)
            
            # Simplified FDI approximation
            indices['fdi'] = nir - red - 0.1 * (green - blue)
            
            # Placeholder for other indices
            indices['mci'] = np.zeros((h, w))
            indices['fai'] = np.zeros((h, w))
            indices['turbidity'] = np.abs(blue - green) / (blue + green + 1e-10)
            indices['sun_glint'] = np.zeros((h, w))
        else:
            # Create zero arrays for all indices
            for idx_name in ['fdi', 'ndwi', 'ndvi', 'mci', 'fai', 'turbidity', 'sun_glint']:
                indices[idx_name] = np.zeros((h, w))
        
        return indices
    
    async def _save_results(self, job: BatchJob, results: List[ProcessingResult]) -> Path:
        """Save job results to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"batch_job_{job.id}_{timestamp}.json"
        output_path = self.results_dir / filename
        
        # Prepare output data
        output_data = {
            'job': asdict(job),
            'summary': {
                'total_regions': len(job.regions),
                'successful_regions': sum(1 for r in results if r.success),
                'failed_regions': sum(1 for r in results if not r.success),
                'total_processing_time': sum(r.processing_time for r in results),
                'average_processing_time': np.mean([r.processing_time for r in results]) if results else 0
            },
            'results': [asdict(result) for result in results]
        }
        
        # Save to JSON file
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            self.thread_pool,
            self._write_json_file,
            output_path, output_data
        )
        
        logger.info(f"Saved job {job.id} results to {output_path}")
        
        return output_path
    
    def _write_json_file(self, path: Path, data: Dict[str, Any]):
        """Write JSON file (blocking operation)"""
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific job"""
        if job_id not in self.jobs:
            return None
        
        job = self.jobs[job_id]
        return {
            'id': job.id,
            'name': job.name,
            'status': job.status.value,
            'progress': job.progress,
            'created_at': job.created_at,
            'started_at': job.started_at,
            'completed_at': job.completed_at,
            'error_message': job.error_message,
            'results_path': job.results_path,
            'region_count': len(job.regions),
            'analysis_types': job.analysis_types
        }
    
    def list_jobs(self, status_filter: Optional[JobStatus] = None) -> List[Dict[str, Any]]:
        """List all jobs with optional status filter"""
        jobs = []
        for job in self.jobs.values():
            if status_filter is None or job.status == status_filter:
                jobs.append(self.get_job_status(job.id))
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda x: x['created_at'], reverse=True)
        
        return jobs
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending or running job"""
        if job_id not in self.jobs:
            return False
        
        job = self.jobs[job_id]
        
        if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return False  # Cannot cancel already finished jobs
        
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now().isoformat()
        
        # Remove from active jobs
        self.active_jobs.discard(job_id)
        
        logger.info(f"Cancelled job {job_id}")
        
        return True
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        current_time = datetime.now()
        start_time = datetime.fromisoformat(self.stats['start_time'])
        uptime_hours = (current_time - start_time).total_seconds() / 3600
        
        return {
            'uptime_hours': round(uptime_hours, 2),
            'active_jobs': len(self.active_jobs),
            'queue_size': self.job_queue.qsize(),
            'total_jobs': self.stats['total_jobs'],
            'completed_jobs': self.stats['completed_jobs'],
            'failed_jobs': self.stats['failed_jobs'],
            'success_rate': (self.stats['completed_jobs'] / max(1, self.stats['total_jobs'])) * 100,
            'total_regions_processed': self.stats['total_regions_processed'],
            'average_processing_time': (
                self.stats['total_processing_time'] / max(1, self.stats['total_regions_processed'])
            ),
            'regions_per_hour': self.stats['total_regions_processed'] / max(0.1, uptime_hours)
        }
    
    async def start_processing(self):
        """Start the batch processing system"""
        logger.info("Starting batch processing system...")
        await self.process_job_queue()
    
    def shutdown(self):
        """Shutdown the processing system"""
        logger.info("Shutting down batch processing system...")
        
        # Cancel all pending jobs
        for job_id, job in self.jobs.items():
            if job.status == JobStatus.PENDING:
                self.cancel_job(job_id)
        
        # Shutdown thread pools
        self.process_pool.shutdown(wait=True)
        self.thread_pool.shutdown(wait=True)

def create_batch_processor(max_workers: int = 4, results_dir: str = "batch_results") -> BatchProcessor:
    """Factory function to create batch processor"""
    return BatchProcessor(max_workers, results_dir)