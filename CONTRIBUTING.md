# Contributing to LibreAssistant


Thank you for your interest in contributing to LibreAssistant! LibreAssistant is a privacy-first, fully local AI assistant and plugin platform. It preserves all legacy Ollama/model management features from my-ollama-wrapper and adds a modern plugin (MCP server) system. All contributions are welcome, whether you are fixing bugs, adding features, improving documentation, or helping with testing.

---

## 📦 Contributing New Plugins (MCP Servers)

LibreAssistant supports a robust plugin system. To contribute a new plugin:

1. **Structure:** Place your plugin in a new subdirectory under `plugins/` (e.g. `plugins/my-plugin/`).
2. **Manifest:** Include a `plugin-manifest.json` file describing your plugin (see [PLUGIN_API.md](./PLUGIN_API.md)).
3. **Entrypoint:** Provide a server script (e.g. `server.py`) that implements the MCP server protocol (Flask/FastAPI recommended).
4. **Testing:** Add tests or a test script for your plugin. Ensure it works independently and with LibreAssistant.
5. **Documentation:** Document your endpoints, config, and permissions in the manifest and a README if needed.
6. **Minimal Permissions:** Request only the permissions your plugin needs.
7. **Security:** Validate all input and sandbox file/network access as appropriate.

For full details, see the [PLUGIN_API.md](./PLUGIN_API.md) file.

---
## Project Scope

LibreAssistant provides a user-friendly, local-first interface for managing Ollama models and interacting with them via chat. The project now supports a plugin system (MCP servers) for extensibility, while all legacy model management features remain fully supported.
## How to Contribute

1. **Fork the repository** and create your branch from `main`.
2. **Install dependencies** using `npm install` (for Node/Electron) or `pip install -r requirements.txt` (for Python backend).
3. **Test your changes** locally. Ensure both model management and plugin features work as expected.
4. **Write clear commit messages** and document your changes in the PR description.
5. **Submit a pull request** and respond to any review feedback.
## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) to keep our community welcoming and inclusive.
## Legacy Compatibility

If you are migrating from my-ollama-wrapper, all your existing workflows and scripts should continue to work. If you encounter any issues, please open an issue or pull request. LibreAssistant is committed to full backward compatibility for model management features.
# Contributing to LibreAssistant

Thank you for your interest in contributing to LibreAssistant! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)
- [Code Architecture](#code-architecture)
- [Release Process](#release-process)

## Code of Conduct

### Our Pledge

We are committed to creating a welcoming and inclusive environment for all contributors, regardless of background, experience level, or personal characteristics.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, trolling, or discriminatory comments
- Personal attacks or political discussions
- Publishing private information without permission
- Any conduct that would be inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have:

1. **Ollama** installed and running
2. **Node.js** 18+ and **npm** 8+
3. **Git** for version control
4. A **GitHub account**

### Development Setup

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
  ```bash
  git clone https://github.com/YOUR_USERNAME/LibreAssistant.git
  cd LibreAssistant
  ```

3. **Add upstream remote**:
  ```bash
  git remote add upstream https://github.com/aubreyhayes47/LibreAssistant.git
  ```

4. **Install dependencies**:
   ```bash
   npm install
   ```

5. **Set up environment**:
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your configuration
   ```

6. **Start development server**:
   ```bash
   npm run dev
   ```

## Development Workflow

### Branch Strategy

We use a simplified Git workflow:

- **`main`**: Stable, production-ready code
- **Feature branches**: `feature/description` or `fix/description`
- **Release branches**: `release/v1.x.x` (when applicable)

### Making Changes

1. **Create a new branch** from `main`:
   ```bash
   git checkout main
   git pull upstream main
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following our coding standards

3. **Test your changes**:
   ```bash
   npm run test
   npm run lint
   npm run type-check
   ```

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: add new feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request** on GitHub

### Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

#### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, etc.)
- **refactor**: Code refactoring
- **perf**: Performance improvements
- **test**: Adding or updating tests
- **chore**: Maintenance tasks
- **ci**: CI/CD changes

#### Examples

```bash
feat(chat): add message history export functionality
fix(api): resolve Ollama connection timeout issue
docs: update installation instructions for Windows
style: format code with prettier
refactor(components): simplify chat message rendering
test(integration): add tests for model switching
chore: update dependencies to latest versions
```

## Coding Standards

### TypeScript Guidelines

- **Use TypeScript** for all new code
- **Define interfaces** for all data structures
- **Avoid `any` type** - use proper typing
- **Use strict mode** settings in tsconfig.json

```typescript
// Good
interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

// Avoid
const message: any = { /* ... */ };
```

### React Best Practices

- **Use functional components** with hooks
- **Follow component naming conventions**: PascalCase
- **Use custom hooks** for reusable logic
- **Implement proper error boundaries**
- **Use React.memo** for performance optimization when needed

```typescript
// Good
const ChatMessage: React.FC<ChatMessageProps> = React.memo(({ message, onEdit }) => {
  const [isEditing, setIsEditing] = useState(false);
  
  // Component logic here
  
  return (
    <div className="chat-message">
      {/* JSX here */}
    </div>
  );
});

ChatMessage.displayName = 'ChatMessage';
```

### Styling Guidelines

- **Use Tailwind CSS** for styling
- **Create custom components** for complex UI patterns
- **Follow mobile-first** responsive design
- **Use CSS custom properties** for theming

```typescript
// Good
<div className="flex flex-col space-y-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow-md">
  <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
    Title
  </h2>
</div>
```

### File Organization

- **Use barrel exports** in index files
- **Group related files** in directories
- **Follow naming conventions**:
  - Components: `PascalCase.tsx`
  - Hooks: `useCamelCase.ts`
  - Utilities: `camelCase.ts`
  - Types: `camelCase.types.ts`

## Testing Guidelines

### Testing Strategy

We maintain comprehensive test coverage across multiple levels:

#### Unit Tests
- **Component testing** with React Testing Library
- **Hook testing** with custom test utilities
- **Utility function testing** with Jest
- **Minimum 80% coverage** for new code

#### Integration Tests
- **API integration** testing
- **User workflow** testing
- **Cross-component** interaction testing

#### End-to-End Tests
- **Critical user paths** with Playwright
- **Browser compatibility** testing
- **Performance testing** for key workflows

### Writing Tests

#### Component Tests

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatMessage } from './ChatMessage';

describe('ChatMessage', () => {
  it('should render message content correctly', () => {
    const message = {
      id: '1',
      content: 'Hello, world!',
      role: 'user' as const,
      timestamp: new Date(),
    };

    render(<ChatMessage message={message} />);
    
    expect(screen.getByText('Hello, world!')).toBeInTheDocument();
  });

  it('should handle edit action', () => {
    const onEdit = jest.fn();
    const message = { /* ... */ };

    render(<ChatMessage message={message} onEdit={onEdit} />);
    
    fireEvent.click(screen.getByRole('button', { name: /edit/i }));
    
    expect(onEdit).toHaveBeenCalledWith(message.id);
  });
});
```

#### Hook Tests

```typescript
import { renderHook, act } from '@testing-library/react';
import { useChat } from './useChat';

describe('useChat', () => {
  it('should send message and update history', async () => {
    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('Hello');
    });

    expect(result.current.messages).toHaveLength(2); // user + assistant
    expect(result.current.messages[0].content).toBe('Hello');
  });
});
```

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test ChatMessage

# Run tests with coverage
npm run test:coverage

# Run E2E tests
npm run test:e2e
```

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass**:
   ```bash
   npm run test
   npm run lint
   npm run type-check
   npm run build
   ```

2. **Update documentation** if needed

3. **Add tests** for new functionality

4. **Check performance impact** for UI changes

### PR Requirements

- **Clear title** following conventional commits
- **Detailed description** explaining:
  - What changes were made
  - Why the changes were necessary
  - How to test the changes
- **Screenshots** for UI changes
- **Breaking changes** clearly documented
- **Linked issues** using keywords (e.g., "Fixes #123")

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)
[Add screenshots here]

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Tests added and passing
- [ ] Documentation updated
```

### Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by maintainers
3. **Manual testing** if needed
4. **Final approval** and merge

## Issue Guidelines

### Reporting Bugs

Use the bug report template and include:

- **Clear title** and description
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Environment details** (OS, Node.js version, etc.)
- **Screenshots** or error logs
- **Minimal reproducible example**

### Feature Requests

Use the feature request template and include:

- **Problem statement** or use case
- **Proposed solution**
- **Alternative solutions** considered
- **Implementation considerations**
- **Mockups** or examples (if applicable)

### Issue Labels

- **`bug`**: Something isn't working
- **`enhancement`**: New feature or request
- **`documentation`**: Documentation improvements
- **`good first issue`**: Good for newcomers
- **`help wanted`**: Extra attention needed
- **`priority:high`**: High priority items
- **`wontfix`**: This won't be worked on

## Code Architecture

### Application Structure

```
src/
├── components/          # React components
│   ├── ui/             # Basic UI components (Button, Input, etc.)
│   ├── chat/           # Chat-related components
│   ├── models/         # Model management components
│   └── layout/         # Layout components
├── hooks/              # Custom React hooks
├── lib/                # Core libraries and utilities
│   ├── ollama/         # Ollama API client
│   ├── storage/        # Local storage management
│   └── utils/          # Utility functions
├── pages/              # Next.js pages
├── styles/             # Global styles and themes
└── types/              # TypeScript type definitions
```

### Key Patterns

#### State Management
- **Local state**: React useState for component-specific state
- **Global state**: Context API for app-wide state
- **Server state**: React Query for API data
- **Persistent state**: Local storage with hooks

#### API Integration
- **Ollama client**: Centralized API client in `lib/ollama/`
- **Error handling**: Consistent error boundaries and try-catch
- **Type safety**: Full TypeScript coverage for API responses
- **Caching**: React Query for intelligent caching

#### Component Design
- **Composition**: Prefer composition over inheritance
- **Props interface**: Clear, well-documented prop interfaces
- **Accessibility**: ARIA labels and keyboard navigation
- **Performance**: React.memo and useMemo for optimization

### Adding New Features

1. **Design the API** first (types and interfaces)
2. **Create hooks** for business logic
3. **Build components** with proper testing
4. **Update documentation** and examples
5. **Add integration tests** for complete workflows

## Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Workflow

1. **Create release branch**: `release/v1.x.x`
2. **Update version**: `npm version [major|minor|patch]`
3. **Update CHANGELOG.md**
4. **Test release candidate**
5. **Merge to main** and tag release
6. **Publish** to npm (if applicable)
7. **Deploy** to production

### Changelog Format

```markdown
## [1.2.0] - 2024-01-15

### Added
- New chat export functionality
- Dark mode theme support

### Changed
- Improved model switching performance
- Updated UI component library

### Fixed
- Connection timeout issues
- Memory leak in chat history

### Deprecated
- Old API endpoint (will be removed in v2.0)
```

## Questions?

If you have questions about contributing:

1. **Check existing documentation** and issues
2. **Ask in discussions** for general questions
3. **Create an issue** for specific problems
4. **Contact maintainers** for urgent matters

Thank you for contributing to LibreAssistant! 🚀

For plugin development, see [PLUGIN_API.md](./PLUGIN_API.md).