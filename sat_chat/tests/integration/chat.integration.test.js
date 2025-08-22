/**
 * Chat API Integration Tests
 * 채팅 API의 전체 흐름을 테스트합니다
 */

const request = require('supertest');
const app = require('../../src/app');
const { setupTestDatabase, teardownTestDatabase } = require('../fixtures/database');
const { createTestUser, createTestChatRoom } = require('../fixtures/testData');

describe('Chat API Integration Tests', () => {
  let authToken;
  let userId;
  let chatRoomId;

  beforeAll(async () => {
    await setupTestDatabase();
  });

  afterAll(async () => {
    await teardownTestDatabase();
  });

  describe('채팅방 관리 (Chat Room Management)', () => {
    beforeEach(async () => {
      // 테스트 사용자 생성 및 로그인
      const user = await createTestUser();
      userId = user.id;
      
      const loginResponse = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: user.email,
          password: 'TestPassword123!'
        });
      
      authToken = loginResponse.body.data.token;
    });

    it('새로운 채팅방을 생성할 수 있어야 함', async () => {
      const chatRoomData = {
        name: 'Test Chat Room',
        description: 'Integration test room',
        type: 'group',
        isPrivate: false
      };

      const response = await request(app)
        .post('/api/v1/chats')
        .set('Authorization', `Bearer ${authToken}`)
        .send(chatRoomData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data.chat).toMatchObject({
        name: chatRoomData.name,
        description: chatRoomData.description,
        type: chatRoomData.type
      });
      
      chatRoomId = response.body.data.chat.id;
    });

    it('채팅방 목록을 조회할 수 있어야 함', async () => {
      // 여러 채팅방 생성
      await createTestChatRoom({ name: 'Room 1', creatorId: userId });
      await createTestChatRoom({ name: 'Room 2', creatorId: userId });
      await createTestChatRoom({ name: 'Room 3', creatorId: userId });

      const response = await request(app)
        .get('/api/v1/chats')
        .set('Authorization', `Bearer ${authToken}`)
        .query({ page: 1, limit: 10 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.chats).toBeInstanceOf(Array);
      expect(response.body.data.chats.length).toBeGreaterThanOrEqual(3);
      expect(response.body.data.pagination).toBeDefined();
    });

    it('특정 채팅방에 참여할 수 있어야 함', async () => {
      const chatRoom = await createTestChatRoom({ 
        name: 'Public Room',
        isPrivate: false 
      });

      const response = await request(app)
        .post(`/api/v1/chats/${chatRoom.id}/join`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.message).toContain('joined');
    });

    it('비공개 채팅방에 초대 없이 참여할 수 없어야 함', async () => {
      const privateChatRoom = await createTestChatRoom({ 
        name: 'Private Room',
        isPrivate: true 
      });

      const response = await request(app)
        .post(`/api/v1/chats/${privateChatRoom.id}/join`)
        .set('Authorization', `Bearer ${authToken}`)
        .expect(403);

      expect(response.body.success).toBe(false);
      expect(response.body.error.code).toBe('PERMISSION_DENIED');
    });
  });

  describe('메시지 전송 (Message Sending)', () => {
    beforeEach(async () => {
      const user = await createTestUser();
      const loginResponse = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: user.email,
          password: 'TestPassword123!'
        });
      
      authToken = loginResponse.body.data.token;
      
      const chatRoom = await createTestChatRoom({
        name: 'Message Test Room',
        creatorId: user.id
      });
      chatRoomId = chatRoom.id;
    });

    it('텍스트 메시지를 전송할 수 있어야 함', async () => {
      const messageData = {
        content: 'Hello, this is a test message!',
        type: 'text'
      };

      const response = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/messages`)
        .set('Authorization', `Bearer ${authToken}`)
        .send(messageData)
        .expect(201);

      expect(response.body.success).toBe(true);
      expect(response.body.data.message).toMatchObject({
        content: messageData.content,
        type: messageData.type,
        chatId: chatRoomId
      });
    });

    it('빈 메시지는 전송할 수 없어야 함', async () => {
      const response = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/messages`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ content: '', type: 'text' })
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.code).toBe('VALIDATION_ERROR');
    });

    it('메시지 히스토리를 조회할 수 있어야 함', async () => {
      // 여러 메시지 전송
      for (let i = 1; i <= 5; i++) {
        await request(app)
          .post(`/api/v1/chats/${chatRoomId}/messages`)
          .set('Authorization', `Bearer ${authToken}`)
          .send({ content: `Message ${i}`, type: 'text' });
      }

      const response = await request(app)
        .get(`/api/v1/chats/${chatRoomId}/messages`)
        .set('Authorization', `Bearer ${authToken}`)
        .query({ limit: 10 })
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.messages).toBeInstanceOf(Array);
      expect(response.body.data.messages.length).toBe(5);
      expect(response.body.data.messages[0].content).toContain('Message');
    });

    it('메시지를 수정할 수 있어야 함', async () => {
      // 메시지 생성
      const createResponse = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/messages`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ content: 'Original message', type: 'text' });

      const messageId = createResponse.body.data.message.id;

      // 메시지 수정
      const updateResponse = await request(app)
        .patch(`/api/v1/messages/${messageId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ content: 'Updated message' })
        .expect(200);

      expect(updateResponse.body.success).toBe(true);
      expect(updateResponse.body.data.message.content).toBe('Updated message');
      expect(updateResponse.body.data.message.edited).toBe(true);
    });

    it('다른 사용자의 메시지는 수정할 수 없어야 함', async () => {
      // 다른 사용자로 메시지 생성
      const otherUser = await createTestUser({ 
        email: 'other@example.com' 
      });
      const otherUserLogin = await request(app)
        .post('/api/v1/auth/login')
        .send({
          email: otherUser.email,
          password: 'TestPassword123!'
        });
      
      const otherUserToken = otherUserLogin.body.data.token;

      const createResponse = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/messages`)
        .set('Authorization', `Bearer ${otherUserToken}`)
        .send({ content: 'Other user message', type: 'text' });

      const messageId = createResponse.body.data.message.id;

      // 원래 사용자가 수정 시도
      const updateResponse = await request(app)
        .patch(`/api/v1/messages/${messageId}`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ content: 'Trying to edit' })
        .expect(403);

      expect(updateResponse.body.success).toBe(false);
      expect(updateResponse.body.error.code).toBe('PERMISSION_DENIED');
    });
  });

  describe('실시간 기능 (Real-time Features)', () => {
    it('타이핑 상태를 브로드캐스트할 수 있어야 함', async () => {
      const response = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/typing`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ isTyping: true })
        .expect(200);

      expect(response.body.success).toBe(true);
    });

    it('읽음 상태를 업데이트할 수 있어야 함', async () => {
      const response = await request(app)
        .post(`/api/v1/chats/${chatRoomId}/read`)
        .set('Authorization', `Bearer ${authToken}`)
        .send({ lastReadMessageId: 'msg_123' })
        .expect(200);

      expect(response.body.success).toBe(true);
    });
  });

  describe('파일 업로드 (File Upload)', () => {
    it('이미지 파일을 업로드할 수 있어야 함', async () => {
      const response = await request(app)
        .post('/api/v1/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', 'tests/fixtures/test-image.jpg')
        .field('type', 'image')
        .expect(200);

      expect(response.body.success).toBe(true);
      expect(response.body.data.fileId).toBeDefined();
      expect(response.body.data.url).toContain('uploads');
    });

    it('허용되지 않은 파일 형식은 거부해야 함', async () => {
      const response = await request(app)
        .post('/api/v1/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', 'tests/fixtures/malicious.exe')
        .field('type', 'file')
        .expect(400);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('File type not allowed');
    });

    it('파일 크기 제한을 초과하면 거부해야 함', async () => {
      // 10MB 이상의 파일 시뮬레이션
      const response = await request(app)
        .post('/api/v1/upload')
        .set('Authorization', `Bearer ${authToken}`)
        .attach('file', 'tests/fixtures/large-file.zip')
        .field('type', 'file')
        .expect(413);

      expect(response.body.success).toBe(false);
      expect(response.body.error.message).toContain('File size exceeds limit');
    });
  });
});