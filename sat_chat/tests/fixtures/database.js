/**
 * Test Database Setup
 * 테스트 데이터베이스 설정 및 관리
 */

const User = require('../../src/models/User');

async function setupTestDatabase() {
  // 테스트 데이터베이스 초기화
  console.log('Setting up test database...');
  
  // 모든 데이터 초기화
  User.clearAll();
  
  // 기본 테스트 데이터 생성
  await User.create({
    username: 'testuser',
    email: 'test@example.com',
    password: '$2a$10$YourHashedPasswordHere', // bcrypt hashed 'TestPassword123!'
    displayName: 'Test User'
  });

  await User.create({
    username: 'user1',
    email: 'user1@example.com',
    password: '$2a$10$YourHashedPasswordHere',
    displayName: 'User One'
  });

  await User.create({
    username: 'user2',
    email: 'user2@example.com',
    password: '$2a$10$YourHashedPasswordHere',
    displayName: 'User Two'
  });
}

async function teardownTestDatabase() {
  // 테스트 데이터베이스 정리
  console.log('Cleaning up test database...');
  User.clearAll();
}

module.exports = {
  setupTestDatabase,
  teardownTestDatabase
};