#!/bin/bash

echo "🚀 SatChat 로컬 테스트 시작"
echo "================================"

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python 가상환경 확인
if [ -d "venv" ]; then
    echo -e "${GREEN}✓${NC} Python 가상환경 발견"
    source venv/bin/activate
else
    echo -e "${YELLOW}!${NC} 가상환경이 없습니다. 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    pip install fastapi uvicorn aiofiles
fi

# 백엔드 서버 확인
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo -e "${GREEN}✓${NC} 백엔드 서버가 이미 실행 중입니다 (포트 8000)"
else
    echo -e "${YELLOW}→${NC} 백엔드 서버 시작 중..."
    python test_app.py &
    sleep 2
fi

# 프론트엔드 안내
echo ""
echo -e "${GREEN}✅ 시스템 준비 완료!${NC}"
echo ""
echo "📋 테스트 방법:"
echo "1. 브라우저에서 다음 파일을 엽니다:"
echo "   → file:///mnt/d/projects/sat_chat/index.html"
echo ""
echo "2. 또는 간단한 HTTP 서버로 실행:"
echo "   python3 -m http.server 3000"
echo "   → http://localhost:3000"
echo ""
echo "API 서버: http://localhost:8000"
echo "API 문서: http://localhost:8000/docs"
echo ""
echo "종료: Ctrl+C"