# Security Policy

⚠️ **Project Status**: LibreAssistant is currently in proof-of-concept state. Security implementations are planned for future development phases.

## Supported Versions

We actively support the latest version of LibreAssistant:

| Version | Supported          | Status |
| ------- | ------------------ | ------ |
| 0.1.x   | :white_check_mark: | Proof-of-concept |

## Current Security State

**Implemented:**
- Local-only data storage (SQLite)
- No external data transmission  
- Basic input validation

**Planned Security Enhancements:**
- **Phase 1.1**: Data encryption at rest
- **Phase 1.2**: Request validation and sanitization
- **Phase 1.3**: User authentication and session security
- **Phase 2**: Advanced privacy controls and audit logging

See the [Implementation Roadmap](../docs/IMPLEMENTATION_ROADMAP.md) for detailed security development plans.

## Reporting a Vulnerability

LibreAssistant is committed to maintaining the privacy and security of our users. If you discover a security vulnerability, we appreciate your help in disclosing it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please send an email to: **aubrey.hayes47@gmail.com**

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact assessment
- Any suggested fixes or mitigations

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Response**: We will provide an initial response within 72 hours
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical issues within 7 days

### Disclosure Policy

- We will work with you to understand and resolve the issue
- We will not take legal action against researchers who:
  - Report vulnerabilities responsibly
  - Do not access or modify user data
  - Do not disrupt our services
- We will publicly acknowledge your responsible disclosure (with your permission)

## Security Features

LibreAssistant is designed with privacy and security in mind:

- **Local-First**: All AI processing happens locally via Ollama
- **No Cloud Dependencies**: No data sent to external services
- **Encrypted Storage**: Sensitive data is encrypted at rest
- **Minimal Attack Surface**: Single-user application with limited network exposure
- **Open Source**: Code is publicly auditable

## Security Best Practices

When using LibreAssistant:

- Keep your installation up to date
- Use the latest stable version of Ollama
- Review the data you allow the application to access
- Keep your system and dependencies updated
- Use strong file system permissions

## Contact

For non-security related issues, please use our [GitHub Issues](https://github.com/aubreyhayes47/LibreAssistant/issues) page.

For security concerns: aubrey.hayes47@gmail.com
