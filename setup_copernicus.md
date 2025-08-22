# 🛰️ Copernicus Data Space 무료 계정 설정 가이드

## 1. 계정 생성 (무료)
1. **가입 사이트**: https://dataspace.copernicus.eu/
2. **"Register" 클릭** → 이메일 인증
3. **로그인 후**: https://shapps.dataspace.copernicus.eu/dashboard/

## 2. OAuth Client 생성
1. Dashboard → **User Settings** (좌측 메뉴)
2. **OAuth clients** 탭
3. **"+ Create new"** 클릭
4. 정보 입력:
   - **Name**: SatChat
   - **URL**: http://localhost:8000
   - **Grant Type**: Client Credentials 선택
5. **Create client** 클릭
6. **Client ID와 Client Secret 복사** (한 번만 표시됨!)

## 3. 환경 변수 업데이트
`.env` 파일에서:
```
SENTINEL_HUB_CLIENT_ID=새로운_client_id
SENTINEL_HUB_CLIENT_SECRET=새로운_secret
```

## 특징
- ✅ **완전 무료**: 신용카드 불필요
- 📊 **충분한 할당량**: 한국 해역 모니터링에 충분
- 🌍 **Sentinel-2 데이터**: 10m 해상도
- 🔄 **5일 주기**: 새로운 이미지