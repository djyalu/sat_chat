# Contributing to SAT Chat

First off, thank you for considering contributing to SAT Chat! It's people like you that make SAT Chat such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Process](#development-process)
- [Style Guidelines](#style-guidelines)
- [Commit Messages](#commit-messages)
- [Pull Request Process](#pull-request-process)

## 📜 Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

### Our Standards

- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

## 🚀 Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/your-username/sat_chat.git
   cd sat_chat
   ```
3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/djyalu/sat_chat.git
   ```
4. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 🤝 How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When creating a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Screenshots (if applicable)
- Your environment details (OS, browser, Node.js version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- A detailed description of the proposed enhancement
- Any possible alternatives you've considered
- Additional context or screenshots

### Your First Code Contribution

Unsure where to begin? Look for issues labeled:
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `documentation` - Documentation improvements needed

## 💻 Development Process

### Setting Up Development Environment

1. Install dependencies:
   ```bash
   npm install
   ```

2. Set up pre-commit hooks:
   ```bash
   npm run prepare
   ```

3. Create a `.env` file based on `.env.example`

4. Run the development server:
   ```bash
   npm run dev
   ```

### Development Workflow

1. **Plan** - Understand the requirements and design your solution
2. **Implement** - Write your code following our style guidelines
3. **Test** - Write and run tests for your changes
4. **Document** - Update documentation if needed
5. **Submit** - Create a pull request

## 📝 Style Guidelines

### JavaScript/TypeScript Style Guide

We use ESLint and Prettier for code formatting. Key conventions:

```javascript
// Use meaningful variable names
const userMessage = "Hello"; // Good
const msg = "Hello"; // Avoid

// Use async/await over promises when possible
// Good
async function fetchUser(id) {
  try {
    const user = await api.getUser(id);
    return user;
  } catch (error) {
    console.error('Failed to fetch user:', error);
  }
}

// Avoid deeply nested callbacks
```

### Component Structure (React/Vue)

```javascript
// Follow a consistent component structure
// 1. Imports
// 2. Type definitions/interfaces
// 3. Component definition
// 4. Styles (if using CSS-in-JS)
// 5. Exports

// Example React component
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

interface UserCardProps {
  user: User;
  onSelect: (user: User) => void;
}

export const UserCard: React.FC<UserCardProps> = ({ user, onSelect }) => {
  // Component logic here
  return (
    // JSX here
  );
};
```

### CSS/SCSS Guidelines

```scss
// Use BEM naming convention
.chat-message {
  &__header {
    // Header styles
  }
  
  &__content {
    // Content styles
  }
  
  &--highlight {
    // Modifier styles
  }
}

// Use CSS variables for theming
:root {
  --primary-color: #007bff;
  --secondary-color: #6c757d;
  --font-family: 'Inter', sans-serif;
}
```

### Testing Guidelines

Write tests for:
- New features
- Bug fixes
- Critical user paths

```javascript
// Example test structure
describe('MessageService', () => {
  describe('sendMessage', () => {
    it('should send message successfully', async () => {
      // Test implementation
    });
    
    it('should handle errors gracefully', async () => {
      // Test implementation
    });
  });
});
```

## 💬 Commit Messages

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, semicolons, etc.)
- **refactor**: Code refactoring without feature changes
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks

### Examples
```bash
feat(chat): add emoji support for messages

- Added emoji picker component
- Integrated with message input
- Updated message rendering to support emojis

Closes #123
```

```bash
fix(auth): resolve token expiration issue

Token was not being refreshed properly when expired.
Added automatic token refresh logic.

Fixes #456
```

## 🔄 Pull Request Process

1. **Update your branch** with the latest upstream changes:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run tests** and ensure they pass:
   ```bash
   npm test
   npm run lint
   ```

3. **Update documentation** if you've changed APIs or added features

4. **Create a Pull Request** with:
   - A clear title and description
   - Reference to related issues
   - Screenshots for UI changes
   - Test results

### PR Title Format
Follow the same convention as commit messages:
- `feat: add user profile page`
- `fix: resolve WebSocket connection issues`
- `docs: update API documentation`

### PR Review Process

1. **Automated checks** - CI/CD runs tests and linting
2. **Code review** - At least one maintainer reviews the code
3. **Discussion** - Address feedback and make necessary changes
4. **Approval** - Maintainer approves the PR
5. **Merge** - PR is merged to main branch

## 🏆 Recognition

Contributors are recognized in:
- The README.md contributors section
- Release notes
- Our hall of fame (for significant contributions)

## 📚 Additional Resources

- [Project Roadmap](https://github.com/djyalu/sat_chat/projects)
- [API Documentation](./docs/api.md)
- [Architecture Guide](./docs/architecture.md)
- [Security Guidelines](./docs/security.md)

## ❓ Questions?

Feel free to:
- Open an issue for questions
- Join our Discord server (link in README)
- Contact maintainers directly

Thank you for contributing to SAT Chat! 🎉