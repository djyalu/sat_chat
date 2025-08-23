#!/usr/bin/env python3
"""
Render 배포 상태 확인 스크립트
"""

import requests
import time
import json

def check_deployment():
    """Render 배포 상태 확인"""
    
    print("🚀 SatChat Render 배포 상태 확인")
    print("=" * 50)
    
    # 예상되는 Render URL들
    possible_urls = [
        "https://sat-chat-api.onrender.com",
        "https://sat-chat-frontend.onrender.com",
        "https://satchat-api.onrender.com",
        "https://satchat-frontend.onrender.com"
    ]
    
    for url in possible_urls:
        print(f"🔍 {url} 확인 중...")
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {url}")
                print(f"   상태: {data.get('status', 'N/A')}")
                print(f"   서비스: {data.get('service', 'N/A')}")
                print(f"   환경: {data.get('environment', 'N/A')}")
                print(f"   응답시간: {response.elapsed.total_seconds():.2f}초")
            else:
                print(f"⚠️ {url} - HTTP {response.status_code}")
        except requests.exceptions.ConnectTimeout:
            print(f"⏰ {url} - 연결 타임아웃 (서비스 시작 중일 수 있음)")
        except requests.exceptions.ConnectionError:
            print(f"❌ {url} - 연결 실패 (배포되지 않았거나 잘못된 URL)")
        except Exception as e:
            print(f"❌ {url} - 오류: {e}")
        print()
    
    # Git 상태 확인
    print("📝 Git 배포 준비 상태:")
    try:
        import subprocess
        
        # 현재 브랜치 확인
        branch = subprocess.check_output(['git', 'branch', '--show-current'], 
                                       text=True).strip()
        print(f"   현재 브랜치: {branch}")
        
        # 마지막 커밋 확인
        last_commit = subprocess.check_output(['git', 'log', '-1', '--oneline'], 
                                            text=True).strip()
        print(f"   마지막 커밋: {last_commit}")
        
        # 배포 관련 파일 확인
        import os
        files_to_check = [
            'render.yaml',
            'requirements_simple.txt', 
            'simple_app.py',
            'Dockerfile'
        ]
        
        print("   배포 파일 상태:")
        for file in files_to_check:
            if os.path.exists(file):
                print(f"   ✅ {file}")
            else:
                print(f"   ❌ {file} (없음)")
                
    except Exception as e:
        print(f"   Git 정보 확인 실패: {e}")
    
    print("\n📋 배포 가이드:")
    print("1. GitHub 저장소에 코드 푸시:")
    print("   git add .")
    print("   git commit -m 'Deploy to Render'")
    print("   git push origin main")
    print()
    print("2. Render 대시보드에서:")
    print("   - New Web Service 생성")
    print("   - GitHub 저장소 연결")
    print("   - render.yaml 설정 확인")
    print("   - 환경 변수 설정 (SENTINEL_HUB_CLIENT_ID, SECRET)")

if __name__ == "__main__":
    check_deployment()