#!/usr/bin/env python3
"""
Render 배포 상태 모니터링 스크립트
"""

import time
import requests
from datetime import datetime

def check_deployment():
    """배포 상태를 확인하고 모니터링"""
    
    print("🔍 Render 배포 상태 모니터링 시작...")
    print("=" * 60)
    
    # 체크할 URL들
    urls = [
        ("API", "https://sat-chat-api.onrender.com/health"),
        ("Main", "https://sat-chat.onrender.com"),
    ]
    
    start_time = time.time()
    max_wait = 300  # 5분 최대 대기
    check_interval = 15  # 15초마다 체크
    
    deployment_complete = False
    
    while time.time() - start_time < max_wait:
        print(f"\n⏰ {datetime.now().strftime('%H:%M:%S')} - 상태 체크 중...")
        
        all_success = True
        for name, url in urls:
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    print(f"  ✅ {name}: 정상 작동 ({url})")
                else:
                    print(f"  ⏳ {name}: 응답 코드 {response.status_code}")
                    all_success = False
            except requests.exceptions.RequestException as e:
                print(f"  ⏳ {name}: 아직 시작 중...")
                all_success = False
        
        if all_success:
            deployment_complete = True
            break
        
        print(f"\n  다음 체크까지 {check_interval}초 대기...")
        time.sleep(check_interval)
    
    print("\n" + "=" * 60)
    
    if deployment_complete:
        elapsed = int(time.time() - start_time)
        print(f"✅ 배포 완료! (소요 시간: {elapsed}초)")
        print("\n🌐 접속 가능한 URL:")
        for name, url in urls:
            print(f"  - {name}: {url}")
    else:
        print("⏰ 배포 시간 초과 (5분)")
        print("💡 Render 대시보드에서 직접 확인하세요:")
        print("   https://dashboard.render.com/")
    
    print("\n✅ 모니터링 완료")

if __name__ == "__main__":
    check_deployment()