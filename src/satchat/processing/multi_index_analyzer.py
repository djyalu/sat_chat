#!/usr/bin/env python3
"""
다중 지표 통합 해양 폐기물 분석 시스템
FDI 단일 지표 대신 복합 지표와 규칙 기반 분석
"""

import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import cv2

@dataclass
class MultiIndexConfig:
    """다중 지표 분석 설정"""
    # 지표별 가중치 (지역별 커스터마이징 가능)
    fdi_weight: float = 0.25
    ndwi_weight: float = 0.20
    mci_weight: float = 0.20  # Marine Chlorophyll Index
    fai_weight: float = 0.15  # Floating Algae Index
    turbidity_weight: float = 0.10
    glint_weight: float = 0.10  # Sun glint 보정 가중치
    
    # 지역별 적응 임계값
    coastal_threshold: float = 0.15
    offshore_threshold: float = 0.08
    
    # 형태학적 필터 파라미터
    min_patch_size: int = 10
    max_elongation: float = 0.3  # 세로/가로 비율 (filament 감지)

class MultiIndexAnalyzer:
    """다중 지표 기반 해양 폐기물 분석기"""
    
    def __init__(self, config: MultiIndexConfig = None):
        self.config = config or MultiIndexConfig()
        
    def calculate_multi_indices(self, bands: np.ndarray) -> Dict[str, np.ndarray]:
        """
        다중 스펙트럴 지수 계산
        
        Parameters:
        -----------
        bands : np.ndarray, shape (H, W, N_bands)
            Sentinel-2 반사도 데이터
            
        Returns:
        --------
        dict : 각 지수별 2D 배열
        """
        # 밴드 추출 (Sentinel-2 기준)
        blue = bands[..., 1]    # B2
        green = bands[..., 2]   # B3
        red = bands[..., 3]     # B4
        red_edge1 = bands[..., 4]  # B5
        red_edge2 = bands[..., 5]  # B6
        red_edge3 = bands[..., 6]  # B7
        nir = bands[..., 7]     # B8
        nir_narrow = bands[..., 8] # B8A
        swir1 = bands[..., 9]   # B11
        swir2 = bands[..., 10] if bands.shape[-1] > 10 else swir1  # B12
        
        indices = {}
        
        # 1. FDI (Floating Debris Index) - 개선된 버전
        lambda_nir = 842
        lambda_re2 = 740
        lambda_swir1 = 1610
        lambda_factor = (lambda_nir - lambda_re2) / (lambda_swir1 - lambda_re2)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['fdi'] = nir - (red_edge2 + (swir1 - red_edge2) * lambda_factor)
            indices['fdi'] = np.nan_to_num(indices['fdi'], nan=0.0)
        
        # 2. NDWI (Normalized Difference Water Index)
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['ndwi'] = (green - nir) / (green + nir + 1e-10)
            indices['ndwi'] = np.nan_to_num(indices['ndwi'], nan=0.0)
        
        # 3. MCI (Marine Chlorophyll Index) - 조류/사르가숨 감지
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['mci'] = red_edge2 - red_edge1 - 0.35 * (red_edge3 - red_edge1)
            indices['mci'] = np.nan_to_num(indices['mci'], nan=0.0)
        
        # 4. FAI (Floating Algae Index) - 부유 조류 감지
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['fai'] = nir - (red + (swir1 - red) * (842 - 665) / (1610 - 665))
            indices['fai'] = np.nan_to_num(indices['fai'], nan=0.0)
        
        # 5. Turbidity Index - 탁도 지수
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['turbidity'] = (red - blue) / (red + blue + 1e-10)
            indices['turbidity'] = np.nan_to_num(indices['turbidity'], nan=0.0)
        
        # 6. Sun Glint Detection - 태양광 반사 감지
        with np.errstate(divide='ignore', invalid='ignore'):
            indices['glint'] = (nir + swir1) / (red + green + 1e-10)
            indices['glint'] = np.nan_to_num(indices['glint'], nan=0.0)
            
        return indices
    
    def apply_atmospheric_correction(self, bands: np.ndarray) -> np.ndarray:
        """
        간단한 대기 보정 (실제로는 Sen2Cor, ACOLITE 등 사용 권장)
        """
        # Dark Object Subtraction (DOS) 간소화 버전
        corrected = bands.copy()
        for i in range(bands.shape[-1]):
            band_data = bands[..., i]
            dark_object = np.percentile(band_data[band_data > 0], 1)
            corrected[..., i] = np.clip(band_data - dark_object, 0, None)
        
        return corrected
    
    def create_composite_mask(self, indices: Dict[str, np.ndarray], 
                            water_mask: np.ndarray) -> np.ndarray:
        """
        다중 지표 결합으로 복합 마스크 생성
        """
        h, w = indices['fdi'].shape
        composite_score = np.zeros((h, w), dtype=np.float32)
        
        # 각 지수별 기여도 계산
        fdi_contrib = np.clip(indices['fdi'] / 0.1, 0, 1) * self.config.fdi_weight
        
        # NDWI는 물 영역에서는 높고, 부유물에서는 낮음
        ndwi_contrib = np.clip((0.2 - indices['ndwi']) / 0.4, 0, 1) * self.config.ndwi_weight
        
        # MCI는 조류 감지 (높으면 사르가숨, 중간이면 플라스틱 가능성)
        mci_contrib = np.clip(np.abs(indices['mci']) / 0.05, 0, 1) * self.config.mci_weight
        
        # FAI는 부유 조류/폐기물 감지
        fai_contrib = np.clip(indices['fai'] / 0.05, 0, 1) * self.config.fai_weight
        
        # 탁도는 중간 값에서 최대 (너무 높으면 침전물, 너무 낮으면 깨끗한 물)
        turbidity_contrib = np.clip(1 - np.abs(indices['turbidity'] - 0.1) / 0.2, 0, 1) * self.config.turbidity_weight
        
        # 글린트 영역은 제외
        glint_mask = indices['glint'] < np.percentile(indices['glint'], 90)
        glint_contrib = glint_mask.astype(float) * self.config.glint_weight
        
        # 복합 점수 계산
        composite_score = (fdi_contrib + ndwi_contrib + mci_contrib + 
                          fai_contrib + turbidity_contrib + glint_contrib)
        
        # 물 영역에서만 유효
        composite_score = composite_score * water_mask
        
        return composite_score
    
    def morphological_filtering(self, mask: np.ndarray) -> np.ndarray:
        """
        형태학적 필터링으로 노이즈 제거 및 형태 기반 분류
        """
        # 이진화
        binary_mask = (mask > 0.3).astype(np.uint8)
        
        # 작은 객체 제거
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        cleaned = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel)
        
        # 연결 성분 분석
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(cleaned)
        
        final_mask = np.zeros_like(mask)
        
        for i in range(1, num_labels):  # 0은 배경
            area = stats[i, cv2.CC_STAT_AREA]
            if area < self.config.min_patch_size:
                continue
            
            # 형태 분석
            x, y, width, height = stats[i, cv2.CC_STAT_LEFT:cv2.CC_STAT_HEIGHT+1]
            elongation = min(width, height) / max(width, height)
            
            # 세로로 긴 형태는 플라스틱 필라멘트 가능성 높음
            if elongation <= self.config.max_elongation and area > 20:
                component_mask = (labels == i)
                final_mask[component_mask] = mask[component_mask]
        
        return final_mask
    
    def detect_hotspots(self, composite_mask: np.ndarray, 
                       bbox: List[float]) -> List[Dict]:
        """
        핫스팟 탐지 및 특성 분석
        """
        # 임계값 이상 영역 찾기
        high_confidence = composite_mask > 0.5
        medium_confidence = (composite_mask > 0.3) & (composite_mask <= 0.5)
        
        hotspots = []
        
        # 연결 성분으로 개별 핫스팟 분리
        for confidence_level, threshold in [("high", high_confidence), ("medium", medium_confidence)]:
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
                threshold.astype(np.uint8)
            )
            
            for i in range(1, num_labels):
                area_pixels = stats[i, cv2.CC_STAT_AREA]
                if area_pixels < 5:  # 너무 작은 영역 제외
                    continue
                
                # 픽셀 좌표를 지리 좌표로 변환
                centroid_y, centroid_x = centroids[i]
                
                # bbox: [west, south, east, north]
                west, south, east, north = bbox
                lat = south + (1 - centroid_y / composite_mask.shape[0]) * (north - south)
                lon = west + (centroid_x / composite_mask.shape[1]) * (east - west)
                
                # 해당 영역의 평균 점수
                component_mask = (labels == i)
                avg_score = composite_mask[component_mask].mean()
                max_score = composite_mask[component_mask].max()
                
                # 면적 추정 (대략적)
                pixel_area_m2 = ((east - west) * 111320) * ((north - south) * 111320) / (composite_mask.shape[1] * composite_mask.shape[0])
                area_m2 = area_pixels * pixel_area_m2
                
                hotspot = {
                    "lat": float(lat),
                    "lon": float(lon),
                    "intensity": float(avg_score),
                    "max_intensity": float(max_score),
                    "confidence_level": confidence_level,
                    "area_pixels": int(area_pixels),
                    "area_m2": float(area_m2),
                    "confidence": min(int(avg_score * 100), 95)
                }
                
                hotspots.append(hotspot)
        
        # 신뢰도 순으로 정렬
        hotspots.sort(key=lambda x: x['intensity'], reverse=True)
        
        return hotspots[:20]  # 상위 20개만 반환
    
    def analyze_region(self, bands: np.ndarray, bbox: List[float], 
                      region_type: str = "coastal") -> Dict:
        """
        지역별 맞춤 분석 실행
        """
        start_time = datetime.now()
        
        # 1. 대기 보정 (간소화)
        corrected_bands = self.apply_atmospheric_correction(bands)
        
        # 2. 다중 지수 계산
        indices = self.calculate_multi_indices(corrected_bands)
        
        # 3. 물 영역 마스크 생성
        water_mask = (indices['ndwi'] > -0.1).astype(float)
        
        # 4. 복합 마스크 생성
        composite_mask = self.create_composite_mask(indices, water_mask)
        
        # 5. 형태학적 필터링
        filtered_mask = self.morphological_filtering(composite_mask)
        
        # 6. 핫스팟 탐지
        hotspots = self.detect_hotspots(filtered_mask, bbox)
        
        # 7. 통계 계산
        total_pixels = np.sum(water_mask > 0)
        debris_pixels = np.sum(filtered_mask > 0.3)
        coverage_percentage = (debris_pixels / total_pixels * 100) if total_pixels > 0 else 0
        
        # 8. 신뢰도 평가
        avg_confidence = np.mean(filtered_mask[filtered_mask > 0.3]) if debris_pixels > 0 else 0
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "processing_time_sec": processing_time,
            "region_type": region_type,
            "bbox": bbox,
            
            # 통계
            "total_water_pixels": int(total_pixels),
            "debris_pixels": int(debris_pixels),
            "coverage_percentage": float(coverage_percentage),
            "avg_confidence": float(avg_confidence),
            
            # 지수별 통계
            "indices_stats": {
                "fdi_mean": float(np.mean(indices['fdi'][water_mask > 0])),
                "ndwi_mean": float(np.mean(indices['ndwi'][water_mask > 0])),
                "mci_mean": float(np.mean(indices['mci'][water_mask > 0])),
                "fai_mean": float(np.mean(indices['fai'][water_mask > 0])),
                "turbidity_mean": float(np.mean(indices['turbidity'][water_mask > 0]))
            },
            
            # 결과
            "hotspots": hotspots,
            "composite_mask": filtered_mask,  # 시각화용
            "confidence_level": "high" if avg_confidence > 0.7 else "medium" if avg_confidence > 0.4 else "low"
        }
        
        return result

def create_enhanced_evalscript() -> str:
    """
    다중 분석용 향상된 Sentinel Hub Evalscript
    """
    return """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12", "SCL"]
            }],
            output: [
                { id: "rgb", bands: 3 },
                { id: "indices", bands: 6, sampleType: "FLOAT32" },  // FDI, NDWI, MCI, FAI, Turbidity, Glint
                { id: "masks", bands: 3 }  // Water, Cloud, Land
            ]
        };
    }
    
    function evaluatePixel(sample) {
        // 구름 및 육지 마스크
        let cloud_mask = (sample.SCL == 3 || sample.SCL == 8 || sample.SCL == 9);
        let water_mask = (sample.SCL == 6);  // Water
        let land_mask = (sample.SCL == 4 || sample.SCL == 5);  // Vegetation, Bare soil
        
        if (cloud_mask) {
            return {
                rgb: [0, 0, 0],
                indices: [0, 0, 0, 0, 0, 0],
                masks: [0, 1, 0]  // Water, Cloud, Land
            };
        }
        
        // 반사도 정규화
        let blue = sample.B02 / 10000;
        let green = sample.B03 / 10000;  
        let red = sample.B04 / 10000;
        let re1 = sample.B05 / 10000;
        let re2 = sample.B06 / 10000;
        let re3 = sample.B07 / 10000;
        let nir = sample.B08 / 10000;
        let nir_narrow = sample.B8A / 10000;
        let swir1 = sample.B11 / 10000;
        let swir2 = sample.B12 / 10000;
        
        // RGB 향상 (대비 증가)
        let rgb_r = Math.min(red * 2.5, 1);
        let rgb_g = Math.min(green * 2.5, 1);
        let rgb_b = Math.min(blue * 2.5, 1);
        
        // 지수 계산
        let lambda_factor = (842 - 740) / (1610 - 740);
        let fdi = nir - (re2 + (swir1 - re2) * lambda_factor);
        
        let ndwi = (green - nir) / (green + nir + 0.001);
        let mci = re2 - re1 - 0.35 * (re3 - re1);
        let fai = nir - (red + (swir1 - red) * (842 - 665) / (1610 - 665));
        let turbidity = (red - blue) / (red + blue + 0.001);
        let glint = (nir + swir1) / (red + green + 0.001);
        
        return {
            rgb: [rgb_r * 255, rgb_g * 255, rgb_b * 255],
            indices: [fdi * 1000, ndwi * 1000, mci * 1000, fai * 1000, turbidity * 1000, glint * 1000],
            masks: [water_mask ? 1 : 0, cloud_mask ? 1 : 0, land_mask ? 1 : 0]
        };
    }
    """

# 사용 예시
if __name__ == "__main__":
    # 설정
    config = MultiIndexConfig(
        fdi_weight=0.30,      # FDI 가중치 증가
        ndwi_weight=0.25,     # 물 감지 중요도 증가
        coastal_threshold=0.12  # 연안 지역 임계값 낮춤
    )
    
    analyzer = MultiIndexAnalyzer(config)
    
    print("✅ 다중 지표 분석 시스템 초기화 완료")
    print("📊 지원 지표: FDI, NDWI, MCI, FAI, Turbidity, Sun Glint")
    print("🎯 특징: 형태학적 필터링, 지역별 적응 임계값, 대기보정")