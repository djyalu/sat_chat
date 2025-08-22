# 🌐 GitHub Pages 배포 가이드

SatChat 해양 폐기물 모니터링 시스템을 GitHub Pages로 배포하는 방법입니다.

## 📋 배포 현황

🔗 **라이브 데모**: https://djyalu.github.io/sat_chat/

### 배포된 페이지들
- **메인 페이지**: https://djyalu.github.io/sat_chat/ (React 기반 대시보드)
- **모니터링 대시보드**: https://djyalu.github.io/sat_chat/dashboard/ (실시간 모니터링)
- **API 문서**: https://djyalu.github.io/sat_chat/api/ (API 가이드)
- **예제 페이지**: https://djyalu.github.io/sat_chat/examples/ (데모 및 예제)

## 🚀 자동 배포 설정

GitHub Actions를 통한 자동 배포가 설정되어 있습니다.

### 배포 트리거
- `main` 브랜치에 push할 때마다 자동 배포
- 수동 배포 가능 (Actions 탭에서 "Deploy to GitHub Pages" 실행)

### 배포 파일 구조
```
_site/
├── index.html                    # 메인 React 대시보드
├── dashboard/
│   └── index.html               # 모니터링 대시보드
├── api/
│   └── index.html               # API 문서
└── examples/
    └── index.html               # 예제 및 데모
```

## 🔧 로컬에서 GitHub Pages 테스트

```bash
# 1. 저장소 클론
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat

# 2. 간단한 HTTP 서버 실행
python -m http.server 8080

# 3. 브라우저에서 확인
# http://localhost:8080
```

## 📱 기능별 페이지 설명

### 1. 메인 페이지 (`index.html`)
- **React 기반** 인터랙티브 대시보드
- **데모 모드** 지원 (API 서버 없이도 동작)
- **실시간 통계** 표시
- **지도 기반 탐지** 결과 시각화
- **반응형 디자인** (모바일 지원)

**주요 기능:**
- 📊 실시간 대시보드
- 🗺️ 실시간 모니터링 (지도)
- 📈 데이터 분석
- 🔔 알림 센터

### 2. 모니터링 대시보드 (`dashboard/index.html`)
- **순수 HTML/CSS/JS** 구현
- **Chart.js** 기반 차트
- **실시간 업데이트** 시뮬레이션
- **애니메이션 효과** 적용

**주요 특징:**
- 🎯 총 탐지 건수
- 🚨 활성 알림
- 🌊 모니터링 면적
- 📊 탐지 정확도

### 3. API 문서 (`api/index.html`)
- **RESTful API** 엔드포인트 설명
- **사용법 가이드**
- **예제 코드** 제공

### 4. 예제 페이지 (`examples/index.html`)
- **Python 스크립트** 실행 가이드
- **데모 결과** 표시
- **시작 가이드** 제공

## 🔄 데모 데이터 모드

GitHub Pages에서는 백엔드 API가 없으므로 **데모 데이터 모드**로 동작합니다:

```javascript
// API_URL이 'demo'일 때 시뮬레이션 데이터 사용
const API_URL = 'demo'; // Demo mode for GitHub Pages

// 데모 데이터 예시
if (endpoint === '/api/v1/statistics') {
    return {
        total_detections: 1247,
        active_alerts: 3,
        monitored_area: 2450,
        detection_rate: 94.2
    };
}
```

## 🛠️ 배포 커스터마이징

### 1. 새로운 페이지 추가
`.github/workflows/deploy-pages.yml` 파일에서 빌드 단계 수정:

```yaml
- name: Create new page
  run: |
    cat > _site/new-page/index.html << 'EOF'
    <!-- 새로운 페이지 내용 -->
    EOF
```

### 2. 도메인 설정
GitHub Pages 설정에서 커스텀 도메인 설정 가능:
- Repository → Settings → Pages → Custom domain

### 3. HTTPS 강제 적용
GitHub Pages 설정에서 "Enforce HTTPS" 활성화 권장

## 📊 성능 최적화

### 현재 최적화 적용 사항:
- ✅ **CDN 사용**: TailwindCSS, Chart.js, Leaflet
- ✅ **압축 CSS**: 인라인 스타일 최적화
- ✅ **지연 로딩**: 이미지 및 차트 최적화
- ✅ **캐싱**: 브라우저 캐싱 활용
- ✅ **반응형 디자인**: 모바일 최적화

### 추가 최적화 가능사항:
- 🔄 Service Worker 적용
- 🔄 Progressive Web App (PWA) 변환
- 🔄 이미지 최적화 (WebP 포맷)

## 🔐 보안 고려사항

### GitHub Pages 기본 보안:
- ✅ **HTTPS 기본 지원**
- ✅ **DDoS 보호** (GitHub 인프라)
- ✅ **정적 파일** 만 서빙 (서버 취약점 없음)

### 추가 보안 권장사항:
- 🔒 **CSP 헤더** 설정 (Content Security Policy)
- 🔒 **XSS 방지** (사용자 입력 검증)
- 🔒 **HTTPS 리다이렉트** 강제

## 🚀 배포 상태 확인

### 성공적인 배포 확인 방법:
1. **Actions 탭** 확인 - ✅ 초록색 체크
2. **Pages 설정** 확인 - URL 활성화 상태
3. **실제 페이지** 접속 테스트

### 배포 실패 시 해결방법:
1. **Actions 로그** 확인
2. **YAML 문법** 검증
3. **파일 경로** 확인
4. **권한 설정** 확인 (Settings → Pages → Source: GitHub Actions)

## 📞 지원 및 문의

- **GitHub Issues**: [https://github.com/djyalu/sat_chat/issues](https://github.com/djyalu/sat_chat/issues)
- **프로젝트 위키**: [https://github.com/djyalu/sat_chat/wiki](https://github.com/djyalu/sat_chat/wiki)
- **라이센스**: MIT License

---

*이 문서는 SatChat 프로젝트의 GitHub Pages 배포를 위한 가이드입니다.*