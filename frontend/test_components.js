// React 컴포넌트 테스트 스크립트
const React = require('react');

console.log('🧪 React 컴포넌트 테스트 시작');

// 기본 React 테스트
try {
  console.log('✅ React 버전:', React.version);
} catch (error) {
  console.error('❌ React 오류:', error.message);
}

// API 서비스 테스트
try {
  const api = require('./src/services/api.js');
  console.log('✅ API 서비스 로드 성공');
} catch (error) {
  console.error('❌ API 서비스 오류:', error.message);
}

// 컴포넌트 파일 존재 확인
const fs = require('fs');
const path = require('path');

const componentsToCheck = [
  'src/App.js',
  'src/components/Layout.js',
  'src/pages/Dashboard.js',
  'src/pages/Monitoring.js',
  'src/store/authStore.js'
];

componentsToCheck.forEach(file => {
  if (fs.existsSync(path.join(__dirname, file))) {
    console.log(`✅ ${file} 존재`);
  } else {
    console.log(`❌ ${file} 누락`);
  }
});

console.log('🎉 컴포넌트 테스트 완료');

module.exports = {};