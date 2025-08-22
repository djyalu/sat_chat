"""실제 Sentinel Hub 데이터 테스트 스크립트"""

import os
from datetime import datetime, timedelta
from sentinelhub import (
    SHConfig,
    CRS,
    BBox,
    DataCollection,
    SentinelHubRequest,
    SentinelHubStatistical,
    MimeType,
    Geometry
)
import matplotlib.pyplot as plt
import numpy as np

# 환경 변수에서 인증 정보 가져오기
from dotenv import load_dotenv
load_dotenv()

def test_sentinel_connection():
    """Sentinel Hub 연결 테스트"""
    
    # 환경 변수에서 인증 정보 가져오기
    client_id = os.getenv('SENTINEL_HUB_CLIENT_ID', 'your_client_id')
    client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET', 'your_client_secret')
    
    if client_id == 'your_client_id' or client_secret == 'your_client_secret':
        print("❌ 에러: .env 파일에 실제 Sentinel Hub 인증 정보를 입력해주세요!")
        print("📝 방법:")
        print("1. https://apps.sentinel-hub.com/dashboard/ 에서 계정 생성")
        print("2. OAuth clients에서 Client ID와 Secret 확인")
        print("3. .env 파일의 TODO(human) 부분에 입력")
        return None
    
    # 설정 객체 생성 - Sentinel Hub 서비스 (유료)
    config = SHConfig()
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    
    # Sentinel Hub 서비스 URL (유료 서비스)
    config.sh_base_url = 'https://services.sentinel-hub.com'
    config.sh_token_url = 'https://services.sentinel-hub.com/oauth/token'
    
    print(f"✅ Sentinel Hub 연결 설정 완료")
    print(f"   Client ID: {client_id[:10]}...")
    print(f"   Base URL: {config.sh_base_url}")
    
    return config

def get_korea_marine_data(config):
    """한국 해역 실제 위성 데이터 가져오기"""
    
    # 한국 남해 (부산 근처) 좌표
    korea_bbox = BBox(bbox=[128.5, 34.5, 129.5, 35.5], crs=CRS.WGS84)
    
    print(f"🌊 한국 남해 지역 데이터 요청 중...")
    print(f"   위치: 부산 근해")
    print(f"   좌표: {korea_bbox}")
    
    # Evalscript - 해양 플라스틱 탐지용
    evalscript_debris = """
    //VERSION=3
    function setup() {
        return {
            input: [{
                bands: ["B02", "B03", "B04", "B06", "B08", "B11", "SCL"],
                units: "DN"
            }],
            output: {
                bands: 4,
                sampleType: "FLOAT32"
            }
        };
    }

    function evaluatePixel(sample) {
        // 구름 마스킹
        if (sample.SCL == 3 || sample.SCL == 8 || sample.SCL == 9 || sample.SCL == 10) {
            return [0, 0, 0, 0];
        }
        
        // 밴드 값 정규화
        let blue = sample.B02 / 10000;
        let green = sample.B03 / 10000;
        let red = sample.B04 / 10000;
        let nir = sample.B08 / 10000;
        let swir1 = sample.B11 / 10000;
        let rededge = sample.B06 / 10000;
        
        // FDI (Floating Debris Index) - 해양 플라스틱 탐지
        let fdi = nir - (red + (swir1 - red) * (833 - 665) / (1610.4 - 665));
        
        // NDWI (정규화 수분 지수)
        let ndwi = (green - nir) / (green + nir + 0.001);
        
        // 플라스틱 가능성 점수
        let plastic_score = 0;
        if (fdi > 0.02 && ndwi > 0.3) {
            plastic_score = Math.min(fdi * 10, 1);
        }
        
        // RGB + 플라스틱 점수
        return [red * 2.5, green * 2.5, blue * 2.5, plastic_score];
    }
    """
    
    # 최근 7일 데이터 요청
    time_interval = (datetime.now() - timedelta(days=7), datetime.now())
    
    request = SentinelHubRequest(
        evalscript=evalscript_debris,
        input_data=[
            SentinelHubRequest.input_data(
                data_collection=DataCollection.SENTINEL2_L2A,
                time_interval=time_interval,
                maxcc=0.3  # 최대 구름 30%
            )
        ],
        responses=[
            SentinelHubRequest.output_response('default', MimeType.TIFF)
        ],
        bbox=korea_bbox,
        size=[512, 512],
        config=config
    )
    
    try:
        print("📡 Sentinel-2 데이터 다운로드 중...")
        data = request.get_data()[0]
        
        print(f"✅ 데이터 수신 완료!")
        print(f"   크기: {data.shape}")
        print(f"   타입: {data.dtype}")
        
        # 시각화
        rgb = data[:, :, :3]
        debris_score = data[:, :, 3]
        
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        
        # RGB 이미지
        axes[0].imshow(np.clip(rgb, 0, 1))
        axes[0].set_title('Sentinel-2 RGB - 한국 남해')
        axes[0].axis('off')
        
        # 해양 플라스틱 탐지
        im = axes[1].imshow(debris_score, cmap='hot', vmin=0, vmax=1)
        axes[1].set_title('해양 플라스틱 가능성 (FDI 기반)')
        axes[1].axis('off')
        plt.colorbar(im, ax=axes[1], label='플라스틱 가능성')
        
        plt.suptitle(f'한국 남해 해양 모니터링 - {datetime.now().strftime("%Y-%m-%d")}')
        plt.tight_layout()
        plt.savefig('korea_marine_debris.png', dpi=150, bbox_inches='tight')
        print(f"📊 결과 저장: korea_marine_debris.png")
        
        # 통계
        debris_pixels = np.sum(debris_score > 0.5)
        total_pixels = debris_score.size
        debris_percentage = (debris_pixels / total_pixels) * 100
        
        print(f"\n📈 분석 결과:")
        print(f"   의심 픽셀: {debris_pixels:,} / {total_pixels:,}")
        print(f"   오염 비율: {debris_percentage:.2f}%")
        
        if debris_percentage > 0.1:
            print(f"⚠️  경고: 해양 플라스틱 오염 가능성 감지!")
        
        return True
        
    except Exception as e:
        print(f"❌ 데이터 요청 실패: {e}")
        print(f"💡 힌트: Client ID와 Secret이 올바른지 확인하세요")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🛰️  Sentinel Hub 실제 데이터 연동 테스트")
    print("=" * 50)
    
    # 1. 연결 테스트
    config = test_sentinel_connection()
    
    if config:
        print("\n" + "=" * 50)
        # 2. 한국 해역 데이터 가져오기
        success = get_korea_marine_data(config)
        
        if success:
            print("\n✅ 테스트 성공! 실제 위성 데이터를 사용할 수 있습니다.")
        else:
            print("\n⚠️  데이터 요청 실패. 인증 정보를 확인해주세요.")
    else:
        print("\n📝 .env 파일을 수정한 후 다시 실행해주세요.")