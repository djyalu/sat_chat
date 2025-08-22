/**
 * Test Data Fixtures
 * 테스트용 데이터 생성 헬퍼
 */

const User = require('../../src/models/User');

let userCounter = 0;
let chatRoomCounter = 0;

async function createTestUser(overrides = {}) {
  userCounter++;
  const userData = {
    username: `testuser${userCounter}`,
    email: overrides.email || `test${userCounter}@example.com`,
    password: 'TestPassword123!',
    displayName: `Test User ${userCounter}`,
    ...overrides
  };

  // 비밀번호 해싱 시뮬레이션
  const bcrypt = require('bcryptjs');
  userData.password = await bcrypt.hash(userData.password, 10);

  return User.create(userData);
}

async function createTestChatRoom(overrides = {}) {
  chatRoomCounter++;
  return {
    id: `chat_${chatRoomCounter}`,
    name: overrides.name || `Test Room ${chatRoomCounter}`,
    type: overrides.type || 'group',
    description: overrides.description || 'Test chat room',
    isPrivate: overrides.isPrivate || false,
    creatorId: overrides.creatorId || `user_${userCounter}`,
    members: overrides.members || [],
    createdAt: new Date().toISOString()
  };
}

module.exports = {
  createTestUser,
  createTestChatRoom
};