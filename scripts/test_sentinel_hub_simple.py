#!/usr/bin/env python
"""Sentinel Hub 간단한 연결 테스트 스크립트 (S3 의존성 제거)"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import aiohttp

# 환경 변수 로드
load_dotenv()


async def test_sentinel_hub_direct():
    """Sentinel Hub 직접 연결 테스트"""
    
    # 환경 변수 확인
    print("=== 환경 변수 확인 ===")
    print(f"Organization ID: {os.getenv('SENTINEL_HUB_ORGANIZATION_ID')}")
    print(f"Client ID 설정: {'✓' if os.getenv('SENTINEL_HUB_CLIENT_ID') else '✗'}")
    print(f"Client Secret 설정: {'✓' if os.getenv('SENTINEL_HUB_CLIENT_SECRET') else '✗'}")
    print(f"Instance ID 설정: {'✓' if os.getenv('SENTINEL_HUB_INSTANCE_ID') else '✗'}")
    
    client_id = os.getenv('SENTINEL_HUB_CLIENT_ID', 'your_client_id')
    client_secret = os.getenv('SENTINEL_HUB_CLIENT_SECRET', 'your_client_secret')
    
    if client_id == 'your_client_id' or client_secret == 'your_client_secret':
        print("\n❌ Sentinel Hub OAuth 자격증명이 설정되지 않았습니다.")
        print("\n해결 방법:")
        print("1. https://apps.sentinel-hub.com/dashboard/ 로그인 (go41@naver.com)")
        print("2. User Settings > OAuth clients에서 새 클라이언트 생성")
        print("3. .env 파일에 SENTINEL_HUB_CLIENT_ID와 SENTINEL_HUB_CLIENT_SECRET 추가")
        print("\n참고: Organization ID는 이미 설정됨 - WS_5a8204bc-452c-454f-b068-b65ee4822073")
        return
    
    print("\n=== Sentinel Hub OAuth 토큰 획득 테스트 ===")
    
    # OAuth 토큰 요청
    auth_url = "https://services.sentinel-hub.com/auth/realms/main/protocol/openid-connect/token"
    
    async with aiohttp.ClientSession() as session:
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret
        }
        
        try:
            async with session.post(auth_url, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    access_token = token_data.get('access_token')
                    print(f"✅ 토큰 획득 성공!")
                    print(f"   토큰 시작: {access_token[:20]}...")
                    print(f"   유효기간: {token_data.get('expires_in')}초")
                    
                    # 토큰으로 간단한 API 호출 테스트
                    await test_process_api(session, access_token)
                    
                else:
                    error_text = await response.text()
                    print(f"❌ 토큰 획득 실패: {response.status}")
                    print(f"   오류: {error_text}")
                    
        except Exception as e:
            print(f"❌ 연결 오류: {e}")


async def test_process_api(session, token):
    """Process API 테스트"""
    print("\n=== Process API 테스트 ===")
    
    # 한국 서해 지역 bbox
    bbox = [124.0, 33.0, 127.0, 39.0]  # [min_lon, min_lat, max_lon, max_lat]
    
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
        return [sample.B04, sample.B03, sample.B02];
    }
    """
    
    # Process API 요청 구성
    process_request = {
        "input": {
            "bounds": {
                "bbox": bbox,
                "properties": {
                    "crs": "http://www.opengis.net/def/crs/EPSG/0/4326"
                }
            },
            "data": [{
                "type": "sentinel-2-l2a",
                "dataFilter": {
                    "timeRange": {
                        "from": "2024-01-01T00:00:00Z",
                        "to": "2024-01-10T00:00:00Z"
                    }
                }
            }]
        },
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": "image/png"
                }
            }]
        },
        "evalscript": evalscript
    }
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Process API URL
    process_url = "https://services.sentinel-hub.com/api/v1/process"
    
    try:
        async with session.post(process_url, json=process_request, headers=headers) as response:
            if response.status == 200:
                content = await response.read()
                print(f"✅ Process API 호출 성공!")
                print(f"   이미지 크기: {len(content)} bytes")
                print(f"   Content-Type: {response.headers.get('Content-Type')}")
                
                # 이미지를 파일로 저장 (선택사항)
                output_path = "test_sentinel_image.png"
                with open(output_path, 'wb') as f:
                    f.write(content)
                print(f"   이미지 저장: {output_path}")
                
            else:
                error_text = await response.text()
                print(f"❌ Process API 호출 실패: {response.status}")
                print(f"   오류: {error_text}")
                
    except Exception as e:
        print(f"❌ API 호출 오류: {e}")


if __name__ == "__main__":
    print("🛰️ SatChat - Sentinel Hub 간단한 연결 테스트")
    print("=" * 50)
    print("Organization: WS_5a8204bc-452c-454f-b068-b65ee4822073")
    print("Account: go41@naver.com")
    print("=" * 50)
    
    asyncio.run(test_sentinel_hub_direct())
    
    print("\n=== 테스트 완료 ===")
    print("\n다음 단계:")
    print("1. OAuth 클라이언트가 없다면 Sentinel Hub Dashboard에서 생성")
    print("2. .env 파일에 자격증명 추가")
    print("3. 성공하면 서버 실행: python -m uvicorn src.satchat.main:app --reload")