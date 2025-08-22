# SAT Chat API Documentation

## Overview

The SAT Chat API provides a RESTful interface for managing chat functionality, user authentication, and real-time messaging. All API requests should be made to:

```
Base URL: https://api.satchat.com/v1
Development URL: http://localhost:3000/api/v1
```

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- **Authenticated requests**: 1000 requests per hour
- **Unauthenticated requests**: 100 requests per hour

## Response Format

All API responses follow this structure:

```json
{
  "success": true,
  "data": { },
  "message": "Operation successful",
  "timestamp": "2025-08-22T10:00:00Z"
}
```

Error responses:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { }
  },
  "timestamp": "2025-08-22T10:00:00Z"
}
```

## Endpoints

### Authentication

#### Register User
**POST** `/auth/register`

Create a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePassword123!",
  "displayName": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "johndoe",
      "email": "john@example.com",
      "displayName": "John Doe",
      "createdAt": "2025-08-22T10:00:00Z"
    },
    "token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### Login
**POST** `/auth/login`

Authenticate user and receive access token.

**Request Body:**
```json
{
  "email": "john@example.com",
  "password": "SecurePassword123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "username": "johndoe",
      "email": "john@example.com",
      "displayName": "John Doe"
    },
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

#### Refresh Token
**POST** `/auth/refresh`

Get a new access token using refresh token.

**Request Body:**
```json
{
  "refreshToken": "eyJhbGciOiJIUzI1NiIs..."
}
```

#### Logout
**POST** `/auth/logout`

Invalidate current session.

**Headers:** Authorization required

### User Management

#### Get Current User
**GET** `/users/me`

Get authenticated user's profile.

**Headers:** Authorization required

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "username": "johndoe",
    "email": "john@example.com",
    "displayName": "John Doe",
    "avatar": "https://cdn.satchat.com/avatars/user_123.jpg",
    "status": "online",
    "bio": "Software developer",
    "createdAt": "2025-08-22T10:00:00Z"
  }
}
```

#### Update Profile
**PATCH** `/users/me`

Update user profile information.

**Headers:** Authorization required

**Request Body:**
```json
{
  "displayName": "John Smith",
  "bio": "Full-stack developer",
  "avatar": "base64_image_data"
}
```

#### Get User by ID
**GET** `/users/:userId`

Get public user information.

**Headers:** Authorization required

### Chat Rooms

#### List Chat Rooms
**GET** `/chats`

Get all available chat rooms for the user.

**Headers:** Authorization required

**Query Parameters:**
- `page` (number): Page number (default: 1)
- `limit` (number): Items per page (default: 20)
- `type` (string): Filter by type (group, direct)

**Response:**
```json
{
  "success": true,
  "data": {
    "chats": [
      {
        "id": "chat_456",
        "name": "General Discussion",
        "type": "group",
        "description": "Main chat room",
        "members": 125,
        "lastMessage": {
          "content": "Hello everyone!",
          "sender": "johndoe",
          "timestamp": "2025-08-22T09:55:00Z"
        },
        "unreadCount": 3
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### Create Chat Room
**POST** `/chats`

Create a new chat room.

**Headers:** Authorization required

**Request Body:**
```json
{
  "name": "Project Discussion",
  "type": "group",
  "description": "Discussion about the new project",
  "isPrivate": false,
  "members": ["user_789", "user_012"]
}
```

#### Join Chat Room
**POST** `/chats/:chatId/join`

Join an existing chat room.

**Headers:** Authorization required

#### Leave Chat Room
**POST** `/chats/:chatId/leave`

Leave a chat room.

**Headers:** Authorization required

### Messages

#### Get Messages
**GET** `/chats/:chatId/messages`

Get messages from a specific chat room.

**Headers:** Authorization required

**Query Parameters:**
- `limit` (number): Number of messages (default: 50)
- `before` (string): Get messages before this message ID
- `after` (string): Get messages after this message ID

**Response:**
```json
{
  "success": true,
  "data": {
    "messages": [
      {
        "id": "msg_789",
        "chatId": "chat_456",
        "sender": {
          "id": "user_123",
          "username": "johndoe",
          "displayName": "John Doe",
          "avatar": "https://cdn.satchat.com/avatars/user_123.jpg"
        },
        "content": "Hello everyone!",
        "type": "text",
        "timestamp": "2025-08-22T09:55:00Z",
        "edited": false,
        "reactions": [
          {
            "emoji": "👍",
            "users": ["user_789", "user_012"]
          }
        ]
      }
    ],
    "hasMore": true
  }
}
```

#### Send Message
**POST** `/chats/:chatId/messages`

Send a new message to a chat room.

**Headers:** Authorization required

**Request Body:**
```json
{
  "content": "Hello everyone!",
  "type": "text",
  "attachments": [],
  "replyTo": "msg_456"
}
```

**Message Types:**
- `text`: Plain text message
- `image`: Image attachment
- `file`: File attachment
- `audio`: Voice message
- `video`: Video message

#### Edit Message
**PATCH** `/messages/:messageId`

Edit an existing message.

**Headers:** Authorization required

**Request Body:**
```json
{
  "content": "Updated message content"
}
```

#### Delete Message
**DELETE** `/messages/:messageId`

Delete a message.

**Headers:** Authorization required

#### Add Reaction
**POST** `/messages/:messageId/reactions`

Add a reaction to a message.

**Headers:** Authorization required

**Request Body:**
```json
{
  "emoji": "👍"
}
```

### File Upload

#### Upload File
**POST** `/upload`

Upload a file for sharing in chat.

**Headers:** 
- Authorization required
- Content-Type: multipart/form-data

**Form Data:**
- `file`: File to upload
- `type`: File type (image, document, video, audio)

**Response:**
```json
{
  "success": true,
  "data": {
    "fileId": "file_123",
    "url": "https://cdn.satchat.com/files/file_123.pdf",
    "thumbnailUrl": "https://cdn.satchat.com/thumbnails/file_123.jpg",
    "size": 1048576,
    "mimeType": "application/pdf",
    "filename": "document.pdf"
  }
}
```

### Search

#### Search Messages
**GET** `/search/messages`

Search for messages across all accessible chats.

**Headers:** Authorization required

**Query Parameters:**
- `q` (string): Search query
- `chatId` (string): Limit to specific chat
- `userId` (string): Filter by sender
- `startDate` (string): Start date (ISO 8601)
- `endDate` (string): End date (ISO 8601)

#### Search Users
**GET** `/search/users`

Search for users.

**Headers:** Authorization required

**Query Parameters:**
- `q` (string): Search query
- `limit` (number): Results limit (default: 10)

### Notifications

#### Get Notifications
**GET** `/notifications`

Get user notifications.

**Headers:** Authorization required

**Query Parameters:**
- `unread` (boolean): Filter unread only
- `limit` (number): Results limit (default: 20)

#### Mark as Read
**PATCH** `/notifications/:notificationId/read`

Mark notification as read.

**Headers:** Authorization required

### WebSocket Events

Connect to WebSocket for real-time updates:

```javascript
const ws = new WebSocket('wss://api.satchat.com/ws?token=YOUR_JWT_TOKEN');
```

#### Client → Server Events

**Send Message:**
```json
{
  "event": "message.send",
  "data": {
    "chatId": "chat_456",
    "content": "Hello!",
    "type": "text"
  }
}
```

**Start Typing:**
```json
{
  "event": "typing.start",
  "data": {
    "chatId": "chat_456"
  }
}
```

**Stop Typing:**
```json
{
  "event": "typing.stop",
  "data": {
    "chatId": "chat_456"
  }
}
```

#### Server → Client Events

**New Message:**
```json
{
  "event": "message.new",
  "data": {
    "message": { }
  }
}
```

**Message Updated:**
```json
{
  "event": "message.updated",
  "data": {
    "message": { }
  }
}
```

**User Typing:**
```json
{
  "event": "user.typing",
  "data": {
    "chatId": "chat_456",
    "userId": "user_789",
    "username": "janedoe"
  }
}
```

**User Online Status:**
```json
{
  "event": "user.status",
  "data": {
    "userId": "user_789",
    "status": "online"
  }
}
```

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|------------|
| AUTH_REQUIRED | Authentication required | 401 |
| AUTH_INVALID | Invalid credentials | 401 |
| AUTH_TOKEN_EXPIRED | Token has expired | 401 |
| PERMISSION_DENIED | Insufficient permissions | 403 |
| RESOURCE_NOT_FOUND | Resource not found | 404 |
| VALIDATION_ERROR | Request validation failed | 400 |
| RATE_LIMIT_EXCEEDED | Too many requests | 429 |
| SERVER_ERROR | Internal server error | 500 |
| SERVICE_UNAVAILABLE | Service temporarily unavailable | 503 |

## SDKs and Libraries

Official SDKs are available for:
- JavaScript/TypeScript
- Python
- Go
- Java
- C#

## Changelog

### Version 1.0.0 (2025-08-22)
- Initial API release
- Authentication endpoints
- Chat room management
- Real-time messaging
- File upload support
- WebSocket events

## Support

For API support:
- Email: api-support@satchat.com
- Documentation: https://docs.satchat.com
- Status Page: https://status.satchat.com