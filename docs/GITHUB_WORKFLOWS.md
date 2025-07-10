# GitHub Workflows Configuration

LibreAssistant uses GitHub Actions for continuous integration and automated testing.

## Current Status

**Implemented**: ✅ Basic workflow files exist in `.github/`
**Missing**: ❌ Comprehensive CI/CD workflows for testing and releases

## Required Workflow Files

### 1. `.github/workflows/test.yml` - Main Test Suite

```yaml
name: LibreAssistant Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  backend-tests:
    name: Backend Tests (Python)
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd backend
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio
    
    - name: Run model validation tests
      run: |
        cd backend
        python test_models_validation.py
    
    - name: Run unit tests
      run: |
        cd backend
        python -m pytest tests/ --cov=. --cov-report=xml --cov-report=html
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        directory: ./backend
        fail_ci_if_error: true

  frontend-tests:
    name: Frontend Tests (Svelte)
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Install dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Run tests
      run: |
        cd frontend
        npm run test
    
    - name: Run linting
      run: |
        cd frontend
        npm run lint

  build-test:
    name: Build Test (Tauri)
    runs-on: ${{ matrix.platform }}
    
    strategy:
      fail-fast: false
      matrix:
        platform: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        cache: 'npm'
        cache-dependency-path: frontend/package-lock.json
    
    - name: Setup Rust
      uses: dtolnay/rust-toolchain@stable
    
    - name: Install Linux dependencies
      if: matrix.platform == 'ubuntu-latest'
      run: |
        sudo apt-get update
        sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev librsvg2-dev
    
    - name: Install frontend dependencies
      run: |
        cd frontend
        npm ci
    
    - name: Build application
      run: |
        cd frontend
        npm run tauri build
```

### 2. `.github/workflows/release.yml` - Release Automation

```yaml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  create-release:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    outputs:
      release_id: ${{ steps.create-release.outputs.result }}

    steps:
      - uses: actions/checkout@v4
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
      - name: Get version
        run: echo "PACKAGE_VERSION=$(node -pe "require('./frontend/package.json').version")" >> $GITHUB_ENV
      - name: Create release
        id: create-release
        uses: actions/github-script@v6
        with:
          script: |
            const { data } = await github.rest.repos.createRelease({
              owner: context.repo.owner,
              repo: context.repo.repo,
              tag_name: `v${process.env.PACKAGE_VERSION}`,
              name: `LibreAssistant v${process.env.PACKAGE_VERSION}`,
              body: 'See CHANGELOG.md for details.',
              draft: true,
              prerelease: false
            })
            return data.id

  build-tauri:
    needs: create-release
    permissions:
      contents: write
    strategy:
      fail-fast: false
      matrix:
        platform: [macos-latest, ubuntu-latest, windows-latest]

    runs-on: ${{ matrix.platform }}
    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable

      - name: Install Linux dependencies
        if: matrix.platform == 'ubuntu-latest'
        run: |
          sudo apt-get update
          sudo apt-get install -y libgtk-3-dev libwebkit2gtk-4.0-dev librsvg2-dev

      - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci

      - uses: tauri-apps/tauri-action@v0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          releaseId: ${{ needs.create-release.outputs.release_id }}
          projectPath: frontend

  publish-release:
    permissions:
      contents: write
    runs-on: ubuntu-latest
    needs: [create-release, build-tauri]

    steps:
      - name: Publish release
        id: publish-release
        uses: actions/github-script@v6
        env:
          release_id: ${{ needs.create-release.outputs.release_id }}
        with:
          script: |
            github.rest.repos.updateRelease({
              owner: context.repo.owner,
              repo: context.repo.repo,
              release_id: process.env.release_id,
              draft: false,
              prerelease: false
            })
```

## Issue Templates

### Bug Report Template

File: `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug report
about: Create a report to help us improve LibreAssistant
title: '[BUG] '
labels: bug
assignees: ''

---

**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Environment (please complete the following information):**
 - OS: [e.g. Windows 11, macOS 13, Ubuntu 22.04]
 - LibreAssistant Version: [e.g. 0.1.0]
 - Ollama Version: [e.g. 0.1.20]
 - Available RAM: [e.g. 16GB]

**Ollama Configuration:**
 - Models installed: [e.g. llama2, codellama]
 - Currently running: [e.g. yes/no]
 - Ollama logs: [if relevant]

**Additional context**
Add any other context about the problem here.

**Privacy Note**
Please ensure you don't include any sensitive personal information in this bug report. LibreAssistant processes data locally, but be mindful of what you share in public issues.
```

### Feature Request Template

File: `.github/ISSUE_TEMPLATE/feature_request.md`

```markdown
---
name: Feature request
about: Suggest an idea for LibreAssistant
title: '[FEATURE] '
labels: enhancement
assignees: ''

---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. Ex. I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**Implementation considerations**
If you have thoughts on how this could be implemented while maintaining LibreAssistant's privacy-first approach, please share them.

**Additional context**
Add any other context or screenshots about the feature request here.

**Privacy implications**
Please consider how this feature might affect user privacy and data handling.
```

## Pull Request Template

File: `.github/pull_request_template.md`

```markdown
## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement

## Related Issues

Fixes #(issue number)

## Implementation Details

### Backend Changes
- [ ] Database model changes
- [ ] API endpoint changes
- [ ] Service layer changes
- [ ] New dependencies added

### Frontend Changes
- [ ] UI component changes
- [ ] Store/state management changes
- [ ] New Tauri commands
- [ ] Styling updates

### Tauri Changes
- [ ] New Rust commands
- [ ] Configuration changes
- [ ] Dependency updates

## Testing

- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed
- [ ] All existing tests pass

### Test Coverage
- Backend coverage: [percentage]
- Frontend coverage: [percentage]

## Privacy & Security

- [ ] No sensitive data exposed in logs
- [ ] Input validation implemented
- [ ] Data retention policies respected
- [ ] Local-only processing maintained

## Performance Impact

- [ ] No significant performance regression
- [ ] Memory usage acceptable
- [ ] Database queries optimized
- [ ] Bundle size impact minimal

## Documentation

- [ ] Code comments added/updated
- [ ] API documentation updated
- [ ] User guide updated (if needed)
- [ ] CHANGELOG.md updated

## Checklist

- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] No console errors or warnings
- [ ] Builds successfully on all platforms
- [ ] All CI checks pass

## Screenshots (if applicable)

[Add screenshots for UI changes]

## Additional Notes

[Any additional information, concerns, or considerations]
```

## Current Implementation Status

**Existing Files in `.github/`:**
- ✅ `ISSUE_TEMPLATE/` directory exists
- ✅ `PULL_REQUEST_TEMPLATE.md` exists
- ✅ `SECURITY.md` exists
- ❌ Missing: `workflows/test.yml`
- ❌ Missing: `workflows/release.yml`
- ❌ Missing: Comprehensive issue templates

## Next Steps

1. **Create Missing Workflows** (Priority: High)
   - Add `test.yml` for automated testing
   - Add `release.yml` for automated releases

2. **Update Issue Templates** (Priority: Medium)
   - Enhance existing templates with LibreAssistant-specific context
   - Add privacy considerations to all templates

3. **Configure Branch Protection** (Priority: Medium)
   - Require PR reviews
   - Require passing tests
   - Require up-to-date branches

This CI/CD infrastructure will ensure code quality and streamline the development process as LibreAssistant grows.
