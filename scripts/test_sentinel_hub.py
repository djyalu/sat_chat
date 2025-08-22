#!/usr/bin/env python
"""Sentinel Hub 연결 테스트 스크립트"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

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
        from src.satchat.services.satellite.sentinel_hub import SentinelHubService
        from src.satchat.core.config import settings
        
        print("\n=== Sentinel Hub 인증 테스트 ===")
        
        # 필수 설정 확인
        if not settings.sentinel_hub_client_id or not settings.sentinel_hub_client_secret:
            print("❌ Client ID 또는 Client Secret이 설정되지 않았습니다.")
            print("\n해결 방법:")
            print("1. https://apps.sentinel-hub.com/dashboard/ 로그인")
            print("2. User Settings > OAuth clients에서 새 클라이언트 생성")
            print("3. .env 파일에 SENTINEL_HUB_CLIENT_ID와 SENTINEL_HUB_CLIENT_SECRET 추가")
            return
        
        service = SentinelHubService()
        token = await service.get_access_token()
        print(f"✓ 토큰 획득 성공: {token[:20]}...")
        
        print("\n=== 한국 해역 테스트 (서해) ===")
        
        # 서해 테스트 (간단한 통계만)
        from shapely.geometry import box
        west_sea_bbox = settings.korea_bbox["west_sea"]
        west_sea_polygon = box(*west_sea_bbox)
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=1)
        
        print(f"테스트 기간: {start_date.date()} ~ {end_date.date()}")
        print(f"테스트 지역: 서해 {west_sea_bbox}")
        
        # 간단한 통계 요청
        stats = await service.get_statistics(
            geometry=west_sea_polygon,
            time_range=(start_date, end_date),
            aggregation_interval="P1D",
            resolution=100  # 빠른 테스트를 위해 낮은 해상도
        )
        
        print("✓ 통계 데이터 수신 성공")
        
        if stats.get("temporal_analysis"):
            print(f"  - 분석된 날짜 수: {len(stats['temporal_analysis'])}")
            for entry in stats["temporal_analysis"][:3]:  # 최대 3개만 표시
                print(f"  - {entry.get('date', 'N/A')}: 폐기물 비율 {entry.get('debris_ratio', 0):.2%}")
        
        print("\n=== 테스트 성공! ===")
        print("🎉 Sentinel Hub가 정상적으로 작동합니다.")
        print("\n다음 단계:")
        print("1. 서버 실행: poetry run uvicorn src.satchat.main:app --reload")
        print("2. API 문서 확인: http://localhost:8000/docs")
        print("3. Sentinel Hub 엔드포인트 테스트: /api/v1/sentinel-hub/statistics/marine-debris")
                
    except ImportError as e:
        print(f"\n❌ 모듈 임포트 오류: {e}")
        print("\n해결 방법:")
        print("poetry install")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        print("\n가능한 원인:")
        print("1. Sentinel Hub 계정이 활성화되지 않음")
        print("2. OAuth 클라이언트 권한 부족")
        print("3. 네트워크 연결 문제")
        print("\n자세한 오류 내용:")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🛰️ SatChat - Sentinel Hub 연결 테스트")
    print("=" * 50)
    print("Organization: WS_5a8204bc-452c-454f-b068-b65ee4822073")
    print("Account: go41@naver.com")
    print("=" * 50)
    
    asyncio.run(test_sentinel_hub())