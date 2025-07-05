# Contributing to LibreAssistant

Thank you for your interest in contributing to LibreAssistant! This document provides guidelines for contributing to our open-source AI assistant browser project.

## 🚀 Getting Started

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/LibreAssistant.git
   cd LibreAssistant
   ```

2. **Follow setup instructions**
   - See the main [README.md](README.md) for detailed installation steps
   - Ensure you have Rust, Node.js, and Python installed

3. **Create a development branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

## 📝 Code Style Guidelines

### Python Backend
- **Formatting**: Use [Black](https://black.readthedocs.io/) with line length 88
- **Linting**: Use [Ruff](https://docs.astral.sh/ruff/) for fast linting
- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Use Google-style docstrings for all public functions and classes

### Rust Frontend
- **Formatting**: Use `rustfmt` for consistent formatting
- **Linting**: Use `clippy` for additional linting
- **Documentation**: Document public functions with `///` comments

### JavaScript/Svelte
- **Formatting**: Use [Prettier](https://prettier.io/) for consistent formatting
- **Style**: Follow modern JavaScript/ES6+ practices
- **Components**: Use Svelte 5 runes syntax (`$state`, `$effect`, etc.)

### Commit Messages
Use [Conventional Commits](https://www.conventionalcommits.org/) format:
```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Examples:
- `feat: add URL processing with content extraction`
- `fix: resolve JSON parsing error in backend communication`
- `docs: update installation instructions for Windows`

## 🧪 Testing

### Running Tests

**Frontend Tests:**
```bash
cd frontend
npm test
```

**Backend Tests:**
```bash
cd backend
python -m pytest
```

**Integration Tests:**
```bash
cd backend
python test_backend.py
```

### Writing Tests

- Add unit tests for all new backend functions
- Include integration tests for new Tauri commands
- Test error conditions and edge cases
- Maintain test coverage above 80%

## 🔧 Development Workflow

### Before You Start

1. **Check existing issues** - Look for related issues or feature requests
2. **Discuss major changes** - Open an issue to discuss significant changes
3. **Update documentation** - Ensure your changes are documented

### Pull Request Process

1. **Ensure tests pass** - All existing tests must continue to pass
2. **Add tests** - Include tests for new functionality
3. **Update documentation** - Update README.md and inline docs as needed
4. **Clean commit history** - Squash commits if necessary
5. **Fill out PR template** - Provide detailed description of changes

### PR Requirements

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts with main branch

## 🐛 Bug Reports

### Before Submitting

1. **Search existing issues** - Check if the bug has already been reported
2. **Reproduce the bug** - Ensure you can consistently reproduce the issue
3. **Gather information** - Collect system info, logs, and steps to reproduce

### Bug Report Template

```markdown
**Describe the bug**
A clear description of the bug.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Environment:**
- OS: [e.g. Windows 10, macOS 12, Ubuntu 20.04]
- LibreAssistant Version: [e.g. 0.1.0]
- Python Version: [e.g. 3.10.5]
- Node.js Version: [e.g. 18.17.0]

**Additional context**
Add any other context, logs, or screenshots.
```

## 💡 Feature Requests

### Before Submitting

1. **Check the roadmap** - See if the feature is already planned
2. **Search existing issues** - Look for similar feature requests
3. **Consider the scope** - Ensure the feature aligns with project goals

### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Problem Statement**
What problem does this feature solve?

**Proposed Solution**
How would you like this feature to work?

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Any other context, mockups, or examples.
```

## 🔒 Security

### Reporting Security Issues

**Do not report security vulnerabilities through public GitHub issues.**

Instead, please email security concerns to: aubreyhayes47@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Any suggested fixes

## 📋 Code Review Process

### What We Look For

- **Functionality** - Does the code work as intended?
- **Performance** - Is the code efficient?
- **Security** - Are there any security implications?
- **Maintainability** - Is the code readable and well-documented?
- **Testing** - Is the code adequately tested?

### Review Timeline

- **Small PRs** - Usually reviewed within 1-2 days
- **Large PRs** - May take 3-5 days for thorough review
- **Critical fixes** - Prioritized for same-day review

## 🌟 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes for significant contributions
- Special recognition for first-time contributors

## 📞 Getting Help

- **GitHub Discussions** - For questions and general discussion
- **GitHub Issues** - For bug reports and feature requests
- **Discord** - [Join our community chat] (link TBD)

## 📜 Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code.

## 📄 License

By contributing to LibreAssistant, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to LibreAssistant! Together, we're building a privacy-first AI assistant that puts users in control. 🚀
