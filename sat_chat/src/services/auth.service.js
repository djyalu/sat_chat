/**
 * Authentication Service
 * 인증 관련 비즈니스 로직을 처리합니다
 */

const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

class AuthService {
  constructor() {
    this.JWT_SECRET = process.env.JWT_SECRET || 'test-secret';
    this.JWT_EXPIRES_IN = process.env.JWT_EXPIRES_IN || '7d';
  }

  /**
   * 사용자 등록
   */
  async register(userData) {
    const { username, email, password } = userData;

    // 비밀번호 강도 검증
    if (!this.validatePassword(password)) {
      throw new Error('Password does not meet requirements');
    }

    // 이메일 중복 검사 (실제로는 DB 조회)
    const User = require('../models/User');
    const existingUser = await User.findOne({ email });
    if (existingUser) {
      throw new Error('Email already registered');
    }

    // 비밀번호 해싱
    const hashedPassword = await bcrypt.hash(password, 10);

    // 사용자 생성
    const user = await User.create({
      username,
      email,
      password: hashedPassword
    });

    // 비밀번호 제거 후 반환
    const userObject = user.toObject();
    delete userObject.password;

    return {
      user: userObject,
      token: this.generateToken(user)
    };
  }

  /**
   * 사용자 로그인
   */
  async login(credentials) {
    const { email, password } = credentials;

    // 사용자 조회
    const User = require('../models/User');
    const user = await User.findOne({ email });
    
    if (!user) {
      throw new Error('User not found');
    }

    // 비밀번호 검증
    const isValidPassword = await bcrypt.compare(password, user.password);
    if (!isValidPassword) {
      throw new Error('Invalid credentials');
    }

    // 토큰 생성
    const token = this.generateToken(user);
    const refreshToken = this.generateRefreshToken(user);

    return {
      user: {
        id: user.id,
        email: user.email,
        username: user.username
      },
      token,
      refreshToken
    };
  }

  /**
   * JWT 토큰 생성
   */
  generateToken(user) {
    return jwt.sign(
      { 
        userId: user.id, 
        email: user.email 
      },
      this.JWT_SECRET,
      { expiresIn: this.JWT_EXPIRES_IN }
    );
  }

  /**
   * Refresh 토큰 생성
   */
  generateRefreshToken(user) {
    return jwt.sign(
      { 
        userId: user.id, 
        type: 'refresh' 
      },
      process.env.JWT_REFRESH_SECRET || 'refresh-secret',
      { expiresIn: '30d' }
    );
  }

  /**
   * 토큰 검증
   */
  verifyToken(token) {
    try {
      return jwt.verify(token, this.JWT_SECRET);
    } catch (error) {
      if (error.name === 'TokenExpiredError') {
        throw new Error('Token expired');
      }
      throw error;
    }
  }

  /**
   * 비밀번호 재설정 토큰 생성
   */
  async generateResetToken(email) {
    const User = require('../models/User');
    const user = await User.findOne({ email });
    
    if (!user) {
      throw new Error('User not found');
    }

    const resetToken = jwt.sign(
      { userId: user.id, type: 'reset' },
      this.JWT_SECRET,
      { expiresIn: '1h' }
    );

    return {
      token: resetToken,
      userId: user.id
    };
  }

  /**
   * 비밀번호 강도 검증
   */
  validatePassword(password) {
    // 최소 8자, 대소문자, 숫자, 특수문자 포함
    if (password.length < 8) return false;
    if (!/[A-Z]/.test(password)) return false;
    if (!/[a-z]/.test(password)) return false;
    if (!/[0-9]/.test(password)) return false;
    if (!/[!@#$%^&*]/.test(password)) return false;
    return true;
  }
}

module.exports = { AuthService };