# eo-learn 빠른 시작 가이드

## 설치

```bash
# 기본 설치
pip install eo-learn

# 전체 패키지 설치 (모든 모듈 포함)
pip install "eo-learn[ALL]"

# 특정 모듈만 설치
pip install "eo-learn[CORE,IO,MASK,FEATURES]"

# 개발 환경 설치
pip install -e ".[DEV]"
```

## 필수 요구사항

- Python 3.8+
- Sentinel Hub 계정 (무료 평가판 가능)
- 최소 8GB RAM (대용량 데이터 처리 시 16GB+ 권장)

## 기본 개념

### 1. EOPatch
eo-learn의 핵심 데이터 구조로, 위성 이미지와 관련 메타데이터를 저장합니다.

```python
from eolearn.core import EOPatch, FeatureType

# EOPatch 생성
eopatch = EOPatch()

# 데이터 추가
eopatch[(FeatureType.DATA, 'BANDS')] = sentinel2_bands
eopatch[(FeatureType.MASK, 'CLOUD')] = cloud_mask
eopatch.bbox = bbox
eopatch.timestamp = timestamps
```

### 2. EOTask
데이터 처리를 위한 기본 단위입니다.

```python
from eolearn.core import EOTask

class CustomTask(EOTask):
    def execute(self, eopatch):
        # 처리 로직
        processed_data = self.process(eopatch.data['BANDS'])
        eopatch.data['PROCESSED'] = processed_data
        return eopatch
```

### 3. EOWorkflow
여러 태스크를 연결하여 파이프라인을 구성합니다.

```python
from eolearn.core import EOWorkflow, LoadTask, SaveTask

# 워크플로우 생성
workflow = EOWorkflow([
    (load_task, [], 'load'),
    (cloud_mask_task, ['load'], 'mask'),
    (ndvi_task, ['mask'], 'ndvi'),
    (save_task, ['ndvi'], 'save')
])

# 실행
result = workflow.execute()
```

## 주요 사용 사례

### 1. 시계열 분석
```python
from eolearn.features import LinearInterpolationTask

# 구름으로 가려진 픽셀 보간
interpolation = LinearInterpolationTask(
    feature=(FeatureType.DATA, 'BANDS'),
    mask_feature=(FeatureType.MASK, 'VALID_DATA')
)
```

### 2. 토지 피복 변화 감지
```python
from eolearn.features import NormalizedDifferenceIndexTask

# NDVI 계산
ndvi = NormalizedDifferenceIndexTask(
    input_feature=(FeatureType.DATA, 'BANDS'),
    output_feature=(FeatureType.DATA, 'NDVI'),
    bands_indices=(7, 3)  # NIR, RED
)
```

### 3. 머신러닝 통합
```python
from eolearn.ml_tools import FractionSamplingTask
from sklearn.ensemble import RandomForestClassifier

# 샘플링
sampling = FractionSamplingTask(
    features_to_sample=[(FeatureType.DATA, 'FEATURES')],
    sampling_fraction=0.1
)

# 분류
rf_classifier = RandomForestClassifier(n_estimators=100)
```

## Sentinel Hub 연동

### 1. 인증 설정
```python
from sentinelhub import SHConfig

config = SHConfig()
config.sh_client_id = 'your-client-id'
config.sh_client_secret = 'your-client-secret'
```

### 2. 데이터 다운로드
```python
from eolearn.io import SentinelHubInputTask
from sentinelhub import DataCollection, BBox, CRS

# 입력 태스크 정의
input_task = SentinelHubInputTask(
    data_collection=DataCollection.SENTINEL2_L1C,
    bands=['B02', 'B03', 'B04', 'B08'],  # Blue, Green, Red, NIR
    resolution=10,
    maxcc=0.2,  # 최대 구름 비율 20%
    time_difference=timedelta(days=1)
)

# 경계 상자 정의
bbox = BBox([14.4, 46.0, 14.6, 46.2], crs=CRS.WGS84)

# 데이터 다운로드
eopatch = input_task.execute(bbox=bbox, time_interval=('2023-01-01', '2023-12-31'))
```

## 시각화

### 1. RGB 이미지 표시
```python
from eolearn.visualization import PlotTask
import matplotlib.pyplot as plt

# RGB 플롯
plot_rgb = PlotTask(
    feature=(FeatureType.DATA, 'BANDS'),
    bands=[2, 1, 0],  # R, G, B
    factor=3.5,
    figsize=(10, 10)
)

fig = plot_rgb.execute(eopatch)
plt.show()
```

### 2. 시계열 그래프
```python
import numpy as np

# NDVI 시계열
ndvi_values = eopatch[(FeatureType.DATA, 'NDVI')]
mean_ndvi = np.mean(ndvi_values, axis=(1, 2, 3))

plt.figure(figsize=(12, 4))
plt.plot(eopatch.timestamp, mean_ndvi)
plt.xlabel('Date')
plt.ylabel('Mean NDVI')
plt.title('NDVI Time Series')
plt.grid(True)
plt.show()
```

## 성능 최적화 팁

1. **메모리 관리**
   - 큰 지역은 타일로 분할 처리
   - 불필요한 밴드는 제외
   - `lazy_loading=True` 옵션 사용

2. **병렬 처리**
   - `EOExecutor`로 여러 EOPatch 동시 처리
   - `multiprocessing=True` 옵션 활용

3. **캐싱**
   - 자주 사용하는 데이터는 로컬에 저장
   - `SaveTask`와 `LoadTask` 활용

## 유용한 리소스

- [공식 문서](https://eo-learn.readthedocs.io/)
- [예제 저장소](https://github.com/sentinel-hub/eo-learn-examples)
- [Sentinel Hub 포럼](https://forum.sentinel-hub.com/)
- [Medium 튜토리얼 시리즈](https://medium.com/sentinel-hub)

## 문제 해결

### 일반적인 오류와 해결 방법

1. **메모리 부족**
   ```python
   # 타일 크기 줄이기
   split_task = SplitTask(tile_size=(512, 512))
   ```

2. **인증 실패**
   ```python
   # 자격 증명 확인
   config = SHConfig()
   print(config.sh_client_id)  # None이면 설정 필요
   ```

3. **시간 초과**
   ```python
   # 타임아웃 증가
   input_task = SentinelHubInputTask(
       ...,
       config=config,
       max_threads=5  # 동시 요청 수 조정
   )
   ```