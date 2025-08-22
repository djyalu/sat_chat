"""
Land Cover Classification with eo-learn
위성 이미지를 사용한 토지 피복 분류 예제
"""

from eolearn.core import EOTask, EOPatch, EOWorkflow, FeatureType, OverwritePermission
from eolearn.io import SentinelHubInputTask
from eolearn.mask import AddValidDataMaskTask, AddCloudMaskTask
from eolearn.features import NormalizedDifferenceIndexTask, SimpleFilterTask
from eolearn.geometry import VectorToRasterTask
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt

class LandCoverClassifier:
    """토지 피복 분류를 위한 eo-learn 워크플로우"""
    
    def __init__(self, bbox, time_interval, resolution=10):
        """
        Parameters:
        -----------
        bbox : BBox
            관심 영역의 경계 상자
        time_interval : tuple
            시작 및 종료 날짜 (datetime 객체)
        resolution : int
            픽셀 해상도 (미터)
        """
        self.bbox = bbox
        self.time_interval = time_interval
        self.resolution = resolution
        
    def create_eopatch_workflow(self):
        """
        EOWorkflow 생성 및 태스크 연결
        
        TODO(human): 아래 함수를 구현하세요.
        이 함수는 다음 단계들을 포함하는 워크플로우를 생성해야 합니다:
        1. Sentinel-2 데이터 로드
        2. 구름 마스크 추가
        3. NDVI 계산
        4. 시계열 데이터 필터링
        5. 분류를 위한 특징 추출
        
        Returns:
        --------
        workflow : EOWorkflow
            구성된 eo-learn 워크플로우
        """
        # 여기에 구현을 추가하세요
        pass
    
    def calculate_indices(self, eopatch):
        """다양한 스펙트럴 인덱스 계산"""
        
        # NDVI (Normalized Difference Vegetation Index)
        ndvi_task = NormalizedDifferenceIndexTask(
            input_feature=(FeatureType.DATA, 'BANDS'),
            output_feature=(FeatureType.DATA, 'NDVI'),
            bands_indices=(7, 3)  # NIR, RED for Sentinel-2
        )
        
        # NDWI (Normalized Difference Water Index)
        ndwi_task = NormalizedDifferenceIndexTask(
            input_feature=(FeatureType.DATA, 'BANDS'),
            output_feature=(FeatureType.DATA, 'NDWI'),
            bands_indices=(2, 7)  # GREEN, NIR
        )
        
        # NDBI (Normalized Difference Built-up Index)
        ndbi_task = NormalizedDifferenceIndexTask(
            input_feature=(FeatureType.DATA, 'BANDS'),
            output_feature=(FeatureType.DATA, 'NDBI'),
            bands_indices=(10, 7)  # SWIR, NIR
        )
        
        eopatch = ndvi_task(eopatch)
        eopatch = ndwi_task(eopatch)
        eopatch = ndbi_task(eopatch)
        
        return eopatch
    
    def classify_land_cover(self, eopatch):
        """
        규칙 기반 토지 피복 분류
        
        Classes:
        - 0: Water (NDWI > 0.3)
        - 1: Vegetation (NDVI > 0.4)
        - 2: Built-up (NDBI > 0)
        - 3: Bare soil (나머지)
        """
        
        # 인덱스 데이터 가져오기
        ndvi = eopatch[(FeatureType.DATA, 'NDVI')]
        ndwi = eopatch[(FeatureType.DATA, 'NDWI')]
        ndbi = eopatch[(FeatureType.DATA, 'NDBI')]
        
        # 분류 수행
        classification = np.zeros_like(ndvi, dtype=np.uint8)
        
        # Water
        classification[ndwi > 0.3] = 0
        
        # Vegetation
        classification[(ndvi > 0.4) & (ndwi <= 0.3)] = 1
        
        # Built-up
        classification[(ndbi > 0) & (ndvi <= 0.4) & (ndwi <= 0.3)] = 2
        
        # Bare soil (default)
        classification[(ndbi <= 0) & (ndvi <= 0.4) & (ndwi <= 0.3)] = 3
        
        # 결과 저장
        eopatch[(FeatureType.MASK, 'LAND_COVER')] = classification
        
        return eopatch
    
    def visualize_results(self, eopatch, time_idx=0):
        """분류 결과 시각화"""
        
        fig, axes = plt.subplots(2, 3, figsize=(15, 10))
        
        # RGB 이미지
        rgb = eopatch[(FeatureType.DATA, 'BANDS')][time_idx, :, :, [3, 2, 1]]
        rgb = np.clip(rgb * 3.5, 0, 1)  # 밝기 조정
        axes[0, 0].imshow(rgb)
        axes[0, 0].set_title('RGB Composite')
        axes[0, 0].axis('off')
        
        # NDVI
        ndvi = eopatch[(FeatureType.DATA, 'NDVI')][time_idx, :, :, 0]
        im1 = axes[0, 1].imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
        axes[0, 1].set_title('NDVI')
        axes[0, 1].axis('off')
        plt.colorbar(im1, ax=axes[0, 1])
        
        # NDWI
        ndwi = eopatch[(FeatureType.DATA, 'NDWI')][time_idx, :, :, 0]
        im2 = axes[0, 2].imshow(ndwi, cmap='Blues', vmin=-1, vmax=1)
        axes[0, 2].set_title('NDWI')
        axes[0, 2].axis('off')
        plt.colorbar(im2, ax=axes[0, 2])
        
        # NDBI
        ndbi = eopatch[(FeatureType.DATA, 'NDBI')][time_idx, :, :, 0]
        im3 = axes[1, 0].imshow(ndbi, cmap='copper', vmin=-1, vmax=1)
        axes[1, 0].set_title('NDBI')
        axes[1, 0].axis('off')
        plt.colorbar(im3, ax=axes[1, 0])
        
        # Land Cover Classification
        land_cover = eopatch[(FeatureType.MASK, 'LAND_COVER')][time_idx, :, :, 0]
        colors = ['blue', 'green', 'red', 'brown']  # Water, Vegetation, Built-up, Bare soil
        cmap = plt.matplotlib.colors.ListedColormap(colors)
        im4 = axes[1, 1].imshow(land_cover, cmap=cmap, vmin=0, vmax=3)
        axes[1, 1].set_title('Land Cover Classification')
        axes[1, 1].axis('off')
        
        # Legend for land cover
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor='blue', label='Water'),
            Patch(facecolor='green', label='Vegetation'),
            Patch(facecolor='red', label='Built-up'),
            Patch(facecolor='brown', label='Bare soil')
        ]
        axes[1, 2].legend(handles=legend_elements, loc='center', fontsize=12)
        axes[1, 2].axis('off')
        axes[1, 2].set_title('Legend')
        
        plt.tight_layout()
        plt.show()
        
        return fig
    
    def calculate_statistics(self, eopatch):
        """토지 피복 통계 계산"""
        
        land_cover = eopatch[(FeatureType.MASK, 'LAND_COVER')]
        
        stats = []
        for t in range(land_cover.shape[0]):
            lc = land_cover[t, :, :, 0]
            
            total_pixels = lc.size
            water_pixels = np.sum(lc == 0)
            vegetation_pixels = np.sum(lc == 1)
            builtup_pixels = np.sum(lc == 2)
            baresoil_pixels = np.sum(lc == 3)
            
            stats.append({
                'timestamp': eopatch.timestamp[t],
                'water_percent': (water_pixels / total_pixels) * 100,
                'vegetation_percent': (vegetation_pixels / total_pixels) * 100,
                'builtup_percent': (builtup_pixels / total_pixels) * 100,
                'baresoil_percent': (baresoil_pixels / total_pixels) * 100
            })
        
        return stats


# 사용 예제
def main():
    """메인 실행 함수"""
    
    # 설정 (예제 좌표 - 서울 지역)
    from sentinelhub import BBox, CRS
    
    # 경계 상자 정의 (서울 일부 지역)
    bbox = BBox(bbox=[126.9, 37.5, 127.0, 37.6], crs=CRS.WGS84)
    
    # 시간 간격 설정
    time_interval = (datetime(2023, 6, 1), datetime(2023, 8, 31))
    
    # 분류기 생성
    classifier = LandCoverClassifier(bbox, time_interval)
    
    # 워크플로우 실행
    print("Creating workflow...")
    workflow = classifier.create_eopatch_workflow()
    
    if workflow:
        print("Executing workflow...")
        eopatch = workflow.execute()
        
        # 인덱스 계산
        print("Calculating spectral indices...")
        eopatch = classifier.calculate_indices(eopatch)
        
        # 분류 수행
        print("Performing land cover classification...")
        eopatch = classifier.classify_land_cover(eopatch)
        
        # 통계 계산
        print("Calculating statistics...")
        stats = classifier.calculate_statistics(eopatch)
        
        # 결과 출력
        print("\nLand Cover Statistics:")
        for stat in stats[:3]:  # 처음 3개 타임스탬프만 출력
            print(f"\nDate: {stat['timestamp']}")
            print(f"  Water: {stat['water_percent']:.2f}%")
            print(f"  Vegetation: {stat['vegetation_percent']:.2f}%")
            print(f"  Built-up: {stat['builtup_percent']:.2f}%")
            print(f"  Bare soil: {stat['baresoil_percent']:.2f}%")
        
        # 시각화
        print("\nVisualizing results...")
        classifier.visualize_results(eopatch)
    else:
        print("Workflow creation not implemented yet. Please complete the TODO section.")


if __name__ == "__main__":
    main()