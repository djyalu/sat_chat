/**
 * WebSocket Real-time Communication Tests
 * 실시간 통신 기능을 테스트합니다
 */

const Client = require('socket.io-client');
const server = require('../../src/server');

describe('WebSocket 실시간 통신 테스트', () => {
  let clientSocket1, clientSocket2;
  let serverSocket;
  const serverUrl = 'http://localhost:3001';

  beforeAll((done) => {
    server.listen(() => {
      done();
    });
  });

  afterAll(() => {
    server.close();
  });

  beforeEach((done) => {
    // 첫 번째 클라이언트 연결
    clientSocket1 = new Client(serverUrl, {
      auth: {
        token: 'test_token_user1'
      }
    });

    // 두 번째 클라이언트 연결
    clientSocket2 = new Client(serverUrl, {
      auth: {
        token: 'test_token_user2'
      }
    });

    clientSocket1.on('connect', () => {
      clientSocket2.on('connect', () => {
        done();
      });
    });
  });

  afterEach(() => {
    if (clientSocket1) clientSocket1.disconnect();
    if (clientSocket2) clientSocket2.disconnect();
  });

  describe('연결 관리 (Connection Management)', () => {
    it('클라이언트가 성공적으로 연결되어야 함', (done) => {
      expect(clientSocket1.connected).toBe(true);
      expect(clientSocket2.connected).toBe(true);
      done();
    });

    it('인증 실패 시 연결이 거부되어야 함', (done) => {
      const unauthorizedClient = new Client(serverUrl, {
        auth: {
          token: 'invalid_token'
        }
      });

      unauthorizedClient.on('connect_error', (error) => {
        expect(error.message).toContain('Authentication failed');
        unauthorizedClient.disconnect();
        done();
      });
    });

    it('재연결 메커니즘이 작동해야 함', (done) => {
      clientSocket1.disconnect();
      
      setTimeout(() => {
        clientSocket1.connect();
        
        clientSocket1.on('connect', () => {
          expect(clientSocket1.connected).toBe(true);
          done();
        });
      }, 100);
    });
  });

  describe('채팅방 관리 (Room Management)', () => {
    it('채팅방에 참여할 수 있어야 함', (done) => {
      const roomId = 'test-room-1';
      
      clientSocket1.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', (data) => {
        expect(data.roomId).toBe(roomId);
        expect(data.success).toBe(true);
        done();
      });
    });

    it('여러 사용자가 같은 채팅방에 참여할 수 있어야 함', (done) => {
      const roomId = 'test-room-2';
      let joinedCount = 0;
      
      const checkComplete = () => {
        joinedCount++;
        if (joinedCount === 2) {
          done();
        }
      };
      
      clientSocket1.emit('join-room', roomId);
      clientSocket2.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', checkComplete);
      clientSocket2.on('room-joined', checkComplete);
    });

    it('채팅방 나가기가 작동해야 함', (done) => {
      const roomId = 'test-room-3';
      
      clientSocket1.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', () => {
        clientSocket1.emit('leave-room', roomId);
        
        clientSocket1.on('room-left', (data) => {
          expect(data.roomId).toBe(roomId);
          done();
        });
      });
    });

    it('새 사용자 참여 시 다른 사용자에게 알림이 가야 함', (done) => {
      const roomId = 'test-room-4';
      
      // User1이 먼저 참여
      clientSocket1.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', () => {
        // User1이 참여한 후 User2 참여 알림 대기
        clientSocket1.on('user-joined', (data) => {
          expect(data.userId).toBeDefined();
          expect(data.roomId).toBe(roomId);
          done();
        });
        
        // User2 참여
        clientSocket2.emit('join-room', roomId);
      });
    });
  });

  describe('메시지 전송 (Message Broadcasting)', () => {
    const roomId = 'message-test-room';
    
    beforeEach((done) => {
      // 두 클라이언트 모두 같은 방에 참여
      let joinedCount = 0;
      
      const checkJoined = () => {
        joinedCount++;
        if (joinedCount === 2) done();
      };
      
      clientSocket1.emit('join-room', roomId);
      clientSocket2.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', checkJoined);
      clientSocket2.on('room-joined', checkJoined);
    });

    it('같은 방의 모든 사용자에게 메시지가 전달되어야 함', (done) => {
      const message = {
        content: 'Hello everyone!',
        timestamp: Date.now()
      };
      
      // Client2가 메시지 수신 대기
      clientSocket2.on('new-message', (data) => {
        expect(data.content).toBe(message.content);
        expect(data.senderId).toBeDefined();
        done();
      });
      
      // Client1이 메시지 전송
      clientSocket1.emit('send-message', { roomId, ...message });
    });

    it('다른 방의 사용자에게는 메시지가 전달되지 않아야 함', (done) => {
      const otherRoomId = 'other-room';
      const message = {
        content: 'This should not be received',
        timestamp: Date.now()
      };
      
      // Client2가 다른 방으로 이동
      clientSocket2.emit('leave-room', roomId);
      clientSocket2.emit('join-room', otherRoomId);
      
      clientSocket2.on('room-joined', (data) => {
        if (data.roomId === otherRoomId) {
          // Client2가 메시지를 받으면 안됨
          clientSocket2.on('new-message', () => {
            fail('Message should not be received in different room');
          });
          
          // Client1이 원래 방에 메시지 전송
          clientSocket1.emit('send-message', { roomId, ...message });
          
          // 1초 후 테스트 성공
          setTimeout(() => {
            done();
          }, 1000);
        }
      });
    });

    it('메시지 전송 확인(acknowledgment)을 받아야 함', (done) => {
      const message = {
        content: 'Message with acknowledgment',
        timestamp: Date.now()
      };
      
      clientSocket1.emit('send-message', 
        { roomId, ...message },
        (acknowledgment) => {
          expect(acknowledgment.success).toBe(true);
          expect(acknowledgment.messageId).toBeDefined();
          done();
        }
      );
    });
  });

  describe('타이핑 인디케이터 (Typing Indicators)', () => {
    const roomId = 'typing-test-room';
    
    beforeEach((done) => {
      let joinedCount = 0;
      const checkJoined = () => {
        joinedCount++;
        if (joinedCount === 2) done();
      };
      
      clientSocket1.emit('join-room', roomId);
      clientSocket2.emit('join-room', roomId);
      
      clientSocket1.on('room-joined', checkJoined);
      clientSocket2.on('room-joined', checkJoined);
    });

    it('타이핑 시작 이벤트가 전달되어야 함', (done) => {
      clientSocket2.on('user-typing', (data) => {
        expect(data.userId).toBeDefined();
        expect(data.isTyping).toBe(true);
        done();
      });
      
      clientSocket1.emit('typing-start', { roomId });
    });

    it('타이핑 중지 이벤트가 전달되어야 함', (done) => {
      clientSocket2.on('user-typing', (data) => {
        if (!data.isTyping) {
          expect(data.userId).toBeDefined();
          expect(data.isTyping).toBe(false);
          done();
        }
      });
      
      clientSocket1.emit('typing-start', { roomId });
      setTimeout(() => {
        clientSocket1.emit('typing-stop', { roomId });
      }, 100);
    });

    it('타이핑 타임아웃이 작동해야 함', (done) => {
      let typingStartReceived = false;
      
      clientSocket2.on('user-typing', (data) => {
        if (data.isTyping && !typingStartReceived) {
          typingStartReceived = true;
        } else if (!data.isTyping && typingStartReceived) {
          // 타임아웃으로 인한 자동 중지
          done();
        }
      });
      
      clientSocket1.emit('typing-start', { roomId });
      // 타임아웃 대기 (일반적으로 3초)
    });
  });

  describe('온라인 상태 (Online Presence)', () => {
    it('사용자 연결 시 온라인 상태가 업데이트되어야 함', (done) => {
      clientSocket1.on('user-status-changed', (data) => {
        expect(data.userId).toBeDefined();
        expect(data.status).toBe('online');
        done();
      });
      
      // 새 클라이언트 연결
      const newClient = new Client(serverUrl, {
        auth: { token: 'test_token_user3' }
      });
      
      newClient.on('connect', () => {
        setTimeout(() => newClient.disconnect(), 100);
      });
    });

    it('사용자 연결 해제 시 오프라인 상태가 업데이트되어야 함', (done) => {
      const tempClient = new Client(serverUrl, {
        auth: { token: 'test_token_temp' }
      });
      
      tempClient.on('connect', () => {
        clientSocket1.on('user-status-changed', (data) => {
          if (data.status === 'offline') {
            expect(data.userId).toBeDefined();
            done();
          }
        });
        
        // 연결 후 즉시 해제
        tempClient.disconnect();
      });
    });
  });

  describe('에러 처리 (Error Handling)', () => {
    it('잘못된 형식의 메시지 전송 시 에러를 반환해야 함', (done) => {
      clientSocket1.emit('send-message', 
        { /* roomId 누락 */ content: 'Invalid message' },
        (response) => {
          expect(response.success).toBe(false);
          expect(response.error).toContain('Room ID is required');
          done();
        }
      );
    });

    it('권한 없는 채팅방 접근 시 에러를 반환해야 함', (done) => {
      clientSocket1.emit('join-room', 'private-room-unauthorized');
      
      clientSocket1.on('error', (error) => {
        expect(error.message).toContain('Access denied');
        done();
      });
    });

    it('Rate limiting이 작동해야 함', (done) => {
      let messageCount = 0;
      let errorReceived = false;
      
      // 빠르게 많은 메시지 전송
      const interval = setInterval(() => {
        clientSocket1.emit('send-message', 
          { roomId: 'test-room', content: `Message ${messageCount}` },
          (response) => {
            if (!response.success && !errorReceived) {
              expect(response.error).toContain('Rate limit exceeded');
              errorReceived = true;
              clearInterval(interval);
              done();
            }
          }
        );
        
        messageCount++;
        if (messageCount > 100) {
          clearInterval(interval);
          fail('Rate limit should have triggered');
        }
      }, 10);
    });
  });

  describe('파일 공유 (File Sharing)', () => {
    it('파일 업로드 이벤트가 전달되어야 함', (done) => {
      const roomId = 'file-test-room';
      
      clientSocket1.emit('join-room', roomId);
      clientSocket2.emit('join-room', roomId);
      
      clientSocket2.on('file-shared', (data) => {
        expect(data.fileName).toBe('test.pdf');
        expect(data.fileSize).toBe(1024000);
        expect(data.fileUrl).toBeDefined();
        done();
      });
      
      setTimeout(() => {
        clientSocket1.emit('share-file', {
          roomId,
          fileName: 'test.pdf',
          fileSize: 1024000,
          fileUrl: 'https://example.com/files/test.pdf'
        });
      }, 100);
    });
  });
});