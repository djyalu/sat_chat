#!/usr/bin/env python3
"""
Render 자동 배포 스크립트
GitHub Actions 또는 로컬에서 실행 가능
"""

import os
import json
import time
import requests
import subprocess
from typing import Dict, Optional

class RenderAutoDeployer:
    """Render 자동 배포 관리자"""
    
    def __init__(self):
        self.api_base = "https://api.render.com/v1"
        # Render API 키는 환경 변수 또는 직접 입력
        self.api_key = os.environ.get("RENDER_API_KEY", "")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def create_service_config(self) -> Dict:
        """Render 서비스 설정 생성"""
        return {
            "type": "web_service",
            "name": "sat-chat-api",
            "ownerId": self.get_owner_id(),
            "repo": "https://github.com/djyalu/sat_chat",
            "autoDeploy": "yes",
            "branch": "main",
            "buildCommand": "pip install -r requirements_simple.txt",
            "startCommand": "python simple_app.py",
            "envVars": [
                {
                    "key": "SENTINEL_HUB_CLIENT_ID",
                    "value": "a02dcc3a-0d6c-408d-b796-c72cf8ad97fa"
                },
                {
                    "key": "SENTINEL_HUB_CLIENT_SECRET", 
                    "value": "xHUnjXzw99EyY0JEofxCn2ScBqCPmkoY"
                },
                {
                    "key": "PYTHON_VERSION",
                    "value": "3.11"
                }
            ],
            "serviceDetails": {
                "env": "python",
                "region": "singapore",
                "plan": "free",
                "buildCommand": "pip install -r requirements_simple.txt",
                "startCommand": "python simple_app.py",
                "healthCheckPath": "/health",
                "numInstances": 1
            }
        }
    
    def get_owner_id(self) -> Optional[str]:
        """Render 계정 Owner ID 가져오기"""
        try:
            response = requests.get(
                f"{self.api_base}/owners",
                headers=self.headers
            )
            if response.status_code == 200:
                owners = response.json()
                if owners:
                    return owners[0]["owner"]["id"]
        except Exception as e:
            print(f"❌ Owner ID 가져오기 실패: {e}")
        return None
    
    def check_existing_service(self, name: str) -> Optional[str]:
        """기존 서비스 확인"""
        try:
            response = requests.get(
                f"{self.api_base}/services",
                headers=self.headers
            )
            if response.status_code == 200:
                services = response.json()
                for service in services:
                    if service["service"]["name"] == name:
                        return service["service"]["id"]
        except Exception as e:
            print(f"❌ 서비스 확인 실패: {e}")
        return None
    
    def create_service(self) -> Optional[str]:
        """새 서비스 생성"""
        config = self.create_service_config()
        
        try:
            response = requests.post(
                f"{self.api_base}/services",
                headers=self.headers,
                json=config
            )
            
            if response.status_code == 201:
                service = response.json()
                return service["service"]["id"]
            else:
                print(f"❌ 서비스 생성 실패: {response.text}")
        except Exception as e:
            print(f"❌ 서비스 생성 오류: {e}")
        
        return None
    
    def deploy_service(self, service_id: str) -> bool:
        """서비스 배포 트리거"""
        try:
            response = requests.post(
                f"{self.api_base}/services/{service_id}/deploys",
                headers=self.headers,
                json={"clearCache": "clear"}
            )
            
            if response.status_code == 201:
                deploy = response.json()
                print(f"✅ 배포 시작: {deploy['deploy']['id']}")
                return True
            else:
                print(f"❌ 배포 실패: {response.text}")
        except Exception as e:
            print(f"❌ 배포 오류: {e}")
        
        return False
    
    def wait_for_deployment(self, service_id: str, timeout: int = 600) -> bool:
        """배포 완료 대기"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = requests.get(
                    f"{self.api_base}/services/{service_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    service = response.json()["service"]
                    status = service.get("suspended", False)
                    
                    if not status:
                        print(f"✅ 배포 완료!")
                        print(f"🌐 URL: https://{service['name']}.onrender.com")
                        return True
                    
            except Exception as e:
                print(f"⚠️ 상태 확인 오류: {e}")
            
            print("⏳ 배포 진행 중...")
            time.sleep(30)
        
        return False
    
    def deploy(self):
        """전체 배포 프로세스"""
        print("🚀 Render 자동 배포 시작")
        print("=" * 50)
        
        if not self.api_key:
            print("❌ RENDER_API_KEY 환경 변수가 필요합니다!")
            print("💡 Render 대시보드에서 API Key를 생성하세요:")
            print("   https://dashboard.render.com/account/api-keys")
            return False
        
        # 1. 기존 서비스 확인
        print("🔍 기존 서비스 확인 중...")
        service_id = self.check_existing_service("sat-chat-api")
        
        # 2. 서비스 생성 또는 업데이트
        if not service_id:
            print("📦 새 서비스 생성 중...")
            service_id = self.create_service()
            if not service_id:
                print("❌ 서비스 생성 실패!")
                return False
        else:
            print(f"♻️ 기존 서비스 업데이트: {service_id}")
        
        # 3. 배포 시작
        print("🔄 배포 시작...")
        if not self.deploy_service(service_id):
            return False
        
        # 4. 배포 완료 대기
        print("⏳ 배포 완료 대기 중 (최대 10분)...")
        if self.wait_for_deployment(service_id):
            print("\n✅ 배포 성공!")
            print(f"🌐 앱 URL: https://sat-chat-api.onrender.com")
            print(f"📊 상태 확인: https://sat-chat-api.onrender.com/health")
            return True
        else:
            print("❌ 배포 타임아웃!")
            return False

def main():
    """메인 실행 함수"""
    
    # Render CLI 대신 API 직접 사용
    print("🤖 SatChat Render 자동 배포 스크립트")
    print("=" * 50)
    
    # API 키 확인
    if not os.environ.get("RENDER_API_KEY"):
        print("\n⚠️ Render API Key가 없습니다!")
        print("다음 단계를 따라주세요:")
        print("\n1. Render 대시보드 접속: https://dashboard.render.com")
        print("2. Account Settings → API Keys")
        print("3. 'Create API Key' 클릭")
        print("4. 생성된 키를 복사")
        print("\n그 다음 아래 명령 실행:")
        print("export RENDER_API_KEY='your-api-key-here'")
        print("python3 auto_deploy_render.py")
        return
    
    deployer = RenderAutoDeployer()
    deployer.deploy()

if __name__ == "__main__":
    main()