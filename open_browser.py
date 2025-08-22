#!/usr/bin/env python3
"""
브라우저 자동 실행 스크립트
SatChat 무료 고해상도 해양 폐기물 모니터링 시스템
"""

import webbrowser
import time
import requests
import sys

def check_server(url, timeout=10):
    """서버가 실행 중인지 확인"""
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                return True
        except:
            pass
        time.sleep(1)
    return False

def main():
    print("🌊 SatChat 무료 고해상도 해양 폐기물 모니터링 시스템")
    print("=" * 50)
    
    # 서버 확인
    web_url = "http://localhost:8888/real_data.html"
    api_url = "http://localhost:8002"
    
    print("📡 서버 상태 확인 중...")
    
    if check_server("http://localhost:8888"):
        print("✅ 웹 서버: 정상 작동")
    else:
        print("❌ 웹 서버: 오프라인")
        return
        
    if check_server(api_url):
        print("✅ API 서버: 정상 작동")
    else:
        print("⚠️ API 서버: 오프라인 (일부 기능 제한)")
    
    print(f"🚀 브라우저에서 열기: {web_url}")
    
    # 브라우저 열기
    try:
        webbrowser.open(web_url)
        print("✅ 브라우저가 열렸습니다!")
    except Exception as e:
        print(f"❌ 브라우저 열기 실패: {e}")
        print(f"수동으로 다음 주소를 브라우저에 입력하세요: {web_url}")
    
    print("\n🆓 무료 향상 기능 테스트 방법:")
    print("1. 지역 선택 (서해, 남해, 동해, 부산항, 인천항)")  
    print("2. 무료 향상 옵션 체크:")
    print("   - Multi-Temporal: 다중 시기 합성")
    print("   - Pan-Sharpening: 해상도 2배 향상")
    print("   - Korean-Optimized: 한국 최적화 FDI")
    print("3. '분석 시작' 버튼 클릭")
    print("4. 6가지 분석 결과 확인 (RGB, NDVI, NDWI, 수심, 클로로필, 히트맵)")

if __name__ == "__main__":
    main()