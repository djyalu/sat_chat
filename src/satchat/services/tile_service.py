#!/usr/bin/env python3
"""OGC/XYZ tile service for real-time marine debris visualization"""

import numpy as np
import io
import math
from typing import Tuple, Optional, Dict, Any
from PIL import Image
from flask import Flask, Response, request, jsonify
import mercantile
from datetime import datetime, timedelta
import logging
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import redis
from functools import lru_cache

from ..processing.multi_index_analyzer import MultiIndexAnalyzer
from ..ml.marine_segmentation import MarineSegmentationML

logger = logging.getLogger(__name__)

class TileService:
    """OGC/XYZ compliant tile service for marine debris monitoring"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        self.analyzer = MultiIndexAnalyzer()
        self.ml_segmentation = MarineSegmentationML()
        
        # Redis cache for tiles
        try:
            self.cache = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=False)
            self.cache_enabled = True
        except:
            logger.warning("Redis not available, running without cache")
            self.cache = None
            self.cache_enabled = False
        
        # Tile configuration
        self.tile_size = 256
        self.max_zoom = 18
        self.min_zoom = 8
        self.cache_ttl = 3600  # 1 hour
        
        # Thread pool for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """Convert lat/lon to tile coordinates"""
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        xtile = int((lon_deg + 180.0) / 360.0 * n)
        ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (xtile, ytile)
    
    def num2deg(self, xtile: int, ytile: int, zoom: int) -> Tuple[float, float, float, float]:
        """Convert tile coordinates to bounding box"""
        n = 2.0 ** zoom
        lon_deg_min = xtile / n * 360.0 - 180.0
        lat_rad_min = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
        lat_deg_min = math.degrees(lat_rad_min)
        
        lon_deg_max = (xtile + 1) / n * 360.0 - 180.0
        lat_rad_max = math.atan(math.sinh(math.pi * (1 - 2 * (ytile + 1) / n)))
        lat_deg_max = math.degrees(lat_rad_max)
        
        return (lon_deg_min, lat_deg_min, lon_deg_max, lat_deg_max)
    
    def get_cache_key(self, layer: str, z: int, x: int, y: int, 
                     timestamp: str = None) -> str:
        """Generate cache key for tile"""
        if timestamp:
            return f"tile:{layer}:{z}:{x}:{y}:{timestamp}"
        else:
            return f"tile:{layer}:{z}:{x}:{y}"
    
    @lru_cache(maxsize=100)
    def get_sentinel_data_for_bbox(self, bbox_str: str, timestamp: str = None) -> Optional[np.ndarray]:
        """Get Sentinel data for bounding box (with caching)"""
        try:
            # Parse bbox
            lon_min, lat_min, lon_max, lat_max = map(float, bbox_str.split(','))
            
            # TODO: Replace with actual Sentinel Hub API call
            # For now, return synthetic data structure
            from ..api.real_sentinel_api import get_real_sentinel_data
            
            # Convert to region format (simplified)
            region_data = {
                'bbox': [lon_min, lat_min, lon_max, lat_max]
            }
            
            # Get sentinel data (this would need to be adapted)
            sentinel_data = get_real_sentinel_data('dynamic_region', region_data)
            
            return sentinel_data
            
        except Exception as e:
            logger.error(f"Error fetching Sentinel data: {e}")
            return None
    
    def create_rgb_tile(self, sentinel_data: np.ndarray, 
                       bbox: Tuple[float, float, float, float]) -> Image.Image:
        """Create RGB tile from Sentinel data"""
        
        # Extract RGB bands (0-2)
        if len(sentinel_data.shape) == 3 and sentinel_data.shape[2] >= 3:
            rgb_data = sentinel_data[..., :3]
        else:
            # Fallback synthetic data
            rgb_data = np.random.rand(self.tile_size, self.tile_size, 3) * 0.1 + 0.05
        
        # Normalize to 0-255
        rgb_normalized = np.clip(rgb_data * 255, 0, 255).astype(np.uint8)
        
        # Resize to tile size
        img = Image.fromarray(rgb_normalized)
        img = img.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
        
        return img
    
    def create_analysis_tile(self, sentinel_data: np.ndarray, 
                           analysis_type: str,
                           bbox: Tuple[float, float, float, float]) -> Image.Image:
        """Create analysis visualization tile"""
        
        try:
            # Create full-band structure for analyzer
            if len(sentinel_data.shape) == 3 and sentinel_data.shape[2] >= 6:
                # Use available bands
                full_bands = sentinel_data
            else:
                # Create synthetic band structure
                h, w = self.tile_size, self.tile_size
                full_bands = np.zeros((h, w, 12))  # 12 Sentinel-2 bands
                
                # Fill with synthetic data
                for i in range(12):
                    full_bands[..., i] = np.random.rand(h, w) * 1000 + 500
            
            # Calculate indices
            indices = self.analyzer.calculate_multi_indices(full_bands)
            
            # Create visualization based on analysis type
            if analysis_type == 'fdi':
                data = indices['fdi']
                colormap = self._apply_heatmap(data, vmin=-0.1, vmax=0.3)
                
            elif analysis_type == 'ndwi':
                data = indices['ndwi'] 
                colormap = self._apply_blue_colormap(data, vmin=-0.5, vmax=0.5)
                
            elif analysis_type == 'mci':
                data = indices['mci']
                colormap = self._apply_green_colormap(data, vmin=-0.01, vmax=0.05)
                
            elif analysis_type == 'debris':
                # ML-based debris detection
                if self.ml_segmentation.is_trained:
                    segmentation, confidence = self.ml_segmentation.predict_segmentation(
                        full_bands, indices)
                    
                    # Highlight debris classes
                    debris_mask = np.isin(segmentation, [7, 20])  # Marine debris classes
                    high_conf = confidence > 0.7
                    
                    colormap = np.zeros((data.shape[0], data.shape[1], 3))
                    colormap[debris_mask & high_conf] = [255, 0, 0]  # Red for high-conf debris
                    colormap[debris_mask & ~high_conf] = [255, 255, 0]  # Yellow for low-conf
                    
                else:
                    # Fallback to FDI-based detection
                    data = indices['fdi']
                    debris_mask = data > 0.1
                    colormap = self._apply_debris_colormap(data, debris_mask)
                
            else:
                # Default to RGB
                return self.create_rgb_tile(sentinel_data, bbox)
            
            # Convert to PIL Image
            img_array = np.clip(colormap, 0, 255).astype(np.uint8)
            img = Image.fromarray(img_array)
            img = img.resize((self.tile_size, self.tile_size), Image.Resampling.LANCZOS)
            
            return img
            
        except Exception as e:
            logger.error(f"Error creating analysis tile: {e}")
            # Return error tile
            return self._create_error_tile()
    
    def _apply_heatmap(self, data: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        """Apply heatmap colormap to data"""
        # Normalize data
        normalized = np.clip((data - vmin) / (vmax - vmin), 0, 1)
        
        # Create RGB heatmap
        colormap = np.zeros((*data.shape, 3))
        colormap[..., 0] = normalized * 255  # Red channel
        colormap[..., 1] = (1 - normalized) * normalized * 255 * 4  # Green channel
        colormap[..., 2] = (1 - normalized) * 255  # Blue channel
        
        return colormap
    
    def _apply_blue_colormap(self, data: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        """Apply blue colormap for water indices"""
        normalized = np.clip((data - vmin) / (vmax - vmin), 0, 1)
        
        colormap = np.zeros((*data.shape, 3))
        colormap[..., 2] = normalized * 255  # Blue channel
        colormap[..., 1] = normalized * 128  # Some green
        
        return colormap
    
    def _apply_green_colormap(self, data: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
        """Apply green colormap for vegetation indices"""
        normalized = np.clip((data - vmin) / (vmax - vmin), 0, 1)
        
        colormap = np.zeros((*data.shape, 3))
        colormap[..., 1] = normalized * 255  # Green channel
        colormap[..., 0] = normalized * 64   # Some red
        
        return colormap
    
    def _apply_debris_colormap(self, data: np.ndarray, debris_mask: np.ndarray) -> np.ndarray:
        """Apply debris-specific colormap"""
        colormap = np.zeros((*data.shape, 3))
        
        # Background water in blue
        water_mask = data > -0.5
        colormap[water_mask, 2] = 64
        
        # Debris in red-yellow gradient
        debris_intensity = np.clip(data[debris_mask], 0, 0.5) / 0.5
        colormap[debris_mask, 0] = 255  # Red
        colormap[debris_mask, 1] = debris_intensity * 255  # Yellow component
        
        return colormap
    
    def _create_error_tile(self) -> Image.Image:
        """Create error tile"""
        img = Image.new('RGB', (self.tile_size, self.tile_size), (128, 128, 128))
        return img
    
    def get_tile(self, layer: str, z: int, x: int, y: int, 
                timestamp: str = None) -> Optional[bytes]:
        """Get tile for specific layer and coordinates"""
        
        # Validate zoom level
        if z < self.min_zoom or z > self.max_zoom:
            return None
        
        # Check cache first
        cache_key = self.get_cache_key(layer, z, x, y, timestamp)
        
        if self.cache_enabled:
            cached_tile = self.cache.get(cache_key)
            if cached_tile:
                logger.debug(f"Cache hit for tile {layer}/{z}/{x}/{y}")
                return cached_tile
        
        try:
            # Get bounding box for tile
            bbox = self.num2deg(x, y, z)
            bbox_str = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
            
            # Get Sentinel data for this bbox
            sentinel_data = self.get_sentinel_data_for_bbox(bbox_str, timestamp)
            
            if sentinel_data is None:
                logger.warning(f"No Sentinel data for tile {layer}/{z}/{x}/{y}")
                return None
            
            # Create tile image based on layer
            if layer == 'rgb':
                tile_img = self.create_rgb_tile(sentinel_data, bbox)
            else:
                tile_img = self.create_analysis_tile(sentinel_data, layer, bbox)
            
            # Convert to bytes
            img_bytes = io.BytesIO()
            tile_img.save(img_bytes, format='PNG', optimize=True)
            tile_data = img_bytes.getvalue()
            
            # Cache the result
            if self.cache_enabled:
                self.cache.setex(cache_key, self.cache_ttl, tile_data)
                logger.debug(f"Cached tile {layer}/{z}/{x}/{y}")
            
            return tile_data
            
        except Exception as e:
            logger.error(f"Error generating tile {layer}/{z}/{x}/{y}: {e}")
            return None
    
    def get_tile_metadata(self, layer: str) -> Dict[str, Any]:
        """Get metadata for tile layer"""
        
        base_metadata = {
            'name': layer,
            'title': f'Marine Debris - {layer.upper()}',
            'description': f'Real-time {layer} visualization from Sentinel-2',
            'format': 'image/png',
            'minzoom': self.min_zoom,
            'maxzoom': self.max_zoom,
            'bounds': [-180, -85, 180, 85],  # Web Mercator bounds
            'center': [128.6, 35.2, 12],  # Korean waters
        }
        
        layer_specific = {
            'rgb': {
                'title': 'Sentinel-2 True Color',
                'description': 'True color RGB imagery from Sentinel-2 L2A',
            },
            'fdi': {
                'title': 'Floating Debris Index',
                'description': 'FDI-based marine debris detection',
                'legend': {
                    'low': {'color': '#0000FF', 'label': 'Clean Water'},
                    'medium': {'color': '#FFFF00', 'label': 'Suspected Debris'},
                    'high': {'color': '#FF0000', 'label': 'High Debris Probability'}
                }
            },
            'ndwi': {
                'title': 'Normalized Difference Water Index',
                'description': 'Water body identification and quality',
                'legend': {
                    'water': {'color': '#0000FF', 'label': 'Water'},
                    'land': {'color': '#8B4513', 'label': 'Land/Vegetation'}
                }
            },
            'mci': {
                'title': 'Marine Chlorophyll Index',
                'description': 'Chlorophyll and algae detection',
                'legend': {
                    'low': {'color': '#000080', 'label': 'Low Chlorophyll'},
                    'high': {'color': '#00FF00', 'label': 'High Chlorophyll'}
                }
            },
            'debris': {
                'title': 'ML-Based Debris Detection',
                'description': 'Machine learning classification of marine surfaces',
                'legend': {
                    'water': {'color': '#0000FF', 'label': 'Clean Water'},
                    'debris_low': {'color': '#FFFF00', 'label': 'Possible Debris'},
                    'debris_high': {'color': '#FF0000', 'label': 'Debris Detected'}
                }
            }
        }
        
        if layer in layer_specific:
            base_metadata.update(layer_specific[layer])
        
        return base_metadata

# Flask application for tile serving
def create_tile_app(tile_service: TileService) -> Flask:
    """Create Flask application for tile serving"""
    
    app = Flask(__name__)
    
    @app.route('/')
    def index():
        return jsonify({
            'service': 'SatChat Tile Service',
            'version': '1.0.0',
            'endpoints': {
                'tiles': '/{layer}/{z}/{x}/{y}.png',
                'metadata': '/{layer}/metadata.json',
                'capabilities': '/capabilities.json'
            },
            'layers': ['rgb', 'fdi', 'ndwi', 'mci', 'debris']
        })
    
    @app.route('/capabilities.json')
    def capabilities():
        """OGC WMTS capabilities"""
        return jsonify({
            'service': 'WMTS',
            'version': '1.0.0',
            'title': 'SatChat Marine Debris Monitoring',
            'abstract': 'Real-time marine debris detection using Sentinel-2 satellite imagery',
            'layers': [tile_service.get_tile_metadata(layer) 
                      for layer in ['rgb', 'fdi', 'ndwi', 'mci', 'debris']],
            'tileMatrixSets': [{
                'identifier': 'WebMercatorQuad',
                'supportedCRS': 'EPSG:3857',
                'tileMatrix': [
                    {
                        'identifier': str(z),
                        'topLeftCorner': [-20037508.3427892, 20037508.3427892],
                        'tileWidth': 256,
                        'tileHeight': 256,
                        'matrixWidth': 2**z,
                        'matrixHeight': 2**z
                    } for z in range(tile_service.min_zoom, tile_service.max_zoom + 1)
                ]
            }]
        })
    
    @app.route('/<layer>/metadata.json')
    def layer_metadata(layer):
        """Layer metadata"""
        if layer not in ['rgb', 'fdi', 'ndwi', 'mci', 'debris']:
            return jsonify({'error': 'Layer not found'}), 404
        
        return jsonify(tile_service.get_tile_metadata(layer))
    
    @app.route('/<layer>/<int:z>/<int:x>/<int:y>.png')
    def get_tile_endpoint(layer, z, x, y):
        """Get tile endpoint"""
        if layer not in ['rgb', 'fdi', 'ndwi', 'mci', 'debris']:
            return 'Layer not found', 404
        
        timestamp = request.args.get('timestamp')
        
        tile_data = tile_service.get_tile(layer, z, x, y, timestamp)
        
        if tile_data is None:
            return 'Tile not found', 404
        
        response = Response(tile_data, mimetype='image/png')
        response.headers['Cache-Control'] = f'max-age={tile_service.cache_ttl}'
        response.headers['Access-Control-Allow-Origin'] = '*'
        
        return response
    
    return app

def create_tile_service(redis_host: str = 'localhost', redis_port: int = 6379) -> TileService:
    """Factory function to create tile service"""
    return TileService(redis_host, redis_port)