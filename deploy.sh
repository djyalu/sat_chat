#!/bin/bash
# SatChat 완전 자동 배포 스크립트 (Git Push = Render Deploy)

echo "🚀 SatChat 완전 자동 배포 시작"
echo "========================================"

# Git 상태 확인
echo "📝 Git 상태 확인 중..."
if [[ -n $(git status --porcelain) ]]; then
    echo "✅ 변경 사항 발견"
    
    # 자동 커밋
    echo "📦 자동 커밋 중..."
    git add -A
    COMMIT_MSG="Auto deployment - $(date '+%Y-%m-%d %H:%M:%S')

🤖 Generated with Claude Code

Co-Authored-By: Claude <noreply@anthropic.com>"
    git commit -m "$COMMIT_MSG"
    
    # GitHub 푸시 (이것이 Render 자동 배포를 트리거)
    echo "🔄 GitHub 푸시 중 (Render 자동 배포 트리거)..."
    git push origin main
    echo "✅ 푸시 완료! Render 배포가 자동으로 시작됩니다."
    
    echo ""
    echo "========================================"
    echo "🎯 Render 자동 배포 시작됨!"
    echo "========================================"
    echo ""
    echo "📊 배포 상태 확인:"
    echo "  https://dashboard.render.com/"
    echo ""
    echo "⏱️ 예상 시간: 3-5분"
    echo ""
    echo "🌐 배포 완료 후 접속:"
    echo "  https://sat-chat.onrender.com"
    echo "  https://sat-chat-api.onrender.com"
    echo ""
    
    # 배포 상태 모니터링 옵션
    echo "배포 상태를 모니터링 하시겠습니까? (y/n): "
    read -t 5 monitor
    if [[ "$monitor" == "y" ]]; then
        echo "🔍 배포 모니터링 시작..."
        python3 monitor_deployment.py
    fi
else
    echo "ℹ️ 변경 사항 없음"
    echo ""
    echo "💡 Tip: 파일을 수정한 후 다시 실행하세요."
fi

echo ""
echo "✅ 자동 배포 프로세스 완료!"