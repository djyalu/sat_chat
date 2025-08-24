#!/usr/bin/env python3
"""
Render 배포 상태 상세 확인 스크립트
"""

import requests
import time
from datetime import datetime

def check_render_status():
    """Render 서비스 상태 확인"""
    
    print("🔍 SatChat Render 배포 상태 상세 확인")
    print("=" * 60)
    print(f"확인 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 가능한 모든 URL 조합 확인
    possible_services = [
        # render.yaml에 정의된 이름
        ("sat-chat-api", "Web API Service"),
        ("sat-chat-frontend", "Static Frontend"),
        
        # 대체 가능한 이름들
        ("satchat-api", "Alternative API"),
        ("satchat", "Base Service"),
        ("sat-chat", "Hyphenated Service"),
        
        # 사용자 이름 기반
        ("djyalu-sat-chat", "User-based naming"),
        ("djyalu-satchat-api", "User API naming"),
    ]
    
    found_service = False
    
    for service_name, description in possible_services:
        url = f"https://{service_name}.onrender.com"
        health_url = f"{url}/health"
        
        print(f"\n📡 {description} ({service_name})")
        print("-" * 50)
        
        # 기본 URL 확인
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                print(f"✅ {url}")
                print(f"   상태: 정상 작동")
                print(f"   응답 시간: {response.elapsed.total_seconds():.2f}초")
                found_service = True
                
                # JSON 응답 확인
                try:
                    data = response.json()
                    print(f"   서비스: {data.get('service', 'N/A')}")
                    print(f"   환경: {data.get('environment', 'N/A')}")
                except:
                    pass
                    
            elif response.status_code == 404:
                print(f"❌ {url} - 서비스 없음 (404)")
            else:
                print(f"⚠️ {url} - HTTP {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ {url} - 타임아웃 (배포 중일 수 있음)")
        except requests.exceptions.ConnectionError:
            print(f"🔌 {url} - 연결 실패")
        except Exception as e:
            print(f"❓ {url} - 오류: {str(e)[:50]}")
        
        # Health endpoint 확인
        if found_service:
            try:
                health_response = requests.get(health_url, timeout=3)
                if health_response.status_code == 200:
                    print(f"   건강 상태: ✅ {health_url}")
            except:
                pass
    
    if not found_service:
        print("\n" + "=" * 60)
        print("⚠️ 배포된 서비스를 찾을 수 없습니다!")
        print("\n가능한 원인:")
        print("1. 아직 배포가 진행 중 (5-10분 소요)")
        print("2. Render Dashboard에서 수동 설정 필요")
        print("3. 다른 서비스 이름 사용")
        
        print("\n📋 확인 방법:")
        print("1. Render Dashboard 접속: https://dashboard.render.com")
        print("2. Services 탭에서 실제 서비스 이름 확인")
        print("3. 서비스 상태가 'Live'인지 확인")
        
        print("\n🔗 빠른 배포 링크:")
        print("https://render.com/deploy?repo=https://github.com/djyalu/sat_chat")
    else:
        print("\n" + "=" * 60)
        print("✅ 배포가 성공적으로 완료되었습니다!")
    
    # 로컬 서버 상태도 확인
    print("\n" + "=" * 60)
    print("💻 로컬 서버 상태:")
    print("-" * 50)
    
    local_services = [
        ("http://localhost:8888/real_data.html", "Web UI"),
        ("http://localhost:8002", "Real Sentinel API"),
        ("http://localhost:8010", "Simple App API"),
        ("http://localhost:8003", "KOMPSAT API"),
        ("http://localhost:8005", "Free Enhancement API"),
    ]
    
    for url, name in local_services:
        try:
            response = requests.get(url.replace("/real_data.html", ""), timeout=1)
            print(f"✅ {name}: {url}")
        except:
            print(f"⭕ {name}: {url} (오프라인)")

if __name__ == "__main__":
    check_render_status()
    
    print("\n" + "=" * 60)
    print("💡 도움말:")
    print("- Render 배포는 보통 5-10분 소요됩니다")
    print("- 처음 배포 시 콜드 스타트로 15분까지 걸릴 수 있습니다")
    print("- Free tier는 비활성 시 자동 슬립 모드로 전환됩니다")
    print("=" * 60)