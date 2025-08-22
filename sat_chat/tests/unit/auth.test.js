/**
 * Authentication Service Unit Tests
 * 인증 서비스의 핵심 기능을 테스트합니다
 */

const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { AuthService } = require('../../src/services/auth.service');
const User = require('../../src/models/User');

// Mock dependencies
jest.mock('../../src/models/User', () => ({
  findOne: jest.fn(),
  create: jest.fn(),
  findById: jest.fn(),
  clearAll: jest.fn()
}));
jest.mock('bcryptjs');
jest.mock('jsonwebtoken');

describe('AuthService', () => {
  let authService;

  beforeEach(() => {
    authService = new AuthService();
    jest.clearAllMocks();
  });

  describe('회원가입 (Registration)', () => {
    it('새로운 사용자를 성공적으로 생성해야 함', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: 'SecurePass123!'
      };

      const hashedPassword = 'hashed_password';
      const savedUser = { 
        id: 'user_123', 
        ...userData, 
        password: hashedPassword,
        toObject: jest.fn().mockReturnValue({
          id: 'user_123',
          username: userData.username,
          email: userData.email,
          password: hashedPassword
        })
      };

      bcrypt.hash.mockResolvedValue(hashedPassword);
      User.findOne.mockResolvedValue(null);
      User.create.mockResolvedValue(savedUser);

      const result = await authService.register(userData);

      expect(bcrypt.hash).toHaveBeenCalledWith(userData.password, 10);
      expect(User.create).toHaveBeenCalledWith({
        ...userData,
        password: hashedPassword
      });
      expect(result.user.password).toBeUndefined();
    });

    it('이미 존재하는 이메일로 가입 시 에러를 발생시켜야 함', async () => {
      const userData = {
        username: 'existinguser',
        email: 'existing@example.com',
        password: 'SecurePass123!'
      };

      User.findOne.mockResolvedValue({ email: userData.email });

      await expect(authService.register(userData))
        .rejects.toThrow('Email already registered');
    });

    it('약한 비밀번호는 거부해야 함', async () => {
      const userData = {
        username: 'testuser',
        email: 'test@example.com',
        password: '123' // 너무 짧은 비밀번호
      };

      await expect(authService.register(userData))
        .rejects.toThrow('Password does not meet requirements');
    });
  });

  describe('로그인 (Login)', () => {
    it('올바른 자격증명으로 로그인 성공해야 함', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'password123'
      };

      const user = {
        id: 'user_123',
        email: credentials.email,
        password: 'hashed_password'
      };

      const token = 'jwt_token';

      User.findOne.mockResolvedValue(user);
      bcrypt.compare.mockResolvedValue(true);
      jwt.sign.mockReturnValue(token);

      const result = await authService.login(credentials);

      expect(User.findOne).toHaveBeenCalledWith({ email: credentials.email });
      expect(bcrypt.compare).toHaveBeenCalledWith(credentials.password, user.password);
      expect(result.token).toBe(token);
    });

    it('잘못된 비밀번호로 로그인 실패해야 함', async () => {
      const credentials = {
        email: 'test@example.com',
        password: 'wrongpassword'
      };

      User.findOne.mockResolvedValue({ 
        email: credentials.email,
        password: 'hashed_password' 
      });
      bcrypt.compare.mockResolvedValue(false);

      await expect(authService.login(credentials))
        .rejects.toThrow('Invalid credentials');
    });

    it('존재하지 않는 사용자로 로그인 실패해야 함', async () => {
      User.findOne.mockResolvedValue(null);

      await expect(authService.login({
        email: 'nonexistent@example.com',
        password: 'password'
      })).rejects.toThrow('User not found');
    });
  });

  describe('토큰 검증 (Token Verification)', () => {
    it('유효한 JWT 토큰을 검증해야 함', () => {
      const token = 'valid_token';
      const decoded = { userId: 'user_123', email: 'test@example.com' };

      jwt.verify.mockReturnValue(decoded);

      const result = authService.verifyToken(token);

      expect(jwt.verify).toHaveBeenCalledWith(token, process.env.JWT_SECRET);
      expect(result).toEqual(decoded);
    });

    it('만료된 토큰을 거부해야 함', () => {
      const token = 'expired_token';
      
      jwt.verify.mockImplementation(() => {
        throw new Error('Token expired');
      });

      expect(() => authService.verifyToken(token))
        .toThrow('Token expired');
    });
  });

  describe('비밀번호 재설정 (Password Reset)', () => {
    it('비밀번호 재설정 토큰을 생성해야 함', async () => {
      const email = 'test@example.com';
      const user = { id: 'user_123', email };
      const resetToken = 'reset_token_123';

      User.findOne.mockResolvedValue(user);
      jwt.sign.mockReturnValue(resetToken);

      const result = await authService.generateResetToken(email);

      expect(result.token).toBe(resetToken);
      expect(jwt.sign).toHaveBeenCalledWith(
        { userId: user.id, type: 'reset' },
        expect.any(String),
        { expiresIn: '1h' }
      );
    });
  });
});