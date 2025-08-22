"""
Marine Debris Detection Pipeline
Implements state-of-the-art detection methods based on research
"""

import asyncio
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)

@dataclass
class DetectionResult:
    """Detection result with comprehensive metadata"""
    id: str
    timestamp: datetime
    location: Dict[str, float]  # lat, lon
    debris_type: str
    confidence: float
    ml_confidence: float
    patch_size: float  # m²
    spectral_indices: Dict[str, float]
    priority: str
    region: str
    image_url: Optional[str] = None
    weather_conditions: Optional[Dict] = None
    verification_status: str = "unverified"
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'location': self.location,
            'debris_type': self.debris_type,
            'confidence': self.confidence,
            'ml_confidence': self.ml_confidence,
            'patch_size': self.patch_size,
            'spectral_indices': self.spectral_indices,
            'priority': self.priority,
            'region': self.region,
            'image_url': self.image_url,
            'weather_conditions': self.weather_conditions,
            'verification_status': self.verification_status
        }

class MarineDebrisDetectionPipeline:
    """
    Complete pipeline for marine debris detection
    Implements best practices from recent research
    """
    
    def __init__(self, sentinel_client):
        self.sentinel = sentinel_client
        self.detection_history = []
        self.alert_queue = []
        
        # Performance metrics
        self.metrics = {
            'true_positives': 0,
            'false_positives': 0,
            'false_negatives': 0,
            'processing_time': [],
            'detection_rate': 0.0
        }
        
    async def run_detection_cycle(self, region: str = 'all') -> List[DetectionResult]:
        """
        Run complete detection cycle for specified region
        """
        logger.info(f"Starting detection cycle for region: {region}")
        start_time = datetime.now()
        
        results = []
        
        # Process each region
        regions_to_process = (
            list(self.sentinel.korea_regions.keys()) 
            if region == 'all' 
            else [region]
        )
        
        for region_name in regions_to_process:
            try:
                region_results = await self._process_region(region_name)
                results.extend(region_results)
            except Exception as e:
                logger.error(f"Error processing region {region_name}: {e}")
                continue
        
        # Apply ML filtering
        filtered_results = self.sentinel.apply_machine_learning_filter(
            [r.to_dict() for r in results]
        )
        
        # Convert back to DetectionResult objects
        final_results = []
        for filtered in filtered_results:
            result = self._dict_to_detection_result(filtered)
            result.priority = self.sentinel.generate_alert_priority(filtered)
            final_results.append(result)
        
        # Update metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics['processing_time'].append(processing_time)
        self.metrics['detection_rate'] = len(final_results) / max(1, len(results))
        
        # Store in history
        self.detection_history.extend(final_results)
        
        # Generate alerts for high-priority detections
        await self._generate_alerts(final_results)
        
        logger.info(f"Detection cycle completed: {len(final_results)} detections in {processing_time:.2f}s")
        
        return final_results
    
    async def _process_region(self, region_name: str) -> List[DetectionResult]:
        """
        Process a specific region for debris detection
        """
        region_data = self.sentinel.korea_regions[region_name]
        bbox = region_data['bbox']
        
        # Get optimal time window
        start_date, end_date = self.sentinel.get_optimal_time_window(region_name)
        
        # Simulate satellite data acquisition and processing
        # In production, this would call actual Sentinel Hub API
        raw_detections = await self._acquire_satellite_data(
            bbox, start_date, end_date
        )
        
        # Process each detection
        results = []
        for idx, detection in enumerate(raw_detections):
            # Calculate spectral indices
            indices = self._calculate_indices(detection)
            
            # Calculate debris probability
            confidence = self.sentinel.calculate_debris_probability(indices)
            
            # Classify debris type
            debris_type = self.sentinel.classify_debris_type(indices)
            
            # Create detection result
            result = DetectionResult(
                id=f"{region_name}_{datetime.now().strftime('%Y%m%d')}_{idx:04d}",
                timestamp=datetime.now(),
                location={
                    'latitude': detection['lat'],
                    'longitude': detection['lon']
                },
                debris_type=debris_type,
                confidence=confidence,
                ml_confidence=confidence,  # Will be updated by ML filter
                patch_size=detection.get('size', 100),
                spectral_indices=indices,
                priority='low',  # Will be updated later
                region=region_data['name']
            )
            
            results.append(result)
        
        return results
    
    async def _acquire_satellite_data(
        self, 
        bbox: List[float], 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """
        Simulate satellite data acquisition
        In production, this would call actual Sentinel Hub API
        """
        # Simulate detection data based on research findings
        detections = []
        
        # Generate realistic mock detections
        num_detections = np.random.poisson(3)  # Average 3 detections per region
        
        for _ in range(num_detections):
            lat = np.random.uniform(bbox[1], bbox[3])
            lon = np.random.uniform(bbox[0], bbox[2])
            
            # Realistic size distribution (log-normal)
            size = np.exp(np.random.normal(5, 1.5))  # Mean ~150m², varies from 10-1000m²
            
            detection = {
                'lat': lat,
                'lon': lon,
                'size': max(10, min(10000, size)),
                'raw_spectral': {
                    'B02': np.random.uniform(0.05, 0.15),  # Blue
                    'B03': np.random.uniform(0.05, 0.15),  # Green
                    'B04': np.random.uniform(0.05, 0.20),  # Red
                    'B06': np.random.uniform(0.10, 0.30),  # Red Edge
                    'B08': np.random.uniform(0.15, 0.40),  # NIR
                    'B8A': np.random.uniform(0.15, 0.40),  # NIR Narrow
                    'B11': np.random.uniform(0.10, 0.25),  # SWIR1
                    'B12': np.random.uniform(0.05, 0.15),  # SWIR2
                }
            }
            detections.append(detection)
        
        await asyncio.sleep(0.1)  # Simulate API delay
        return detections
    
    def _calculate_indices(self, detection: Dict) -> Dict[str, float]:
        """
        Calculate spectral indices from raw spectral data
        """
        bands = detection.get('raw_spectral', {})
        
        # Extract bands
        blue = bands.get('B02', 0.1)
        green = bands.get('B03', 0.1)
        red = bands.get('B04', 0.1)
        red_edge = bands.get('B06', 0.2)
        nir = bands.get('B08', 0.3)
        nir_narrow = bands.get('B8A', 0.3)
        swir1 = bands.get('B11', 0.15)
        swir2 = bands.get('B12', 0.1)
        
        # Calculate indices
        indices = {}
        
        # FDI - Floating Debris Index
        indices['fdi'] = nir - (red + (nir_narrow - red) * (833 - 665) / (865 - 665))
        
        # FAI - Floating Algae Index
        indices['fai'] = nir - (red + (swir1 - red) * (833 - 665) / (1610 - 665))
        
        # NDVI
        indices['ndvi'] = (nir - red) / (nir + red + 0.0001)
        
        # NDWI
        indices['ndwi'] = (green - nir) / (green + nir + 0.0001)
        
        # NDMI
        indices['ndmi'] = (nir - swir1) / (nir + swir1 + 0.0001)
        
        # BSI - Bare Soil Index
        indices['bsi'] = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + 0.0001)
        
        # SI - Shadow Index
        indices['si'] = ((1 - blue) * (1 - green) * (1 - red)) ** (1/3)
        
        # Cloud-free flag (simulated)
        indices['cloud_free'] = 1 if np.random.random() > 0.2 else 0
        
        return indices
    
    async def _generate_alerts(self, detections: List[DetectionResult]):
        """
        Generate alerts for high-priority detections
        """
        for detection in detections:
            if detection.priority in ['critical', 'high']:
                alert = {
                    'id': f"ALERT_{detection.id}",
                    'timestamp': datetime.now().isoformat(),
                    'priority': detection.priority,
                    'title': f"{detection.priority.upper()}: {detection.debris_type} detected",
                    'message': (
                        f"Marine debris detected in {detection.region} "
                        f"at coordinates {detection.location['latitude']:.4f}°N, "
                        f"{detection.location['longitude']:.4f}°E. "
                        f"Estimated size: {detection.patch_size:.0f}m². "
                        f"Confidence: {detection.ml_confidence:.1%}"
                    ),
                    'detection_id': detection.id,
                    'action_required': self._get_required_action(detection)
                }
                self.alert_queue.append(alert)
    
    def _get_required_action(self, detection: DetectionResult) -> str:
        """
        Determine required action based on detection characteristics
        """
        if detection.priority == 'critical':
            if detection.patch_size > 10000:
                return "Immediate cleanup operation required. Contact maritime authorities."
            else:
                return "Urgent verification and cleanup assessment needed."
        elif detection.priority == 'high':
            if '어망' in detection.debris_type:
                return "Fishing net hazard - notify local fishing vessels and coast guard."
            else:
                return "Schedule cleanup operation within 48 hours."
        else:
            return "Monitor and include in next scheduled cleanup."
    
    def _dict_to_detection_result(self, data: Dict) -> DetectionResult:
        """
        Convert dictionary back to DetectionResult
        """
        return DetectionResult(
            id=data.get('id', ''),
            timestamp=datetime.fromisoformat(data.get('timestamp', datetime.now().isoformat())),
            location=data.get('location', {}),
            debris_type=data.get('debris_type', ''),
            confidence=data.get('confidence', 0),
            ml_confidence=data.get('ml_confidence', 0),
            patch_size=data.get('patch_size', 0),
            spectral_indices=data.get('spectral_indices', {}),
            priority=data.get('priority', 'low'),
            region=data.get('region', ''),
            image_url=data.get('image_url'),
            weather_conditions=data.get('weather_conditions'),
            verification_status=data.get('verification_status', 'unverified')
        )
    
    def get_performance_metrics(self) -> Dict:
        """
        Get current performance metrics
        """
        avg_processing_time = (
            np.mean(self.metrics['processing_time']) 
            if self.metrics['processing_time'] 
            else 0
        )
        
        return {
            'total_detections': len(self.detection_history),
            'detection_rate': self.metrics['detection_rate'],
            'average_processing_time': avg_processing_time,
            'alerts_generated': len(self.alert_queue),
            'regions_monitored': len(self.sentinel.korea_regions),
            'last_update': datetime.now().isoformat()
        }
    
    def export_results(self, format: str = 'json') -> str:
        """
        Export detection results in various formats
        """
        if format == 'json':
            return json.dumps([d.to_dict() for d in self.detection_history], indent=2)
        elif format == 'csv':
            # Simple CSV export
            lines = ['id,timestamp,latitude,longitude,debris_type,confidence,patch_size,priority,region']
            for d in self.detection_history:
                lines.append(
                    f"{d.id},{d.timestamp.isoformat()},"
                    f"{d.location['latitude']},{d.location['longitude']},"
                    f"{d.debris_type},{d.ml_confidence:.3f},{d.patch_size:.1f},"
                    f"{d.priority},{d.region}"
                )
            return '\n'.join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")