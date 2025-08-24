#!/bin/bash
# SatChat 원클릭 자동 배포 스크립트

echo "🚀 SatChat 원클릭 자동 배포"
echo "========================================"

# Git 상태 확인
echo "📝 Git 상태 확인 중..."
if [[ -n $(git status --porcelain) ]]; then
    echo "✅ 변경 사항 발견"
    
    # 자동 커밋
    echo "📦 자동 커밋 중..."
    git add -A
    git commit -m "Auto deployment - $(date '+%Y-%m-%d %H:%M:%S')

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
    
    # GitHub 푸시
    echo "🔄 GitHub 푸시 중..."
    git push origin main
    echo "✅ 푸시 완료!"
else
    echo "ℹ️ 변경 사항 없음"
fi

# Render 배포 URL 생성
DEPLOY_URL="https://render.com/deploy?repo=https://github.com/djyalu/sat_chat"

echo ""
echo "========================================"
echo "🌐 Render 자동 배포 준비 완료!"
echo "========================================"
echo ""
echo "다음 URL을 브라우저에서 열어주세요:"
echo "$DEPLOY_URL"
echo ""
echo "또는 아래 명령 실행:"
echo "open '$DEPLOY_URL'  # macOS"
echo "xdg-open '$DEPLOY_URL'  # Linux"
echo "start '$DEPLOY_URL'  # Windows"
echo ""
echo "📋 브라우저에서:"
echo "1. 'Connect GitHub' 클릭"
echo "2. 'Deploy' 클릭"
echo "3. 5분 대기"
echo ""
echo "✅ 완료!"