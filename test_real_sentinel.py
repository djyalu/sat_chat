#!/usr/bin/env python3
"""실제 Sentinel Hub 데이터 다운로드 테스트"""

import os
import sys
import json
import base64
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# sentinelhub 패키지 임포트
try:
    from sentinelhub import (
        SHConfig, 
        CRS, 
        BBox, 
        DataCollection,
        SentinelHubRequest, 
        MimeType,
        SentinelHubDownloadClient
    )
except ImportError:
    print("❌ sentinelhub 패키지가 설치되지 않았습니다.")
    print("설치: pip install sentinelhub")
    sys.exit(1)

# 환경 변수 로드
load_dotenv()

def setup_config():
    """Sentinel Hub 설정"""
    config = SHConfig()
    
    # 환경 변수에서 인증 정보 가져오기
    client_id = os.getenv('SENTINEL_HUB_CLIENT_ID')
    client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET')
    
    if not client_id or not client_secret or 'your' in client_id:
        print("❌ 유효한 Sentinel Hub 인증 정보가 필요합니다!")
        print("   .env 파일을 확인하세요.")
        return None
    
    # Sentinel Hub 설정
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    
    # 서비스 URL 설정 (유료 Sentinel Hub 서비스)
    config.sh_base_url = 'https://services.sentinel-hub.com'
    config.sh_token_url = 'https://services.sentinel-hub.com/oauth/token'
    
    print(f"✅ Sentinel Hub 설정 완료")
    print(f"   Client ID: {client_id[:20]}...")
    print(f"   Service: Sentinel Hub (Paid)")
    
    return config

def test_simple_request(config):
    """간단한 데이터 요청 테스트"""
    print("\n🔍 간단한 데이터 요청 테스트...")
    
    # 한국 부산 근해 좌표
    bbox = BBox(bbox=[128.8, 34.8, 129.2, 35.2], crs=CRS.WGS84)
    print(f"   지역: 부산 근해 {bbox}")
    
    # 최근 30일 이내 데이터
    time_interval = (datetime.now() - timedelta(days=30), datetime.now())
    print(f"   기간: {time_interval[0].date()} ~ {time_interval[1].date()}")
    
    # 간단한 True Color 이미지 요청
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B02", "B03", "B04"],
            output: { bands: 3 }
        };
    }
    
    function evaluatePixel(sample) {
        return [sample.B04/3000, sample.B03/3000, sample.B02/3000];
    }
    """
    
    try:
        request = SentinelHubRequest(
            evalscript=evalscript,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L1C,
                    time_interval=time_interval,
                    maxcc=0.5  # 최대 구름 50%
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.PNG)
            ],
            bbox=bbox,
            size=[256, 256],
            config=config
        )
        
        print("📡 데이터 다운로드 중...")
        data = request.get_data()
        
        if data and len(data) > 0:
            print(f"✅ 데이터 수신 성공!")
            print(f"   데이터 타입: {type(data[0])}")
            
            # 이미지 저장
            if isinstance(data[0], np.ndarray):
                img = Image.fromarray(data[0].astype(np.uint8))
                img.save('real_sentinel_test.png')
                print(f"   이미지 저장: real_sentinel_test.png")
                print(f"   크기: {img.size}")
                return True
            else:
                print(f"   예상치 못한 데이터 형식: {type(data[0])}")
                return False
        else:
            print("❌ 데이터가 비어있습니다")
            return False
            
    except Exception as e:
        print(f"❌ 요청 실패: {e}")
        return False

def get_korea_marine_debris_data(config):
    """한국 해역 해양 플라스틱 탐지"""
    print("\n🌊 한국 해역 해양 플라스틱 탐지...")
    
    # 한국 남해 (거제도 근처)
    bbox = BBox(bbox=[128.4, 34.6, 128.8, 35.0], crs=CRS.WGS84)
    print(f"   지역: 거제도 근해")
    
    # 최근 데이터
    time_interval = (datetime.now() - timedelta(days=14), datetime.now())
    
    # 해양 플라스틱 탐지 스크립트
    evalscript_debris = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "B08", "B11", "SCL"]
            }],
            output: [{
                id: "default",
                bands: 4
            }]
        };
    }
    
    function evaluatePixel(sample) {
        // 구름 제거
        if (sample.SCL == 3 || sample.SCL == 9) {
            return [0, 0, 0, 0];
        }
        
        // 정규화
        let blue = sample.B02 / 10000;
        let green = sample.B03 / 10000;
        let red = sample.B04 / 10000;
        let nir = sample.B08 / 10000;
        let swir = sample.B11 / 10000;
        
        // NDWI (물 탐지)
        let ndwi = (green - nir) / (green + nir + 0.001);
        
        // FDI (부유 물질 탐지)
        let fdi = nir - red - 0.5 * (swir - red);
        
        // 플라스틱 가능성
        let plastic = 0;
        if (ndwi > 0 && fdi > 0.01) {
            plastic = Math.min(fdi * 20, 1);
        }
        
        // RGB + 플라스틱 점수
        return [red * 3, green * 3, blue * 3, plastic];
    }
    """
    
    try:
        request = SentinelHubRequest(
            evalscript=evalscript_debris,
            input_data=[
                SentinelHubRequest.input_data(
                    data_collection=DataCollection.SENTINEL2_L2A,
                    time_interval=time_interval,
                    maxcc=0.3
                )
            ],
            responses=[
                SentinelHubRequest.output_response('default', MimeType.TIFF)
            ],
            bbox=bbox,
            size=[512, 512],
            config=config
        )
        
        print("📡 Sentinel-2 데이터 다운로드 중...")
        data = request.get_data()
        
        if data and len(data) > 0 and isinstance(data[0], np.ndarray):
            image_data = data[0]
            print(f"✅ 데이터 수신 성공!")
            print(f"   Shape: {image_data.shape}")
            print(f"   dtype: {image_data.dtype}")
            
            # RGB 이미지와 플라스틱 레이어 분리
            if image_data.shape[2] >= 4:
                rgb = image_data[:, :, :3]
                plastic = image_data[:, :, 3]
                
                # 통계
                plastic_pixels = np.sum(plastic > 0.3)
                total_pixels = plastic.size
                percentage = (plastic_pixels / total_pixels) * 100
                
                print(f"\n📊 분석 결과:")
                print(f"   플라스틱 의심 픽셀: {plastic_pixels:,}/{total_pixels:,}")
                print(f"   오염 비율: {percentage:.2f}%")
                
                # 시각화
                fig, axes = plt.subplots(1, 3, figsize=(15, 5))
                
                # RGB
                axes[0].imshow(np.clip(rgb, 0, 1))
                axes[0].set_title('Sentinel-2 RGB - 거제도 근해')
                axes[0].axis('off')
                
                # 플라스틱 탐지
                im1 = axes[1].imshow(plastic, cmap='hot', vmin=0, vmax=1)
                axes[1].set_title(f'플라스틱 탐지 ({percentage:.1f}%)')
                axes[1].axis('off')
                plt.colorbar(im1, ax=axes[1], fraction=0.046)
                
                # 오버레이
                axes[2].imshow(np.clip(rgb, 0, 1))
                mask = plastic > 0.3
                overlay = np.zeros_like(rgb)
                overlay[:, :, 0] = mask  # Red channel for plastic
                axes[2].imshow(overlay, alpha=0.5)
                axes[2].set_title('오염 지역 표시')
                axes[2].axis('off')
                
                plt.suptitle(f'한국 남해 해양 플라스틱 모니터링 - {datetime.now().strftime("%Y-%m-%d")}')
                plt.tight_layout()
                plt.savefig('korea_real_marine_debris.png', dpi=150, bbox_inches='tight')
                print(f"   결과 저장: korea_real_marine_debris.png")
                
                return True
            else:
                print(f"❌ 예상치 못한 데이터 형식")
                return False
        else:
            print("❌ 데이터 수신 실패")
            return False
            
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🛰️  Sentinel Hub 실제 데이터 다운로드 테스트")
    print("=" * 60)
    
    # 설정
    config = setup_config()
    if not config:
        return
    
    # 간단한 테스트
    success = test_simple_request(config)
    
    if success:
        print("\n" + "=" * 60)
        # 해양 플라스틱 탐지
        get_korea_marine_debris_data(config)
    
    print("\n" + "=" * 60)
    print("✅ 테스트 완료")

if __name__ == "__main__":
    main()