#!/usr/bin/env python3
"""
SatChat 완전 자동 배포 스크립트
GitHub push만 하면 자동으로 Render에 배포됨
"""

import os
import json
import subprocess
import time
import requests
from datetime import datetime

class AutoDeployer:
    def __init__(self):
        self.github_repo = "https://github.com/djyalu/sat_chat"
        self.render_deploy_url = "https://render.com/deploy"
        
    def check_git_status(self):
        """Git 상태 확인"""
        print("📝 Git 상태 확인...")
        result = subprocess.run(['git', 'status', '--porcelain'], 
                              capture_output=True, text=True)
        if result.stdout:
            print("   변경된 파일이 있습니다.")
            return True
        print("   변경 사항 없음")
        return False
    
    def git_add_commit_push(self, message=None):
        """Git 자동 커밋 및 푸시"""
        if not message:
            message = f"Auto deploy at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        print("📦 Git 커밋 및 푸시...")
        
        # Add all changes
        subprocess.run(['git', 'add', '-A'])
        
        # Commit
        commit_message = f"{message}\n\n🤖 Generated with Claude Code\n\nCo-Authored-By: Claude <noreply@anthropic.com>"
        subprocess.run(['git', 'commit', '-m', commit_message])
        
        # Push
        result = subprocess.run(['git', 'push', 'origin', 'main'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ GitHub 푸시 성공!")
            return True
        else:
            print(f"❌ 푸시 실패: {result.stderr}")
            return False
    
    def create_render_blueprint(self):
        """Render Blueprint URL 생성"""
        blueprint_url = f"{self.render_deploy_url}?repo={self.github_repo}"
        return blueprint_url
    
    def trigger_render_deploy(self):
        """Render 배포 트리거"""
        print("\n🚀 Render 배포 시작...")
        
        # Blueprint URL로 배포 페이지 오픈
        blueprint_url = self.create_render_blueprint()
        print(f"📋 배포 URL: {blueprint_url}")
        
        # 브라우저 자동 열기
        try:
            import webbrowser
            webbrowser.open(blueprint_url)
            print("✅ 브라우저에서 배포 페이지 열림")
        except:
            print("⚠️ 브라우저를 열 수 없습니다. 수동으로 접속하세요:")
            print(f"   {blueprint_url}")
        
        return blueprint_url
    
    def check_deployment_status(self, timeout=600):
        """배포 상태 확인"""
        print("\n📊 배포 상태 모니터링...")
        
        possible_urls = [
            "https://sat-chat.onrender.com",
            "https://sat-chat-api.onrender.com"
        ]
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            for url in possible_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        print(f"✅ 배포 성공! {url}")
                        return True
                except:
                    pass
            
            print(f"⏳ 대기 중... ({int(time.time() - start_time)}초)")
            time.sleep(30)
        
        print("⏰ 배포 타임아웃")
        return False
    
    def auto_deploy(self, fully_automatic=False):
        """완전 자동 배포 실행"""
        print("=" * 60)
        print("🤖 SatChat 완전 자동 배포 시작")
        print("=" * 60)
        
        # 1. Git 상태 확인
        if self.check_git_status():
            # 2. Git 커밋 및 푸시 (이것이 Render 자동 배포를 트리거)
            if not self.git_add_commit_push("Auto deployment update"):
                print("❌ Git 푸시 실패. 수동 확인 필요")
                return False
            
            print("\n✅ GitHub 푸시 완료!")
            print("🎯 Render가 자동으로 배포를 시작합니다.")
            print("\n" + "=" * 60)
            print("📊 배포 상태:")
            print("  - GitHub → Render 웹훅 트리거됨")
            print("  - 빌드 시작 (1-2분)")
            print("  - 배포 진행 (3-5분)")
            print("  - 서비스 재시작 (30초)")
            print("=" * 60)
        else:
            print("ℹ️ 변경 사항이 없습니다.")
            return False
        
        # 3. 자동 모니터링 (fully_automatic 모드에서만)
        if fully_automatic:
            print("\n🔄 자동 배포 모니터링 시작...")
            time.sleep(10)  # 웹훅 처리 대기
            self.check_deployment_status(timeout=300)  # 5분 모니터링
        else:
            # 4. 배포 상태 확인 옵션
            print("\n📌 배포 상태 확인 옵션:")
            print("1. Render 대시보드: https://dashboard.render.com/")
            print("2. 서비스 URL: https://sat-chat.onrender.com")
            print("\n배포 상태를 자동 모니터링할까요? (y/n): ")
            check = input().strip()
            if check.lower() == 'y':
                self.check_deployment_status(timeout=300)
        
        return True

def create_auto_deploy_script():
    """자동 배포를 위한 쉘 스크립트 생성"""
    script_content = """#!/bin/bash
# SatChat 원클릭 자동 배포

echo "🚀 SatChat 자동 배포 시작"

# Python 스크립트 실행
python3 auto_deploy.py

echo "✅ 자동 배포 프로세스 완료"
"""
    
    with open('deploy.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('deploy.sh', 0o755)
    print("✅ deploy.sh 스크립트 생성됨")
    print("   실행: ./deploy.sh")

def save_and_deploy():
    """Save 명령 시 자동으로 배포하는 함수"""
    deployer = AutoDeployer()
    print("\n💾 /ccsave 명령 감지 - 자동 배포 시작")
    deployer.auto_deploy(fully_automatic=True)

if __name__ == "__main__":
    import sys
    
    # 자동 배포 실행
    deployer = AutoDeployer()
    
    # 커맨드라인 인자 확인 (자동 모드)
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        print("🚀 완전 자동 모드로 실행")
        deployer.auto_deploy(fully_automatic=True)
    else:
        print("🎯 SatChat 자동 배포 옵션:")
        print("1. 즉시 자동 배포")
        print("2. 배포 스크립트 생성")
        print("3. 배포 URL만 보기")
        print("4. 완전 자동 배포 (모니터링 포함)")
        
        choice = input("\n선택 (1/2/3/4): ")
        
        if choice == '1':
            deployer.auto_deploy()
        elif choice == '2':
            create_auto_deploy_script()
        elif choice == '3':
            url = deployer.create_render_blueprint()
            print(f"\n📋 배포 URL: {url}")
            print("브라우저에서 이 URL을 열어 배포하세요.")
        elif choice == '4':
            deployer.auto_deploy(fully_automatic=True)
        else:
            print("잘못된 선택입니다.")