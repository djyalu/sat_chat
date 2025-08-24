#!/usr/bin/env python3
"""
즉시 Render 배포 스크립트 - render.yaml 사용
"""

import os
import json
import subprocess
import time

def deploy_to_render():
    """Render.yaml을 사용한 간단한 배포"""
    
    print("🚀 SatChat Render 즉시 배포")
    print("=" * 50)
    
    # 1. render.yaml 확인
    if not os.path.exists("render.yaml"):
        print("❌ render.yaml 파일이 없습니다!")
        return False
    
    print("✅ render.yaml 발견")
    
    # 2. Render Blueprint URL 생성
    repo_url = "https://github.com/djyalu/sat_chat"
    render_deploy_url = f"https://render.com/deploy?repo={repo_url}"
    
    print("\n📋 배포 방법:")
    print("=" * 50)
    print("\n방법 1: 웹 브라우저로 직접 배포 (가장 간단)")
    print("-" * 50)
    print("1. 아래 URL을 브라우저에 복사하세요:")
    print(f"\n   {render_deploy_url}\n")
    print("2. 'Connect GitHub' 버튼 클릭")
    print("3. GitHub 계정 연결 승인")
    print("4. 환경 변수 확인:")
    print("   - SENTINEL_HUB_CLIENT_ID")
    print("   - SENTINEL_HUB_CLIENT_SECRET")
    print("5. 'Deploy' 버튼 클릭")
    
    print("\n방법 2: Render Dashboard 직접 설정")
    print("-" * 50)
    print("1. https://dashboard.render.com 접속")
    print("2. 'New +' → 'Blueprint' 클릭")
    print("3. GitHub 저장소 연결: djyalu/sat_chat")
    print("4. render.yaml 자동 감지됨")
    print("5. 'Apply' 클릭")
    
    print("\n🔑 필요한 환경 변수:")
    print("-" * 50)
    print("SENTINEL_HUB_CLIENT_ID = a02dcc3a-0d6c-408d-b796-c72cf8ad97fa")
    print("SENTINEL_HUB_CLIENT_SECRET = xHUnjXzw99EyY0JEofxCn2ScBqCPmkoY")
    
    print("\n📊 배포 후 확인 URL:")
    print("-" * 50)
    print("API: https://sat-chat-api.onrender.com")
    print("Health: https://sat-chat-api.onrender.com/health")
    print("Frontend: https://sat-chat-frontend.onrender.com")
    
    # 브라우저 자동 열기 시도
    try:
        import webbrowser
        print("\n🌐 브라우저에서 배포 페이지를 여는 중...")
        webbrowser.open(render_deploy_url)
        print("✅ 브라우저가 열렸습니다!")
    except:
        print("\n⚠️ 브라우저를 자동으로 열 수 없습니다.")
        print("위 URL을 복사해서 직접 열어주세요.")
    
    return True

def check_deployment_status():
    """배포 상태 확인"""
    print("\n🔍 배포 상태 확인 중...")
    
    urls = [
        "https://sat-chat-api.onrender.com",
        "https://sat-chat-api.onrender.com/health"
    ]
    
    for url in urls:
        try:
            import requests
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {url} - 정상 작동")
            else:
                print(f"⚠️ {url} - 상태 코드: {response.status_code}")
        except:
            print(f"❌ {url} - 연결 실패 (아직 배포 중일 수 있음)")

if __name__ == "__main__":
    deploy_to_render()
    
    # 배포 상태 확인 옵션
    check = input("\n배포 상태를 확인하시겠습니까? (y/n): ")
    if check.lower() == 'y':
        check_deployment_status()