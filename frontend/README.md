# SatChat Frontend

React 기반 해양 폐기물 모니터링 시스템 UI

## 기능

- 📊 **대시보드**: 실시간 통계 및 시각화
- 🗺️ **실시간 모니터링**: Leaflet 기반 지도 시각화
- 📈 **데이터 분석**: 트렌드 분석 및 예측
- 🔔 **알림 시스템**: 실시간 알림 관리
- ⚙️ **설정**: 시스템 구성 관리

## 기술 스택

- **React 18**: UI 프레임워크
- **Tailwind CSS**: 스타일링
- **React Router**: 라우팅
- **Leaflet**: 지도 시각화
- **Chart.js**: 차트 라이브러리
- **Zustand**: 상태 관리
- **Axios**: API 통신

## 시작하기

### 설치

```bash
npm install
```

### 개발 서버 실행

```bash
npm start
```

http://localhost:3000 에서 확인 가능

### 프로덕션 빌드

```bash
npm run build
```

## 프로젝트 구조

```
src/
├── components/     # 재사용 가능한 컴포넌트
├── pages/         # 페이지 컴포넌트
├── services/      # API 서비스
├── store/         # 상태 관리
├── App.js         # 메인 앱 컴포넌트
└── index.js       # 엔트리 포인트
```

## 주요 페이지

### 대시보드
- 주요 통계 카드
- 월별 탐지 추이
- 지역별 현황
- 최근 탐지 목록

### 실시간 모니터링
- 한국 해역 지도
- 실시간 탐지 마커
- 필터링 옵션
- 상세 정보 패널

### 데이터 분석
- 트렌드 차트
- 상관관계 분석
- 예측 모델 결과
- 데이터 테이블

## 환경 변수

`.env` 파일 생성:

```
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_MAPBOX_TOKEN=your_mapbox_token
```

## 개발 가이드

### 컴포넌트 생성

```jsx
import React from 'react';

const MyComponent = ({ prop1, prop2 }) => {
  return (
    <div className="card">
      {/* 컴포넌트 내용 */}
    </div>
  );
};

export default MyComponent;
```

### API 호출

```javascript
import { api } from '../services/api';

const fetchData = async () => {
  try {
    const response = await api.get('/endpoint');
    return response.data;
  } catch (error) {
    console.error('Error:', error);
  }
};
```

## 라이선스

© 2024 Telefix. All rights reserved.