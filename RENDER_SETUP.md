# Render 수동 배포 설정 가이드

Render의 자동 감지 시스템이 render.yaml을 무시하고 Poetry를 강제 사용하므로, 웹 대시보드에서 수동 설정이 필요합니다.

## 🎯 Render 대시보드 설정

### 1. 서비스 생성/수정
1. https://dashboard.render.com/ 접속
2. "sat-chat-api" 서비스 선택 또는 새로 생성
3. GitHub 저장소: `https://github.com/djyalu/sat_chat`

### 2. 빌드 & 배포 설정

**Build Command**:
```bash
pip install --upgrade pip && pip install -r requirements.txt
```

**Start Command**:
```bash
python -m uvicorn real_sentinel_api:app --host 0.0.0.0 --port $PORT
```

### 3. 환경 변수 설정
- `PYTHON_VERSION`: `3.11`
- `SENTINEL_HUB_CLIENT_ID`: (선택적 - 없어도 데모 모드로 작동)
- `SENTINEL_HUB_CLIENT_SECRET`: (선택적 - 없어도 데모 모드로 작동)

### 4. 런타임 설정
- **Runtime**: Python
- **Plan**: Free
- **Auto-Deploy**: Enabled (GitHub push 시 자동 배포)

## 🧪 테스트 앱 배포 (권장)

복잡한 SatChat 대신 간단한 테스트 앱으로 먼저 검증:

**테스트 앱 Start Command**:
```bash
python simple_test_app.py
```

**테스트 앱 Build Command**:
```bash
pip install -r requirements-minimal.txt
```

## 📊 배포 후 테스트 URL
- Root: https://sat-chat-api.onrender.com/
- Health: https://sat-chat-api.onrender.com/health
- Region: https://sat-chat-api.onrender.com/region/west_sea

## ⚠️ 주의사항
1. Poetry 감지를 완전히 비활성화할 수 없음
2. render.yaml이 무시됨 (Render 플랫폼 제한)
3. 웹 대시보드에서만 올바른 설정 가능
4. 첫 배포 후에는 GitHub 푸시로 자동 배포됨

## ✅ 로컬 환경 완전 작동 중
- http://localhost:8002/ (메인 SatChat API)
- http://localhost:8010/ (SimpleApp)
- http://localhost:8011/ (기본 앱)

모든 로컬 서비스는 정상 작동하므로 코드에는 문제가 없습니다.