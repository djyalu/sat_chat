"""
eo-learn 실제 응용 사례 모음
다양한 지구 관측 분석 시나리오
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Tuple, Dict
# matplotlib는 선택적 import
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

class ForestChangeDetection:
    """산림 변화 감지 분석"""
    
    def detect_deforestation(self, eopatch_before, eopatch_after):
        """
        두 시점 간 산림 손실 감지
        
        Parameters:
        -----------
        eopatch_before : EOPatch
            이전 시점 데이터
        eopatch_after : EOPatch
            이후 시점 데이터
            
        Returns:
        --------
        deforestation_map : np.ndarray
            산림 손실 지역 맵
        statistics : dict
            통계 정보
        """
        
        # NDVI 차이 계산
        ndvi_before = self._calculate_mean_ndvi(eopatch_before)
        ndvi_after = self._calculate_mean_ndvi(eopatch_after)
        
        ndvi_change = ndvi_after - ndvi_before
        
        # 산림 손실 임계값 적용 (NDVI 0.3 이상 감소)
        deforestation_map = ndvi_change < -0.3
        
        # 통계 계산
        total_pixels = deforestation_map.size
        deforested_pixels = np.sum(deforestation_map)
        deforestation_area = deforested_pixels * 100  # 10m 해상도 가정 (100m²/pixel)
        
        statistics = {
            'total_area_ha': (total_pixels * 100) / 10000,
            'deforested_area_ha': deforestation_area / 10000,
            'deforestation_percentage': (deforested_pixels / total_pixels) * 100,
            'mean_ndvi_change': np.mean(ndvi_change)
        }
        
        return deforestation_map, statistics
    
    def _calculate_mean_ndvi(self, eopatch):
        """평균 NDVI 계산"""
        # 시간 축에 대한 평균
        ndvi = eopatch.data['NDVI']
        return np.mean(ndvi, axis=0)
    
    def monitor_forest_health(self, eopatch_series: List):
        """
        시계열 산림 건강도 모니터링
        
        Parameters:
        -----------
        eopatch_series : List[EOPatch]
            시계열 EOPatch 리스트
            
        Returns:
        --------
        health_scores : List[float]
            시간별 건강도 점수
        """
        
        health_scores = []
        
        for eopatch in eopatch_series:
            ndvi = self._calculate_mean_ndvi(eopatch)
            
            # 건강한 산림 기준: NDVI > 0.6
            healthy_forest = ndvi > 0.6
            health_score = np.mean(healthy_forest) * 100
            
            health_scores.append({
                'timestamp': eopatch.timestamp[0],
                'health_score': health_score,
                'mean_ndvi': np.mean(ndvi),
                'stressed_area_percent': 100 - health_score
            })
        
        return health_scores


class FloodMappingSystem:
    """홍수 매핑 시스템"""
    
    def detect_flood_extent(self, eopatch_normal, eopatch_flood):
        """
        홍수 범위 탐지
        
        Parameters:
        -----------
        eopatch_normal : EOPatch
            평상시 데이터
        eopatch_flood : EOPatch
            홍수 시 데이터
            
        Returns:
        --------
        flood_map : np.ndarray
            홍수 지역 맵
        affected_area : float
            피해 면적 (헥타르)
        """
        
        # NDWI (Normalized Difference Water Index) 계산
        ndwi_normal = self._calculate_ndwi(eopatch_normal)
        ndwi_flood = self._calculate_ndwi(eopatch_flood)
        
        # 물 지역 탐지 (NDWI > 0.3)
        water_normal = ndwi_normal > 0.3
        water_flood = ndwi_flood > 0.3
        
        # 새로운 물 지역 = 홍수 지역
        flood_map = water_flood & ~water_normal
        
        # 피해 면적 계산
        flood_pixels = np.sum(flood_map)
        affected_area = (flood_pixels * 100) / 10000  # 헥타르
        
        return flood_map, affected_area
    
    def _calculate_ndwi(self, eopatch):
        """NDWI 계산"""
        green = eopatch.data['BANDS'][:, :, :, 2]  # Green band
        nir = eopatch.data['BANDS'][:, :, :, 7]     # NIR band
        
        ndwi = (green - nir) / (green + nir + 1e-10)
        return np.mean(ndwi, axis=0)
    
    def assess_flood_risk(self, eopatch, dem_data):
        """
        홍수 위험도 평가
        
        Parameters:
        -----------
        eopatch : EOPatch
            위성 데이터
        dem_data : np.ndarray
            수치표고모델 데이터
            
        Returns:
        --------
        risk_map : np.ndarray
            위험도 맵 (0-1)
        risk_categories : dict
            위험도 카테고리별 면적
        """
        
        # 요인별 가중치
        weights = {
            'elevation': 0.3,
            'slope': 0.2,
            'distance_to_water': 0.3,
            'land_cover': 0.2
        }
        
        # 고도 기반 위험도 (낮은 지역일수록 위험)
        elevation_risk = 1 - (dem_data - np.min(dem_data)) / (np.max(dem_data) - np.min(dem_data))
        
        # 경사도 계산 (평탄할수록 위험)
        slope = self._calculate_slope(dem_data)
        slope_risk = 1 - slope / np.max(slope)
        
        # 수역 근접도 (가까울수록 위험)
        ndwi = self._calculate_ndwi(eopatch)
        water_mask = ndwi > 0.3
        distance_to_water = self._distance_transform(water_mask)
        distance_risk = 1 - distance_to_water / np.max(distance_to_water)
        
        # 토지 피복 위험도 (도시 지역 높음)
        ndbi = self._calculate_ndbi(eopatch)
        urban_risk = (ndbi > 0).astype(float)
        
        # 종합 위험도 계산
        risk_map = (
            weights['elevation'] * elevation_risk +
            weights['slope'] * slope_risk +
            weights['distance_to_water'] * distance_risk +
            weights['land_cover'] * urban_risk
        )
        
        # 위험도 카테고리 분류
        risk_categories = {
            'very_high': np.sum(risk_map > 0.8),
            'high': np.sum((risk_map > 0.6) & (risk_map <= 0.8)),
            'moderate': np.sum((risk_map > 0.4) & (risk_map <= 0.6)),
            'low': np.sum((risk_map > 0.2) & (risk_map <= 0.4)),
            'very_low': np.sum(risk_map <= 0.2)
        }
        
        return risk_map, risk_categories
    
    def _calculate_slope(self, dem):
        """경사도 계산"""
        dy, dx = np.gradient(dem)
        slope = np.sqrt(dx**2 + dy**2)
        return slope
    
    def _distance_transform(self, binary_mask):
        """거리 변환 (간단한 구현)"""
        try:
            from scipy.ndimage import distance_transform_edt
            return distance_transform_edt(~binary_mask)
        except ImportError:
            # scipy가 없는 경우 간단한 대체 구현
            return np.ones_like(binary_mask, dtype=float)
    
    def _calculate_ndbi(self, eopatch):
        """NDBI 계산"""
        swir = eopatch.data['BANDS'][:, :, :, 10]  # SWIR band
        nir = eopatch.data['BANDS'][:, :, :, 7]     # NIR band
        
        ndbi = (swir - nir) / (swir + nir + 1e-10)
        return np.mean(ndbi, axis=0)


class AgriculturalMonitoring:
    """농업 모니터링 시스템"""
    
    def assess_crop_health(self, eopatch, crop_calendar):
        """
        작물 건강도 평가
        
        Parameters:
        -----------
        eopatch : EOPatch
            위성 데이터
        crop_calendar : dict
            작물 재배 일정
            
        Returns:
        --------
        health_assessment : dict
            건강도 평가 결과
        """
        
        # 생육 단계별 NDVI 임계값
        growth_stages = {
            'planting': {'min_ndvi': 0.1, 'max_ndvi': 0.3},
            'growing': {'min_ndvi': 0.3, 'max_ndvi': 0.6},
            'maturity': {'min_ndvi': 0.6, 'max_ndvi': 0.8},
            'harvest': {'min_ndvi': 0.2, 'max_ndvi': 0.4}
        }
        
        current_stage = self._get_current_stage(eopatch.timestamp[0], crop_calendar)
        stage_thresholds = growth_stages.get(current_stage, growth_stages['growing'])
        
        # NDVI 분석
        ndvi = eopatch.data['NDVI']
        mean_ndvi = np.mean(ndvi)
        
        # 건강도 점수 계산
        if stage_thresholds['min_ndvi'] <= mean_ndvi <= stage_thresholds['max_ndvi']:
            health_score = 100
        else:
            deviation = min(
                abs(mean_ndvi - stage_thresholds['min_ndvi']),
                abs(mean_ndvi - stage_thresholds['max_ndvi'])
            )
            health_score = max(0, 100 - deviation * 200)
        
        # 스트레스 지역 탐지
        stressed_areas = ndvi < stage_thresholds['min_ndvi']
        stress_percentage = np.mean(stressed_areas) * 100
        
        health_assessment = {
            'growth_stage': current_stage,
            'mean_ndvi': mean_ndvi,
            'health_score': health_score,
            'stress_percentage': stress_percentage,
            'expected_ndvi_range': stage_thresholds,
            'recommendation': self._get_recommendation(health_score, stress_percentage)
        }
        
        return health_assessment
    
    def _get_current_stage(self, timestamp, crop_calendar):
        """현재 생육 단계 결정"""
        # 간단한 구현 (실제로는 더 복잡한 로직 필요)
        month = timestamp.month
        
        if month in [3, 4]:
            return 'planting'
        elif month in [5, 6, 7]:
            return 'growing'
        elif month in [8, 9]:
            return 'maturity'
        else:
            return 'harvest'
    
    def _get_recommendation(self, health_score, stress_percentage):
        """관리 권고사항 생성"""
        recommendations = []
        
        if health_score < 60:
            recommendations.append("작물 건강도가 낮습니다. 영양 상태 점검이 필요합니다.")
        
        if stress_percentage > 20:
            recommendations.append(f"전체 면적의 {stress_percentage:.1f}%에서 스트레스가 감지됩니다.")
            recommendations.append("관개 또는 병해충 관리가 필요할 수 있습니다.")
        
        if health_score >= 80:
            recommendations.append("작물 상태가 양호합니다. 현재 관리 방식을 유지하세요.")
        
        return " ".join(recommendations)
    
    def estimate_yield(self, eopatch_series, historical_yields):
        """
        수확량 예측
        
        Parameters:
        -----------
        eopatch_series : List[EOPatch]
            생육 기간 시계열 데이터
        historical_yields : dict
            과거 수확량 데이터
            
        Returns:
        --------
        yield_estimate : float
            예상 수확량 (톤/헥타르)
        confidence : float
            예측 신뢰도 (0-1)
        """
        
        # 생육 기간 NDVI 적산
        ndvi_sum = 0
        for eopatch in eopatch_series:
            ndvi = np.mean(eopatch.data['NDVI'])
            ndvi_sum += ndvi
        
        # 평균 NDVI
        avg_ndvi = ndvi_sum / len(eopatch_series)
        
        # 과거 데이터와 비교
        historical_ndvi = historical_yields.get('avg_ndvi', [])
        historical_yield = historical_yields.get('yield', [])
        
        if len(historical_ndvi) > 0:
            # 선형 회귀 (간단한 구현)
            correlation = np.corrcoef(historical_ndvi, historical_yield)[0, 1]
            
            # 수확량 예측
            mean_yield = np.mean(historical_yield)
            std_yield = np.std(historical_yield)
            
            # NDVI 기반 조정
            ndvi_factor = avg_ndvi / np.mean(historical_ndvi)
            yield_estimate = mean_yield * ndvi_factor
            
            # 신뢰도 계산
            confidence = abs(correlation)
        else:
            # 기본값
            yield_estimate = 5.0  # 톤/헥타르
            confidence = 0.3
        
        return yield_estimate, confidence


class UrbanHeatIslandAnalysis:
    """도시 열섬 분석"""
    
    def calculate_lst(self, eopatch):
        """
        지표면 온도(LST) 계산
        
        Parameters:
        -----------
        eopatch : EOPatch
            열적외선 밴드를 포함한 위성 데이터
            
        Returns:
        --------
        lst_map : np.ndarray
            지표면 온도 맵 (섭씨)
        """
        
        # Landsat 8 Band 10 (Thermal) 사용 가정
        # 실제로는 더 복잡한 대기 보정 필요
        thermal_band = eopatch.data['THERMAL']
        
        # 간단한 변환 (실제로는 더 정확한 공식 필요)
        # DN to Radiance
        ml = 0.0003342  # Multiplicative rescaling factor
        al = 0.1  # Additive rescaling factor
        radiance = ml * thermal_band + al
        
        # Radiance to Temperature
        k1 = 774.89  # Thermal constant
        k2 = 1321.08  # Thermal constant
        
        lst_kelvin = k2 / np.log((k1 / radiance) + 1)
        lst_celsius = lst_kelvin - 273.15
        
        return lst_celsius
    
    def identify_heat_islands(self, lst_map, urban_mask):
        """
        도시 열섬 지역 식별
        
        Parameters:
        -----------
        lst_map : np.ndarray
            지표면 온도 맵
        urban_mask : np.ndarray
            도시 지역 마스크
            
        Returns:
        --------
        heat_island_map : np.ndarray
            열섬 강도 맵
        statistics : dict
            열섬 통계
        """
        
        # 도시와 비도시 지역 온도
        urban_temp = lst_map[urban_mask]
        rural_temp = lst_map[~urban_mask]
        
        # 평균 온도
        mean_urban = np.mean(urban_temp)
        mean_rural = np.mean(rural_temp)
        
        # 열섬 강도 (UHI Intensity)
        uhi_intensity = mean_urban - mean_rural
        
        # 열섬 맵 생성 (도시 지역의 온도 편차)
        heat_island_map = np.zeros_like(lst_map)
        heat_island_map[urban_mask] = lst_map[urban_mask] - mean_rural
        
        # 열섬 등급 분류
        statistics = {
            'mean_urban_temp': mean_urban,
            'mean_rural_temp': mean_rural,
            'uhi_intensity': uhi_intensity,
            'max_temp': np.max(lst_map),
            'min_temp': np.min(lst_map),
            'hot_spots': np.sum(heat_island_map > 5),  # 5도 이상 높은 지역
            'cool_spots': np.sum(heat_island_map < -2)  # 2도 이상 낮은 지역
        }
        
        return heat_island_map, statistics


# 사용 예제
def demonstrate_applications():
    """응용 사례 시연"""
    
    print("=" * 60)
    print("eo-learn 응용 사례 시연")
    print("=" * 60)
    
    # 1. 산림 변화 감지
    print("\n1. 산림 변화 감지")
    print("-" * 40)
    forest_detector = ForestChangeDetection()
    print("✓ 산림 손실 탐지 알고리즘 준비 완료")
    print("✓ NDVI 차이 분석을 통한 변화 감지")
    print("✓ 시계열 산림 건강도 모니터링 가능")
    
    # 2. 홍수 매핑
    print("\n2. 홍수 매핑 시스템")
    print("-" * 40)
    flood_mapper = FloodMappingSystem()
    print("✓ NDWI 기반 수역 탐지")
    print("✓ 홍수 전후 비교 분석")
    print("✓ DEM 통합 위험도 평가")
    
    # 3. 농업 모니터링
    print("\n3. 농업 모니터링")
    print("-" * 40)
    agri_monitor = AgriculturalMonitoring()
    print("✓ 작물 생육 단계별 건강도 평가")
    print("✓ 스트레스 지역 조기 탐지")
    print("✓ 수확량 예측 모델")
    
    # 4. 도시 열섬 분석
    print("\n4. 도시 열섬 분석")
    print("-" * 40)
    uhi_analyzer = UrbanHeatIslandAnalysis()
    print("✓ 지표면 온도 계산")
    print("✓ 열섬 강도 정량화")
    print("✓ 핫스팟 식별 및 매핑")
    
    print("\n" + "=" * 60)
    print("모든 응용 모듈이 준비되었습니다!")
    print("실제 데이터와 Sentinel Hub 계정이 있으면 바로 사용 가능합니다.")
    

if __name__ == "__main__":
    demonstrate_applications()