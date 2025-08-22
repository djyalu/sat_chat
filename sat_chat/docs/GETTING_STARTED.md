# Getting Started with SAT Chat

Welcome to SAT Chat! This guide will help you get up and running quickly.

## Prerequisites

Before starting, ensure you have:
- Node.js 16+ and npm 8+ installed
- Git for version control
- A database (PostgreSQL recommended)
- Redis for caching (optional but recommended)

## Quick Start

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/djyalu/sat_chat.git
cd sat_chat

# Install dependencies
npm install
```

### 2. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit the .env file with your settings
# At minimum, configure:
# - DATABASE_URL
# - JWT_SECRET
# - SESSION_SECRET
```

### 3. Set Up Database

```bash
# Run database migrations
npm run migrate

# (Optional) Seed with sample data
npm run seed
```

### 4. Start Development Server

```bash
# Start the development server with hot reload
npm run dev

# The app will be available at:
# - API: http://localhost:3000
# - WebSocket: ws://localhost:3001
```

## Project Structure Overview

```
sat_chat/
├── src/                 # Source code
│   ├── controllers/     # Request handlers
│   ├── models/         # Data models
│   ├── routes/         # API routes
│   ├── services/       # Business logic
│   ├── middleware/     # Express middleware
│   ├── utils/          # Utility functions
│   ├── config/         # Configuration files
│   └── index.js        # Application entry point
├── tests/              # Test files
├── docs/               # Documentation
├── scripts/            # Utility scripts
└── public/             # Static files
```

## Development Workflow

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run with coverage
npm run test:coverage
```

### Code Quality

```bash
# Run linter
npm run lint

# Auto-fix linting issues
npm run lint:fix

# Format code
npm run format
```

### Making Your First Change

1. **Create a new branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make your changes** following our coding standards

3. **Test your changes:**
   ```bash
   npm test
   npm run lint
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add my new feature"
   ```

5. **Push to GitHub:**
   ```bash
   git push origin feature/my-feature
   ```

6. **Create a Pull Request** on GitHub

## Common Tasks

### Adding a New API Endpoint

1. Create a controller in `src/controllers/`
2. Define the route in `src/routes/`
3. Add validation middleware if needed
4. Write tests in `tests/`

Example:
```javascript
// src/controllers/example.controller.js
exports.getExample = async (req, res) => {
  res.json({ message: 'Hello World' });
};

// src/routes/example.routes.js
router.get('/example', exampleController.getExample);
```

### Adding a New Database Model

1. Create model in `src/models/`
2. Define schema and methods
3. Export for use in controllers

Example:
```javascript
// src/models/Message.js
const messageSchema = new Schema({
  content: String,
  sender: { type: Schema.Types.ObjectId, ref: 'User' },
  chatRoom: { type: Schema.Types.ObjectId, ref: 'ChatRoom' },
  createdAt: { type: Date, default: Date.now }
});

module.exports = mongoose.model('Message', messageSchema);
```

### Working with WebSockets

```javascript
// Emit to all clients in a room
io.to(roomId).emit('message', data);

// Listen for client events
socket.on('join-room', (roomId) => {
  socket.join(roomId);
});
```

## Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 3000
lsof -i :3000

# Kill the process
kill -9 <PID>
```

#### Database Connection Failed
- Check DATABASE_URL in .env
- Ensure database server is running
- Verify credentials

#### Module Not Found
```bash
# Clear cache and reinstall
npm run clean
```

## Environment-Specific Configuration

### Development
- Hot reload enabled
- Detailed error messages
- Debug logging

### Production
```bash
# Build for production
npm run build

# Start production server
npm run start:prod
```

### Testing
- Uses separate test database
- Mocked external services
- Isolated test environment

## Getting Help

- Check the [Documentation](../README.md)
- Review [API Documentation](./API.md)
- Open an [Issue](https://github.com/djyalu/sat_chat/issues)
- Read [Contributing Guidelines](../CONTRIBUTING.md)

## Next Steps

1. **Explore the API:** Review the [API Documentation](./API.md)
2. **Understand the Architecture:** Read about our design decisions
3. **Join the Community:** Contribute to the project
4. **Build Something:** Start creating with SAT Chat!

## Useful Commands Reference

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm test` | Run tests |
| `npm run lint` | Check code quality |
| `npm run format` | Format code |
| `npm run build` | Build for production |
| `npm run migrate` | Run database migrations |
| `npm run seed` | Seed database with sample data |

Happy coding! 🚀