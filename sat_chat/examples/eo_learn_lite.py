"""
eo-learn Lite: 간소화된 eo-learn 스타일 구현
실제 eo-learn 패키지 없이도 핵심 개념을 체험할 수 있는 버전
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
import os

class FeatureType(Enum):
    """eo-learn의 FeatureType을 모방"""
    DATA = 'data'
    MASK = 'mask'
    SCALAR = 'scalar'
    LABEL = 'label'
    VECTOR = 'vector'
    META_INFO = 'meta_info'
    BBOX = 'bbox'
    TIMESTAMP = 'timestamp'


class EOPatch:
    """
    eo-learn의 핵심 데이터 구조인 EOPatch를 간소화한 구현
    위성 이미지와 관련 데이터를 저장하는 컨테이너
    """
    
    def __init__(self, **kwargs):
        """EOPatch 초기화"""
        self.data = {}
        self.mask = {}
        self.scalar = {}
        self.label = {}
        self.vector = {}
        self.meta_info = {}
        self.bbox = kwargs.get('bbox', None)
        self.timestamp = kwargs.get('timestamp', [])
        
        # 초기 데이터 설정
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def __getitem__(self, feature):
        """특징 접근자"""
        feature_type, feature_name = feature
        
        if feature_type == FeatureType.DATA:
            return self.data.get(feature_name)
        elif feature_type == FeatureType.MASK:
            return self.mask.get(feature_name)
        elif feature_type == FeatureType.SCALAR:
            return self.scalar.get(feature_name)
        elif feature_type == FeatureType.LABEL:
            return self.label.get(feature_name)
        elif feature_type == FeatureType.VECTOR:
            return self.vector.get(feature_name)
        elif feature_type == FeatureType.META_INFO:
            return self.meta_info.get(feature_name)
        elif feature_type == FeatureType.BBOX:
            return self.bbox
        elif feature_type == FeatureType.TIMESTAMP:
            return self.timestamp
        else:
            raise KeyError(f"Unknown feature type: {feature_type}")
    
    def __setitem__(self, feature, value):
        """특징 설정자"""
        feature_type, feature_name = feature
        
        if feature_type == FeatureType.DATA:
            self.data[feature_name] = value
        elif feature_type == FeatureType.MASK:
            self.mask[feature_name] = value
        elif feature_type == FeatureType.SCALAR:
            self.scalar[feature_name] = value
        elif feature_type == FeatureType.LABEL:
            self.label[feature_name] = value
        elif feature_type == FeatureType.VECTOR:
            self.vector[feature_name] = value
        elif feature_type == FeatureType.META_INFO:
            self.meta_info[feature_name] = value
        elif feature_type == FeatureType.BBOX:
            self.bbox = value
        elif feature_type == FeatureType.TIMESTAMP:
            self.timestamp = value
        else:
            raise KeyError(f"Unknown feature type: {feature_type}")
    
    def get_feature_list(self):
        """모든 특징 목록 반환"""
        features = []
        for feature_name in self.data:
            features.append((FeatureType.DATA, feature_name))
        for feature_name in self.mask:
            features.append((FeatureType.MASK, feature_name))
        for feature_name in self.scalar:
            features.append((FeatureType.SCALAR, feature_name))
        return features
    
    def __repr__(self):
        """EOPatch 표현"""
        return f"EOPatch(\n" \
               f"  data: {list(self.data.keys())}\n" \
               f"  mask: {list(self.mask.keys())}\n" \
               f"  scalar: {list(self.scalar.keys())}\n" \
               f"  timestamp: {len(self.timestamp)} dates\n" \
               f"  bbox: {self.bbox}\n" \
               f")"


class EOTask:
    """
    eo-learn의 EOTask 기본 클래스
    모든 처리 작업의 기본이 되는 추상 클래스
    """
    
    def __init__(self, name="EOTask"):
        self.name = name
    
    def execute(self, eopatch, **kwargs):
        """태스크 실행 - 서브클래스에서 구현"""
        raise NotImplementedError("Subclasses must implement execute method")
    
    def __call__(self, eopatch, **kwargs):
        """함수처럼 호출 가능"""
        return self.execute(eopatch, **kwargs)


class LoadDataTask(EOTask):
    """데이터 로드 태스크"""
    
    def __init__(self, data_path=None):
        super().__init__("LoadDataTask")
        self.data_path = data_path
    
    def execute(self, eopatch=None, **kwargs):
        """모의 데이터 로드"""
        if eopatch is None:
            eopatch = EOPatch()
        
        # 모의 Sentinel-2 데이터 생성 (10개 밴드)
        # 시간, 높이, 너비, 채널
        height, width = 512, 512
        n_bands = 10
        n_timestamps = 5
        
        # 랜덤 데이터 생성 (실제로는 위성 이미지)
        bands_data = np.random.rand(n_timestamps, height, width, n_bands) * 0.3
        
        # 타임스탬프 생성
        base_date = datetime(2024, 1, 1)
        timestamps = [base_date + timedelta(days=i*10) for i in range(n_timestamps)]
        
        # EOPatch에 데이터 추가
        eopatch[(FeatureType.DATA, 'BANDS')] = bands_data
        eopatch[(FeatureType.TIMESTAMP, 'timestamps')] = timestamps
        eopatch[(FeatureType.META_INFO, 'sensor')] = 'Sentinel-2'
        
        print(f"✓ 데이터 로드 완료: {n_timestamps} 시점, {height}x{width} 픽셀, {n_bands} 밴드")
        
        return eopatch


class AddCloudMaskTask(EOTask):
    """구름 마스크 추가 태스크"""
    
    def __init__(self, threshold=0.3):
        super().__init__("AddCloudMaskTask")
        self.threshold = threshold
    
    def execute(self, eopatch, **kwargs):
        """구름 마스크 생성"""
        bands = eopatch[(FeatureType.DATA, 'BANDS')]
        
        # 간단한 구름 탐지 (실제로는 더 복잡한 알고리즘 사용)
        # 밝은 픽셀을 구름으로 가정
        cloud_mask = np.mean(bands, axis=-1) > self.threshold
        
        eopatch[(FeatureType.MASK, 'CLOUD')] = cloud_mask.astype(np.uint8)
        
        cloud_percentage = np.mean(cloud_mask) * 100
        print(f"✓ 구름 마스크 생성 완료: 평균 구름 비율 {cloud_percentage:.1f}%")
        
        return eopatch


class NormalizedDifferenceIndexTask(EOTask):
    """정규화 차이 지수 계산 태스크 (NDVI, NDWI 등)"""
    
    def __init__(self, input_feature, output_feature, bands_indices):
        super().__init__("NormalizedDifferenceIndexTask")
        self.input_feature = input_feature
        self.output_feature = output_feature
        self.band1_idx, self.band2_idx = bands_indices
    
    def execute(self, eopatch, **kwargs):
        """지수 계산"""
        bands = eopatch[self.input_feature]
        
        band1 = bands[..., self.band1_idx]
        band2 = bands[..., self.band2_idx]
        
        # NDI = (band1 - band2) / (band1 + band2)
        with np.errstate(divide='ignore', invalid='ignore'):
            ndi = (band1 - band2) / (band1 + band2 + 1e-10)
            ndi = np.nan_to_num(ndi, nan=0.0)
        
        # 차원 추가 (시간, 높이, 너비, 1)
        ndi = np.expand_dims(ndi, axis=-1)
        
        eopatch[self.output_feature] = ndi
        
        index_name = self.output_feature[1]
        mean_value = np.mean(ndi)
        print(f"✓ {index_name} 계산 완료: 평균값 {mean_value:.3f}")
        
        return eopatch


class InterpolationTask(EOTask):
    """시계열 보간 태스크"""
    
    def __init__(self, feature, mask_feature=None):
        super().__init__("InterpolationTask")
        self.feature = feature
        self.mask_feature = mask_feature
    
    def execute(self, eopatch, **kwargs):
        """선형 보간 수행"""
        data = eopatch[self.feature]
        
        if self.mask_feature:
            mask = eopatch[self.mask_feature]
            # 마스크된 영역 보간
            for t in range(data.shape[0]):
                if t > 0 and t < data.shape[0] - 1:
                    masked_pixels = mask[t] == 1
                    if np.any(masked_pixels):
                        # 이전과 다음 시점의 평균으로 보간
                        data[t][masked_pixels] = (
                            data[t-1][masked_pixels] + data[t+1][masked_pixels]
                        ) / 2
        
        print(f"✓ 시계열 보간 완료")
        return eopatch


class EOWorkflow:
    """
    eo-learn의 EOWorkflow를 모방
    여러 태스크를 연결하여 파이프라인 구성
    """
    
    def __init__(self, tasks):
        """
        Parameters:
        -----------
        tasks : list
            (task, input_tasks, name) 형태의 튜플 리스트
        """
        self.tasks = tasks
        self.results = {}
    
    def execute(self, eopatch=None, **kwargs):
        """워크플로우 실행"""
        print("\n" + "="*60)
        print("EOWorkflow 실행 시작")
        print("="*60)
        
        for task, dependencies, name in self.tasks:
            print(f"\n▶ {name} 태스크 실행 중...")
            
            # 의존성이 있으면 이전 결과 사용
            if dependencies:
                # 간단한 구현: 마지막 의존성의 결과 사용
                last_dep = dependencies[-1] if dependencies else None
                if last_dep in self.results:
                    eopatch = self.results[last_dep]
            
            # 태스크 실행
            eopatch = task.execute(eopatch, **kwargs)
            self.results[name] = eopatch
        
        print("\n" + "="*60)
        print("EOWorkflow 실행 완료!")
        print("="*60)
        
        return eopatch


# 실제 사용 예제
def demonstrate_eo_learn():
    """eo-learn 스타일 워크플로우 시연"""
    
    print("\n🛰️ eo-learn Lite 데모 시작")
    print("-" * 60)
    
    # 1. 태스크 정의
    load_task = LoadDataTask()
    cloud_mask_task = AddCloudMaskTask(threshold=0.3)
    
    # NDVI 계산 (NIR - RED) / (NIR + RED)
    # Sentinel-2: Band 8 (NIR) = index 7, Band 4 (RED) = index 3
    ndvi_task = NormalizedDifferenceIndexTask(
        input_feature=(FeatureType.DATA, 'BANDS'),
        output_feature=(FeatureType.DATA, 'NDVI'),
        bands_indices=(7, 3)
    )
    
    # NDWI 계산 (GREEN - NIR) / (GREEN + NIR)
    # Sentinel-2: Band 3 (GREEN) = index 2, Band 8 (NIR) = index 7
    ndwi_task = NormalizedDifferenceIndexTask(
        input_feature=(FeatureType.DATA, 'BANDS'),
        output_feature=(FeatureType.DATA, 'NDWI'),
        bands_indices=(2, 7)
    )
    
    interpolation_task = InterpolationTask(
        feature=(FeatureType.DATA, 'BANDS'),
        mask_feature=(FeatureType.MASK, 'CLOUD')
    )
    
    # 2. 워크플로우 생성
    workflow = EOWorkflow([
        (load_task, [], 'load'),
        (cloud_mask_task, ['load'], 'cloud_mask'),
        (interpolation_task, ['cloud_mask'], 'interpolate'),
        (ndvi_task, ['interpolate'], 'ndvi'),
        (ndwi_task, ['ndvi'], 'ndwi')
    ])
    
    # 3. 워크플로우 실행
    eopatch = workflow.execute()
    
    # 4. 결과 확인
    print("\n📊 최종 EOPatch 내용:")
    print(eopatch)
    
    # 5. 통계 출력
    if eopatch[(FeatureType.DATA, 'NDVI')] is not None:
        ndvi_data = eopatch[(FeatureType.DATA, 'NDVI')]
        print(f"\n📈 NDVI 통계:")
        print(f"  - 최소값: {np.min(ndvi_data):.3f}")
        print(f"  - 최대값: {np.max(ndvi_data):.3f}")
        print(f"  - 평균값: {np.mean(ndvi_data):.3f}")
        print(f"  - 표준편차: {np.std(ndvi_data):.3f}")
    
    if eopatch[(FeatureType.DATA, 'NDWI')] is not None:
        ndwi_data = eopatch[(FeatureType.DATA, 'NDWI')]
        print(f"\n💧 NDWI 통계:")
        print(f"  - 최소값: {np.min(ndwi_data):.3f}")
        print(f"  - 최대값: {np.max(ndwi_data):.3f}")
        print(f"  - 평균값: {np.mean(ndwi_data):.3f}")
        print(f"  - 표준편차: {np.std(ndwi_data):.3f}")
    
    # 6. 시계열 분석
    timestamps = eopatch[(FeatureType.TIMESTAMP, 'timestamps')]
    if timestamps:
        print(f"\n📅 시계열 정보:")
        print(f"  - 시작일: {timestamps[0].strftime('%Y-%m-%d')}")
        print(f"  - 종료일: {timestamps[-1].strftime('%Y-%m-%d')}")
        print(f"  - 총 {len(timestamps)}개 시점")
        
        # NDVI 시계열 변화
        ndvi_time_series = np.mean(ndvi_data, axis=(1, 2, 3))
        print(f"\n📊 NDVI 시계열 변화:")
        for i, (date, value) in enumerate(zip(timestamps, ndvi_time_series)):
            print(f"  {date.strftime('%Y-%m-%d')}: {value:.3f}")
    
    return eopatch


if __name__ == "__main__":
    # 데모 실행
    eopatch = demonstrate_eo_learn()
    
    print("\n" + "="*60)
    print("✅ eo-learn Lite 데모 완료!")
    print("실제 eo-learn 패키지를 사용하면 더 많은 기능을 활용할 수 있습니다.")
    print("="*60)