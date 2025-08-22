# SAT Chat

A modern real-time chat application built with scalability and user experience in mind.

## 🚀 Features

- Real-time messaging
- User authentication and authorization
- Multiple chat rooms/channels
- Direct messaging
- File sharing capabilities
- Message history and search
- Online presence indicators
- Typing indicators
- Read receipts

## 📋 Prerequisites

Before you begin, ensure you have the following installed:
- Node.js (v16.0.0 or higher)
- npm (v8.0.0 or higher) or yarn
- Git

## 🛠️ Installation

1. Clone the repository:
```bash
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat
```

2. Install dependencies:
```bash
npm install
# or
yarn install
```

3. Set up environment variables:
```bash
cp .env.example .env
```
Edit the `.env` file with your configuration settings.

4. Run database migrations (if applicable):
```bash
npm run migrate
```

5. Start the development server:
```bash
npm run dev
# or
yarn dev
```

The application will be available at `http://localhost:3000`

## 🏗️ Project Structure

```
sat_chat/
├── src/              # Source code
│   ├── components/   # Reusable UI components
│   ├── pages/        # Application pages/routes
│   ├── services/     # Business logic and API calls
│   ├── utils/        # Utility functions
│   └── styles/       # Global styles and themes
├── public/           # Static assets
├── tests/            # Test files
├── docs/             # Documentation
└── config/           # Configuration files
```

## 🔧 Configuration

The application uses environment variables for configuration. Key settings include:

- `PORT` - Server port (default: 3000)
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - Secret key for JWT authentication
- `WEBSOCKET_PORT` - WebSocket server port

## 📝 API Documentation

### Authentication Endpoints

#### POST /api/auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

#### POST /api/auth/login
Authenticate user and receive access token.

**Request Body:**
```json
{
  "email": "string",
  "password": "string"
}
```

### Chat Endpoints

#### GET /api/chats
Get list of available chat rooms.

#### POST /api/messages
Send a new message.

**Request Body:**
```json
{
  "chatId": "string",
  "content": "string",
  "type": "text|image|file"
}
```

## 🧪 Testing

Run the test suite:
```bash
# Unit tests
npm run test

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e

# Test coverage
npm run test:coverage
```

## 🚢 Deployment

### Production Build

Create a production build:
```bash
npm run build
```

### Docker Deployment

Build and run with Docker:
```bash
docker build -t sat_chat .
docker run -p 3000:3000 sat_chat
```

### Environment-Specific Deployment

- **Development**: `npm run dev`
- **Staging**: `npm run start:staging`
- **Production**: `npm run start:prod`

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on:
- Code of conduct
- Development process
- How to submit pull requests
- Coding standards

## 📈 Performance

The application is optimized for:
- Fast initial load times (<3s on 3G)
- Efficient WebSocket connections
- Optimized bundle size
- Lazy loading of components
- Caching strategies

## 🔒 Security

Security features include:
- JWT-based authentication
- Input validation and sanitization
- Rate limiting
- CORS configuration
- XSS and CSRF protection
- Encrypted passwords (bcrypt)
- Secure WebSocket connections (WSS)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Lead Developer** - [@djyalu](https://github.com/djyalu)

## 🙏 Acknowledgments

- Thanks to all contributors
- Built with modern web technologies
- Inspired by best practices in real-time communication

## 📞 Support

For support, please:
- Check the [documentation](docs/)
- Open an [issue](https://github.com/djyalu/sat_chat/issues)
- Contact the team

---

**Version**: 1.0.0  
**Last Updated**: August 2025