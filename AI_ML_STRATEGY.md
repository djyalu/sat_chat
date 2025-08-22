# SatChat 시스템 AI/ML 및 이미지 처리 전략 설계서

## 목차
1. [해상 폐기물 탐지 알고리즘](#1-해상-폐기물-탐지-알고리즘)
2. [위성 이미지 전처리 기법](#2-위성-이미지-전처리-기법)
3. [딥러닝 모델 아키텍처](#3-딥러닝-모델-아키텍처)
4. [학습 데이터 준비 및 라벨링 전략](#4-학습-데이터-준비-및-라벨링-전략)
5. [모델 성능 평가 지표](#5-모델-성능-평가-지표)
6. [Edge AI 및 온보드 처리](#6-edge-ai-및-온보드-처리)
7. [멀티스펙트럴/하이퍼스펙트럴 데이터 활용](#7-멀티스펙트럴하이퍼스펙트럴-데이터-활용)
8. [시계열 분석 기반 폐기물 이동 예측](#8-시계열-분석-기반-폐기물-이동-예측)
9. [해양 환경 특수성 대응 기술](#9-해양-환경-특수성-대응-기술)

---

## 1. 해상 폐기물 탐지 알고리즘

### 1.1 폐기물 분류 체계

```yaml
폐기물_분류:
  플라스틱_폐기물:
    - 플라스틱_병: [크기: 5-50cm, 반사율: 중간, 스펙트럴_특성: 800-900nm 흡수]
    - 비닐봉지: [크기: 10-100cm, 반사율: 높음, 형태: 불규칙]
    - 플라스틱_시트: [크기: 50-500cm, 반사율: 높음, 형태: 평면]
    - 미세플라스틱: [크기: <5mm, 집합체_형태, 스펙트럴_서명: 특수]
  
  유류_오염:
    - 원유_유출: [두께: 0.1-10mm, 무지개_반사, NIR_흡수_강함]
    - 연료유: [점성_높음, 적외선_서명_특수, 가장자리_불규칙]
    - 유화물: [물-기름_혼합, 갈색_계열, 중간_반사율]
  
  기타_부유물:
    - 목재: [자연_갈색_톤, 700-800nm_흡수, 선형_형태]
    - 금속: [높은_반사율, 각진_형태, 자기장_영향]
    - 해초/자연물: [녹색_스펙트럴, 계절적_변화, 생물학적_패턴]
```

### 1.2 다단계 탐지 알고리즘

```python
class MarineDebrisDetector:
    """해상 폐기물 탐지 통합 알고리즘"""
    
    def __init__(self):
        self.stages = {
            'preprocessing': PreprocessingPipeline(),
            'segmentation': SemanticSegmentation(),
            'classification': DebrisClassifier(),
            'tracking': TemporalTracker(),
            'validation': FalsePositiveFilter()
        }
    
    def detect_debris(self, satellite_image):
        # Stage 1: 전처리 및 정규화
        processed_img = self.stages['preprocessing'].process(satellite_image)
        
        # Stage 2: 의심 영역 분할
        candidate_regions = self.stages['segmentation'].segment(processed_img)
        
        # Stage 3: 폐기물 분류
        classified_debris = self.stages['classification'].classify(candidate_regions)
        
        # Stage 4: 시간적 추적
        tracked_objects = self.stages['tracking'].track(classified_debris)
        
        # Stage 5: 거짓 양성 필터링
        validated_debris = self.stages['validation'].filter(tracked_objects)
        
        return validated_debris
```

### 1.3 스펙트럴 서명 기반 탐지

```python
class SpectralSignatureAnalyzer:
    """스펙트럴 서명 기반 폐기물 식별"""
    
    SPECTRAL_SIGNATURES = {
        'plastic': {
            'peak_wavelengths': [850, 950, 1050],  # nm
            'absorption_bands': [800-900, 1000-1100],
            'ratio_indices': ['NDPI', 'PLI']  # 플라스틱 지수
        },
        'oil': {
            'peak_wavelengths': [1600, 2200],
            'absorption_bands': [1700-1800, 2300-2400],
            'ratio_indices': ['OI', 'HIR']  # 오일 지수, 탄화수소 지수
        },
        'organic': {
            'peak_wavelengths': [550, 670, 750],
            'absorption_bands': [680, 760],
            'ratio_indices': ['NDVI', 'EVI']
        }
    }
    
    def calculate_plastic_index(self, bands):
        """플라스틱 탐지 지수 (NDPI) 계산"""
        # NDPI = (NIR - SWIR1) / (NIR + SWIR1)
        return (bands['nir'] - bands['swir1']) / (bands['nir'] + bands['swir1'])
    
    def calculate_oil_index(self, bands):
        """오일 탐지 지수 계산"""
        # OI = SWIR2 / SWIR1
        return bands['swir2'] / bands['swir1']
```

---

## 2. 위성 이미지 전처리 기법

### 2.1 대기 보정 및 정규화

```python
class AtmosphericCorrection:
    """대기 효과 보정 파이프라인"""
    
    def __init__(self):
        self.correction_methods = {
            'rayleigh_scattering': self.correct_rayleigh,
            'aerosol_scattering': self.correct_aerosol,
            'water_vapor': self.correct_water_vapor,
            'ozone_absorption': self.correct_ozone
        }
    
    def dark_object_subtraction(self, image, percentile=1):
        """암객체 차감법 - 대기 산란 보정"""
        dark_values = np.percentile(image, percentile, axis=(0,1))
        return np.clip(image - dark_values, 0, None)
    
    def bidirectional_reflectance(self, image, sun_angle, view_angle):
        """양방향 반사율 정규화"""
        brdf_factor = self.calculate_brdf_factor(sun_angle, view_angle)
        return image / brdf_factor
    
    def topographic_correction(self, image, dem, sun_angle):
        """지형 효과 보정"""
        illumination = self.calculate_illumination(dem, sun_angle)
        return image * (np.cos(np.radians(sun_angle)) / illumination)
```

### 2.2 해수면 반사 및 Sun-glint 제거

```python
class SunGlintCorrection:
    """태양 반사광 제거 알고리즘"""
    
    def detect_sun_glint(self, image, threshold=0.15):
        """태양 반사광 영역 탐지"""
        # NIR 밴드에서 높은 반사율 영역 탐지
        nir_band = image[:,:,3]  # NIR 밴드
        glint_mask = nir_band > threshold
        
        # 형태학적 연산으로 노이즈 제거
        glint_mask = cv2.morphologyEx(glint_mask.astype(np.uint8), 
                                     cv2.MORPH_CLOSE, 
                                     np.ones((5,5), np.uint8))
        return glint_mask.astype(bool)
    
    def remove_sun_glint(self, image, wind_speed=5.0):
        """Cox-Munk 모델 기반 sun-glint 제거"""
        glint_mask = self.detect_sun_glint(image)
        
        # 선형 회귀를 통한 glint 추정
        for band in range(image.shape[2]):
            band_data = image[:,:,band]
            nir_data = image[:,:,3]  # NIR을 참조 밴드로 사용
            
            # glint가 없는 영역에서 관계식 학습
            clean_pixels = ~glint_mask
            if np.sum(clean_pixels) > 1000:
                coeffs = np.polyfit(nir_data[clean_pixels], 
                                  band_data[clean_pixels], 1)
                
                # glint 영역 보정
                corrected_values = band_data[glint_mask] - \
                                 (coeffs[0] * nir_data[glint_mask] + coeffs[1])
                image[glint_mask, band] = np.clip(corrected_values, 0, 1)
        
        return image
```

### 2.3 구름 탐지 및 마스킹

```python
class CloudDetection:
    """멀티스펙트럴 구름 탐지"""
    
    def __init__(self):
        self.cloud_indices = {
            'normalized_difference_snow_index': self.calculate_ndsi,
            'brightness_temperature': self.calculate_bt,
            'cirrus_band': self.calculate_cirrus,
            'visible_threshold': self.calculate_visible_threshold
        }
    
    def fmask_algorithm(self, image, thermal_bands):
        """Fmask 알고리즘 기반 구름 탐지"""
        # 1단계: 기본 구름 테스트
        basic_cloud = self.basic_cloud_test(image)
        
        # 2단계: 열적 테스트
        thermal_cloud = self.thermal_test(thermal_bands)
        
        # 3단계: 구름 그림자 탐지
        cloud_shadow = self.cloud_shadow_test(image, basic_cloud)
        
        # 4단계: 얇은 구름 테스트 (Cirrus)
        thin_cloud = self.thin_cloud_test(image)
        
        # 최종 마스크 생성
        final_mask = basic_cloud | thermal_cloud | thin_cloud
        return final_mask, cloud_shadow
    
    def calculate_ndsi(self, green_band, swir_band):
        """정규화차이설지수 - 구름/눈 구분"""
        return (green_band - swir_band) / (green_band + swir_band)
```

---

## 3. 딥러닝 모델 아키텍처

### 3.1 CNN 기반 세맨틱 세그멘테이션

```python
import torch
import torch.nn as nn
import torchvision.transforms as transforms

class MarineDebrisUNet(nn.Module):
    """해상 폐기물 탐지를 위한 U-Net 아키텍처"""
    
    def __init__(self, n_channels=8, n_classes=5):  # 8채널 입력, 5클래스 출력
        super(MarineDebrisUNet, self).__init__()
        
        # Encoder (다운샘플링)
        self.enc1 = self.conv_block(n_channels, 64)
        self.enc2 = self.conv_block(64, 128)
        self.enc3 = self.conv_block(128, 256)
        self.enc4 = self.conv_block(256, 512)
        
        # Bottleneck
        self.bottleneck = self.conv_block(512, 1024)
        
        # Decoder (업샘플링)
        self.dec4 = self.upconv_block(1024, 512)
        self.dec3 = self.upconv_block(512, 256)
        self.dec2 = self.upconv_block(256, 128)
        self.dec1 = self.upconv_block(128, 64)
        
        # 최종 분류층
        self.final_conv = nn.Conv2d(64, n_classes, kernel_size=1)
        
        # 어텐션 메커니즘
        self.attention = SpatialAttention()
        
    def conv_block(self, in_channels, out_channels):
        return nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_channels, out_channels, 3, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )
    
    def upconv_block(self, in_channels, out_channels):
        return nn.Sequential(
            nn.ConvTranspose2d(in_channels, out_channels, 2, stride=2),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(inplace=True)
        )

class SpatialAttention(nn.Module):
    """공간적 어텐션 모듈"""
    
    def __init__(self):
        super(SpatialAttention, self).__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size=7, padding=3)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        avg_pool = torch.mean(x, dim=1, keepdim=True)
        max_pool, _ = torch.max(x, dim=1, keepdim=True)
        combined = torch.cat([avg_pool, max_pool], dim=1)
        attention = self.sigmoid(self.conv(combined))
        return x * attention
```

### 3.2 Vision Transformer for Marine Debris

```python
class MarineDebrisViT(nn.Module):
    """해상 폐기물 탐지를 위한 Vision Transformer"""
    
    def __init__(self, image_size=256, patch_size=16, num_classes=5, 
                 dim=768, depth=12, heads=12, mlp_dim=3072):
        super().__init__()
        
        self.patch_size = patch_size
        self.num_patches = (image_size // patch_size) ** 2
        self.patch_dim = (patch_size ** 2) * 8  # 8 채널
        
        # 패치 임베딩
        self.patch_embedding = nn.Linear(self.patch_dim, dim)
        self.pos_embedding = nn.Parameter(torch.randn(1, self.num_patches + 1, dim))
        self.cls_token = nn.Parameter(torch.randn(1, 1, dim))
        
        # Transformer 블록
        self.transformer = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(
                d_model=dim,
                nhead=heads,
                dim_feedforward=mlp_dim,
                dropout=0.1,
                activation='gelu'
            ),
            num_layers=depth
        )
        
        # 분류 헤드
        self.classifier = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, num_classes)
        )
        
        # 세그멘테이션을 위한 디코더
        self.segmentation_head = SegmentationHead(dim, num_classes, image_size)
    
    def forward(self, x):
        b, c, h, w = x.shape
        
        # 패치로 분할
        patches = self.extract_patches(x)  # [B, num_patches, patch_dim]
        
        # 패치 임베딩
        patch_embeddings = self.patch_embedding(patches)
        
        # CLS 토큰 추가
        cls_tokens = self.cls_token.expand(b, -1, -1)
        embeddings = torch.cat([cls_tokens, patch_embeddings], dim=1)
        
        # 위치 임베딩 추가
        embeddings += self.pos_embedding
        
        # Transformer 적용
        encoded = self.transformer(embeddings)
        
        # 분류 및 세그멘테이션
        cls_output = self.classifier(encoded[:, 0])  # CLS 토큰
        seg_output = self.segmentation_head(encoded[:, 1:])  # 패치 토큰들
        
        return cls_output, seg_output

class SegmentationHead(nn.Module):
    """세그멘테이션을 위한 디코더 헤드"""
    
    def __init__(self, embed_dim, num_classes, image_size):
        super().__init__()
        self.embed_dim = embed_dim
        self.image_size = image_size
        
        self.decoder = nn.Sequential(
            nn.Linear(embed_dim, embed_dim // 2),
            nn.ReLU(),
            nn.Linear(embed_dim // 2, embed_dim // 4),
            nn.ReLU(),
            nn.Linear(embed_dim // 4, num_classes)
        )
    
    def forward(self, x):
        # [B, num_patches, embed_dim] -> [B, num_patches, num_classes]
        decoded = self.decoder(x)
        
        # 패치를 이미지 형태로 재구성
        b, num_patches, num_classes = decoded.shape
        patch_size = int(self.image_size / int(num_patches ** 0.5))
        
        # Reshape to [B, num_classes, H, W]
        h_patches = w_patches = int(num_patches ** 0.5)
        segmentation = decoded.transpose(1, 2).contiguous().view(
            b, num_classes, h_patches, w_patches
        )
        
        # 원본 이미지 크기로 업샘플링
        segmentation = F.interpolate(
            segmentation, 
            size=(self.image_size, self.image_size), 
            mode='bilinear', 
            align_corners=False
        )
        
        return segmentation
```

### 3.3 하이브리드 CNN-Transformer 모델

```python
class HybridMarineNet(nn.Module):
    """CNN과 Transformer를 결합한 하이브리드 모델"""
    
    def __init__(self, num_classes=5):
        super(HybridMarineNet, self).__init__()
        
        # CNN 백본 (특징 추출)
        self.cnn_backbone = self.build_cnn_backbone()
        
        # Transformer 처리를 위한 특징 변환
        self.feature_projection = nn.Conv2d(512, 256, 1)
        
        # Spatial Transformer
        self.spatial_transformer = SpatialTransformer(256, 8, 4)
        
        # 최종 분류/세그멘테이션 헤드
        self.classification_head = nn.Linear(256, num_classes)
        self.segmentation_head = nn.Conv2d(256, num_classes, 1)
        
    def build_cnn_backbone(self):
        """ResNet 기반 CNN 백본"""
        backbone = torchvision.models.resnet50(pretrained=True)
        # 첫 번째 conv 레이어를 8채널 입력으로 수정
        backbone.conv1 = nn.Conv2d(8, 64, kernel_size=7, stride=2, padding=3, bias=False)
        # 분류 레이어 제거
        backbone = nn.Sequential(*list(backbone.children())[:-2])
        return backbone
    
    def forward(self, x):
        # CNN 특징 추출
        cnn_features = self.cnn_backbone(x)  # [B, 2048, H/32, W/32]
        
        # 특징 차원 감소
        projected_features = self.feature_projection(cnn_features)  # [B, 256, H/32, W/32]
        
        # Transformer로 글로벌 컨텍스트 학습
        transformer_features = self.spatial_transformer(projected_features)
        
        # 글로벌 평균 풀링 for 분류
        global_features = F.adaptive_avg_pool2d(transformer_features, 1).flatten(1)
        classification = self.classification_head(global_features)
        
        # 세그멘테이션
        segmentation = self.segmentation_head(transformer_features)
        segmentation = F.interpolate(segmentation, size=x.shape[-2:], mode='bilinear')
        
        return classification, segmentation

class SpatialTransformer(nn.Module):
    """공간적 관계를 학습하는 Transformer"""
    
    def __init__(self, dim, heads, depth):
        super().__init__()
        self.layers = nn.ModuleList([])
        for _ in range(depth):
            self.layers.append(nn.ModuleList([
                PreNorm(dim, Attention(dim, heads=heads)),
                PreNorm(dim, FeedForward(dim))
            ]))
    
    def forward(self, x):
        b, c, h, w = x.shape
        
        # [B, C, H, W] -> [B, H*W, C]
        x = x.flatten(2).transpose(1, 2)
        
        for attn, ff in self.layers:
            x = attn(x) + x
            x = ff(x) + x
        
        # [B, H*W, C] -> [B, C, H, W]
        x = x.transpose(1, 2).view(b, c, h, w)
        return x
```

---

## 4. 학습 데이터 준비 및 라벨링 전략

### 4.1 데이터 수집 전략

```yaml
데이터_소스:
  위성_데이터:
    고해상도: [WorldView-3/4, GeoEye-1, QuickBird, IKONOS]
    중해상도: [Landsat-8/9, Sentinel-2, SPOT-6/7]
    하이퍼스펙트럴: [Hyperion, PRISMA, EnMAP]
    레이더: [Sentinel-1, COSMO-SkyMed, TerraSAR-X]
  
  보조_데이터:
    해양_조건: [파고, 바람, 해류, 조류]
    기상_데이터: [구름량, 가시거리, 강수량]
    환경_변수: [수온, 염분, 클로로필]
    지상_관측: [부이_데이터, 선박_관측, 항공_조사]

데이터_품질_기준:
  구름_덮개: <20%
  태양_고도각: >30도
  대기_가시도: >10km
  파고: <3m (정확한 탐지를 위해)
  공간_해상도: <10m (소형 폐기물 탐지)
```

### 4.2 능동 학습 기반 라벨링

```python
class ActiveLearningLabeler:
    """능동 학습을 통한 효율적 라벨링"""
    
    def __init__(self, model, uncertainty_threshold=0.3):
        self.model = model
        self.uncertainty_threshold = uncertainty_threshold
        self.labeled_pool = []
        self.unlabeled_pool = []
        
    def select_samples_for_labeling(self, unlabeled_data, budget=100):
        """불확실성 기반 샘플 선택"""
        uncertainties = []
        
        for sample in unlabeled_data:
            # 모델 예측 및 불확실성 계산
            prediction = self.model.predict(sample)
            uncertainty = self.calculate_uncertainty(prediction)
            uncertainties.append(uncertainty)
        
        # 불확실성이 높은 순서로 정렬
        sorted_indices = np.argsort(uncertainties)[::-1]
        
        # 다양성을 고려한 선택
        selected_indices = self.diversity_sampling(
            sorted_indices[:budget*3], budget
        )
        
        return [unlabeled_data[i] for i in selected_indices]
    
    def calculate_uncertainty(self, prediction):
        """몬테카를로 드롭아웃을 통한 불확실성 계산"""
        predictions = []
        
        # 드롭아웃을 활성화한 여러 번의 예측
        for _ in range(10):
            pred = self.model.predict_with_dropout(sample)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        # 예측 분산을 불확실성으로 사용
        uncertainty = np.var(predictions, axis=0).mean()
        return uncertainty
    
    def diversity_sampling(self, candidate_indices, budget):
        """다양성을 고려한 샘플링"""
        selected = [candidate_indices[0]]  # 가장 불확실한 샘플 선택
        
        for _ in range(budget - 1):
            max_distance = -1
            best_candidate = None
            
            for candidate in candidate_indices:
                if candidate in selected:
                    continue
                
                # 선택된 샘플들과의 최소 거리 계산
                min_distance = min([
                    self.calculate_feature_distance(candidate, selected_idx)
                    for selected_idx in selected
                ])
                
                if min_distance > max_distance:
                    max_distance = min_distance
                    best_candidate = candidate
            
            if best_candidate is not None:
                selected.append(best_candidate)
        
        return selected
```

### 4.3 약한 지도학습 및 자동 라벨링

```python
class WeakSupervisionLabeler:
    """약한 지도학습을 통한 대규모 라벨링"""
    
    def __init__(self):
        self.labeling_functions = [
            self.spectral_signature_lf,
            self.size_constraint_lf,
            self.location_prior_lf,
            self.temporal_consistency_lf,
            self.context_based_lf
        ]
    
    def spectral_signature_lf(self, image, threshold=0.7):
        """스펙트럴 서명 기반 라벨링 함수"""
        plastic_index = self.calculate_plastic_index(image)
        oil_index = self.calculate_oil_index(image)
        
        labels = np.zeros(image.shape[:2])
        labels[plastic_index > threshold] = 1  # 플라스틱
        labels[oil_index > threshold] = 2      # 오일
        
        return labels
    
    def size_constraint_lf(self, detected_objects):
        """크기 제약 기반 필터링"""
        valid_labels = []
        
        for obj in detected_objects:
            area = obj['area']
            aspect_ratio = obj['width'] / obj['height']
            
            # 크기 및 형태 기반 분류
            if 10 < area < 1000 and 0.5 < aspect_ratio < 2.0:
                valid_labels.append(obj['label'])
            else:
                valid_labels.append(0)  # 배경
        
        return valid_labels
    
    def temporal_consistency_lf(self, time_series_data):
        """시간적 일관성 검사"""
        consistent_labels = []
        
        for t in range(1, len(time_series_data)):
            current_objects = time_series_data[t]
            previous_objects = time_series_data[t-1]
            
            # 객체 추적을 통한 일관성 검사
            tracked_objects = self.track_objects(previous_objects, current_objects)
            
            for obj in tracked_objects:
                if obj['consistency_score'] > 0.8:
                    consistent_labels.append(obj['label'])
                else:
                    consistent_labels.append(-1)  # 불확실
        
        return consistent_labels
    
    def generate_probabilistic_labels(self, image):
        """여러 라벨링 함수의 결과를 결합"""
        lf_outputs = []
        
        for lf in self.labeling_functions:
            output = lf(image)
            lf_outputs.append(output)
        
        # Snorkel 방식의 라벨 결합
        final_labels = self.combine_weak_labels(lf_outputs)
        return final_labels
```

### 4.4 합성 데이터 생성

```python
class SyntheticDataGenerator:
    """합성 해상 폐기물 데이터 생성기"""
    
    def __init__(self):
        self.background_generator = OceanBackgroundGenerator()
        self.debris_renderer = DebrisRenderer()
        self.atmospheric_effects = AtmosphericEffectsSimulator()
    
    def generate_synthetic_scene(self, scene_params):
        """합성 해상 장면 생성"""
        # 1. 배경 생성 (바다 표면)
        background = self.background_generator.generate_ocean_surface(
            wave_height=scene_params['wave_height'],
            wind_speed=scene_params['wind_speed'],
            sun_angle=scene_params['sun_angle']
        )
        
        # 2. 폐기물 객체 배치
        debris_objects = self.debris_renderer.place_debris(
            background,
            debris_types=scene_params['debris_types'],
            density=scene_params['debris_density']
        )
        
        # 3. 대기 효과 적용
        final_image = self.atmospheric_effects.apply_effects(
            debris_objects,
            visibility=scene_params['visibility'],
            aerosol_type=scene_params['aerosol_type']
        )
        
        # 4. 센서 특성 시뮬레이션
        sensor_image = self.simulate_sensor_response(
            final_image,
            sensor_type=scene_params['sensor_type']
        )
        
        return sensor_image, self.generate_ground_truth(debris_objects)
    
    def augment_with_domain_adaptation(self, synthetic_data, real_data):
        """도메인 적응을 통한 합성 데이터 개선"""
        # CycleGAN 또는 UNIT을 사용한 도메인 변환
        domain_adapted_data = self.domain_adapter.transform(
            synthetic_data, 
            target_domain=real_data
        )
        
        return domain_adapted_data
```

---

## 5. 모델 성능 평가 지표

### 5.1 탐지 성능 지표

```python
class PerformanceMetrics:
    """해상 폐기물 탐지 성능 평가 지표"""
    
    def __init__(self):
        self.metrics = {
            'detection': DetectionMetrics(),
            'segmentation': SegmentationMetrics(),
            'classification': ClassificationMetrics(),
            'temporal': TemporalMetrics()
        }
    
    def calculate_detection_metrics(self, predictions, ground_truth, iou_threshold=0.5):
        """객체 탐지 성능 지표"""
        tp, fp, fn = self.calculate_detection_statistics(predictions, ground_truth, iou_threshold)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        # mAP 계산
        map_score = self.calculate_map(predictions, ground_truth)
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'mAP': map_score,
            'mAP@0.5': self.calculate_map(predictions, ground_truth, iou_threshold=0.5),
            'mAP@0.75': self.calculate_map(predictions, ground_truth, iou_threshold=0.75)
        }
    
    def calculate_segmentation_metrics(self, pred_mask, gt_mask):
        """세맨틱 세그멘테이션 성능 지표"""
        # 픽셀 단위 정확도
        pixel_accuracy = np.sum(pred_mask == gt_mask) / pred_mask.size
        
        # 클래스별 IoU
        class_ious = []
        for class_id in np.unique(gt_mask):
            pred_class = (pred_mask == class_id)
            gt_class = (gt_mask == class_id)
            
            intersection = np.sum(pred_class & gt_class)
            union = np.sum(pred_class | gt_class)
            
            iou = intersection / union if union > 0 else 0
            class_ious.append(iou)
        
        mean_iou = np.mean(class_ious)
        
        # Dice 계수
        dice_scores = []
        for class_id in np.unique(gt_mask):
            pred_class = (pred_mask == class_id)
            gt_class = (gt_mask == class_id)
            
            intersection = np.sum(pred_class & gt_class)
            dice = 2 * intersection / (np.sum(pred_class) + np.sum(gt_class))
            dice_scores.append(dice)
        
        mean_dice = np.mean(dice_scores)
        
        return {
            'pixel_accuracy': pixel_accuracy,
            'mean_iou': mean_iou,
            'class_ious': class_ious,
            'mean_dice': mean_dice,
            'dice_scores': dice_scores
        }

class EnvironmentalRobustnessMetrics:
    """환경 조건에 대한 강건성 평가"""
    
    def evaluate_robustness(self, model, test_data):
        """다양한 환경 조건에서의 성능 평가"""
        robustness_results = {}
        
        # 날씨 조건별 성능
        weather_conditions = ['clear', 'cloudy', 'hazy', 'stormy']
        for condition in weather_conditions:
            condition_data = test_data.filter_by_weather(condition)
            performance = self.evaluate_model(model, condition_data)
            robustness_results[f'weather_{condition}'] = performance
        
        # 파고 조건별 성능
        wave_heights = ['calm', 'moderate', 'rough']
        for wave_condition in wave_heights:
            wave_data = test_data.filter_by_wave_height(wave_condition)
            performance = self.evaluate_model(model, wave_data)
            robustness_results[f'wave_{wave_condition}'] = performance
        
        # 태양 각도별 성능
        sun_angles = ['low', 'medium', 'high']
        for angle in sun_angles:
            angle_data = test_data.filter_by_sun_angle(angle)
            performance = self.evaluate_model(model, angle_data)
            robustness_results[f'sun_angle_{angle}'] = performance
        
        # 전체 강건성 점수 계산
        robustness_score = self.calculate_robustness_score(robustness_results)
        
        return robustness_results, robustness_score
    
    def calculate_robustness_score(self, results):
        """환경 조건 간 성능 일관성 점수"""
        all_scores = []
        for condition, metrics in results.items():
            all_scores.append(metrics['f1_score'])
        
        # 표준편차가 낮을수록 강건함
        mean_score = np.mean(all_scores)
        std_score = np.std(all_scores)
        
        robustness_score = mean_score * (1 - std_score)
        return robustness_score
```

### 5.2 실시간 성능 지표

```python
class RealTimePerformanceMetrics:
    """실시간 처리 성능 지표"""
    
    def __init__(self):
        self.latency_tracker = LatencyTracker()
        self.throughput_tracker = ThroughputTracker()
        self.resource_monitor = ResourceMonitor()
    
    def measure_inference_time(self, model, input_data):
        """추론 시간 측정"""
        times = []
        
        # GPU 워밍업
        for _ in range(10):
            _ = model.predict(input_data[0])
        
        # 실제 측정
        for sample in input_data:
            start_time = time.time()
            prediction = model.predict(sample)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        return {
            'mean_latency': np.mean(times),
            'std_latency': np.std(times),
            'p95_latency': np.percentile(times, 95),
            'p99_latency': np.percentile(times, 99),
            'fps': 1.0 / np.mean(times)
        }
    
    def measure_throughput(self, model, batch_sizes=[1, 4, 8, 16]):
        """배치 크기별 처리량 측정"""
        throughput_results = {}
        
        for batch_size in batch_sizes:
            batch_data = self.create_batch_data(batch_size)
            
            start_time = time.time()
            predictions = model.predict_batch(batch_data)
            end_time = time.time()
            
            total_time = end_time - start_time
            throughput = batch_size / total_time
            
            throughput_results[batch_size] = {
                'throughput': throughput,
                'latency_per_sample': total_time / batch_size
            }
        
        return throughput_results
    
    def monitor_resource_usage(self, model, duration=300):
        """리소스 사용량 모니터링"""
        import psutil
        import GPUtil
        
        gpu_usage = []
        cpu_usage = []
        memory_usage = []
        
        start_time = time.time()
        
        while time.time() - start_time < duration:
            # GPU 사용률
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu_usage.append(gpus[0].load * 100)
            
            # CPU 사용률
            cpu_usage.append(psutil.cpu_percent())
            
            # 메모리 사용률
            memory_usage.append(psutil.virtual_memory().percent)
            
            time.sleep(1)
        
        return {
            'gpu_usage': {
                'mean': np.mean(gpu_usage),
                'max': np.max(gpu_usage),
                'std': np.std(gpu_usage)
            },
            'cpu_usage': {
                'mean': np.mean(cpu_usage),
                'max': np.max(cpu_usage),
                'std': np.std(cpu_usage)
            },
            'memory_usage': {
                'mean': np.mean(memory_usage),
                'max': np.max(memory_usage),
                'std': np.std(memory_usage)
            }
        }
```

---

## 6. Edge AI 및 온보드 처리

### 6.1 모델 경량화 기법

```python
class ModelOptimization:
    """모델 경량화 및 최적화"""
    
    def __init__(self):
        self.quantization = ModelQuantization()
        self.pruning = ModelPruning()
        self.distillation = KnowledgeDistillation()
        self.compression = ModelCompression()
    
    def apply_quantization(self, model, calibration_data):
        """양자화를 통한 모델 크기 및 연산량 감소"""
        # INT8 양자화
        quantized_model = torch.quantization.quantize_dynamic(
            model, 
            {torch.nn.Linear, torch.nn.Conv2d}, 
            dtype=torch.qint8
        )
        
        # 정적 양자화를 위한 캘리브레이션
        quantized_model.qconfig = torch.quantization.get_default_qconfig('fbgemm')
        torch.quantization.prepare(quantized_model, inplace=True)
        
        # 캘리브레이션 데이터로 forward pass
        with torch.no_grad():
            for data in calibration_data:
                quantized_model(data)
        
        # 양자화 완료
        torch.quantization.convert(quantized_model, inplace=True)
        
        return quantized_model
    
    def apply_pruning(self, model, sparsity=0.3):
        """가지치기를 통한 모델 압축"""
        import torch.nn.utils.prune as prune
        
        # 전역 구조화 가지치기
        parameters_to_prune = []
        for module in model.modules():
            if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear)):
                parameters_to_prune.append((module, 'weight'))
        
        prune.global_unstructured(
            parameters_to_prune,
            pruning_method=prune.L1Unstructured,
            amount=sparsity,
        )
        
        # 가지치기 적용
        for module, param in parameters_to_prune:
            prune.remove(module, param)
        
        return model
    
    def knowledge_distillation(self, teacher_model, student_model, train_loader):
        """지식 증류를 통한 경량 모델 학습"""
        criterion = DistillationLoss(temperature=4.0, alpha=0.7)
        optimizer = torch.optim.Adam(student_model.parameters(), lr=0.001)
        
        teacher_model.eval()
        student_model.train()
        
        for epoch in range(100):
            total_loss = 0
            
            for batch_idx, (data, target) in enumerate(train_loader):
                optimizer.zero_grad()
                
                # Teacher와 Student 예측
                with torch.no_grad():
                    teacher_outputs = teacher_model(data)
                
                student_outputs = student_model(data)
                
                # 증류 손실 계산
                loss = criterion(student_outputs, teacher_outputs, target)
                
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            print(f'Epoch {epoch}: Loss = {total_loss/len(train_loader)}')
        
        return student_model

class DistillationLoss(nn.Module):
    """지식 증류 손실 함수"""
    
    def __init__(self, temperature=3.0, alpha=0.7):
        super().__init__()
        self.temperature = temperature
        self.alpha = alpha
        self.kl_div = nn.KLDivLoss(reduction='batchmean')
        self.ce_loss = nn.CrossEntropyLoss()
    
    def forward(self, student_outputs, teacher_outputs, targets):
        # 소프트 타겟 손실
        soft_targets = F.softmax(teacher_outputs / self.temperature, dim=1)
        soft_student = F.log_softmax(student_outputs / self.temperature, dim=1)
        
        soft_loss = self.kl_div(soft_student, soft_targets) * (self.temperature ** 2)
        
        # 하드 타겟 손실
        hard_loss = self.ce_loss(student_outputs, targets)
        
        # 가중 결합
        total_loss = self.alpha * soft_loss + (1 - self.alpha) * hard_loss
        
        return total_loss
```

### 6.2 하드웨어 가속 최적화

```python
class HardwareOptimization:
    """하드웨어별 최적화"""
    
    def __init__(self):
        self.optimization_strategies = {
            'gpu': self.optimize_for_gpu,
            'cpu': self.optimize_for_cpu,
            'edge_tpu': self.optimize_for_edge_tpu,
            'fpga': self.optimize_for_fpga
        }
    
    def optimize_for_gpu(self, model):
        """GPU 최적화"""
        # TensorRT 최적화
        import torch_tensorrt
        
        # 모델을 TensorRT로 컴파일
        trt_model = torch_tensorrt.compile(
            model,
            inputs=[torch_tensorrt.Input((1, 8, 256, 256))],
            enabled_precisions={torch.float, torch.half},
            workspace_size=1 << 22
        )
        
        return trt_model
    
    def optimize_for_cpu(self, model):
        """CPU 최적화"""
        # Intel OpenVINO 최적화
        # ONNX 변환 후 OpenVINO 모델 최적화
        
        # PyTorch JIT 컴파일
        model.eval()
        traced_model = torch.jit.trace(model, torch.randn(1, 8, 256, 256))
        optimized_model = torch.jit.optimize_for_inference(traced_model)
        
        return optimized_model
    
    def optimize_for_edge_tpu(self, model):
        """Edge TPU 최적화"""
        # TensorFlow Lite 변환
        import tensorflow as tf
        
        # 양자화 인식 훈련
        converter = tf.lite.TFLiteConverter.from_saved_model(model_path)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        converter.representative_dataset = self.representative_dataset_gen
        converter.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
        converter.inference_input_type = tf.int8
        converter.inference_output_type = tf.int8
        
        tflite_model = converter.convert()
        
        # Edge TPU 컴파일
        edgetpu_model = self.compile_for_edgetpu(tflite_model)
        
        return edgetpu_model
    
    def create_mobile_pipeline(self, model, target_device='cpu'):
        """모바일 환경용 추론 파이프라인"""
        # 최적화된 모델 로드
        optimized_model = self.optimization_strategies[target_device](model)
        
        # 모바일 파이프라인 구성
        pipeline = MobileInferencePipeline(
            model=optimized_model,
            preprocessing=self.get_mobile_preprocessing(),
            postprocessing=self.get_mobile_postprocessing()
        )
        
        return pipeline

class MobileInferencePipeline:
    """모바일 환경용 추론 파이프라인"""
    
    def __init__(self, model, preprocessing, postprocessing):
        self.model = model
        self.preprocessing = preprocessing
        self.postprocessing = postprocessing
        
        # 배치 처리 설정
        self.batch_size = 1  # 모바일에서는 단일 이미지 처리
        self.memory_optimization = True
    
    def predict(self, image):
        """단일 이미지 예측"""
        # 전처리
        processed_image = self.preprocessing(image)
        
        # 메모리 효율적 추론
        with torch.no_grad():
            if self.memory_optimization:
                # 그래디언트 계산 비활성화로 메모리 절약
                prediction = self.model(processed_image)
            else:
                prediction = self.model(processed_image)
        
        # 후처리
        result = self.postprocessing(prediction)
        
        return result
    
    def predict_streaming(self, image_stream):
        """스트리밍 이미지 처리"""
        for image in image_stream:
            yield self.predict(image)
```

### 6.3 온보드 추론 시스템

```python
class OnboardInferenceSystem:
    """위성 온보드 추론 시스템"""
    
    def __init__(self, model_config):
        self.model = self.load_optimized_model(model_config)
        self.preprocessing_pipeline = self.setup_preprocessing()
        self.result_buffer = ResultBuffer(max_size=1000)
        self.power_manager = PowerManager()
        
    def load_optimized_model(self, config):
        """최적화된 모델 로드"""
        if config['hardware'] == 'gpu':
            model = torch.jit.load(config['model_path'])
            model = model.cuda()
        elif config['hardware'] == 'cpu':
            model = torch.jit.load(config['model_path'])
            model = model.cpu()
        elif config['hardware'] == 'edge_tpu':
            model = self.load_tflite_model(config['model_path'])
        
        return model
    
    def real_time_inference(self, image_acquisition_system):
        """실시간 추론 처리"""
        while True:
            try:
                # 이미지 획득
                raw_image = image_acquisition_system.capture()
                
                # 전력 관리
                if self.power_manager.should_process(raw_image):
                    # 전처리
                    processed_image = self.preprocessing_pipeline(raw_image)
                    
                    # 추론
                    start_time = time.time()
                    result = self.model(processed_image)
                    inference_time = time.time() - start_time
                    
                    # 결과 처리
                    processed_result = self.postprocess_result(result, raw_image)
                    
                    # 결과 저장
                    self.result_buffer.add(processed_result)
                    
                    # 전력 소비 업데이트
                    self.power_manager.update_power_consumption(inference_time)
                    
                    # 우선순위가 높은 결과는 즉시 전송
                    if processed_result['priority'] == 'high':
                        self.transmit_result(processed_result)
                
                else:
                    # 전력 절약 모드 - 처리 건너뛰기
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"Inference error: {e}")
                continue
    
    def adaptive_processing(self, power_level):
        """전력 수준에 따른 적응형 처리"""
        if power_level > 0.8:
            # 고전력 모드 - 최대 성능
            self.model.set_precision('fp32')
            self.preprocessing_pipeline.set_quality('high')
            self.processing_interval = 1  # 초
            
        elif power_level > 0.5:
            # 중간 전력 모드 - 균형
            self.model.set_precision('fp16')
            self.preprocessing_pipeline.set_quality('medium')
            self.processing_interval = 5  # 초
            
        else:
            # 저전력 모드 - 절약
            self.model.set_precision('int8')
            self.preprocessing_pipeline.set_quality('low')
            self.processing_interval = 30  # 초

class PowerManager:
    """전력 관리 시스템"""
    
    def __init__(self, total_power_budget=100):  # 와트 단위
        self.total_budget = total_power_budget
        self.current_consumption = 0
        self.power_history = []
        
    def should_process(self, image):
        """전력 상황을 고려한 처리 여부 결정"""
        # 이미지 중요도 평가
        importance = self.evaluate_image_importance(image)
        
        # 전력 여유도 계산
        power_headroom = (self.total_budget - self.current_consumption) / self.total_budget
        
        # 임계값 기반 결정
        if importance > 0.8:  # 중요한 이미지는 항상 처리
            return True
        elif importance > 0.5 and power_headroom > 0.3:
            return True
        elif power_headroom > 0.7:  # 전력 여유가 충분할 때
            return True
        else:
            return False
    
    def evaluate_image_importance(self, image):
        """이미지 중요도 평가"""
        # 간단한 휴리스틱 기반 중요도 계산
        # 실제로는 더 정교한 평가 시스템 필요
        
        # 변화량 기반 중요도
        if hasattr(self, 'previous_image'):
            change_magnitude = np.mean(np.abs(image - self.previous_image))
            importance = min(change_magnitude / 0.1, 1.0)
        else:
            importance = 0.5
        
        self.previous_image = image
        return importance
```

---

## 7. 멀티스펙트럴/하이퍼스펙트럴 데이터 활용

### 7.1 스펙트럴 밴드 선택 및 최적화

```python
class SpectralBandOptimizer:
    """스펙트럴 밴드 선택 및 최적화"""
    
    def __init__(self):
        self.band_importance = BandImportanceAnalyzer()
        self.feature_selector = SpectralFeatureSelector()
        
    def optimize_band_selection(self, hyperspectral_data, target_labels):
        """최적 밴드 조합 선택"""
        
        # 1. 정보 이론 기반 밴드 중요도 분석
        mutual_info = self.calculate_mutual_information(hyperspectral_data, target_labels)
        
        # 2. 상관관계 분석으로 중복 밴드 제거
        correlation_matrix = self.calculate_band_correlation(hyperspectral_data)
        redundant_bands = self.find_redundant_bands(correlation_matrix, threshold=0.95)
        
        # 3. 유전 알고리즘 기반 최적화
        optimal_bands = self.genetic_algorithm_selection(
            hyperspectral_data, 
            target_labels,
            population_size=50,
            generations=100,
            target_band_count=10
        )
        
        return optimal_bands
    
    def calculate_mutual_information(self, spectral_data, labels):
        """각 밴드와 타겟 간의 상호정보량 계산"""
        from sklearn.feature_selection import mutual_info_classif
        
        n_bands = spectral_data.shape[-1]
        mi_scores = []
        
        for band_idx in range(n_bands):
            band_data = spectral_data[:, :, band_idx].flatten()
            labels_flat = labels.flatten()
            
            # 유효한 픽셀만 선택 (라벨이 있는 픽셀)
            valid_mask = labels_flat != 0
            
            if np.sum(valid_mask) > 100:  # 충분한 샘플이 있는 경우만
                mi_score = mutual_info_classif(
                    band_data[valid_mask].reshape(-1, 1),
                    labels_flat[valid_mask]
                )[0]
                mi_scores.append(mi_score)
            else:
                mi_scores.append(0)
        
        return np.array(mi_scores)
    
    def genetic_algorithm_selection(self, data, labels, population_size=50, 
                                   generations=100, target_band_count=10):
        """유전 알고리즘을 이용한 밴드 선택"""
        
        def fitness_function(band_indices):
            """밴드 조합의 적합도 평가"""
            selected_data = data[:, :, band_indices]
            
            # 간단한 분류기로 성능 평가
            classifier = RandomForestClassifier(n_estimators=10, random_state=42)
            
            # 학습 데이터 준비
            X, y = self.prepare_training_data(selected_data, labels)
            
            # 교차 검증 성능
            scores = cross_val_score(classifier, X, y, cv=3, scoring='f1_macro')
            return np.mean(scores)
        
        # 초기 개체군 생성
        population = []
        for _ in range(population_size):
            individual = np.random.choice(
                data.shape[-1], 
                size=target_band_count, 
                replace=False
            )
            population.append(individual)
        
        # 진화 과정
        for generation in range(generations):
            # 적합도 평가
            fitness_scores = [fitness_function(individual) for individual in population]
            
            # 선택, 교배, 변이
            new_population = []
            
            for _ in range(population_size):
                # 토너먼트 선택
                parent1 = self.tournament_selection(population, fitness_scores)
                parent2 = self.tournament_selection(population, fitness_scores)
                
                # 교배
                offspring = self.crossover(parent1, parent2)
                
                # 변이
                offspring = self.mutation(offspring, data.shape[-1])
                
                new_population.append(offspring)
            
            population = new_population
        
        # 최종 최적 개체 선택
        final_fitness = [fitness_function(individual) for individual in population]
        best_individual = population[np.argmax(final_fitness)]
        
        return best_individual

class SpectralIndicesCalculator:
    """스펙트럴 지수 계산기"""
    
    def __init__(self):
        self.indices = {
            'plastic_detection': self.calculate_plastic_indices,
            'oil_detection': self.calculate_oil_indices,
            'water_quality': self.calculate_water_indices,
            'vegetation': self.calculate_vegetation_indices
        }
    
    def calculate_plastic_indices(self, bands):
        """플라스틱 탐지용 스펙트럴 지수"""
        indices = {}
        
        # Normalized Difference Plastic Index (NDPI)
        if 'nir' in bands and 'red' in bands:
            indices['ndpi'] = (bands['nir'] - bands['red']) / (bands['nir'] + bands['red'])
        
        # Plastic Absorption Feature (PAF)
        if 'swir1' in bands and 'swir2' in bands:
            indices['paf'] = bands['swir1'] / bands['swir2']
        
        # Modified Plastic Index (MPI)
        if 'green' in bands and 'nir' in bands and 'swir1' in bands:
            indices['mpi'] = (bands['nir'] - bands['green']) / (bands['swir1'] - bands['green'])
        
        return indices
    
    def calculate_oil_indices(self, bands):
        """오일 탐지용 스펙트럴 지수"""
        indices = {}
        
        # Oil Index (OI)
        if 'swir1' in bands and 'swir2' in bands:
            indices['oi'] = bands['swir2'] / bands['swir1']
        
        # Hydrocarbon Index (HI)
        if 'band2100' in bands and 'band2300' in bands:  # 특정 파장 밴드
            indices['hi'] = bands['band2100'] / bands['band2300']
        
        # Normalized Oil Index (NOI)
        if 'nir' in bands and 'swir2' in bands:
            indices['noi'] = (bands['nir'] - bands['swir2']) / (bands['nir'] + bands['swir2'])
        
        return indices
    
    def calculate_advanced_spectral_features(self, hyperspectral_cube):
        """고급 스펙트럴 특징 추출"""
        h, w, n_bands = hyperspectral_cube.shape
        features = {}
        
        # 스펙트럴 각도 매퍼 (SAM)
        reference_spectra = self.get_reference_spectra()
        sam_features = self.calculate_sam(hyperspectral_cube, reference_spectra)
        features['sam'] = sam_features
        
        # 스펙트럴 정보 발산 (SID)
        sid_features = self.calculate_sid(hyperspectral_cube, reference_spectra)
        features['sid'] = sid_features
        
        # 연속체 제거 (Continuum Removal)
        cr_features = self.continuum_removal(hyperspectral_cube)
        features['continuum_removed'] = cr_features
        
        # 1차 및 2차 미분
        first_derivative = np.gradient(hyperspectral_cube, axis=2)
        second_derivative = np.gradient(first_derivative, axis=2)
        features['first_derivative'] = first_derivative
        features['second_derivative'] = second_derivative
        
        # 스펙트럴 곡률
        curvature = self.calculate_spectral_curvature(hyperspectral_cube)
        features['curvature'] = curvature
        
        return features
    
    def calculate_sam(self, hyperspectral_cube, reference_spectra):
        """스펙트럴 각도 매퍼 계산"""
        h, w, n_bands = hyperspectral_cube.shape
        sam_maps = {}
        
        for material, ref_spectrum in reference_spectra.items():
            sam_map = np.zeros((h, w))
            
            for i in range(h):
                for j in range(w):
                    pixel_spectrum = hyperspectral_cube[i, j, :]
                    
                    # 코사인 유사도 계산
                    cos_angle = np.dot(pixel_spectrum, ref_spectrum) / \
                               (np.linalg.norm(pixel_spectrum) * np.linalg.norm(ref_spectrum))
                    
                    # 각도 계산 (라디안)
                    angle = np.arccos(np.clip(cos_angle, -1, 1))
                    sam_map[i, j] = angle
            
            sam_maps[material] = sam_map
        
        return sam_maps
```

### 7.2 딥러닝 기반 하이퍼스펙트럴 분석

```python
class HyperspectralCNN(nn.Module):
    """하이퍼스펙트럴 데이터를 위한 3D CNN"""
    
    def __init__(self, n_bands, n_classes, spatial_size=7):
        super(HyperspectralCNN, self).__init__()
        
        # 3D 합성곱층 (스펙트럴-공간 특징 학습)
        self.conv3d_1 = nn.Conv3d(1, 8, kernel_size=(3, 3, 7), padding=(1, 1, 0))
        self.conv3d_2 = nn.Conv3d(8, 16, kernel_size=(3, 3, 5), padding=(1, 1, 0))
        self.conv3d_3 = nn.Conv3d(16, 32, kernel_size=(3, 3, 3), padding=(1, 1, 0))
        
        # 2D 합성곱층 (공간 특징 학습)
        self.conv2d_1 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.conv2d_2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        
        # 어텐션 메커니즘
        self.spectral_attention = SpectralAttention(n_bands)
        self.spatial_attention = SpatialAttention()
        
        # 분류층
        self.global_pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(128, n_classes)
        
        # 정규화
        self.batch_norm_3d = nn.BatchNorm3d(32)
        self.batch_norm_2d = nn.BatchNorm2d(128)
        self.dropout = nn.Dropout(0.5)
    
    def forward(self, x):
        # 입력: [B, H, W, Bands] -> [B, 1, H, W, Bands]
        x = x.permute(0, 3, 1, 2).unsqueeze(1)
        
        # 3D 합성곱
        x = F.relu(self.conv3d_1(x))
        x = F.relu(self.conv3d_2(x))
        x = F.relu(self.conv3d_3(x))
        x = self.batch_norm_3d(x)
        
        # 3D -> 2D 변환
        x = x.squeeze(4)  # [B, 32, H, W]
        
        # 스펙트럴 어텐션 적용
        x = self.spectral_attention(x)
        
        # 2D 합성곱
        x = F.relu(self.conv2d_1(x))
        x = F.relu(self.conv2d_2(x))
        x = self.batch_norm_2d(x)
        
        # 공간 어텐션 적용
        x = self.spatial_attention(x)
        
        # 글로벌 풀링 및 분류
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)
        x = self.dropout(x)
        x = self.classifier(x)
        
        return x

class SpectralAttention(nn.Module):
    """스펙트럴 채널 어텐션"""
    
    def __init__(self, n_bands):
        super(SpectralAttention, self).__init__()
        self.n_bands = n_bands
        
        # 채널별 가중치 학습
        self.channel_attention = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(n_bands, n_bands // 4, 1),
            nn.ReLU(),
            nn.Conv2d(n_bands // 4, n_bands, 1),
            nn.Sigmoid()
        )
    
    def forward(self, x):
        # 채널별 가중치 계산
        weights = self.channel_attention(x)
        
        # 가중치 적용
        return x * weights

class HyperspectralTransformer(nn.Module):
    """하이퍼스펙트럴 데이터를 위한 Transformer"""
    
    def __init__(self, n_bands, n_classes, patch_size=4):
        super(HyperspectralTransformer, self).__init__()
        
        self.patch_size = patch_size
        self.n_bands = n_bands
        
        # 패치 임베딩
        self.patch_embedding = nn.Linear(patch_size * patch_size * n_bands, 512)
        
        # 스펙트럴 임베딩
        self.spectral_embedding = nn.Linear(n_bands, 512)
        
        # 위치 임베딩
        self.pos_embedding = nn.Parameter(torch.randn(1, 65, 512))  # 64 패치 + 1 CLS
        
        # CLS 토큰
        self.cls_token = nn.Parameter(torch.randn(1, 1, 512))
        
        # Transformer 인코더
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=512,
            nhead=8,
            dim_feedforward=2048,
            dropout=0.1
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=6)
        
        # 분류 헤드
        self.classifier = nn.Linear(512, n_classes)
        
    def forward(self, x):
        b, h, w, c = x.shape
        
        # 패치 추출
        patches = self.extract_patches(x)  # [B, num_patches, patch_dim]
        
        # 패치 임베딩
        patch_embeddings = self.patch_embedding(patches)
        
        # CLS 토큰 추가
        cls_tokens = self.cls_token.expand(b, -1, -1)
        embeddings = torch.cat([cls_tokens, patch_embeddings], dim=1)
        
        # 위치 임베딩 추가
        embeddings += self.pos_embedding
        
        # Transformer 적용
        encoded = self.transformer(embeddings)
        
        # CLS 토큰으로 분류
        cls_output = self.classifier(encoded[:, 0])
        
        return cls_output
    
    def extract_patches(self, x):
        """이미지를 패치로 분할"""
        b, h, w, c = x.shape
        patch_h = h // self.patch_size
        patch_w = w // self.patch_size
        
        patches = x.unfold(1, self.patch_size, self.patch_size).unfold(2, self.patch_size, self.patch_size)
        patches = patches.contiguous().view(b, patch_h * patch_w, -1)
        
        return patches
```

---

## 8. 시계열 분석 기반 폐기물 이동 예측

### 8.1 시공간 추적 알고리즘

```python
class SpatioTemporalTracker:
    """시공간 폐기물 추적 시스템"""
    
    def __init__(self):
        self.tracker = MultiObjectTracker()
        self.motion_model = OceanCurrentMotionModel()
        self.kalman_filters = {}
        self.trajectory_predictor = TrajectoryPredictor()
        
    def track_debris_over_time(self, detection_sequence):
        """시간에 따른 폐기물 추적"""
        tracked_objects = []
        
        for timestamp, detections in detection_sequence:
            # 기존 추적 객체와 새 탐지 결과 매칭
            matched_objects = self.associate_detections(detections, tracked_objects)
            
            # 각 객체에 대해 칼만 필터 업데이트
            for obj_id, detection in matched_objects.items():
                if obj_id not in self.kalman_filters:
                    # 새 객체 - 칼만 필터 초기화
                    self.kalman_filters[obj_id] = self.initialize_kalman_filter(detection)
                else:
                    # 기존 객체 - 상태 업데이트
                    self.kalman_filters[obj_id].update(detection)
                
                # 예측된 다음 위치 계산
                predicted_state = self.kalman_filters[obj_id].predict()
                
                # 해류 정보를 이용한 모션 모델 적용
                ocean_current = self.get_ocean_current(detection['location'], timestamp)
                corrected_prediction = self.motion_model.apply_ocean_dynamics(
                    predicted_state, ocean_current
                )
                
                tracked_objects.append({
                    'id': obj_id,
                    'timestamp': timestamp,
                    'current_state': detection,
                    'predicted_state': corrected_prediction,
                    'trajectory': self.get_trajectory(obj_id)
                })
        
        return tracked_objects
    
    def associate_detections(self, detections, tracked_objects):
        """헝가리안 알고리즘을 이용한 객체 연관"""
        if not tracked_objects:
            # 첫 프레임 - 모든 탐지를 새 객체로 등록
            return {i: det for i, det in enumerate(detections)}
        
        # 비용 행렬 계산
        cost_matrix = self.calculate_cost_matrix(detections, tracked_objects)
        
        # 헝가리안 알고리즘 적용
        from scipy.optimize import linear_sum_assignment
        row_indices, col_indices = linear_sum_assignment(cost_matrix)
        
        matched_objects = {}
        for det_idx, obj_idx in zip(row_indices, col_indices):
            if cost_matrix[det_idx, obj_idx] < self.association_threshold:
                matched_objects[tracked_objects[obj_idx]['id']] = detections[det_idx]
        
        # 매칭되지 않은 탐지를 새 객체로 추가
        unmatched_detections = set(range(len(detections))) - set(row_indices)
        new_obj_id = max([obj['id'] for obj in tracked_objects]) + 1 if tracked_objects else 0
        
        for det_idx in unmatched_detections:
            matched_objects[new_obj_id] = detections[det_idx]
            new_obj_id += 1
        
        return matched_objects
    
    def calculate_cost_matrix(self, detections, tracked_objects):
        """객체 연관을 위한 비용 행렬 계산"""
        n_detections = len(detections)
        n_tracked = len(tracked_objects)
        cost_matrix = np.zeros((n_detections, n_tracked))
        
        for i, detection in enumerate(detections):
            for j, tracked_obj in enumerate(tracked_objects):
                # 공간적 거리
                spatial_distance = self.calculate_spatial_distance(
                    detection['location'], 
                    tracked_obj['predicted_state']['location']
                )
                
                # 특징 유사도
                feature_similarity = self.calculate_feature_similarity(
                    detection['features'], 
                    tracked_obj['current_state']['features']
                )
                
                # 종합 비용 계산
                cost_matrix[i, j] = spatial_distance * 0.7 + (1 - feature_similarity) * 0.3
        
        return cost_matrix

class OceanCurrentMotionModel:
    """해류를 고려한 모션 모델"""
    
    def __init__(self):
        self.current_data_source = OceanCurrentDataSource()
        self.wind_data_source = WindDataSource()
        
    def apply_ocean_dynamics(self, predicted_state, environmental_data):
        """해양 역학을 적용한 상태 보정"""
        current_velocity = environmental_data['ocean_current']
        wind_velocity = environmental_data['wind']
        
        # 폐기물 유형에 따른 드리프트 계수
        drift_coefficients = {
            'plastic_bottle': {'current': 0.8, 'wind': 0.1},
            'plastic_bag': {'current': 0.6, 'wind': 0.3},
            'oil_spill': {'current': 0.9, 'wind': 0.05},
            'wooden_debris': {'current': 0.7, 'wind': 0.15}
        }
        
        debris_type = predicted_state['debris_type']
        coeffs = drift_coefficients.get(debris_type, {'current': 0.75, 'wind': 0.15})
        
        # 드리프트 속도 계산
        drift_velocity = (
            current_velocity * coeffs['current'] + 
            wind_velocity * coeffs['wind']
        )
        
        # 예측 위치 보정
        time_step = predicted_state['time_step']  # 시간 간격 (시간 단위)
        
        corrected_location = predicted_state['location'] + drift_velocity * time_step
        
        # 확률적 노이즈 추가 (해류의 불확실성)
        noise_std = 0.01  # 위치 노이즈 표준편차 (도 단위)
        location_noise = np.random.normal(0, noise_std, 2)
        corrected_location += location_noise
        
        corrected_state = predicted_state.copy()
        corrected_state['location'] = corrected_location
        corrected_state['velocity'] = drift_velocity
        
        return corrected_state

class TrajectoryPredictor:
    """궤적 예측 시스템"""
    
    def __init__(self):
        self.lstm_model = self.build_trajectory_lstm()
        self.physics_model = PhysicsBasedPredictor()
        self.ensemble_weights = {'lstm': 0.6, 'physics': 0.4}
        
    def build_trajectory_lstm(self):
        """LSTM 기반 궤적 예측 모델"""
        model = nn.Sequential(
            nn.LSTM(
                input_size=6,  # lat, lon, velocity_x, velocity_y, current_x, current_y
                hidden_size=128,
                num_layers=2,
                batch_first=True,
                dropout=0.2
            ),
            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 2)  # 예측 위치 (lat, lon)
        )
        return model
    
    def predict_trajectory(self, trajectory_history, forecast_horizon=24):
        """미래 궤적 예측"""
        # LSTM 기반 예측
        lstm_prediction = self.lstm_predict(trajectory_history, forecast_horizon)
        
        # 물리 기반 예측
        physics_prediction = self.physics_model.predict(trajectory_history, forecast_horizon)
        
        # 앙상블 예측
        ensemble_prediction = (
            lstm_prediction * self.ensemble_weights['lstm'] +
            physics_prediction * self.ensemble_weights['physics']
        )
        
        # 불확실성 추정
        uncertainty = self.estimate_prediction_uncertainty(
            lstm_prediction, physics_prediction, trajectory_history
        )
        
        return {
            'predicted_trajectory': ensemble_prediction,
            'uncertainty_bounds': uncertainty,
            'confidence_intervals': self.calculate_confidence_intervals(
                ensemble_prediction, uncertainty
            )
        }
    
    def lstm_predict(self, trajectory_history, forecast_horizon):
        """LSTM을 이용한 궤적 예측"""
        # 시계열 데이터 준비
        sequence_length = 10  # 지난 10개 시점 사용
        
        if len(trajectory_history) < sequence_length:
            # 데이터가 부족한 경우 물리 모델만 사용
            return self.physics_model.predict(trajectory_history, forecast_horizon)
        
        # 입력 시퀀스 구성
        input_sequence = self.prepare_lstm_input(trajectory_history[-sequence_length:])
        
        predictions = []
        current_input = input_sequence
        
        # 순차적 예측
        for _ in range(forecast_horizon):
            with torch.no_grad():
                output = self.lstm_model(current_input.unsqueeze(0))
                predictions.append(output.squeeze(0).numpy())
                
                # 다음 입력을 위해 시퀀스 업데이트
                current_input = self.update_sequence(current_input, output.squeeze(0))
        
        return np.array(predictions)
    
    def estimate_prediction_uncertainty(self, lstm_pred, physics_pred, history):
        """예측 불확실성 추정"""
        # 모델 간 불일치도
        model_disagreement = np.mean(np.abs(lstm_pred - physics_pred), axis=1)
        
        # 과거 예측 오차 기반 불확실성
        historical_errors = self.calculate_historical_errors(history)
        
        # 시간에 따른 불확실성 증가
        time_decay_factor = np.exp(np.arange(len(lstm_pred)) * 0.1)
        
        # 종합 불확실성
        uncertainty = (
            model_disagreement * 0.4 +
            historical_errors * 0.4 +
            time_decay_factor * 0.2
        )
        
        return uncertainty
```

### 8.2 시계열 딥러닝 모델

```python
class DebrisMovementLSTM(nn.Module):
    """폐기물 이동 예측을 위한 LSTM 모델"""
    
    def __init__(self, input_dim=10, hidden_dim=128, num_layers=3, output_dim=2):
        super(DebrisMovementLSTM, self).__init__()
        
        # 다층 LSTM
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.2,
            bidirectional=True
        )
        
        # 어텐션 메커니즘
        self.attention = TemporalAttention(hidden_dim * 2)
        
        # 출력층
        self.fc_layers = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, output_dim)
        )
        
        # 불확실성 추정을 위한 분산 예측층
        self.uncertainty_layer = nn.Linear(hidden_dim * 2, output_dim)
        
    def forward(self, x):
        # LSTM 처리
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # 어텐션 적용
        attended_output = self.attention(lstm_out)
        
        # 위치 예측
        position_pred = self.fc_layers(attended_output)
        
        # 불확실성 예측
        uncertainty_pred = torch.exp(self.uncertainty_layer(attended_output))
        
        return position_pred, uncertainty_pred

class TemporalAttention(nn.Module):
    """시간적 어텐션 메커니즘"""
    
    def __init__(self, hidden_dim):
        super(TemporalAttention, self).__init__()
        self.attention_layer = nn.Linear(hidden_dim, 1)
        self.softmax = nn.Softmax(dim=1)
        
    def forward(self, lstm_output):
        # 어텐션 스코어 계산
        attention_scores = self.attention_layer(lstm_output)
        attention_weights = self.softmax(attention_scores)
        
        # 가중 평균 계산
        attended_output = torch.sum(lstm_output * attention_weights, dim=1)
        
        return attended_output

class TransformerDebrisTracker(nn.Module):
    """Transformer 기반 폐기물 추적 모델"""
    
    def __init__(self, input_dim=10, d_model=256, nhead=8, num_layers=6):
        super(TransformerDebrisTracker, self).__init__()
        
        # 입력 임베딩
        self.input_embedding = nn.Linear(input_dim, d_model)
        
        # 위치 인코딩
        self.pos_encoder = PositionalEncoding(d_model)
        
        # Transformer 인코더
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=d_model * 4,
            dropout=0.1
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # 출력 헤드
        self.prediction_head = nn.Linear(d_model, 2)  # x, y 좌표
        self.velocity_head = nn.Linear(d_model, 2)    # vx, vy 속도
        self.confidence_head = nn.Linear(d_model, 1)  # 신뢰도
        
    def forward(self, x):
        # 입력 임베딩
        embedded = self.input_embedding(x)
        
        # 위치 인코딩 추가
        embedded = self.pos_encoder(embedded)
        
        # Transformer 인코더 적용
        encoded = self.transformer_encoder(embedded.transpose(0, 1))
        
        # 마지막 시점의 출력 사용
        final_output = encoded[-1]
        
        # 예측 결과
        position = self.prediction_head(final_output)
        velocity = self.velocity_head(final_output)
        confidence = torch.sigmoid(self.confidence_head(final_output))
        
        return {
            'position': position,
            'velocity': velocity,
            'confidence': confidence
        }

class PositionalEncoding(nn.Module):
    """Transformer용 위치 인코딩"""
    
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * 
                           (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        return x + self.pe[:x.size(0), :]
```

---

## 9. 해양 환경 특수성 대응 기술

### 9.1 파도 및 해면 반사 처리

```python
class WaveEffectCorrection:
    """파도 효과 보정 시스템"""
    
    def __init__(self):
        self.wave_detector = WavePatternDetector()
        self.reflection_corrector = SeaSurfaceReflectionCorrector()
        
    def detect_wave_patterns(self, image, metadata):
        """파도 패턴 탐지 및 분석"""
        # 해면 거칠기 분석
        surface_roughness = self.calculate_surface_roughness(image)
        
        # 파고 추정 (SAR 데이터 활용 시)
        if metadata.get('sensor_type') == 'SAR':
            wave_height = self.estimate_wave_height_sar(image)
        else:
            wave_height = self.estimate_wave_height_optical(image, metadata)
        
        # 파도 방향 분석
        wave_direction = self.analyze_wave_direction(image)
        
        return {
            'surface_roughness': surface_roughness,
            'wave_height': wave_height,
            'wave_direction': wave_direction,
            'wave_period': self.estimate_wave_period(image)
        }
    
    def correct_wave_effects(self, image, wave_params):
        """파도 효과 보정"""
        corrected_image = image.copy()
        
        # 1. 기하학적 왜곡 보정
        corrected_image = self.correct_geometric_distortion(
            corrected_image, wave_params['wave_height']
        )
        
        # 2. 반사 효과 제거
        corrected_image = self.remove_wave_reflection(
            corrected_image, wave_params
        )
        
        # 3. 스펙클 노이즈 제거 (SAR의 경우)
        if self.is_sar_image(image):
            corrected_image = self.remove_speckle_noise(corrected_image)
        
        return corrected_image
    
    def calculate_surface_roughness(self, image):
        """해면 거칠기 계산"""
        # 텍스처 분석을 통한 거칠기 추정
        gray_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        
        # GLCM (Gray Level Co-occurrence Matrix) 기반 텍스처 특징
        glcm = graycomatrix(gray_image, [1, 2, 3], [0, 45, 90, 135])
        
        # 텍스처 특징 계산
        contrast = graycoprops(glcm, 'contrast').mean()
        homogeneity = graycoprops(glcm, 'homogeneity').mean()
        energy = graycoprops(glcm, 'energy').mean()
        
        # 거칠기 지수 계산
        roughness_index = contrast / (homogeneity + energy)
        
        return roughness_index
    
    def estimate_wave_height_optical(self, image, metadata):
        """광학 이미지에서 파고 추정"""
        # 태양 각도 및 센서 각도 정보 활용
        sun_angle = metadata.get('sun_elevation_angle', 45)
        view_angle = metadata.get('view_angle', 0)
        
        # 그림자 길이 분석
        shadow_map = self.detect_wave_shadows(image, sun_angle)
        
        # 그림자 길이로부터 파고 계산
        shadow_lengths = self.measure_shadow_lengths(shadow_map)
        wave_heights = shadow_lengths / np.tan(np.radians(sun_angle))
        
        return np.mean(wave_heights)
    
    def remove_wave_reflection(self, image, wave_params):
        """파도로 인한 반사 효과 제거"""
        # 파도 기울기 추정
        wave_slopes = self.estimate_wave_slopes(wave_params)
        
        # 기울기별 반사 보정 계수 계산
        correction_factors = self.calculate_reflection_correction(wave_slopes)
        
        # 픽셀별 보정 적용
        corrected_image = image * correction_factors[:, :, np.newaxis]
        
        return np.clip(corrected_image, 0, 1)

class SeaSurfaceReflectionCorrector:
    """해수면 반사 보정기"""
    
    def __init__(self):
        self.fresnel_calculator = FresnelReflectionCalculator()
        
    def correct_fresnel_reflection(self, image, view_angle, refractive_index=1.33):
        """프레넬 반사 보정"""
        # 프레넬 반사율 계산
        fresnel_reflectance = self.fresnel_calculator.calculate_reflectance(
            view_angle, refractive_index
        )
        
        # 반사 성분 추정 및 제거
        reflected_component = image * fresnel_reflectance
        corrected_image = image - reflected_component
        
        return np.clip(corrected_image, 0, 1)
    
    def adaptive_reflection_removal(self, image, wind_speed):
        """바람 속도에 따른 적응적 반사 제거"""
        # 바람 속도에 따른 해면 상태 모델링
        if wind_speed < 3:  # 평온한 바다
            reflection_model = self.calm_sea_reflection_model
        elif wind_speed < 7:  # 보통 바다
            reflection_model = self.moderate_sea_reflection_model
        else:  # 거친 바다
            reflection_model = self.rough_sea_reflection_model
        
        # 반사 모델 적용
        corrected_image = reflection_model.apply_correction(image)
        
        return corrected_image
```

### 9.2 구름 및 대기 조건 처리

```python
class AtmosphericConditionHandler:
    """대기 조건 처리 시스템"""
    
    def __init__(self):
        self.cloud_processor = CloudProcessor()
        self.haze_remover = HazeRemover()
        self.atmospheric_corrector = AtmosphericCorrector()
        
    def assess_atmospheric_conditions(self, image, metadata):
        """대기 조건 평가"""
        conditions = {}
        
        # 구름 덮개율 계산
        cloud_mask = self.cloud_processor.detect_clouds(image)
        conditions['cloud_coverage'] = np.sum(cloud_mask) / cloud_mask.size
        
        # 대기 가시도 추정
        visibility = self.estimate_visibility(image)
        conditions['visibility'] = visibility
        
        # 에어로졸 농도 추정
        aerosol_optical_depth = self.estimate_aerosol_optical_depth(image, metadata)
        conditions['aerosol_optical_depth'] = aerosol_optical_depth
        
        # 수증기 함량 추정
        water_vapor = self.estimate_water_vapor(image, metadata)
        conditions['water_vapor'] = water_vapor
        
        return conditions
    
    def adaptive_atmospheric_correction(self, image, conditions):
        """적응적 대기 보정"""
        corrected_image = image.copy()
        
        # 구름 조건에 따른 처리
        if conditions['cloud_coverage'] > 0.7:
            # 구름이 많은 경우 - 구름 제거 시도
            corrected_image = self.cloud_processor.remove_thin_clouds(corrected_image)
            
        elif conditions['cloud_coverage'] > 0.3:
            # 부분적 구름 - 구름 그림자 보정
            corrected_image = self.cloud_processor.correct_cloud_shadows(corrected_image)
        
        # 대기 가시도에 따른 처리
        if conditions['visibility'] < 10:  # km
            # 낮은 가시도 - 헤이즈 제거
            corrected_image = self.haze_remover.remove_haze(
                corrected_image, conditions['visibility']
            )
        
        # 에어로졸 보정
        if conditions['aerosol_optical_depth'] > 0.2:
            corrected_image = self.atmospheric_corrector.correct_aerosol_scattering(
                corrected_image, conditions['aerosol_optical_depth']
            )
        
        return corrected_image
    
    def estimate_visibility(self, image):
        """대기 가시도 추정"""
        # 다크 픽셀 방법 사용
        dark_pixels = np.percentile(image, 1, axis=(0, 1))
        
        # 가시도와 다크 픽셀 값의 관계식 (경험적)
        visibility = 50 / (1 + np.exp(-10 * (0.1 - np.mean(dark_pixels))))
        
        return visibility

class CloudProcessor:
    """구름 처리 전문 클래스"""
    
    def __init__(self):
        self.cloud_model = CloudDetectionModel()
        
    def detect_clouds(self, image):
        """멀티스펙트럴 구름 탐지"""
        # 간단한 임계값 기반 탐지
        if image.shape[2] >= 4:  # NIR 밴드가 있는 경우
            # NDSI (Normalized Difference Snow Index) 활용
            green = image[:, :, 1]
            nir = image[:, :, 3]
            ndsi = (green - nir) / (green + nir + 1e-8)
            
            # 밝기 임계값
            brightness = np.mean(image[:, :, :3], axis=2)
            
            # 구름 마스크
            cloud_mask = (ndsi > 0.4) & (brightness > 0.5)
        else:
            # RGB만 있는 경우
            brightness = np.mean(image, axis=2)
            cloud_mask = brightness > 0.7
        
        return cloud_mask
    
    def remove_thin_clouds(self, image):
        """얇은 구름 제거"""
        # 호모모르픽 필터링 적용
        corrected_image = np.zeros_like(image)
        
        for channel in range(image.shape[2]):
            # 로그 변환
            log_image = np.log(image[:, :, channel] + 1e-8)
            
            # 고주파 통과 필터 적용
            high_pass = self.apply_high_pass_filter(log_image)
            
            # 지수 변환
            corrected_image[:, :, channel] = np.exp(high_pass)
        
        return np.clip(corrected_image, 0, 1)
    
    def apply_high_pass_filter(self, image):
        """고주파 통과 필터"""
        # 가우시안 저주파 통과 필터
        low_pass = cv2.GaussianBlur(image, (15, 15), 5)
        
        # 고주파 성분 추출
        high_pass = image - low_pass + 0.5
        
        return high_pass

class HazeRemover:
    """헤이즈 제거 시스템"""
    
    def __init__(self):
        self.dark_channel_processor = DarkChannelProcessor()
        
    def remove_haze(self, image, visibility):
        """다크 채널 프라이어 기반 헤이즈 제거"""
        # 다크 채널 계산
        dark_channel = self.dark_channel_processor.get_dark_channel(image)
        
        # 대기광 추정
        atmospheric_light = self.estimate_atmospheric_light(image, dark_channel)
        
        # 전송률 추정
        transmission = self.estimate_transmission(image, atmospheric_light, dark_channel)
        
        # 헤이즈 제거
        dehazed_image = np.zeros_like(image)
        
        for channel in range(image.shape[2]):
            dehazed_image[:, :, channel] = (
                (image[:, :, channel] - atmospheric_light[channel]) / 
                np.maximum(transmission, 0.1) + atmospheric_light[channel]
            )
        
        return np.clip(dehazed_image, 0, 1)
    
    def estimate_atmospheric_light(self, image, dark_channel):
        """대기광 추정"""
        # 다크 채널에서 가장 밝은 0.1% 픽셀 선택
        flat_dark = dark_channel.flatten()
        flat_indices = np.argsort(flat_dark)
        top_indices = flat_indices[-int(0.001 * len(flat_indices)):]
        
        # 해당 픽셀들의 원본 이미지 값에서 최대값 선택
        atmospheric_light = np.zeros(image.shape[2])
        
        for channel in range(image.shape[2]):
            flat_channel = image[:, :, channel].flatten()
            atmospheric_light[channel] = np.max(flat_channel[top_indices])
        
        return atmospheric_light
```

### 9.3 다중 센서 융합

```python
class MultiSensorFusion:
    """다중 센서 융합 시스템"""
    
    def __init__(self):
        self.fusion_strategies = {
            'optical_sar': self.fuse_optical_sar,
            'multispectral_hyperspectral': self.fuse_spectral_data,
            'thermal_optical': self.fuse_thermal_optical
        }
        
    def fuse_optical_sar(self, optical_image, sar_image):
        """광학-SAR 융합"""
        # 1. 공간 정합
        aligned_sar = self.spatial_registration(sar_image, optical_image)
        
        # 2. 특징 추출
        optical_features = self.extract_optical_features(optical_image)
        sar_features = self.extract_sar_features(aligned_sar)
        
        # 3. 융합 규칙 적용
        fused_features = self.apply_fusion_rules(optical_features, sar_features)
        
        # 4. 융합 이미지 생성
        fused_image = self.generate_fused_image(optical_image, aligned_sar, fused_features)
        
        return fused_image
    
    def extract_optical_features(self, optical_image):
        """광학 영상 특징 추출"""
        features = {}
        
        # 색상 특징
        features['color_moments'] = self.calculate_color_moments(optical_image)
        
        # 텍스처 특징
        features['texture'] = self.calculate_texture_features(optical_image)
        
        # 형태 특징
        features['shape'] = self.calculate_shape_features(optical_image)
        
        # 스펙트럴 특징
        features['spectral_indices'] = self.calculate_spectral_indices(optical_image)
        
        return features
    
    def extract_sar_features(self, sar_image):
        """SAR 영상 특징 추출"""
        features = {}
        
        # 후방산란 계수
        features['backscatter'] = sar_image
        
        # 편파 특징 (다편파 SAR인 경우)
        if self.is_polarimetric_sar(sar_image):
            features['polarimetric'] = self.extract_polarimetric_features(sar_image)
        
        # 간섭성 특징 (InSAR인 경우)
        if self.is_interferometric_sar(sar_image):
            features['interferometric'] = self.extract_interferometric_features(sar_image)
        
        # 텍스처 특징
        features['texture'] = self.calculate_sar_texture(sar_image)
        
        return features
    
    def apply_fusion_rules(self, optical_features, sar_features):
        """융합 규칙 적용"""
        fused_features = {}
        
        # 가중 평균 융합
        weights = self.calculate_adaptive_weights(optical_features, sar_features)
        
        # 광학 데이터가 유리한 특징
        fused_features['color'] = optical_features['color_moments']
        fused_features['spectral'] = optical_features['spectral_indices']
        
        # SAR 데이터가 유리한 특징
        fused_features['surface_roughness'] = sar_features['backscatter']
        
        # 융합 특징
        fused_features['combined_texture'] = (
            optical_features['texture'] * weights['optical'] +
            sar_features['texture'] * weights['sar']
        )
        
        return fused_features
    
    def calculate_adaptive_weights(self, optical_features, sar_features):
        """적응적 가중치 계산"""
        # 데이터 품질 평가
        optical_quality = self.assess_optical_quality(optical_features)
        sar_quality = self.assess_sar_quality(sar_features)
        
        # 정규화된 가중치
        total_quality = optical_quality + sar_quality
        weights = {
            'optical': optical_quality / total_quality,
            'sar': sar_quality / total_quality
        }
        
        return weights

class KalmanFilterTracker:
    """칼만 필터 기반 다중 센서 추적"""
    
    def __init__(self, state_dim=6):  # [x, y, vx, vy, ax, ay]
        self.state_dim = state_dim
        self.observation_dim = 2  # [x, y]
        
        # 상태 전이 행렬
        self.F = np.eye(state_dim)
        self.F[0, 2] = 1  # x += vx * dt
        self.F[1, 3] = 1  # y += vy * dt
        self.F[2, 4] = 1  # vx += ax * dt
        self.F[3, 5] = 1  # vy += ay * dt
        
        # 관측 행렬
        self.H = np.zeros((self.observation_dim, state_dim))
        self.H[0, 0] = 1  # 위치 x 관측
        self.H[1, 1] = 1  # 위치 y 관측
        
        # 초기 공분산
        self.P = np.eye(state_dim) * 1000
        
        # 프로세스 노이즈
        self.Q = np.eye(state_dim) * 0.1
        
    def predict(self, dt=1.0):
        """예측 단계"""
        # 시간 간격 업데이트
        self.F[0, 2] = dt
        self.F[1, 3] = dt
        self.F[2, 4] = dt
        self.F[3, 5] = dt
        
        # 상태 예측
        self.x = self.F @ self.x
        
        # 공분산 예측
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.x
    
    def update(self, measurement, measurement_noise):
        """업데이트 단계"""
        # 관측 노이즈 행렬
        R = np.eye(self.observation_dim) * measurement_noise
        
        # 칼만 게인 계산
        S = self.H @ self.P @ self.H.T + R
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # 상태 업데이트
        y = measurement - self.H @ self.x  # 관측 잔차
        self.x = self.x + K @ y
        
        # 공분산 업데이트
        self.P = (np.eye(self.state_dim) - K @ self.H) @ self.P
        
        return self.x
    
    def multi_sensor_update(self, measurements, sensor_reliabilities):
        """다중 센서 업데이트"""
        for measurement, reliability in zip(measurements, sensor_reliabilities):
            if measurement is not None:
                # 센서 신뢰도에 따른 관측 노이즈 조정
                measurement_noise = 1.0 / reliability
                self.update(measurement, measurement_noise)
        
        return self.x
```

이 설계서는 SatChat 시스템의 AI/ML 및 이미지 처리 전략을 포괄적으로 다룹니다. 각 섹션은 해양 환경의 특수성을 고려하여 실제 구현 가능한 기술적 해결방안을 제시하고 있습니다.

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"content": "AI/ML \uc804\ub7b5 \ubb38\uc11c \uc791\uc131 - \ud574\uc0c1 \ud3d0\uae30\ubb3c \ud0d0\uc9c0 \uc54c\uace0\ub9ac\uc998 \uc124\uacc4", "status": "completed"}, {"content": "\uc704\uc131 \uc774\ubbf8\uc9c0 \uc804\ucc98\ub9ac \uae30\ubc95 \ubc0f \ud30c\uc774\ud504\ub77c\uc778 \uc124\uacc4", "status": "completed"}, {"content": "\ub525\ub7ec\ub2dd \ubaa8\ub378 \uc544\ud0a4\ud14d\ucc98 \uc124\uacc4 (CNN, Vision Transformer)", "status": "completed"}, {"content": "\ud559\uc2b5 \ub370\uc774\ud130 \uc900\ube44 \ubc0f \ub77c\ubca8\ub9c1 \uc804\ub7b5 \uc218\ub9bd", "status": "completed"}, {"content": "\ubaa8\ub378 \uc131\ub2a5 \ud3c9\uac00 \uc9c0\ud45c \ubc0f \uba54\ud2b8\ub9ad \uc815\uc758", "status": "completed"}, {"content": "Edge AI \ubc0f \uc628\ubcf4\ub4dc \ucc98\ub9ac \ubc29\uc548 \uc124\uacc4", "status": "completed"}, {"content": "\uba40\ud2f0/\ud558\uc774\ud37c\uc2a4\ud399\ud2b8\ub7f4 \ub370\uc774\ud130 \ud65c\uc6a9 \uc804\ub7b5", "status": "completed"}, {"content": "\uc2dc\uacc4\uc5f4 \ubd84\uc11d \uae30\ubc18 \ud3d0\uae30\ubb3c \uc774\ub3d9 \uc608\uce21 \ubaa8\ub378", "status": "completed"}, {"content": "\ud574\uc591 \ud658\uacbd \ud2b9\uc218\uc131 \ub300\uc751 \uae30\uc220 \uc194\ub8e8\uc158", "status": "completed"}]