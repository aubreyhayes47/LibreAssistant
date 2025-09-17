# Security Policy

## Supported Versions

We actively support the following versions of My Ollama Wrapper:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

The My Ollama Wrapper team takes security seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Open a Public Issue

Please **do not** report security vulnerabilities through public GitHub issues, discussions, or pull requests.

### 2. Send a Private Report

Instead, please send an email to [security@yourproject.com] with:

- A clear description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes (if you have them)

### 3. What to Include

Please include as much information as possible:

- **Type of vulnerability** (e.g., authentication bypass, XSS, etc.)
- **Location** of the vulnerability (file paths, line numbers, etc.)
- **Proof of concept** or exploit code (if applicable)
- **Environment details** (OS, browser, Node.js version, etc.)
- **Screenshots** or video demonstrations (if helpful)

### 4. Response Timeline

We aim to respond to security reports within:

- **Initial response**: 48 hours
- **Vulnerability assessment**: 1 week
- **Fix development**: 2-4 weeks (depending on complexity)
- **Public disclosure**: After fix is released

### 5. Responsible Disclosure

We follow a responsible disclosure process:

1. You report the vulnerability privately
2. We confirm and assess the vulnerability
3. We develop and test a fix
4. We release the fix
5. We publicly acknowledge your contribution (if desired)

## Security Best Practices

### For Users

- Keep your installation up to date
- Use HTTPS when possible
- Regularly update Ollama and Node.js
- Review and configure environment variables properly
- Use strong authentication if exposing the service

### For Contributors

- Follow secure coding practices
- Validate all user inputs
- Use parameterized queries for any database operations
- Implement proper authentication and authorization
- Regularly update dependencies
- Use static analysis tools

## Common Security Considerations

### Ollama Integration

- Ensure Ollama is properly configured and secured
- Validate all API responses from Ollama
- Implement rate limiting for API calls
- Sanitize user inputs before sending to models

### Web Application Security

- Implement Content Security Policy (CSP)
- Use HTTPS in production
- Validate and sanitize all user inputs
- Implement proper session management
- Protect against XSS and CSRF attacks

### Data Privacy

- Do not log sensitive user conversations
- Implement proper data retention policies
- Provide clear privacy controls for users
- Ensure compliance with relevant privacy regulations

## Security Updates

Security updates will be released as:

1. **Patch releases** for minor vulnerabilities
2. **Minor releases** for moderate vulnerabilities
3. **Emergency releases** for critical vulnerabilities

All security updates will be clearly marked in:
- Release notes
- CHANGELOG.md
- Security advisories

## Bug Bounty

Currently, we do not offer a formal bug bounty program. However, we greatly appreciate security researchers who help improve the security of our project and will acknowledge contributions appropriately.

## Contact

For security-related questions or concerns:
- Email: [security@yourproject.com]
- For urgent matters, use the subject line: "URGENT SECURITY ISSUE"

Thank you for helping keep My Ollama Wrapper secure! 🔒