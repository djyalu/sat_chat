/**
 * Simple Integration Test
 * 기본적인 API 통합 테스트
 */

const request = require('supertest');
const app = require('../../src/app');
const { setupTestDatabase, teardownTestDatabase } = require('../fixtures/database');

describe('Basic API Integration Tests', () => {
  beforeAll(async () => {
    await setupTestDatabase();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  describe('Health Check', () => {
    it('헬스체크 엔드포인트가 작동해야 함', async () => {
      const response = await request(app)
        .get('/health')
        .expect(200);

      expect(response.body).toHaveProperty('status', 'healthy');
      expect(response.body).toHaveProperty('timestamp');
    });
  });

  describe('Authentication API', () => {
    it('새로운 사용자를 등록할 수 있어야 함', async () => {
      const userData = {
        username: 'newuser',
        email: 'newuser@example.com',
        password: 'SecurePass123!',
        displayName: 'New User'
      };

      const response = await request(app)
        .post('/api/v1/auth/register')
        .send(userData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('user');
      expect(response.body.data).toHaveProperty('token');
      expect(response.body.data.user.email).toBe(userData.email);
      expect(response.body.data.user.password).toBeUndefined();
    });

    it('중복된 이메일로 등록할 수 없어야 함', async () => {
      const userData = {
        username: 'duplicate',
        email: 'test@example.com', // 이미 존재하는 이메일
        password: 'SecurePass123!'
      };

      const response = await request(app)
        .post('/api/v1/auth/register')
        .send(userData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('Email already registered');
    });

    it('약한 비밀번호로 등록할 수 없어야 함', async () => {
      const userData = {
        username: 'weakpass',
        email: 'weak@example.com',
        password: '123' // 약한 비밀번호
      };

      const response = await request(app)
        .post('/api/v1/auth/register')
        .send(userData)
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('Password does not meet requirements');
    });

    it('올바른 자격증명으로 로그인할 수 있어야 함', async () => {
      // 먼저 사용자 등록
      const userData = {
        username: 'logintest',
        email: 'login@example.com',
        password: 'SecurePass123!'
      };

      await request(app)
        .post('/api/v1/auth/register')
        .send(userData);

      // 로그인 시도
      const response = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: userData.email,
          password: userData.password
        })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data).toHaveProperty('token');
      expect(response.body.data).toHaveProperty('refreshToken');
      expect(response.body.data.user.email).toBe(userData.email);
    });

    it('잘못된 비밀번호로 로그인할 수 없어야 함', async () => {
      const response = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: 'test@example.com',
          password: 'WrongPassword123!'
        })
        .expect(401);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('Invalid credentials');
    });

    it('존재하지 않는 사용자로 로그인할 수 없어야 함', async () => {
      const response = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: 'nonexistent@example.com',
          password: 'Password123!'
        })
        .expect(401);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('User not found');
    });
  });

  describe('Error Handling', () => {
    it('잘못된 JSON 형식을 처리해야 함', async () => {
      const response = await request(app)
        .post('/api/v1/auth/register')
        .send('invalid json')
        .set('Content-Type', 'application/json')
        .expect(400);

      expect(response.body.success).toBe(false);
    });

    it('빈 요청 본문을 처리해야 함', async () => {
      const response = await request(app)
        .post('/api/v1/auth/register')
        .send({})
        .expect(400);

      expect(response.body.success).toBe(false);
    });
  });
});