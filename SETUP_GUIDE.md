# SatChat 설정 가이드 - 텔레픽스

## 계정 정보

### Sentinel Hub
- **Organization ID**: WS_5a8204bc-452c-454f-b068-b65ee4822073
- **Account Email**: go41@naver.com
- **Dashboard**: https://apps.sentinel-hub.com/dashboard/

### Planet Labs
- **API Key**: PLAK1027cc537c4549eab7d80397256fd454
- **Dashboard**: https://www.planet.com/account/

## 빠른 시작 가이드

### 1단계: Sentinel Hub OAuth 클라이언트 생성

1. [Sentinel Hub Dashboard](https://apps.sentinel-hub.com/dashboard/) 로그인
2. User Settings → OAuth clients 이동
3. "+ NEW" 클릭하여 새 OAuth 클라이언트 생성
4. 다음 정보 입력:
   - **Client name**: SatChat Production
   - **Client grant type**: Client Credentials
5. Client ID와 Client Secret 저장 (한 번만 표시됨!)

### 2단계: Configuration (Instance) 생성

1. Dashboard에서 "Configuration utility" 클릭
2. "+ Add new configuration" 클릭
3. 설정:
   - **Name**: SatChat Korea Waters
   - **Based on**: Sentinel-2 L2A
4. Instance ID 복사 (URL에서 확인 가능)

### 3단계: 환경 변수 설정

`.env` 파일 생성:
```bash
cp .env.example .env
```

`.env` 파일 편집:
```env
# Sentinel Hub API
SENTINEL_HUB_CLIENT_ID=<위에서 생성한 Client ID>
SENTINEL_HUB_CLIENT_SECRET=<위에서 생성한 Client Secret>
SENTINEL_HUB_INSTANCE_ID=<위에서 생성한 Instance ID>
SENTINEL_HUB_ORGANIZATION_ID=WS_5a8204bc-452c-454f-b068-b65ee4822073

# Planet Labs API
PLANET_API_KEY=PLAK1027cc537c4549eab7d80397256fd454
```

### 4단계: 연결 테스트

```bash
# Python 환경 활성화
poetry shell

# 테스트 스크립트 실행
python scripts/test_sentinel_hub.py
```

## 테스트 스크립트

`scripts/test_sentinel_hub.py` 파일을 생성하고 실행하세요:

```python
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

async def test_sentinel_hub():
    """Sentinel Hub 연결 테스트"""
    
    # 환경 변수 확인
    print("=== 환경 변수 확인 ===")
    print(f"Organization ID: {os.getenv('SENTINEL_HUB_ORGANIZATION_ID')}")
    print(f"Client ID 설정: {'✓' if os.getenv('SENTINEL_HUB_CLIENT_ID') else '✗'}")
    print(f"Client Secret 설정: {'✓' if os.getenv('SENTINEL_HUB_CLIENT_SECRET') else '✗'}")
    print(f"Instance ID 설정: {'✓' if os.getenv('SENTINEL_HUB_INSTANCE_ID') else '✗'}")
    print(f"Planet API Key 설정: {'✓' if os.getenv('PLANET_API_KEY') else '✗'}")
    
    # Sentinel Hub 서비스 테스트
    try:
        from satchat.services.satellite.sentinel_hub import SentinelHubService
        
        print("\n=== Sentinel Hub 인증 테스트 ===")
        service = SentinelHubService()
        token = await service.get_access_token()
        print(f"✓ 토큰 획득 성공: {token[:20]}...")
        
        print("\n=== 한국 해역 처리 테스트 ===")
        # 최근 1일 데이터로 간단한 테스트
        results = await service.process_korean_waters(days_back=1, resolution=60)
        
        for area, result in results.items():
            if "error" in result:
                print(f"✗ {area}: {result['error']}")
            else:
                print(f"✓ {area}: 처리 완료")
                
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n해결 방법:")
        print("1. Sentinel Hub Dashboard에서 OAuth 클라이언트를 생성했는지 확인")
        print("2. .env 파일에 Client ID와 Secret이 정확히 입력되었는지 확인")
        print("3. Instance ID가 올바른지 확인")

if __name__ == "__main__":
    print("SatChat - Sentinel Hub 연결 테스트")
    print("=" * 40)
    asyncio.run(test_sentinel_hub())
```

## 사용 가능한 데이터 소스

### Sentinel-2 L2A
- **해상도**: 10m (RGB), 20m (Red Edge, SWIR)
- **재방문 주기**: 5일
- **커버리지**: 전 세계
- **용도**: 해양 폐기물 탐지, 수질 모니터링

### Planet Scope (Planet API)
- **해상도**: 3-5m
- **재방문 주기**: 매일
- **커버리지**: 전 세계
- **용도**: 고해상도 상세 분석

## API 사용량 및 제한

### Sentinel Hub
- **Process API**: 요청당 최대 2500x2500 픽셀
- **Statistical API**: 요청당 최대 100개 폴리곤
- **Batch Processing**: 작업당 최대 1000 타일
- **Rate Limit**: 분당 100 요청 (기본)

### Planet Labs
- **일일 다운로드 한도**: 계약에 따라 다름
- **API Rate Limit**: 분당 10 요청

## 비용 최적화 팁

1. **캐싱 활용**
   - Redis에 처리 결과 캐싱
   - 동일 지역/기간 재요청 방지

2. **해상도 조정**
   - 초기 스캔: 60m
   - 상세 분석: 10m
   - 통계 분석: 100m

3. **배치 처리**
   - 실시간 불필요한 작업은 배치로
   - 야간 시간대 활용

4. **구역 최적화**
   - 관심 지역만 처리
   - 타일 단위로 분할 처리

## 문제 해결

### 인증 실패
```
Error: Invalid client credentials
```
**해결**: OAuth 클라이언트 재생성 후 .env 업데이트

### 데이터 없음
```
Error: No data available for the selected time range
```
**해결**: 
- 날짜 범위 확장 (구름이 많은 날 제외)
- maxCloudCoverage 값 증가

### 요청 제한 초과
```
Error: Rate limit exceeded
```
**해결**:
- 요청 간 지연 시간 추가
- 배치 처리 API 사용

## 지원 연락처

### 텔레픽스 기술 지원
- Email: dev@telefix.co.kr
- GitHub: https://github.com/djyalu/sat_chat

### Sentinel Hub 지원
- Forum: https://forum.sentinel-hub.com/
- Email: support@sentinel-hub.com

### Planet Labs 지원
- Support: https://support.planet.com/
- API Docs: https://developers.planet.com/