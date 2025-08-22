# 🚀 SatChat 로컬 테스트 가이드

## 🎯 빠른 시작

### Windows 사용자
```bash
# 더블클릭으로 실행
start_local.bat
```

### Linux/Mac 사용자
```bash
# 터미널에서 실행
./start_local.sh
```

### 수동 실행
```bash
# 백엔드 서버 시작
python test_app.py

# 브라우저에서 열기
# index.html 파일을 더블클릭
```

## 현재 상태

### ✅ 백엔드 API 서버 (실행 중)
- **URL**: http://localhost:8000
- **상태**: 정상 작동 중
- **테스트 엔드포인트**:
  - http://localhost:8000/ - 서버 상태
  - http://localhost:8000/api/v1/detections - 탐지 데이터
  - http://localhost:8000/api/v1/statistics - 통계
  - http://localhost:8000/api/v1/alerts - 알림

### 🎨 프론트엔드 옵션

#### 옵션 1: index.html (추천) ⭐
- **완전한 React 스타일 UI**
- **Node.js 없이 실행 가능**
- **모든 기능 포함**
- 파일을 브라우저에서 직접 열기

#### 옵션 2: test.html
- **간단한 API 테스터**
- **버튼 클릭으로 테스트**
- 디버깅 및 개발용

### 📁 프로젝트 구조
```
sat_chat/
├── index.html         # 메인 UI (Node.js 불필요) ⭐
├── test.html          # API 테스터
├── test_app.py        # 백엔드 서버
├── start_local.sh     # Linux/Mac 시작 스크립트
├── start_local.bat    # Windows 시작 스크립트
├── frontend/          # React 소스 (참고용)
└── venv/              # Python 가상환경
```

---

## 🧪 로컬 테스트 방법

### 방법 1: 브라우저에서 API 직접 테스트

1. **브라우저 열기**
2. **다음 URL 접속**:
   ```
   http://localhost:8000/
   http://localhost:8000/api/v1/detections
   http://localhost:8000/api/v1/statistics
   ```

3. **예상 결과**:
   - JSON 형식의 데이터 표시
   - 한국 해역 폐기물 탐지 모의 데이터

### 방법 2: curl 명령어로 테스트

```bash
# 서버 상태 확인
curl http://localhost:8000/

# 탐지 데이터 조회
curl http://localhost:8000/api/v1/detections

# 통계 조회
curl http://localhost:8000/api/v1/statistics

# 알림 조회
curl http://localhost:8000/api/v1/alerts
```

### 방법 3: 간단한 HTML 테스트 페이지

1. 아래 HTML 파일을 `test.html`로 저장
2. 브라우저에서 열기

```html
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>SatChat API 테스트</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        button { margin: 10px; padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #45a049; }
        #result { margin-top: 20px; padding: 10px; background: #f5f5f5; border-radius: 4px; }
        pre { white-space: pre-wrap; }
    </style>
</head>
<body>
    <h1>🛰️ SatChat API 테스트</h1>
    
    <button onclick="testAPI('/')">서버 상태</button>
    <button onclick="testAPI('/api/v1/detections')">탐지 데이터</button>
    <button onclick="testAPI('/api/v1/statistics')">통계</button>
    <button onclick="testAPI('/api/v1/alerts')">알림</button>
    
    <div id="result"></div>

    <script>
        async function testAPI(endpoint) {
            const resultDiv = document.getElementById('result');
            resultDiv.innerHTML = '로딩 중...';
            
            try {
                const response = await fetch('http://localhost:8000' + endpoint);
                const data = await response.json();
                resultDiv.innerHTML = `<h3>${endpoint}</h3><pre>${JSON.stringify(data, null, 2)}</pre>`;
            } catch (error) {
                resultDiv.innerHTML = `<h3>오류</h3><pre>${error.message}</pre>`;
            }
        }
    </script>
</body>
</html>
```

---

## 🎨 프론트엔드 실행 (선택사항)

### Node.js 의존성 문제 해결

현재 React 앱에 의존성 충돌이 있습니다. 다음 방법으로 해결할 수 있습니다:

```bash
# frontend 디렉토리로 이동
cd frontend

# node_modules 삭제 및 재설치
rm -rf node_modules package-lock.json
npm install

# 개발 서버 실행
npm start
```

### 대안: 정적 빌드 사용

```bash
cd frontend
npm run build
# build 폴더가 생성되면, 웹 서버로 제공
npx serve -s build
```

---

## 📊 테스트 시나리오

### 1. 대시보드 데이터 확인
- 통계 API 호출 → 대시보드 카드에 표시
- 총 탐지 건수: 142건
- 활성 알림: 7개
- 모니터링 면적: 25,000 km²
- 탐지 정확도: 89.3%

### 2. 실시간 모니터링 시뮬레이션
- 탐지 데이터 API → 지도에 마커 표시
- 서해, 남해, 동해 각 지역별 데이터
- 폐기물 유형: 플라스틱, 어망, 부표 등

### 3. 알림 시스템 테스트
- 알림 API → 우선순위별 알림 표시
- Critical, Warning, Info 레벨 구분

---

## 🔧 문제 해결

### 포트 충돌 (8000번 포트 사용 중)
```bash
# 사용 중인 프로세스 확인
lsof -i :8000

# 프로세스 종료
kill -9 [PID]
```

### CORS 오류
백엔드 서버가 CORS를 허용하도록 설정되어 있습니다.
프론트엔드는 http://localhost:3000 에서 실행되어야 합니다.

### Python 가상환경 활성화
```bash
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

---

## 📝 다음 단계

1. **Sentinel Hub OAuth 설정**
   - https://apps.sentinel-hub.com/dashboard/ 로그인
   - OAuth 클라이언트 생성
   - .env 파일에 자격증명 추가

2. **실제 위성 데이터 연동**
   - Sentinel-2 데이터 수집
   - BYOC 컬렉션 활용
   - 실시간 모니터링 구현

3. **ML 모델 통합**
   - 폐기물 탐지 모델 학습
   - 실시간 추론 파이프라인
   - 정확도 향상

---

## 📞 지원

문제가 있으신가요?
- GitHub Issues: https://github.com/djyalu/sat_chat/issues
- Email: go41@naver.com

**Happy Testing! 🎉**