/**
 * WebSocket Server
 * Socket.io 서버 설정
 */

const { Server } = require('socket.io');
const http = require('http');

const httpServer = http.createServer();
const io = new Server(httpServer, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// Connection handler
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });

  socket.on('join-room', (roomId) => {
    socket.join(roomId);
    socket.emit('room-joined', { roomId, success: true });
    socket.to(roomId).emit('user-joined', { userId: socket.id, roomId });
  });

  socket.on('leave-room', (roomId) => {
    socket.leave(roomId);
    socket.emit('room-left', { roomId });
  });

  socket.on('send-message', (data, callback) => {
    if (!data.roomId) {
      if (callback) callback({ success: false, error: 'Room ID is required' });
      return;
    }
    
    const messageId = `msg_${Date.now()}`;
    io.to(data.roomId).emit('new-message', {
      ...data,
      messageId,
      senderId: socket.id
    });
    
    if (callback) callback({ success: true, messageId });
  });

  socket.on('typing-start', ({ roomId }) => {
    socket.to(roomId).emit('user-typing', { userId: socket.id, isTyping: true });
  });

  socket.on('typing-stop', ({ roomId }) => {
    socket.to(roomId).emit('user-typing', { userId: socket.id, isTyping: false });
  });
});

module.exports = httpServer;