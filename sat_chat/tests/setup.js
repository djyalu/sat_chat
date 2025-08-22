/**
 * Jest Test Setup
 * 테스트 실행 전 환경 설정
 */

// 환경 변수 설정
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret';
process.env.JWT_REFRESH_SECRET = 'test-refresh-secret';

// 전역 테스트 헬퍼
global.testHelpers = {
  generateToken: () => 'test-token-123',
  generateUserId: () => `user_${Date.now()}`,
  generateChatId: () => `chat_${Date.now()}`
};

// 테스트 타임아웃 설정
jest.setTimeout(10000);

// Mock 설정
jest.mock('socket.io-client', () => {
  return jest.fn().mockImplementation(() => ({
    on: jest.fn(),
    emit: jest.fn(),
    disconnect: jest.fn(),
    connected: true
  }));
});

// 콘솔 경고 무시 (테스트 출력 정리)
global.console = {
  ...console,
  error: jest.fn(),
  warn: jest.fn()
};