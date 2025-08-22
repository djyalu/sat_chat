"""
해양 폐기물(부유 쓰레기) 탐지 시스템
Sentinel Hub + eo-learn 기반 정기 모니터링 파이프라인
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import json
import sys
import os

# eo_learn_lite 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from eo_learn_lite import (
    EOPatch, EOTask, EOWorkflow,
    FeatureType, LoadDataTask
)


class FloatingDebrisIndexTask(EOTask):
    """
    Floating Debris Index (FDI) 계산 태스크
    해양 부유물 탐지를 위한 핵심 지표
    """
    
    def __init__(self, threshold=0.0):
        super().__init__("FloatingDebrisIndexTask")
        self.threshold = threshold
    
    def execute(self, eopatch, **kwargs):
        """FDI 계산 및 부유물 탐지"""
        
        bands = eopatch[(FeatureType.DATA, 'BANDS')]
        
        # Sentinel-2 밴드 인덱스
        # B3: Green (560nm) - index 2
        # B4: Red (665nm) - index 3  
        # B5: Red Edge 1 (705nm) - index 4
        # B6: Red Edge 2 (740nm) - index 5
        # B8: NIR (842nm) - index 7
        # B11: SWIR1 (1610nm) - index 10
        
        green = bands[..., 2]
        red = bands[..., 3]
        red_edge1 = bands[..., 4]
        red_edge2 = bands[..., 5]
        nir = bands[..., 7]
        swir1 = bands[..., 9] if bands.shape[-1] > 9 else bands[..., 8]
        
        # FDI 계산
        # FDI = NIR - (Red_edge2 + (SWIR1 - Red_edge2) * λ_factor)
        # λ_factor는 파장 비율로 계산
        
        lambda_nir = 842
        lambda_re2 = 740
        lambda_swir1 = 1610
        
        lambda_factor = (lambda_nir - lambda_re2) / (lambda_swir1 - lambda_re2)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            fdi = nir - (red_edge2 + (swir1 - red_edge2) * lambda_factor)
            fdi = np.nan_to_num(fdi, nan=0.0)
        
        # 부유물 마스크 생성
        floating_debris_mask = fdi > self.threshold
        
        # NDWI로 물 영역 확인
        ndwi = (green - nir) / (green + nir + 1e-10)
        water_mask = ndwi > -0.1
        
        # 물 위의 부유물만 추출
        marine_debris = floating_debris_mask & water_mask
        
        # 결과 저장
        eopatch[(FeatureType.DATA, 'FDI')] = np.expand_dims(fdi, axis=-1)
        eopatch[(FeatureType.MASK, 'FLOATING_DEBRIS')] = floating_debris_mask.astype(np.uint8)
        eopatch[(FeatureType.MASK, 'MARINE_DEBRIS')] = marine_debris.astype(np.uint8)
        
        # 통계 계산
        debris_percentage = np.mean(marine_debris) * 100
        print(f"✓ FDI 계산 완료: 부유 쓰레기 의심 영역 {debris_percentage:.2f}%")
        
        return eopatch


class PlasticDebrisClassifierTask(EOTask):
    """
    플라스틱 쓰레기 분류 태스크
    자연 부유물(사르가숨, 거품 등)과 구분
    """
    
    def __init__(self):
        super().__init__("PlasticDebrisClassifierTask")
        self.debris_types = {
            0: 'Clear Water',
            1: 'Plastic Debris',
            2: 'Sargassum/Algae',
            3: 'Sea Foam',
            4: 'Turbid Water',
            5: 'Unknown'
        }
    
    def execute(self, eopatch, **kwargs):
        """플라스틱 쓰레기 분류"""
        
        # 필요한 데이터 가져오기
        bands = eopatch[(FeatureType.DATA, 'BANDS')]
        fdi = eopatch[(FeatureType.DATA, 'FDI')][..., 0]
        marine_debris = eopatch[(FeatureType.MASK, 'MARINE_DEBRIS')]
        
        # 스펙트럴 특징 추출
        features = self.extract_spectral_features(bands)
        
        # 분류 규칙 (MARIDA 데이터셋 기반 임계값)
        classification = np.zeros(fdi.shape, dtype=np.uint8)
        
        # Clear Water
        clear_water = (fdi < -0.01) & (features['brightness'] < 0.2)
        classification[clear_water] = 0
        
        # Plastic Debris - 높은 NIR/SWIR 반사율
        plastic_indicators = (
            (fdi > 0.02) & 
            (features['nir_swir_ratio'] > 1.5) &
            (features['plastic_index'] > 0.1)
        )
        classification[plastic_indicators] = 1
        
        # Sargassum/Algae - 높은 Red Edge 반사율
        sargassum_indicators = (
            (fdi > 0.01) &
            (features['red_edge_position'] > 720) &
            (features['chlorophyll_index'] > 0.3)
        )
        classification[sargassum_indicators] = 2
        
        # Sea Foam - 높은 밝기, 낮은 FDI
        foam_indicators = (
            (features['brightness'] > 0.4) &
            (fdi < 0.01) &
            (features['whiteness_index'] > 0.7)
        )
        classification[foam_indicators] = 3
        
        # Turbid Water
        turbid_indicators = (
            (features['turbidity_index'] > 0.2) &
            (fdi < 0.0)
        )
        classification[turbid_indicators] = 4
        
        # Unknown
        unknown_mask = classification == 0
        classification[unknown_mask & marine_debris] = 5
        
        # 결과 저장
        eopatch[(FeatureType.MASK, 'DEBRIS_CLASSIFICATION')] = classification
        
        # 통계 계산
        stats = self.calculate_statistics(classification)
        eopatch[(FeatureType.SCALAR, 'DEBRIS_STATS')] = stats
        
        print(f"✓ 쓰레기 분류 완료:")
        print(f"  - 플라스틱 쓰레기: {stats['plastic_percentage']:.2f}%")
        print(f"  - 해조류: {stats['sargassum_percentage']:.2f}%")
        print(f"  - 거품: {stats['foam_percentage']:.2f}%")
        
        return eopatch
    
    def extract_spectral_features(self, bands):
        """스펙트럴 특징 추출"""
        
        # 밴드별 평균값
        blue = bands[..., 1]
        green = bands[..., 2]
        red = bands[..., 3]
        red_edge1 = bands[..., 4]
        red_edge2 = bands[..., 5]
        red_edge3 = bands[..., 6]
        nir = bands[..., 7]
        swir1 = bands[..., 9] if bands.shape[-1] > 9 else bands[..., 8]
        swir2 = bands[..., 9] if bands.shape[-1] > 9 else bands[..., 8]
        
        features = {}
        
        # 밝기 (Brightness)
        features['brightness'] = np.mean([blue, green, red], axis=0)
        
        # NIR/SWIR 비율
        with np.errstate(divide='ignore', invalid='ignore'):
            features['nir_swir_ratio'] = nir / (swir1 + 1e-10)
            
            # Plastic Index (PI)
            # PI = NIR / (NIR + Red)
            features['plastic_index'] = nir / (nir + red + 1e-10)
            
            # Chlorophyll Index
            features['chlorophyll_index'] = (red_edge1 - red) / (red_edge1 + red + 1e-10)
            
            # Red Edge Position (simplified)
            features['red_edge_position'] = 705 + 35 * (red_edge2 - red_edge1) / (red_edge3 - red_edge1 + 1e-10)
            
            # Whiteness Index
            features['whiteness_index'] = np.min([blue, green, red], axis=0) / (np.max([blue, green, red], axis=0) + 1e-10)
            
            # Turbidity Index
            features['turbidity_index'] = (red + green) / (blue + 1e-10)
        
        # NaN 처리
        for key in features:
            features[key] = np.nan_to_num(features[key], nan=0.0)
        
        return features
    
    def calculate_statistics(self, classification):
        """분류 통계 계산"""
        
        total_pixels = classification.size
        stats = {}
        
        for class_id, class_name in self.debris_types.items():
            pixel_count = np.sum(classification == class_id)
            percentage = (pixel_count / total_pixels) * 100
            stats[f'{class_name.lower().replace(" ", "_")}_percentage'] = percentage
        
        # 플라스틱 쓰레기 특별 통계
        plastic_pixels = np.sum(classification == 1)
        stats['plastic_percentage'] = (plastic_pixels / total_pixels) * 100
        stats['sargassum_percentage'] = (np.sum(classification == 2) / total_pixels) * 100
        stats['foam_percentage'] = (np.sum(classification == 3) / total_pixels) * 100
        
        return stats


class SunGlintCorrectionTask(EOTask):
    """
    Sun Glint (햇빛 반사) 보정 태스크
    해양 관측의 주요 오류 원인 제거
    """
    
    def execute(self, eopatch, **kwargs):
        """Sun glint 보정"""
        
        bands = eopatch[(FeatureType.DATA, 'BANDS')]
        
        # 간단한 glint 탐지 (NIR 밴드 기반)
        nir = bands[..., 7]
        
        # Glint 영역: NIR이 비정상적으로 높은 곳
        glint_threshold = np.percentile(nir, 95)
        glint_mask = nir > glint_threshold
        
        # Glint 보정 (간단한 선형 보정)
        for i in range(bands.shape[-1]):
            band = bands[..., i]
            
            # Glint가 없는 영역의 평균값
            non_glint_mean = np.mean(band[~glint_mask])
            
            # Glint 영역 보정
            band[glint_mask] = non_glint_mean
            bands[..., i] = band
        
        # 보정된 데이터 저장
        eopatch[(FeatureType.DATA, 'BANDS')] = bands
        eopatch[(FeatureType.MASK, 'GLINT')] = glint_mask.astype(np.uint8)
        
        glint_percentage = np.mean(glint_mask) * 100
        print(f"✓ Sun glint 보정 완료: {glint_percentage:.1f}% 영역 보정됨")
        
        return eopatch


class DebrisTrackingTask(EOTask):
    """
    부유 쓰레기 추적 태스크
    시계열 분석으로 이동 경로 추정
    """
    
    def execute(self, eopatch, **kwargs):
        """쓰레기 이동 추적"""
        
        debris_mask = eopatch[(FeatureType.MASK, 'MARINE_DEBRIS')]
        timestamps = eopatch[(FeatureType.TIMESTAMP, 'timestamps')]
        
        if len(timestamps) < 2:
            print("⚠️ 추적을 위해서는 최소 2개 시점이 필요합니다")
            return eopatch
        
        # 시간별 중심점 계산
        centroids = []
        for t in range(debris_mask.shape[0]):
            mask_t = debris_mask[t]
            if np.any(mask_t):
                y_coords, x_coords = np.where(mask_t)
                centroid_y = np.mean(y_coords)
                centroid_x = np.mean(x_coords)
                centroids.append({
                    'timestamp': timestamps[t],
                    'centroid': (centroid_x, centroid_y),
                    'area': np.sum(mask_t)
                })
        
        # 이동 벡터 계산
        if len(centroids) > 1:
            movements = []
            for i in range(1, len(centroids)):
                dx = centroids[i]['centroid'][0] - centroids[i-1]['centroid'][0]
                dy = centroids[i]['centroid'][1] - centroids[i-1]['centroid'][1]
                dt = (centroids[i]['timestamp'] - centroids[i-1]['timestamp']).total_seconds() / 3600  # hours
                
                if dt > 0:
                    speed = np.sqrt(dx**2 + dy**2) / dt  # pixels/hour
                    direction = np.arctan2(dy, dx) * 180 / np.pi  # degrees
                    
                    movements.append({
                        'from': centroids[i-1]['timestamp'],
                        'to': centroids[i]['timestamp'],
                        'speed': speed,
                        'direction': direction,
                        'area_change': float(centroids[i]['area']) - float(centroids[i-1]['area'])
                    })
            
            eopatch[(FeatureType.SCALAR, 'DEBRIS_MOVEMENTS')] = movements
            
            if movements:
                avg_speed = np.mean([m['speed'] for m in movements])
                print(f"✓ 쓰레기 추적 완료: 평균 이동 속도 {avg_speed:.2f} pixels/hour")
        
        return eopatch


class MarineDebrisMonitoringSystem:
    """
    통합 해양 쓰레기 모니터링 시스템
    """
    
    def __init__(self, roi_coordinates, monitoring_frequency='weekly'):
        """
        Parameters:
        -----------
        roi_coordinates : dict
            관심 지역 좌표 (연안, 하구, 항만 등)
        monitoring_frequency : str
            모니터링 주기 ('daily', 'weekly', 'monthly')
        """
        self.roi_coordinates = roi_coordinates
        self.monitoring_frequency = monitoring_frequency
        self.alert_thresholds = {
            'plastic_debris': 0.1,  # 10% 이상
            'total_debris': 0.2,     # 20% 이상
            'speed': 5.0            # 5 pixels/hour 이상
        }
    
    def create_monitoring_workflow(self):
        """모니터링 워크플로우 생성"""
        
        tasks = []
        
        # 1. 데이터 로드
        load_task = LoadDataTask()
        tasks.append((load_task, [], 'load'))
        
        # 2. Sun glint 보정
        glint_task = SunGlintCorrectionTask()
        tasks.append((glint_task, ['load'], 'glint_correction'))
        
        # 3. FDI 계산
        fdi_task = FloatingDebrisIndexTask(threshold=0.01)
        tasks.append((fdi_task, ['glint_correction'], 'fdi'))
        
        # 4. 플라스틱 분류
        classifier_task = PlasticDebrisClassifierTask()
        tasks.append((classifier_task, ['fdi'], 'classification'))
        
        # 5. 추적
        tracking_task = DebrisTrackingTask()
        tasks.append((tracking_task, ['classification'], 'tracking'))
        
        workflow = EOWorkflow(tasks)
        return workflow
    
    def generate_alert(self, eopatch):
        """경보 생성"""
        
        alerts = []
        
        # 통계 확인
        if (FeatureType.SCALAR, 'DEBRIS_STATS') in eopatch.get_feature_list():
            stats = eopatch[(FeatureType.SCALAR, 'DEBRIS_STATS')]
            
            # 플라스틱 쓰레기 경보
            if stats['plastic_percentage'] > self.alert_thresholds['plastic_debris'] * 100:
                alerts.append({
                    'type': 'HIGH_PLASTIC_DEBRIS',
                    'severity': 'HIGH',
                    'message': f"높은 플라스틱 쓰레기 농도 감지: {stats['plastic_percentage']:.1f}%",
                    'timestamp': datetime.now()
                })
            
            # 전체 쓰레기 경보
            total_debris = stats['plastic_percentage'] + stats['sargassum_percentage']
            if total_debris > self.alert_thresholds['total_debris'] * 100:
                alerts.append({
                    'type': 'HIGH_DEBRIS_CONCENTRATION',
                    'severity': 'MEDIUM',
                    'message': f"높은 부유물 농도: {total_debris:.1f}%",
                    'timestamp': datetime.now()
                })
        
        # 이동 속도 확인
        if (FeatureType.SCALAR, 'DEBRIS_MOVEMENTS') in eopatch.get_feature_list():
            movements = eopatch[(FeatureType.SCALAR, 'DEBRIS_MOVEMENTS')]
            if movements:
                max_speed = max([m['speed'] for m in movements])
                if max_speed > self.alert_thresholds['speed']:
                    alerts.append({
                        'type': 'FAST_MOVING_DEBRIS',
                        'severity': 'MEDIUM',
                        'message': f"빠르게 이동하는 쓰레기 감지: {max_speed:.1f} pixels/hour",
                        'timestamp': datetime.now()
                    })
        
        return alerts
    
    def generate_report(self, eopatch, alerts):
        """모니터링 보고서 생성"""
        
        report = {
            'monitoring_date': datetime.now().isoformat(),
            'roi': self.roi_coordinates,
            'summary': {},
            'alerts': alerts,
            'recommendations': []
        }
        
        # 요약 통계
        if (FeatureType.SCALAR, 'DEBRIS_STATS') in eopatch.get_feature_list():
            stats = eopatch[(FeatureType.SCALAR, 'DEBRIS_STATS')]
            report['summary'] = {
                'plastic_debris_percentage': stats['plastic_percentage'],
                'sargassum_percentage': stats['sargassum_percentage'],
                'foam_percentage': stats['foam_percentage'],
                'clear_water_percentage': stats['clear_water_percentage']
            }
        
        # 권고사항 생성
        if alerts:
            if any(a['type'] == 'HIGH_PLASTIC_DEBRIS' for a in alerts):
                report['recommendations'].append("즉시 청소 작업 필요")
                report['recommendations'].append("오염원 조사 권장")
            
            if any(a['type'] == 'FAST_MOVING_DEBRIS' for a in alerts):
                report['recommendations'].append("하류 지역 경보 발령")
                report['recommendations'].append("수거 장비 사전 배치")
        
        return report


def demonstrate_marine_monitoring():
    """해양 쓰레기 모니터링 시연"""
    
    print("\n" + "="*60)
    print("🌊 해양 폐기물 모니터링 시스템")
    print("="*60)
    
    # ROI 설정 (예: 부산항 인근)
    roi = {
        'name': 'Busan Port Area',
        'bbox': [129.0, 35.0, 129.2, 35.2],  # [min_lon, min_lat, max_lon, max_lat]
        'type': 'coastal'
    }
    
    # 모니터링 시스템 초기화
    monitoring_system = MarineDebrisMonitoringSystem(
        roi_coordinates=roi,
        monitoring_frequency='weekly'
    )
    
    # 워크플로우 실행
    print("\n📡 위성 데이터 처리 중...")
    workflow = monitoring_system.create_monitoring_workflow()
    eopatch = workflow.execute()
    
    # 경보 확인
    print("\n🚨 경보 확인...")
    alerts = monitoring_system.generate_alert(eopatch)
    
    if alerts:
        print(f"\n⚠️ {len(alerts)}개 경보 발생:")
        for alert in alerts:
            print(f"  - [{alert['severity']}] {alert['message']}")
    else:
        print("✅ 정상 범위 내")
    
    # 보고서 생성
    report = monitoring_system.generate_report(eopatch, alerts)
    
    print("\n📊 모니터링 보고서:")
    print(f"  - 모니터링 일시: {report['monitoring_date']}")
    print(f"  - 대상 지역: {report['roi']['name']}")
    
    if report['summary']:
        print("\n  부유물 구성:")
        for key, value in report['summary'].items():
            if 'percentage' in key:
                name = key.replace('_percentage', '').replace('_', ' ').title()
                print(f"    • {name}: {value:.2f}%")
    
    if report['recommendations']:
        print("\n  권고사항:")
        for rec in report['recommendations']:
            print(f"    → {rec}")
    
    return eopatch, report


if __name__ == "__main__":
    # 모니터링 실행
    eopatch, report = demonstrate_marine_monitoring()
    
    print("\n" + "="*60)
    print("✅ 해양 폐기물 모니터링 완료!")
    print("실제 Sentinel Hub 연동 시 더 정확한 탐지가 가능합니다.")
    print("="*60)
    
    # 보고서 저장 (선택사항)
    with open('marine_debris_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)