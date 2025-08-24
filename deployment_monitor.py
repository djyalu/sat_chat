#!/usr/bin/env python3
"""
🔍 SatChat Lite 배포 모니터링 스크립트
실시간으로 배포 상태를 확인합니다.
"""

import time
import requests
import sys
from datetime import datetime

def check_deployment():
    urls = [
        "https://satchat-lite.onrender.com",
        "https://sat-chat-api.onrender.com"
    ]
    
    print("🚀 SatChat Lite 배포 모니터링 시작")
    print("=" * 50)
    
    for attempt in range(20):  # 10분간 모니터링
        print(f"\n📊 시도 {attempt + 1}/20 - {datetime.now().strftime('%H:%M:%S')}")
        
        for url in urls:
            try:
                response = requests.get(f"{url}/health", timeout=10)
                if response.status_code == 200:
                    print(f"✅ 배포 성공! {url}")
                    print(f"📊 응답: {response.json()}")
                    print(f"🌐 대시보드: {url}")
                    return url
                else:
                    print(f"⚠️  {url} - 상태코드: {response.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"❌ {url} - 연결 실패: {str(e)[:50]}...")
        
        if attempt < 19:
            print("⏳ 30초 대기 중...")
            time.sleep(30)
    
    print("\n❌ 배포 타임아웃 - 수동 확인 필요")
    return None

if __name__ == "__main__":
    result = check_deployment()
    if result:
        print(f"\n🎉 배포 완료: {result}")
        sys.exit(0)
    else:
        print("\n⚠️  배포 실패 또는 지연")
        sys.exit(1)