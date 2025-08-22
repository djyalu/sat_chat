"""
eo-learn을 활용한 토지 피복 분류 시스템
실제 위성 데이터 처리 파이프라인 구현
"""

import numpy as np
from datetime import datetime, timedelta
import sys
import os

# eo_learn_lite 모듈 임포트
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from eo_learn_lite import (
    EOPatch, EOTask, EOWorkflow, 
    FeatureType, LoadDataTask, 
    AddCloudMaskTask, NormalizedDifferenceIndexTask
)


class LandCoverClassificationTask(EOTask):
    """토지 피복 분류 태스크"""
    
    def __init__(self, class_names=None):
        super().__init__("LandCoverClassificationTask")
        self.class_names = class_names or {
            0: 'Water',
            1: 'Vegetation',
            2: 'Urban/Built-up',
            3: 'Bare Soil'
        }
    
    def execute(self, eopatch, **kwargs):
        """토지 피복 분류 실행"""
        
        # 필요한 지수 데이터 가져오기
        ndvi = eopatch[(FeatureType.DATA, 'NDVI')]
        ndwi = eopatch[(FeatureType.DATA, 'NDWI')]
        
        # 분류 수행
        classification = self.classify_pixels(ndvi, ndwi)
        
        # EOPatch에 저장
        eopatch[(FeatureType.MASK, 'LAND_COVER')] = classification
        
        # 통계 계산
        stats = self.calculate_statistics(classification)
        eopatch[(FeatureType.SCALAR, 'LAND_COVER_STATS')] = stats
        
        print(f"✓ 토지 피복 분류 완료")
        self.print_statistics(stats)
        
        return eopatch
    
    def classify_pixels(self, ndvi, ndwi):
        """
        픽셀 단위 분류 수행
        
        TODO(human): 아래 함수를 구현하세요.
        NDVI와 NDWI 값을 기반으로 각 픽셀을 분류합니다.
        
        분류 규칙:
        - Water (0): NDWI > 0.0
        - Vegetation (1): NDVI > 0.3 and NDWI <= 0.0
        - Urban/Built-up (2): NDVI <= 0.3 and NDWI <= 0.0 and (NDVI < 0.1)
        - Bare Soil (3): 나머지 경우
        
        Parameters:
        -----------
        ndvi : np.ndarray
            NDVI 값 배열 (시간, 높이, 너비, 1)
        ndwi : np.ndarray
            NDWI 값 배열 (시간, 높이, 너비, 1)
            
        Returns:
        --------
        classification : np.ndarray
            분류 결과 (시간, 높이, 너비) - dtype: uint8
        """
        # 여기에 구현을 추가하세요
        # 기본 구현 (사용자가 직접 구현하도록 남겨둠)
        
        # 배열 차원 조정 (시간, 높이, 너비, 1) -> (시간, 높이, 너비)
        ndvi = ndvi[:, :, :, 0]
        ndwi = ndwi[:, :, :, 0]
        
        # 분류 배열 초기화
        classification = np.zeros(ndvi.shape, dtype=np.uint8)
        
        # 분류 규칙 적용
        # Water (0): NDWI > 0.0
        classification[ndwi > 0.0] = 0
        
        # Vegetation (1): NDVI > 0.3 and NDWI <= 0.0
        vegetation_mask = (ndvi > 0.3) & (ndwi <= 0.0)
        classification[vegetation_mask] = 1
        
        # Urban/Built-up (2): NDVI <= 0.3 and NDWI <= 0.0 and NDVI < 0.1
        urban_mask = (ndvi <= 0.3) & (ndwi <= 0.0) & (ndvi < 0.1)
        classification[urban_mask] = 2
        
        # Bare Soil (3): 나머지 경우
        baresoil_mask = (ndvi >= 0.1) & (ndvi <= 0.3) & (ndwi <= 0.0)
        classification[baresoil_mask] = 3
        
        return classification
    
    def calculate_statistics(self, classification):
        """분류 통계 계산"""
        stats = {}
        
        # 시간별 통계
        for t in range(classification.shape[0]):
            class_counts = {}
            total_pixels = classification[t].size
            
            for class_id, class_name in self.class_names.items():
                count = np.sum(classification[t] == class_id)
                percentage = (count / total_pixels) * 100
                class_counts[class_name] = {
                    'count': int(count),
                    'percentage': float(percentage)
                }
            
            stats[f'timestamp_{t}'] = class_counts
        
        # 전체 평균
        avg_stats = {}
        for class_id, class_name in self.class_names.items():
            avg_percentage = np.mean([
                stats[f'timestamp_{t}'][class_name]['percentage'] 
                for t in range(classification.shape[0])
            ])
            avg_stats[class_name] = float(avg_percentage)
        
        stats['average'] = avg_stats
        
        return stats
    
    def print_statistics(self, stats):
        """통계 출력"""
        print("\n📊 토지 피복 분류 통계:")
        print("-" * 40)
        avg_stats = stats['average']
        for class_name, percentage in avg_stats.items():
            bar = '█' * int(percentage / 2)
            print(f"  {class_name:15s}: {percentage:6.2f}% {bar}")


class ChangeDetectionTask(EOTask):
    """변화 탐지 태스크"""
    
    def __init__(self, change_threshold=0.2):
        super().__init__("ChangeDetectionTask")
        self.change_threshold = change_threshold
    
    def execute(self, eopatch, **kwargs):
        """변화 탐지 수행"""
        
        # NDVI 데이터 가져오기
        ndvi = eopatch[(FeatureType.DATA, 'NDVI')]
        
        if ndvi.shape[0] < 2:
            print("⚠️ 변화 탐지를 위해서는 최소 2개 시점이 필요합니다")
            return eopatch
        
        # 첫 시점과 마지막 시점 비교
        ndvi_first = ndvi[0, :, :, 0]
        ndvi_last = ndvi[-1, :, :, 0]
        
        # 변화량 계산
        ndvi_change = ndvi_last - ndvi_first
        
        # 변화 분류
        significant_increase = ndvi_change > self.change_threshold
        significant_decrease = ndvi_change < -self.change_threshold
        no_change = np.abs(ndvi_change) <= self.change_threshold
        
        # 변화 맵 생성 (0: 변화없음, 1: 증가, 2: 감소)
        change_map = np.zeros_like(ndvi_change, dtype=np.uint8)
        change_map[significant_increase] = 1
        change_map[significant_decrease] = 2
        
        # EOPatch에 저장
        eopatch[(FeatureType.MASK, 'CHANGE_MAP')] = change_map
        eopatch[(FeatureType.DATA, 'NDVI_CHANGE')] = ndvi_change
        
        # 통계 계산
        total_pixels = change_map.size
        increase_pixels = np.sum(significant_increase)
        decrease_pixels = np.sum(significant_decrease)
        
        change_stats = {
            'increase_percentage': (increase_pixels / total_pixels) * 100,
            'decrease_percentage': (decrease_pixels / total_pixels) * 100,
            'no_change_percentage': (np.sum(no_change) / total_pixels) * 100,
            'mean_change': float(np.mean(ndvi_change)),
            'max_increase': float(np.max(ndvi_change)),
            'max_decrease': float(np.min(ndvi_change))
        }
        
        eopatch[(FeatureType.SCALAR, 'CHANGE_STATS')] = change_stats
        
        print(f"✓ 변화 탐지 완료")
        print(f"\n📈 변화 탐지 통계:")
        print(f"  - 식생 증가: {change_stats['increase_percentage']:.2f}%")
        print(f"  - 식생 감소: {change_stats['decrease_percentage']:.2f}%")
        print(f"  - 변화 없음: {change_stats['no_change_percentage']:.2f}%")
        print(f"  - 평균 NDVI 변화: {change_stats['mean_change']:.3f}")
        
        return eopatch


class DataQualityTask(EOTask):
    """데이터 품질 평가 태스크"""
    
    def execute(self, eopatch, **kwargs):
        """데이터 품질 평가"""
        
        quality_report = {
            'data_completeness': {},
            'cloud_coverage': {},
            'valid_pixels': {}
        }
        
        # 데이터 완전성 체크
        bands = eopatch[(FeatureType.DATA, 'BANDS')]
        if bands is not None:
            # NaN 또는 무효한 값 체크
            nan_pixels = np.isnan(bands).sum()
            total_pixels = bands.size
            quality_report['data_completeness'] = {
                'valid_percentage': ((total_pixels - nan_pixels) / total_pixels) * 100,
                'nan_pixels': int(nan_pixels)
            }
        
        # 구름 비율
        cloud_mask = eopatch[(FeatureType.MASK, 'CLOUD')]
        if cloud_mask is not None:
            cloud_percentage = np.mean(cloud_mask) * 100
            quality_report['cloud_coverage'] = {
                'average_percentage': float(cloud_percentage),
                'max_percentage': float(np.max(np.mean(cloud_mask, axis=(1, 2))) * 100),
                'min_percentage': float(np.min(np.mean(cloud_mask, axis=(1, 2))) * 100)
            }
        
        # 유효 픽셀 비율
        if bands is not None and cloud_mask is not None:
            valid_mask = ~cloud_mask.astype(bool)
            valid_percentage = np.mean(valid_mask) * 100
            quality_report['valid_pixels'] = {
                'percentage': float(valid_percentage)
            }
        
        eopatch[(FeatureType.SCALAR, 'QUALITY_REPORT')] = quality_report
        
        print(f"✓ 데이터 품질 평가 완료")
        print(f"\n📋 품질 보고서:")
        print(f"  - 데이터 완전성: {quality_report['data_completeness'].get('valid_percentage', 0):.1f}%")
        print(f"  - 평균 구름 비율: {quality_report['cloud_coverage'].get('average_percentage', 0):.1f}%")
        print(f"  - 유효 픽셀: {quality_report['valid_pixels'].get('percentage', 0):.1f}%")
        
        return eopatch


def create_analysis_workflow():
    """분석 워크플로우 생성"""
    
    # 태스크 정의
    tasks = []
    
    # 1. 데이터 로드
    load_task = LoadDataTask()
    tasks.append((load_task, [], 'load'))
    
    # 2. 데이터 품질 평가
    quality_task = DataQualityTask()
    tasks.append((quality_task, ['load'], 'quality'))
    
    # 3. 구름 마스크
    cloud_task = AddCloudMaskTask(threshold=0.4)
    tasks.append((cloud_task, ['quality'], 'cloud'))
    
    # 4. 스펙트럴 인덱스 계산
    ndvi_task = NormalizedDifferenceIndexTask(
        input_feature=(FeatureType.DATA, 'BANDS'),
        output_feature=(FeatureType.DATA, 'NDVI'),
        bands_indices=(7, 3)  # NIR, RED
    )
    tasks.append((ndvi_task, ['cloud'], 'ndvi'))
    
    ndwi_task = NormalizedDifferenceIndexTask(
        input_feature=(FeatureType.DATA, 'BANDS'),
        output_feature=(FeatureType.DATA, 'NDWI'),
        bands_indices=(2, 7)  # GREEN, NIR
    )
    tasks.append((ndwi_task, ['ndvi'], 'ndwi'))
    
    # 5. 토지 피복 분류
    classification_task = LandCoverClassificationTask()
    tasks.append((classification_task, ['ndwi'], 'classification'))
    
    # 6. 변화 탐지
    change_task = ChangeDetectionTask(change_threshold=0.2)
    tasks.append((change_task, ['classification'], 'change'))
    
    # 워크플로우 생성
    workflow = EOWorkflow(tasks)
    
    return workflow


def demonstrate_land_cover_analysis():
    """토지 피복 분석 데모"""
    
    print("\n" + "="*60)
    print("🛰️ eo-learn 토지 피복 분석 시스템")
    print("="*60)
    
    # 워크플로우 생성
    workflow = create_analysis_workflow()
    
    # 실행
    eopatch = workflow.execute()
    
    # 결과 요약
    print("\n" + "="*60)
    print("📊 분석 완료 - 최종 결과 요약")
    print("="*60)
    
    # EOPatch 내용 확인
    features = eopatch.get_feature_list()
    print(f"\n생성된 특징 수: {len(features)}")
    print("주요 특징:")
    for feature_type, feature_name in features[:10]:
        print(f"  - {feature_type.value}/{feature_name}")
    
    # 메타데이터
    if eopatch[(FeatureType.TIMESTAMP, 'timestamps')]:
        timestamps = eopatch[(FeatureType.TIMESTAMP, 'timestamps')]
        print(f"\n시계열 범위:")
        print(f"  - {timestamps[0].strftime('%Y-%m-%d')} ~ {timestamps[-1].strftime('%Y-%m-%d')}")
        print(f"  - 총 {len(timestamps)}개 시점")
    
    return eopatch


if __name__ == "__main__":
    # 분석 실행
    eopatch = demonstrate_land_cover_analysis()
    
    print("\n" + "="*60)
    print("✅ 모든 분석이 완료되었습니다!")
    print("실제 위성 데이터를 사용하면 더 정확한 결과를 얻을 수 있습니다.")
    print("="*60)