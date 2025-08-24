#!/bin/bash

echo "🚀 Render 배포 모니터링 시작..."
echo "================================"

for i in {1..10}; do
    echo -e "\n테스트 $i/10 ($(date +%H:%M:%S))"
    
    # HTTP 응답 코드 확인
    response=$(curl -s -o /dev/null -w "%{http_code}" https://sat-chat-api.onrender.com/)
    
    if [ "$response" = "200" ]; then
        echo "✅ 배포 성공! (HTTP $response)"
        echo -e "\n📡 API 응답:"
        curl -s https://sat-chat-api.onrender.com/ | python3 -m json.tool
        echo -e "\n🎉 서비스가 정상적으로 실행 중입니다!"
        break
    else
        echo "⏳ 아직 배포 중... (HTTP $response)"
        
        # Render 라우팅 상태 확인
        routing=$(curl -s -I https://sat-chat-api.onrender.com/ | grep -i "x-render-routing" | cut -d' ' -f2)
        if [ ! -z "$routing" ]; then
            echo "   Render 상태: $routing"
        fi
        
        if [ $i -lt 10 ]; then
            echo "   30초 후 재시도..."
            sleep 30
        else
            echo "❌ 배포 타임아웃. Render 대시보드를 확인하세요."
        fi
    fi
done
