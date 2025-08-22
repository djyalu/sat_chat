#!/usr/bin/env python3
"""ML-based marine debris segmentation system"""

import numpy as np
from typing import Dict, Tuple, Optional, List
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import cv2
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MarineSegmentationML:
    """ML-based segmentation for marine debris detection"""
    
    def __init__(self):
        self.rf_classifier = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
        # MARIDA dataset inspired class definitions
        self.classes = {
            0: "Marine_Water",
            1: "Sediment-Laden_Water", 
            2: "Foam",
            3: "Turbid_Water",
            4: "Shallow_Water",
            5: "Waves",
            6: "Oil_Spill",
            7: "Marine_Debris",
            8: "Dense_Sargassum",
            9: "Sparse_Sargassum",
            10: "Natural_Organic_Material",
            11: "Ship",
            12: "Clouds",
            13: "Marine_Water_2",
            14: "Sediment-Laden_Water_2",
            15: "Foam_2",
            16: "Turbid_Water_2",
            17: "Shallow_Water_2",
            18: "Waves_2",
            19: "Oil_Spill_2",
            20: "Marine_Debris_2",
            21: "Dense_Sargassum_2",
            22: "Sparse_Sargassum_2"
        }
        
        # Priority classes for marine debris detection
        self.debris_classes = [7, 20]  # Marine_Debris classes
        self.organic_classes = [8, 9, 10, 21, 22]  # Sargassum and organic
        self.water_classes = [0, 1, 3, 4, 13, 14, 16, 17]  # Water types
        
    def extract_ml_features(self, bands: np.ndarray, indices: Dict[str, np.ndarray]) -> np.ndarray:
        """Extract comprehensive feature vector for ML classification"""
        
        # Spectral features
        blue = bands[..., 0] / 10000.0
        green = bands[..., 1] / 10000.0
        red = bands[..., 2] / 10000.0
        nir = bands[..., 7] / 10000.0
        swir1 = bands[..., 9] if bands.shape[-1] > 9 else bands[..., 8] / 10000.0
        swir2 = bands[..., 10] if bands.shape[-1] > 10 else swir1 / 10000.0
        
        features = []
        
        # 1. Raw spectral bands
        features.extend([blue.flatten(), green.flatten(), red.flatten(), 
                        nir.flatten(), swir1.flatten(), swir2.flatten()])
        
        # 2. Spectral indices
        features.append(indices['fdi'].flatten())
        features.append(indices['ndwi'].flatten())
        features.append(indices['mci'].flatten())
        features.append(indices['fai'].flatten())
        
        # 3. Derived ratios
        red_green_ratio = red / (green + 1e-10)
        nir_red_ratio = nir / (red + 1e-10)
        swir_nir_ratio = swir1 / (nir + 1e-10)
        
        features.extend([red_green_ratio.flatten(), nir_red_ratio.flatten(), 
                        swir_nir_ratio.flatten()])
        
        # 4. Texture features (using OpenCV for efficiency)
        gray = cv2.cvtColor((np.stack([red, green, blue], axis=-1) * 255).astype(np.uint8), 
                           cv2.COLOR_RGB2GRAY)
        
        # Gradient magnitude
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        gradient_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Local standard deviation (texture)
        kernel = np.ones((5,5), np.float32) / 25
        local_mean = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        local_std = cv2.filter2D((gray.astype(np.float32) - local_mean)**2, -1, kernel)
        
        features.extend([gradient_mag.flatten(), local_std.flatten()])
        
        # 5. Contextual features
        # Distance from water edge (simplified)
        water_mask = indices['ndwi'] > 0
        dist_from_water = cv2.distanceTransform(
            (~water_mask).astype(np.uint8), cv2.DIST_L2, 5)
        
        features.append(dist_from_water.flatten())
        
        return np.column_stack(features)
    
    def create_training_data(self, multi_bands: List[np.ndarray], 
                           multi_indices: List[Dict[str, np.ndarray]],
                           labels: Optional[List[np.ndarray]] = None) -> Tuple[np.ndarray, np.ndarray]:
        """Create training dataset from multiple images"""
        
        all_features = []
        all_labels = []
        
        for i, (bands, indices) in enumerate(zip(multi_bands, multi_indices)):
            features = self.extract_ml_features(bands, indices)
            all_features.append(features)
            
            if labels is not None and i < len(labels):
                all_labels.append(labels[i].flatten())
            else:
                # Generate pseudo-labels using rule-based approach
                pseudo_labels = self._generate_pseudo_labels(bands, indices)
                all_labels.append(pseudo_labels.flatten())
        
        X = np.vstack(all_features)
        y = np.hstack(all_labels)
        
        return X, y
    
    def _generate_pseudo_labels(self, bands: np.ndarray, 
                              indices: Dict[str, np.ndarray]) -> np.ndarray:
        """Generate pseudo-labels using rule-based classification"""
        
        h, w = indices['fdi'].shape
        labels = np.zeros((h, w), dtype=np.int32)
        
        # Water classification
        water_mask = indices['ndwi'] > 0.0
        labels[water_mask] = 0  # Marine_Water
        
        # High turbidity water
        turbid_mask = water_mask & (indices['turbidity'] > 0.05)
        labels[turbid_mask] = 3  # Turbid_Water
        
        # Marine debris (high FDI in water areas)
        debris_mask = water_mask & (indices['fdi'] > 0.1) & (indices['sun_glint'] < 0.02)
        labels[debris_mask] = 7  # Marine_Debris
        
        # Sargassum (high MCI/FAI in water)
        sargassum_dense = water_mask & (indices['mci'] > 0.01) & (indices['fai'] > 0.005)
        sargassum_sparse = water_mask & (indices['mci'] > 0.005) & (indices['fai'] > 0.002)
        
        labels[sargassum_dense] = 8   # Dense_Sargassum
        labels[sargassum_sparse] = 9  # Sparse_Sargassum
        
        # Foam/waves (high reflectance in water)
        blue = bands[..., 0] / 10000.0
        green = bands[..., 1] / 10000.0
        foam_mask = water_mask & (blue > 0.15) & (green > 0.15) & (indices['ndwi'] > 0.1)
        labels[foam_mask] = 2  # Foam
        
        return labels
    
    def train_classifier(self, bands_list: List[np.ndarray], 
                        indices_list: List[Dict[str, np.ndarray]],
                        labels_list: Optional[List[np.ndarray]] = None,
                        validation_split: float = 0.2) -> Dict:
        """Train Random Forest classifier"""
        
        logger.info("Creating training dataset...")
        X, y = self.create_training_data(bands_list, indices_list, labels_list)
        
        # Handle invalid values
        valid_mask = np.isfinite(X).all(axis=1) & (y >= 0)
        X = X[valid_mask]
        y = y[valid_mask]
        
        logger.info(f"Training with {len(X)} samples, {len(np.unique(y))} classes")
        
        # Split data
        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y
        )
        
        # Standardize features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_val_scaled = self.scaler.transform(X_val)
        
        # Train Random Forest
        self.rf_classifier = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        
        logger.info("Training Random Forest classifier...")
        self.rf_classifier.fit(X_train_scaled, y_train)
        
        # Validation
        val_score = self.rf_classifier.score(X_val_scaled, y_val)
        
        # Feature importance
        feature_names = [
            'blue', 'green', 'red', 'nir', 'swir1', 'swir2',
            'fdi', 'ndwi', 'mci', 'fai',
            'red_green_ratio', 'nir_red_ratio', 'swir_nir_ratio',
            'gradient_mag', 'texture_std', 'dist_from_water'
        ]
        
        importance = dict(zip(feature_names, self.rf_classifier.feature_importances_))
        
        self.is_trained = True
        
        training_results = {
            'validation_accuracy': val_score,
            'n_samples': len(X),
            'n_classes': len(np.unique(y)),
            'feature_importance': importance,
            'class_distribution': dict(zip(*np.unique(y, return_counts=True)))
        }
        
        logger.info(f"Training completed. Validation accuracy: {val_score:.3f}")
        
        return training_results
    
    def predict_segmentation(self, bands: np.ndarray, 
                           indices: Dict[str, np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """Predict segmentation map using trained ML model"""
        
        if not self.is_trained:
            logger.warning("Classifier not trained. Using rule-based fallback.")
            return self._generate_pseudo_labels(bands, indices), np.ones_like(indices['fdi']) * 0.5
        
        # Extract features
        features = self.extract_ml_features(bands, indices)
        
        # Handle invalid values
        valid_mask = np.isfinite(features).all(axis=1)
        
        # Initialize outputs
        h, w = indices['fdi'].shape
        segmentation = np.zeros((h, w), dtype=np.int32)
        confidence = np.zeros((h, w), dtype=np.float32)
        
        if np.any(valid_mask):
            # Scale features
            valid_features = self.scaler.transform(features[valid_mask])
            
            # Predict
            predictions = self.rf_classifier.predict(valid_features)
            probabilities = self.rf_classifier.predict_proba(valid_features)
            
            # Map back to image space
            segmentation_flat = segmentation.flatten()
            confidence_flat = confidence.flatten()
            
            segmentation_flat[valid_mask] = predictions
            confidence_flat[valid_mask] = np.max(probabilities, axis=1)
            
            segmentation = segmentation_flat.reshape((h, w))
            confidence = confidence_flat.reshape((h, w))
        
        return segmentation, confidence
    
    def analyze_marine_debris(self, segmentation: np.ndarray, 
                            confidence: np.ndarray,
                            min_confidence: float = 0.7) -> Dict:
        """Analyze marine debris from segmentation results"""
        
        # High-confidence debris pixels
        debris_mask = np.isin(segmentation, self.debris_classes)
        high_conf_debris = debris_mask & (confidence > min_confidence)
        
        # Connected component analysis
        debris_components, n_components = cv2.connectedComponents(
            high_conf_debris.astype(np.uint8), connectivity=8
        )
        
        # Analyze each debris cluster
        debris_clusters = []
        
        for i in range(1, n_components + 1):  # Skip background (0)
            cluster_mask = debris_components == i
            cluster_area = np.sum(cluster_mask)
            
            if cluster_area < 10:  # Filter small noise
                continue
            
            # Calculate cluster properties
            y_coords, x_coords = np.where(cluster_mask)
            centroid_y, centroid_x = np.mean(y_coords), np.mean(x_coords)
            
            # Confidence statistics
            cluster_confidences = confidence[cluster_mask]
            avg_confidence = np.mean(cluster_confidences)
            max_confidence = np.max(cluster_confidences)
            
            # Shape properties
            contours, _ = cv2.findContours(
                cluster_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if contours:
                contour = max(contours, key=cv2.contourArea)
                area_cv = cv2.contourArea(contour)
                perimeter = cv2.arcLength(contour, True)
                
                # Shape descriptors
                aspect_ratio = 1.0
                compactness = 4 * np.pi * area_cv / (perimeter ** 2) if perimeter > 0 else 0
                
                if len(contour) >= 5:
                    ellipse = cv2.fitEllipse(contour)
                    aspect_ratio = max(ellipse[1]) / (min(ellipse[1]) + 1e-10)
            else:
                area_cv = cluster_area
                perimeter = 0
                aspect_ratio = 1.0
                compactness = 0
            
            debris_clusters.append({
                'id': i,
                'centroid': (float(centroid_x), float(centroid_y)),
                'area_pixels': int(cluster_area),
                'area_m2': float(cluster_area * 100),  # 10m resolution
                'avg_confidence': float(avg_confidence),
                'max_confidence': float(max_confidence),
                'aspect_ratio': float(aspect_ratio),
                'compactness': float(compactness),
                'perimeter': float(perimeter)
            })
        
        # Overall statistics
        total_debris_area = np.sum(high_conf_debris)
        total_pixels = segmentation.size
        debris_percentage = (total_debris_area / total_pixels) * 100
        
        # Classification summary
        unique_classes, class_counts = np.unique(segmentation, return_counts=True)
        class_summary = {}
        
        for cls, count in zip(unique_classes, class_counts):
            if cls in self.classes:
                class_summary[self.classes[cls]] = {
                    'pixel_count': int(count),
                    'percentage': float(count / total_pixels * 100)
                }
        
        return {
            'debris_clusters': debris_clusters,
            'total_debris_area_m2': float(total_debris_area * 100),
            'debris_percentage': float(debris_percentage),
            'n_clusters': len(debris_clusters),
            'class_summary': class_summary,
            'analysis_timestamp': datetime.now().isoformat()
        }

def create_ml_segmentation_pipeline():
    """Factory function to create ML segmentation pipeline"""
    return MarineSegmentationML()