/**
 * User Model
 * 사용자 데이터 모델 (간단한 Mock 구현)
 */

// In-memory storage for testing
const users = [];

class User {
  constructor(data) {
    this.id = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    this.username = data.username;
    this.email = data.email;
    this.password = data.password;
    this.displayName = data.displayName || data.username;
    this.createdAt = new Date().toISOString();
    this.updatedAt = new Date().toISOString();
  }

  static async findOne(query) {
    if (query.email) {
      return users.find(user => user.email === query.email);
    }
    if (query.id) {
      return users.find(user => user.id === query.id);
    }
    return null;
  }

  static async create(data) {
    const user = new User(data);
    users.push(user);
    return user;
  }

  static async findById(id) {
    return users.find(user => user.id === id);
  }

  toObject() {
    return {
      id: this.id,
      username: this.username,
      email: this.email,
      displayName: this.displayName,
      createdAt: this.createdAt,
      updatedAt: this.updatedAt,
      password: this.password
    };
  }

  static clearAll() {
    users.length = 0;
  }

  static getAll() {
    return users;
  }
}

module.exports = User;