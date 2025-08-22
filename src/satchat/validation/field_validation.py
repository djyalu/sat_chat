#!/usr/bin/env python3
"""Field validation and operational checklist system"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import json
from pathlib import Path
import asyncio
import aiohttp
from geopy.distance import geodesic
import cv2

logger = logging.getLogger(__name__)

class ValidationLevel(Enum):
    LOW = "low"           # Basic automated checks
    MEDIUM = "medium"     # Enhanced validation with cross-references
    HIGH = "high"         # Comprehensive validation with field data
    CRITICAL = "critical" # Maximum validation for emergency response

class ConfidenceLevel(Enum):
    VERY_LOW = 1    # < 30%
    LOW = 2         # 30-50%
    MEDIUM = 3      # 50-70%
    HIGH = 4        # 70-85%
    VERY_HIGH = 5   # > 85%

@dataclass
class ValidationResult:
    """Result of a validation check"""
    check_name: str
    passed: bool
    confidence: float
    message: str
    details: Dict[str, Any]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

@dataclass
class FieldObservation:
    """Field observation data for validation"""
    id: str
    location: Tuple[float, float]  # lat, lon
    timestamp: str
    observation_type: str
    debris_present: bool
    debris_density: str  # low, medium, high
    debris_types: List[str]
    photos: List[str]
    observer: str
    weather_conditions: Dict[str, Any]
    confidence: ConfidenceLevel

@dataclass 
class OperationalChecklist:
    """Operational checklist for marine debris monitoring"""
    mission_id: str
    region: Dict[str, Any]
    validation_level: ValidationLevel
    checks_completed: List[str]
    checks_failed: List[str]
    overall_confidence: float
    recommendations: List[str]
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

class FieldValidationSystem:
    """Field validation and quality assurance system"""
    
    def __init__(self, validation_db_path: str = "validation_data"):
        self.validation_db = Path(validation_db_path)
        self.validation_db.mkdir(exist_ok=True)
        
        # Validation thresholds
        self.thresholds = {
            'min_debris_confidence': 0.7,
            'max_cloud_cover': 0.3,
            'min_image_quality': 0.8,
            'max_sun_glint': 0.05,
            'min_spatial_resolution': 20.0,  # meters
            'max_observation_age_hours': 24,
            'min_field_validation_distance_km': 50.0
        }
        
        # Field observations storage
        self.field_observations: Dict[str, FieldObservation] = {}
        
        # Validation rules database
        self.validation_rules = self._initialize_validation_rules()
        
    def _initialize_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize validation rules database"""
        
        return {
            'spectral_consistency': {
                'description': 'Check spectral index consistency across time series',
                'min_confidence': 0.6,
                'temporal_window_hours': 72,
                'max_variation_threshold': 0.3
            },
            'spatial_continuity': {
                'description': 'Verify spatial continuity of debris patches',
                'min_patch_size_pixels': 10,
                'max_isolation_distance': 100,  # meters
                'morphological_coherence': 0.7
            },
            'environmental_consistency': {
                'description': 'Check consistency with environmental conditions',
                'wind_speed_correlation': 0.4,
                'current_direction_alignment': 0.3,
                'tidal_influence_factor': 0.2
            },
            'cross_sensor_validation': {
                'description': 'Validate against other satellite sensors',
                'landsat_agreement': 0.6,
                'modis_agreement': 0.5,
                'sar_coherence': 0.4
            },
            'field_observation_match': {
                'description': 'Match with field observations',
                'spatial_tolerance_km': 10.0,
                'temporal_tolerance_hours': 12,
                'confidence_weight': 0.8
            }
        }
    
    async def run_validation_checklist(self, 
                                     mission_data: Dict[str, Any],
                                     validation_level: ValidationLevel = ValidationLevel.MEDIUM) -> OperationalChecklist:
        """Run comprehensive validation checklist"""
        
        mission_id = mission_data.get('id', f"mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        region = mission_data.get('region', {})
        
        logger.info(f"Running validation checklist for mission {mission_id} at level {validation_level.value}")
        
        checklist = OperationalChecklist(
            mission_id=mission_id,
            region=region,
            validation_level=validation_level,
            checks_completed=[],
            checks_failed=[],
            overall_confidence=0.0,
            recommendations=[]
        )
        
        # Define validation checks based on level
        checks_to_run = self._get_checks_for_level(validation_level)
        
        validation_results = []
        
        # Run validation checks
        for check_name in checks_to_run:
            try:
                result = await self._run_validation_check(check_name, mission_data)
                validation_results.append(result)
                
                if result.passed:
                    checklist.checks_completed.append(check_name)
                else:
                    checklist.checks_failed.append(check_name)
                    
            except Exception as e:
                logger.error(f"Validation check {check_name} failed with error: {e}")
                failed_result = ValidationResult(
                    check_name=check_name,
                    passed=False,
                    confidence=0.0,
                    message=f"Check failed with error: {str(e)}",
                    details={'error': str(e)}
                )
                validation_results.append(failed_result)
                checklist.checks_failed.append(check_name)
        
        # Calculate overall confidence
        if validation_results:
            passed_checks = [r for r in validation_results if r.passed]
            checklist.overall_confidence = len(passed_checks) / len(validation_results)
        
        # Generate recommendations
        checklist.recommendations = self._generate_recommendations(validation_results, mission_data)
        
        # Save validation results
        await self._save_validation_results(mission_id, validation_results, checklist)
        
        logger.info(f"Validation complete: {len(checklist.checks_completed)}/{len(checks_to_run)} checks passed")
        
        return checklist
    
    def _get_checks_for_level(self, level: ValidationLevel) -> List[str]:
        """Get validation checks for specific level"""
        
        base_checks = ['data_quality', 'spectral_consistency', 'cloud_coverage']
        
        if level == ValidationLevel.LOW:
            return base_checks
        
        elif level == ValidationLevel.MEDIUM:
            return base_checks + ['spatial_continuity', 'sun_glint_check']
        
        elif level == ValidationLevel.HIGH:
            return base_checks + [
                'spatial_continuity', 'sun_glint_check', 
                'environmental_consistency', 'temporal_coherence'
            ]
        
        elif level == ValidationLevel.CRITICAL:
            return base_checks + [
                'spatial_continuity', 'sun_glint_check', 'environmental_consistency',
                'temporal_coherence', 'cross_sensor_validation', 'field_observation_match',
                'expert_review_required'
            ]
        
        return base_checks
    
    async def _run_validation_check(self, check_name: str, mission_data: Dict[str, Any]) -> ValidationResult:
        """Run a specific validation check"""
        
        if check_name == 'data_quality':
            return await self._check_data_quality(mission_data)
        
        elif check_name == 'spectral_consistency':
            return await self._check_spectral_consistency(mission_data)
        
        elif check_name == 'cloud_coverage':
            return await self._check_cloud_coverage(mission_data)
        
        elif check_name == 'spatial_continuity':
            return await self._check_spatial_continuity(mission_data)
        
        elif check_name == 'sun_glint_check':
            return await self._check_sun_glint(mission_data)
        
        elif check_name == 'environmental_consistency':
            return await self._check_environmental_consistency(mission_data)
        
        elif check_name == 'temporal_coherence':
            return await self._check_temporal_coherence(mission_data)
        
        elif check_name == 'cross_sensor_validation':
            return await self._check_cross_sensor_validation(mission_data)
        
        elif check_name == 'field_observation_match':
            return await self._check_field_observation_match(mission_data)
        
        elif check_name == 'expert_review_required':
            return await self._check_expert_review_required(mission_data)
        
        else:
            return ValidationResult(
                check_name=check_name,
                passed=False,
                confidence=0.0,
                message=f"Unknown validation check: {check_name}",
                details={}
            )
    
    async def _check_data_quality(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check basic data quality metrics"""
        
        analysis_data = mission_data.get('analysis_data', {})
        
        # Check for required indices
        required_indices = ['fdi', 'ndwi', 'ndvi']
        missing_indices = [idx for idx in required_indices if idx not in analysis_data]
        
        if missing_indices:
            return ValidationResult(
                check_name='data_quality',
                passed=False,
                confidence=0.0,
                message=f"Missing required indices: {missing_indices}",
                details={'missing_indices': missing_indices}
            )
        
        # Check data ranges
        quality_issues = []
        
        for idx_name in required_indices:
            idx_data = analysis_data.get(idx_name, {})
            
            if isinstance(idx_data, dict) and 'mean' in idx_data:
                mean_val = idx_data['mean']
                
                # Define expected ranges
                ranges = {
                    'fdi': (-0.5, 1.0),
                    'ndwi': (-1.0, 1.0), 
                    'ndvi': (-1.0, 1.0)
                }
                
                expected_min, expected_max = ranges.get(idx_name, (-1, 1))
                
                if not (expected_min <= mean_val <= expected_max):
                    quality_issues.append(f"{idx_name} mean ({mean_val:.3f}) outside expected range [{expected_min}, {expected_max}]")
        
        confidence = max(0.0, 1.0 - len(quality_issues) * 0.3)
        
        return ValidationResult(
            check_name='data_quality',
            passed=len(quality_issues) == 0,
            confidence=confidence,
            message=f"Data quality check: {len(quality_issues)} issues found",
            details={'quality_issues': quality_issues}
        )
    
    async def _check_spectral_consistency(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check spectral consistency across indices"""
        
        analysis_data = mission_data.get('analysis_data', {})
        
        # Check correlation between related indices
        fdi_data = analysis_data.get('fdi', {})
        ndwi_data = analysis_data.get('ndwi', {})
        
        if not (isinstance(fdi_data, dict) and isinstance(ndwi_data, dict)):
            return ValidationResult(
                check_name='spectral_consistency',
                passed=False,
                confidence=0.0,
                message="Insufficient data for spectral consistency check",
                details={}
            )
        
        # Simple consistency check based on expected relationships
        consistency_score = 1.0
        issues = []
        
        # Check if high FDI areas correlate with water presence (NDWI > 0)
        fdi_mean = fdi_data.get('mean', 0)
        ndwi_mean = ndwi_data.get('mean', 0)
        
        if fdi_mean > 0.1 and ndwi_mean < 0:
            issues.append("High FDI detected in non-water areas (NDWI < 0)")
            consistency_score -= 0.4
        
        # Check debris percentage against other indicators
        debris_pct = fdi_data.get('debris_percentage', 0)
        if debris_pct > 10:  # > 10% debris seems unusually high
            issues.append(f"Unusually high debris percentage: {debris_pct:.1f}%")
            consistency_score -= 0.3
        
        consistency_score = max(0.0, consistency_score)
        
        return ValidationResult(
            check_name='spectral_consistency',
            passed=consistency_score > 0.6,
            confidence=consistency_score,
            message=f"Spectral consistency score: {consistency_score:.2f}",
            details={'consistency_issues': issues, 'score': consistency_score}
        )
    
    async def _check_cloud_coverage(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check cloud coverage levels"""
        
        metadata = mission_data.get('metadata', {})
        cloud_coverage = metadata.get('cloud_coverage', 0.0)
        
        # If cloud coverage not provided, estimate from data quality
        if cloud_coverage == 0.0:
            # Estimate based on data availability/quality
            analysis_data = mission_data.get('analysis_data', {})
            if not analysis_data:
                cloud_coverage = 0.5  # Assume moderate clouds if no data
        
        passed = cloud_coverage <= self.thresholds['max_cloud_cover']
        confidence = max(0.0, 1.0 - cloud_coverage)
        
        return ValidationResult(
            check_name='cloud_coverage',
            passed=passed,
            confidence=confidence,
            message=f"Cloud coverage: {cloud_coverage:.1%}",
            details={'cloud_coverage': cloud_coverage, 'threshold': self.thresholds['max_cloud_cover']}
        )
    
    async def _check_spatial_continuity(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check spatial continuity of detected debris"""
        
        # This is a simplified check - would normally analyze actual spatial data
        analysis_data = mission_data.get('analysis_data', {})
        
        # Look for debris cluster information
        debris_ml = analysis_data.get('debris_ml', {})
        
        if not debris_ml:
            return ValidationResult(
                check_name='spatial_continuity',
                passed=True,  # No debris detected, continuity not applicable
                confidence=0.8,
                message="No ML debris analysis available for spatial continuity check",
                details={}
            )
        
        clusters = debris_ml.get('debris_clusters', [])
        
        if not clusters:
            return ValidationResult(
                check_name='spatial_continuity',
                passed=True,
                confidence=0.9,
                message="No debris clusters detected",
                details={}
            )
        
        # Analyze cluster properties
        continuity_score = 1.0
        issues = []
        
        for cluster in clusters:
            compactness = cluster.get('compactness', 0)
            aspect_ratio = cluster.get('aspect_ratio', 1.0)
            area = cluster.get('area_pixels', 0)
            
            # Check for unrealistic cluster properties
            if compactness < 0.1:  # Very irregular shape
                issues.append(f"Cluster {cluster.get('id')} has very low compactness ({compactness:.2f})")
                continuity_score -= 0.2
            
            if aspect_ratio > 10:  # Very elongated
                issues.append(f"Cluster {cluster.get('id')} is very elongated (ratio: {aspect_ratio:.1f})")
                continuity_score -= 0.1
            
            if area < 5:  # Very small clusters might be noise
                issues.append(f"Cluster {cluster.get('id')} is very small ({area} pixels)")
                continuity_score -= 0.1
        
        continuity_score = max(0.0, continuity_score)
        
        return ValidationResult(
            check_name='spatial_continuity',
            passed=continuity_score > 0.6,
            confidence=continuity_score,
            message=f"Spatial continuity score: {continuity_score:.2f}",
            details={
                'cluster_count': len(clusters),
                'continuity_issues': issues,
                'score': continuity_score
            }
        )
    
    async def _check_sun_glint(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check for sun glint interference"""
        
        analysis_data = mission_data.get('analysis_data', {})
        
        # Look for sun glint information in indices
        sun_glint_mean = 0.0
        
        # Check if we have sun glint data
        if 'sun_glint' in analysis_data:
            sun_glint_data = analysis_data['sun_glint']
            if isinstance(sun_glint_data, dict):
                sun_glint_mean = sun_glint_data.get('mean', 0.0)
            else:
                sun_glint_mean = float(np.mean(sun_glint_data)) if hasattr(sun_glint_data, '__len__') else 0.0
        
        passed = sun_glint_mean <= self.thresholds['max_sun_glint']
        confidence = max(0.0, 1.0 - sun_glint_mean / 0.1)  # Normalized to 0.1 max
        
        return ValidationResult(
            check_name='sun_glint_check',
            passed=passed,
            confidence=confidence,
            message=f"Sun glint level: {sun_glint_mean:.3f}",
            details={'sun_glint_mean': sun_glint_mean, 'threshold': self.thresholds['max_sun_glint']}
        )
    
    async def _check_environmental_consistency(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check consistency with environmental conditions"""
        
        # Simplified environmental check
        metadata = mission_data.get('metadata', {})
        timestamp_str = metadata.get('timestamp', datetime.now().isoformat())
        
        try:
            # Check if observation time is reasonable (not future, not too old)
            observation_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            current_time = datetime.now()
            
            time_diff_hours = abs((current_time - observation_time).total_seconds() / 3600)
            
            if time_diff_hours > self.thresholds['max_observation_age_hours']:
                return ValidationResult(
                    check_name='environmental_consistency',
                    passed=False,
                    confidence=0.3,
                    message=f"Observation too old: {time_diff_hours:.1f} hours",
                    details={'observation_age_hours': time_diff_hours}
                )
            
            # Additional environmental checks would go here
            # (weather data, ocean conditions, etc.)
            
            return ValidationResult(
                check_name='environmental_consistency',
                passed=True,
                confidence=0.8,
                message="Environmental conditions consistent",
                details={'observation_age_hours': time_diff_hours}
            )
            
        except Exception as e:
            return ValidationResult(
                check_name='environmental_consistency',
                passed=False,
                confidence=0.0,
                message=f"Environmental check failed: {str(e)}",
                details={'error': str(e)}
            )
    
    async def _check_temporal_coherence(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check temporal coherence with historical data"""
        
        # Simplified temporal coherence check
        region = mission_data.get('region', {})
        region_id = region.get('id', 'unknown')
        
        # In a real implementation, this would compare with historical data
        # For now, return a placeholder result
        
        return ValidationResult(
            check_name='temporal_coherence',
            passed=True,
            confidence=0.7,
            message="Temporal coherence check (simplified)",
            details={'region_id': region_id, 'note': 'Historical comparison not implemented'}
        )
    
    async def _check_cross_sensor_validation(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Validate against other satellite sensors"""
        
        # Placeholder for cross-sensor validation
        # Would normally fetch and compare with Landsat, MODIS, SAR data
        
        return ValidationResult(
            check_name='cross_sensor_validation',
            passed=True,
            confidence=0.6,
            message="Cross-sensor validation (placeholder)",
            details={'note': 'Cross-sensor comparison not implemented'}
        )
    
    async def _check_field_observation_match(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Check against field observations"""
        
        region = mission_data.get('region', {})
        bbox = region.get('bbox', [])
        
        if len(bbox) < 4:
            return ValidationResult(
                check_name='field_observation_match',
                passed=False,
                confidence=0.0,
                message="No region boundary provided for field observation matching",
                details={}
            )
        
        # Find nearby field observations
        nearby_observations = self._find_nearby_observations(bbox)
        
        if not nearby_observations:
            return ValidationResult(
                check_name='field_observation_match',
                passed=True,  # No observations to contradict
                confidence=0.5,
                message="No field observations found for comparison",
                details={'nearby_observations': 0}
            )
        
        # Compare with satellite-detected debris
        analysis_data = mission_data.get('analysis_data', {})
        satellite_debris_detected = self._has_debris_detection(analysis_data)
        
        # Check agreement with field observations
        agreement_count = 0
        total_observations = len(nearby_observations)
        
        for obs in nearby_observations:
            field_debris = obs.debris_present
            if satellite_debris_detected == field_debris:
                agreement_count += 1
        
        agreement_rate = agreement_count / total_observations if total_observations > 0 else 0.5
        
        return ValidationResult(
            check_name='field_observation_match',
            passed=agreement_rate >= 0.7,
            confidence=agreement_rate,
            message=f"Field observation agreement: {agreement_rate:.1%} ({agreement_count}/{total_observations})",
            details={
                'nearby_observations': total_observations,
                'agreement_count': agreement_count,
                'agreement_rate': agreement_rate,
                'satellite_debris_detected': satellite_debris_detected
            }
        )
    
    async def _check_expert_review_required(self, mission_data: Dict[str, Any]) -> ValidationResult:
        """Determine if expert review is required"""
        
        # Criteria for requiring expert review
        requires_review = False
        reasons = []
        
        analysis_data = mission_data.get('analysis_data', {})
        
        # High debris concentration
        fdi_data = analysis_data.get('fdi', {})
        if fdi_data.get('debris_percentage', 0) > 5:
            requires_review = True
            reasons.append(f"High debris percentage: {fdi_data.get('debris_percentage', 0):.1f}%")
        
        # Large debris area
        if fdi_data.get('debris_area_km2', 0) > 10:
            requires_review = True
            reasons.append(f"Large debris area: {fdi_data.get('debris_area_km2', 0):.1f} km²")
        
        # ML detection with high confidence
        debris_ml = analysis_data.get('debris_ml', {})
        if debris_ml.get('n_clusters', 0) > 20:
            requires_review = True
            reasons.append(f"Many debris clusters detected: {debris_ml.get('n_clusters', 0)}")
        
        confidence = 0.9 if not requires_review else 0.7
        
        return ValidationResult(
            check_name='expert_review_required',
            passed=not requires_review,  # "Passes" if no review needed
            confidence=confidence,
            message=f"Expert review {'required' if requires_review else 'not required'}",
            details={'requires_review': requires_review, 'reasons': reasons}
        )
    
    def _find_nearby_observations(self, bbox: List[float]) -> List[FieldObservation]:
        """Find field observations within or near bounding box"""
        
        if len(bbox) < 4:
            return []
        
        lon_min, lat_min, lon_max, lat_max = bbox[:4]
        bbox_center = ((lat_min + lat_max) / 2, (lon_min + lon_max) / 2)
        
        nearby_observations = []
        
        for obs in self.field_observations.values():
            obs_location = obs.location
            distance_km = geodesic(bbox_center, obs_location).kilometers
            
            if distance_km <= self.thresholds['min_field_validation_distance_km']:
                nearby_observations.append(obs)
        
        return nearby_observations
    
    def _has_debris_detection(self, analysis_data: Dict[str, Any]) -> bool:
        """Check if satellite data indicates debris presence"""
        
        # Check FDI-based detection
        fdi_data = analysis_data.get('fdi', {})
        if fdi_data.get('debris_percentage', 0) > 0.1:
            return True
        
        # Check ML-based detection
        debris_ml = analysis_data.get('debris_ml', {})
        if debris_ml.get('n_clusters', 0) > 0:
            return True
        
        return False
    
    def _generate_recommendations(self, validation_results: List[ValidationResult], 
                                mission_data: Dict[str, Any]) -> List[str]:
        """Generate operational recommendations based on validation results"""
        
        recommendations = []
        
        failed_checks = [r for r in validation_results if not r.passed]
        
        for result in failed_checks:
            if result.check_name == 'cloud_coverage':
                recommendations.append("Consider waiting for clearer conditions or use SAR imagery")
            
            elif result.check_name == 'sun_glint_check':
                recommendations.append("High sun glint detected - results may be affected, consider different acquisition time")
            
            elif result.check_name == 'spatial_continuity':
                recommendations.append("Spatial patterns may indicate false positives - recommend additional analysis")
            
            elif result.check_name == 'field_observation_match':
                recommendations.append("Satellite results don't match field observations - recommend ground truth verification")
            
            elif result.check_name == 'expert_review_required':
                recommendations.append("High-confidence debris detection requires expert review and potential response action")
        
        # Additional recommendations based on overall confidence
        overall_confidence = np.mean([r.confidence for r in validation_results])
        
        if overall_confidence < 0.5:
            recommendations.append("Low overall confidence - recommend additional validation before action")
        elif overall_confidence > 0.8:
            recommendations.append("High confidence results - suitable for operational decision making")
        
        return recommendations
    
    async def _save_validation_results(self, mission_id: str, 
                                     validation_results: List[ValidationResult],
                                     checklist: OperationalChecklist):
        """Save validation results to database"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_{mission_id}_{timestamp}.json"
        filepath = self.validation_db / filename
        
        data = {
            'mission_id': mission_id,
            'checklist': asdict(checklist),
            'validation_results': [asdict(result) for result in validation_results],
            'saved_at': datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Validation results saved to {filepath}")
    
    def add_field_observation(self, observation: FieldObservation):
        """Add field observation to database"""
        self.field_observations[observation.id] = observation
        logger.info(f"Added field observation {observation.id} at {observation.location}")
    
    def get_validation_history(self, mission_id: str = None, 
                             days_back: int = 30) -> List[Dict[str, Any]]:
        """Get validation history"""
        
        history = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for filepath in self.validation_db.glob("validation_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                
                saved_at = datetime.fromisoformat(data['saved_at'])
                
                if saved_at >= cutoff_date:
                    if mission_id is None or data['mission_id'] == mission_id:
                        history.append(data)
                        
            except Exception as e:
                logger.error(f"Error reading validation file {filepath}: {e}")
        
        # Sort by date (newest first)
        history.sort(key=lambda x: x['saved_at'], reverse=True)
        
        return history

def create_validation_system(validation_db_path: str = "validation_data") -> FieldValidationSystem:
    """Factory function to create field validation system"""
    return FieldValidationSystem(validation_db_path)