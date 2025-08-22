"""
Advanced Sentinel Hub integration for marine debris detection
Based on best practices and research findings
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass
from enum import Enum

class SpectralIndex(Enum):
    """Spectral indices for marine debris detection"""
    FDI = "fdi"  # Floating Debris Index - Best for plastic detection
    FAI = "fai"  # Floating Algae Index
    NDVI = "ndvi"  # Normalized Difference Vegetation Index
    NDWI = "ndwi"  # Normalized Difference Water Index
    NDMI = "ndmi"  # Normalized Difference Moisture Index
    BSI = "bsi"  # Bare Soil Index
    SI = "si"  # Shadow Index

@dataclass
class DetectionConfig:
    """Configuration for marine debris detection"""
    # Spectral thresholds based on research
    fdi_threshold: float = 0.02  # FDI > 0.02 indicates potential debris
    ndvi_threshold: float = -0.1  # NDVI for water/debris distinction
    ndwi_threshold: float = 0.3  # NDWI for water body detection
    
    # Minimum patch size (m²) for detection
    min_patch_size: float = 100  # 10x10m minimum (Sentinel-2 resolution)
    
    # Confidence scoring weights
    weights: Dict[str, float] = None
    
    def __post_init__(self):
        if self.weights is None:
            # Based on research: FDI and NDWI are most important
            self.weights = {
                'fdi': 0.35,
                'ndvi': 0.20,
                'ndwi': 0.25,
                'ndmi': 0.10,
                'cloud_free': 0.10
            }

class SentinelHubAdvanced:
    """Advanced Sentinel Hub client for marine debris detection"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.config = DetectionConfig()
        
        # Korean waters bounding boxes
        self.korea_regions = {
            'west_sea': {
                'bbox': [124.0, 33.0, 127.0, 39.0],
                'name': '서해',
                'priority_zones': [
                    [125.5, 36.5, 126.5, 37.5],  # 충남 연안
                    [126.0, 37.0, 127.0, 38.0],  # 경기만
                ]
            },
            'south_sea': {
                'bbox': [126.0, 32.0, 130.0, 35.0],
                'name': '남해',
                'priority_zones': [
                    [127.5, 34.0, 128.5, 35.0],  # 부산 연안
                    [128.0, 33.5, 129.0, 34.5],  # 거제도 주변
                ]
            },
            'east_sea': {
                'bbox': [128.0, 35.0, 132.0, 38.5],
                'name': '동해',
                'priority_zones': [
                    [129.0, 35.5, 130.0, 36.5],  # 울산 연안
                    [129.5, 37.0, 130.5, 38.0],  # 강원 연안
                ]
            }
        }
        
    def get_evalscript_advanced(self) -> str:
        """
        Advanced evalscript for marine debris detection
        Implements multiple spectral indices
        """
        return """
        //VERSION=3
        
        function setup() {
            return {
                input: [{
                    bands: ["B02", "B03", "B04", "B06", "B08", "B8A", "B11", "B12", "SCL"],
                    units: "REFLECTANCE"
                }],
                output: [
                    {
                        id: "indices",
                        bands: 7,
                        sampleType: "FLOAT32"
                    },
                    {
                        id: "rgb",
                        bands: 3,
                        sampleType: "AUTO"
                    },
                    {
                        id: "quality",
                        bands: 1,
                        sampleType: "UINT8"
                    }
                ]
            };
        }
        
        function evaluatePixel(samples) {
            // Band definitions
            let blue = samples.B02;
            let green = samples.B03;
            let red = samples.B04;
            let red_edge = samples.B06;  // ~740nm for FDI
            let nir = samples.B08;
            let nir_narrow = samples.B8A;
            let swir1 = samples.B11;
            let swir2 = samples.B12;
            let scl = samples.SCL;
            
            // Cloud mask (SCL: 8=cloud medium, 9=cloud high, 10=cirrus)
            let cloud_free = (scl < 8) ? 1 : 0;
            
            // Floating Debris Index (FDI) - Primary index for plastic detection
            // Based on FAI but uses Red Edge band
            let fdi = nir - (red + (nir_narrow - red) * (833 - 665) / (865 - 665));
            
            // Floating Algae Index (FAI) - Helps distinguish algae from plastic
            let fai = nir - (red + (swir1 - red) * (833 - 665) / (1610 - 665));
            
            // NDVI - Vegetation/debris distinction
            let ndvi = (nir - red) / (nir + red + 0.0001);
            
            // NDWI - Water body identification
            let ndwi = (green - nir) / (green + nir + 0.0001);
            
            // NDMI - Moisture content
            let ndmi = (nir - swir1) / (nir + swir1 + 0.0001);
            
            // Bare Soil Index - Helps identify non-vegetated floating materials
            let bsi = ((swir1 + red) - (nir + blue)) / ((swir1 + red) + (nir + blue) + 0.0001);
            
            // Shadow Index - Reduces false positives from shadows
            let si = Math.pow((1 - blue) * (1 - green) * (1 - red), 1/3);
            
            // Marine Debris Detection Logic
            let debris_score = 0;
            
            // FDI is primary indicator (weight: 0.35)
            if (fdi > 0.02) debris_score += 0.35;
            else if (fdi > 0.01) debris_score += 0.15;
            
            // NDVI helps distinguish from vegetation (weight: 0.20)
            if (ndvi > -0.1 && ndvi < 0.3) debris_score += 0.20;
            else if (ndvi > -0.2 && ndvi < 0.4) debris_score += 0.10;
            
            // NDWI confirms water presence (weight: 0.25)
            if (ndwi > 0.3) debris_score += 0.25;
            else if (ndwi > 0.1) debris_score += 0.15;
            
            // NDMI for moisture detection (weight: 0.10)
            if (ndmi < 0.1 && ndmi > -0.2) debris_score += 0.10;
            
            // Cloud-free bonus (weight: 0.10)
            debris_score += cloud_free * 0.10;
            
            // Quality flag (0-255 scale)
            let quality = Math.min(255, Math.round(debris_score * 255));
            
            return {
                indices: [fdi, fai, ndvi, ndwi, ndmi, bsi, si],
                rgb: [red * 2.5, green * 2.5, blue * 2.5],
                quality: [quality]
            };
        }
        """
    
    def calculate_debris_probability(self, indices: Dict[str, float]) -> float:
        """
        Calculate probability of marine debris presence
        Based on multiple spectral indices
        """
        score = 0.0
        
        # FDI - Primary indicator
        if indices.get('fdi', 0) > self.config.fdi_threshold:
            score += self.config.weights['fdi']
        elif indices.get('fdi', 0) > self.config.fdi_threshold * 0.5:
            score += self.config.weights['fdi'] * 0.5
            
        # NDVI - Should be low for water, slightly positive for debris
        ndvi = indices.get('ndvi', 0)
        if -0.1 < ndvi < 0.3:
            score += self.config.weights['ndvi']
        elif -0.2 < ndvi < 0.4:
            score += self.config.weights['ndvi'] * 0.5
            
        # NDWI - Should be positive for water bodies
        if indices.get('ndwi', 0) > self.config.ndwi_threshold:
            score += self.config.weights['ndwi']
            
        # NDMI - Moisture content indicator
        ndmi = indices.get('ndmi', 0)
        if -0.2 < ndmi < 0.1:
            score += self.config.weights['ndmi']
            
        # Cloud-free bonus
        if indices.get('cloud_free', 1) == 1:
            score += self.config.weights['cloud_free']
            
        return min(1.0, score)
    
    def classify_debris_type(self, indices: Dict[str, float]) -> str:
        """
        Classify type of marine debris based on spectral characteristics
        """
        fdi = indices.get('fdi', 0)
        ndvi = indices.get('ndvi', 0)
        fai = indices.get('fai', 0)
        
        # Classification logic based on research
        if fdi > 0.03 and ndvi < 0.1:
            return "플라스틱 (Plastic)"
        elif fdi > 0.02 and ndvi > 0.2:
            return "혼합 폐기물 (Mixed debris)"
        elif fai > fdi and ndvi > 0.3:
            return "해조류/유기물 (Seaweed/Organic)"
        elif fdi > 0.015 and ndvi < 0.2:
            return "어망/로프 (Fishing nets/Ropes)"
        else:
            return "미분류 폐기물 (Unclassified debris)"
    
    def get_optimal_time_window(self, region: str) -> Tuple[datetime, datetime]:
        """
        Get optimal time window for detection based on region and season
        """
        now = datetime.now()
        
        # Korean waters have different optimal periods
        if region in ['west_sea', 'south_sea']:
            # Summer monsoon brings more debris (June-September)
            if 6 <= now.month <= 9:
                # Look at recent data during monsoon season
                return now - timedelta(days=7), now
            else:
                # Look at longer window during dry season
                return now - timedelta(days=14), now
        else:  # East Sea
            # Less seasonal variation, consistent monitoring
            return now - timedelta(days=10), now
    
    def apply_machine_learning_filter(self, detections: List[Dict]) -> List[Dict]:
        """
        Apply ML-based filtering to reduce false positives
        Based on research findings
        """
        filtered = []
        
        for detection in detections:
            # Multi-criteria filtering
            confidence = detection.get('confidence', 0)
            size = detection.get('patch_size', 0)
            indices = detection.get('indices', {})
            
            # Size filter - minimum 100m² (10x10m)
            if size < self.config.min_patch_size:
                continue
                
            # Spectral consistency check
            fdi = indices.get('fdi', 0)
            ndwi = indices.get('ndwi', 0)
            
            # Research shows FDI and NDWI are most reliable
            if fdi > self.config.fdi_threshold and ndwi > self.config.ndwi_threshold:
                # High confidence detection
                detection['ml_confidence'] = min(1.0, confidence * 1.2)
                filtered.append(detection)
            elif fdi > self.config.fdi_threshold * 0.7 and confidence > 0.6:
                # Medium confidence detection
                detection['ml_confidence'] = confidence
                filtered.append(detection)
                
        return filtered
    
    def generate_alert_priority(self, detection: Dict) -> str:
        """
        Generate alert priority based on detection characteristics
        """
        confidence = detection.get('ml_confidence', detection.get('confidence', 0))
        size = detection.get('patch_size', 0)
        location = detection.get('location', {})
        debris_type = detection.get('debris_type', '')
        
        # Priority scoring
        priority_score = 0
        
        # Confidence contribution
        priority_score += confidence * 30
        
        # Size contribution (larger patches = higher priority)
        if size > 10000:  # > 1 hectare
            priority_score += 30
        elif size > 1000:  # > 0.1 hectare
            priority_score += 20
        elif size > 100:
            priority_score += 10
            
        # Location contribution (priority zones)
        for region_data in self.korea_regions.values():
            for priority_zone in region_data.get('priority_zones', []):
                if self._in_bbox(location, priority_zone):
                    priority_score += 20
                    break
                    
        # Debris type contribution
        if '플라스틱' in debris_type:
            priority_score += 10
        elif '어망' in debris_type:
            priority_score += 15  # Fishing nets are high priority
            
        # Determine priority level
        if priority_score >= 70:
            return "critical"
        elif priority_score >= 50:
            return "high"
        elif priority_score >= 30:
            return "medium"
        else:
            return "low"
    
    def _in_bbox(self, location: Dict, bbox: List[float]) -> bool:
        """Check if location is within bounding box"""
        lon = location.get('longitude', 0)
        lat = location.get('latitude', 0)
        return (bbox[0] <= lon <= bbox[2] and 
                bbox[1] <= lat <= bbox[3])
    
    def get_detection_statistics(self, detections: List[Dict]) -> Dict:
        """
        Generate statistics from detections
        """
        stats = {
            'total_detections': len(detections),
            'by_type': {},
            'by_region': {},
            'by_priority': {},
            'total_area': 0,
            'average_confidence': 0
        }
        
        for detection in detections:
            # By type
            debris_type = detection.get('debris_type', 'Unknown')
            stats['by_type'][debris_type] = stats['by_type'].get(debris_type, 0) + 1
            
            # By region
            region = detection.get('region', 'Unknown')
            stats['by_region'][region] = stats['by_region'].get(region, 0) + 1
            
            # By priority
            priority = detection.get('priority', 'low')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Total area
            stats['total_area'] += detection.get('patch_size', 0)
            
            # Average confidence
            stats['average_confidence'] += detection.get('ml_confidence', 
                                                        detection.get('confidence', 0))
        
        if detections:
            stats['average_confidence'] /= len(detections)
            
        return stats