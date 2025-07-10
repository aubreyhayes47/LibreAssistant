# LibreAssistant Build Guide

⚠️ **Project Status**: LibreAssistant is currently in proof-of-concept state. This guide covers building the current CLI-based backend with Tauri frontend.

This guide covers building LibreAssistant from source for all supported platforms.

## Current Architecture

- **Frontend**: Tauri + Svelte 4 (Svelte 5 migration planned)
- **Backend**: Python CLI processing (FastAPI migration planned)
- **Database**: SQLite with SQLAlchemy
- **AI**: Local Ollama integration

See the [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) for planned architecture improvements.

## Prerequisites

### System Requirements

**Windows:**
- Windows 10/11 (64-bit)
- Visual Studio Build Tools 2019+ or Visual Studio 2019+
- Git for Windows

**macOS:**
- macOS 10.15+ 
- Xcode Command Line Tools
- Homebrew (recommended)

**Linux:**
- Ubuntu 20.04+ or equivalent
- Build essentials package
- Git

### Development Tools

**Required:**
- Node.js 18.17.0+ 
- Python 3.11+
- Rust 1.70.0+
- Ollama (for AI features)

**Installation Commands:**

```bash
# Windows (using chocolatey)
choco install nodejs python rust ollama

# macOS (using homebrew)
brew install node python@3.11 rust ollama

# Ubuntu/Debian
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs python3.11 python3.11-venv
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
curl -fsSL https://ollama.ai/install.sh | sh
```

## Build Process

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/LibreAssistant.git
cd LibreAssistant
```

### 2. Setup Python Backend

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Setup Frontend

```bash
cd frontend

# Install Node.js dependencies
npm install

# Install Tauri CLI (if not already installed)
npm install -g @tauri-apps/cli
```

### 4. Development Build

```bash
# From frontend directory
npm run tauri dev
```

This will:
- Start the Python backend
- Compile Rust components
- Launch the development app
- Enable hot reload for frontend changes

### 5. Production Build

```bash
# From frontend directory
npm run tauri build
```

Build artifacts will be in:
- **Windows:** `frontend/src-tauri/target/release/bundle/`
- **macOS:** `frontend/src-tauri/target/release/bundle/dmg/`
- **Linux:** `frontend/src-tauri/target/release/bundle/`

## Platform-Specific Instructions

### Windows

**Additional Requirements:**
- Microsoft C++ Build Tools
- Windows SDK

**Build Commands:**
```cmd
# Set up environment
call "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

# Build
cd frontend
npm run tauri build
```

**Troubleshooting:**
- If Rust compiler fails, ensure Visual Studio Build Tools are installed
- For signing issues, see code signing section below

### macOS

**Additional Requirements:**
- Xcode Command Line Tools: `xcode-select --install`

**Build Commands:**
```bash
cd frontend
npm run tauri build
```

**Troubleshooting:**
- For notarization, you'll need an Apple Developer account
- Ensure all dependencies are compatible with your macOS version

### Linux

**Additional Requirements:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y \
    libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
```

**Build Commands:**
```bash
cd frontend
npm run tauri build
```

## Build Optimization

### Release Optimization

For smaller binary sizes:

```toml
# In frontend/src-tauri/Cargo.toml
[profile.release]
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

### Bundle Optimization

```json
// In frontend/src-tauri/tauri.conf.json
{
  "tauri": {
    "bundle": {
      "targets": ["nsis", "msi"], // Windows
      "resources": ["../backend/**/*"]
    }
  }
}
```

## Distribution

### Code Signing

**Windows:**
```bash
# Sign with certificate
tauri build -- --sign-tool signtool \
  --sign-tool-args "/f path/to/cert.p12 /p password"
```

**macOS:**
```bash
# Sign with Apple Developer certificate
export APPLE_CERTIFICATE="Developer ID Application: Your Name"
export APPLE_ID="your@email.com"
export APPLE_PASSWORD="app-specific-password"

npm run tauri build
```

### Creating Installers

**Windows Installer (NSIS):**
```json
{
  "bundle": {
    "targets": ["nsis"],
    "windows": {
      "nsis": {
        "displayLanguageSelector": true,
        "languages": ["English"],
        "template": "./installer.nsi"
      }
    }
  }
}
```

**macOS DMG:**
```json
{
  "bundle": {
    "targets": ["dmg"],
    "macOS": {
      "dmg": {
        "background": "./dmg-background.png",
        "windowSize": {
          "width": 660,
          "height": 400
        }
      }
    }
  }
}
```

**Linux AppImage:**
```json
{
  "bundle": {
    "targets": ["appimage"],
    "linux": {
      "appimage": {
        "bundleMediaFramework": true
      }
    }
  }
}
```

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/build.yml
name: Build LibreAssistant

on:
  push:
    tags: ['v*']

jobs:
  build:
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    runs-on: ${{ matrix.os }}
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
          
      - name: Install dependencies
        run: |
          cd backend && pip install -r requirements.txt
          cd frontend && npm install
          
      - name: Build
        run: |
          cd frontend
          npm run tauri build
          
      - name: Upload artifacts
        uses: actions/upload-artifact@v3
        with:
          name: LibreAssistant-${{ matrix.os }}
          path: frontend/src-tauri/target/release/bundle/
```

## Troubleshooting

### Common Build Issues

**Python Virtual Environment:**
```bash
# If venv creation fails
python -m pip install --upgrade pip
python -m pip install virtualenv
python -m virtualenv venv
```

**Rust Compilation Errors:**
```bash
# Update Rust toolchain
rustup update

# Clear build cache
cd frontend/src-tauri
cargo clean
```

**Node.js Dependencies:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Tauri Build Failures:**
```bash
# Ensure Tauri CLI is up to date
npm install -g @tauri-apps/cli@latest

# Check system dependencies
tauri info
```

### Performance Issues

**Slow Builds:**
- Use `cargo build --release` for optimized builds
- Enable parallel compilation: `export CARGO_BUILD_JOBS=4`
- Use SSD storage for faster I/O

**Large Bundle Size:**
- Enable LTO (Link Time Optimization)
- Strip debug symbols
- Exclude unnecessary files from bundle

### Platform-Specific Issues

**Windows:**
- Path length limitations: Use shorter paths
- Antivirus interference: Add build directory to exclusions
- Permission issues: Run as administrator if needed

**macOS:**
- Gatekeeper issues: Sign binaries properly
- Notarization required for distribution
- Architecture-specific builds for Intel/Apple Silicon

**Linux:**
- Missing system libraries: Install dev packages
- AppImage permissions: Make executable after build
- Distribution-specific package managers

## Build Verification

### Testing Builds

```bash
# Test development build
npm run tauri dev

# Test production build
./target/release/bundle/LibreAssistant

# Run integration tests
npm run test
python -m pytest backend/tests/
```

### Automated Testing

```bash
# Frontend tests
cd frontend
npm run test

# Backend tests
cd backend
python -m pytest

# E2E tests
npm run test:e2e
```

## Docker Development (Optional)

### Development Container

```dockerfile
# Dockerfile.dev
FROM ubuntu:22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    libwebkit2gtk-4.0-dev \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
RUN apt-get install -y nodejs

# Install Python
RUN apt-get install -y python3.11 python3.11-venv python3-pip

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /app
COPY . .

# Setup environment
RUN cd backend && python3.11 -m venv venv && \
    . venv/bin/activate && pip install -r requirements.txt

RUN cd frontend && npm install

EXPOSE 3000 1420

CMD ["npm", "run", "tauri", "dev"]
```

### Usage

```bash
# Build development container
docker build -f Dockerfile.dev -t libreassistant-dev .

# Run development environment
docker run -it -p 3000:3000 -p 1420:1420 \
  -v $(pwd):/app libreassistant-dev
```

## Release Checklist

### Pre-Release

- [ ] All tests pass
- [ ] Documentation updated
- [ ] Version numbers bumped
- [ ] Changelog updated
- [ ] Security review completed

### Build Process

- [ ] Clean build environment
- [ ] Run full test suite
- [ ] Build for all platforms
- [ ] Sign binaries (if applicable)
- [ ] Create installers

### Post-Release

- [ ] Upload to distribution channels
- [ ] Update website/documentation
- [ ] Announce release
- [ ] Monitor for issues

## Build Automation

### Makefile Example

```makefile
# Makefile
.PHONY: setup dev build test clean

setup:
	cd backend && python -m venv venv && \
	. venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

dev:
	cd frontend && npm run tauri dev

build:
	cd frontend && npm run tauri build

test:
	cd backend && . venv/bin/activate && python -m pytest
	cd frontend && npm test

clean:
	cd frontend && rm -rf node_modules target
	cd backend && rm -rf venv __pycache__ .pytest_cache

install-deps-ubuntu:
	sudo apt update && sudo apt install -y \
		libwebkit2gtk-4.0-dev build-essential curl wget \
		libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev

install-deps-macos:
	brew install node python@3.11 rust

install-deps-windows:
	choco install nodejs python rust
```

### Usage

```bash
# Setup development environment
make setup

# Start development server
make dev

# Build for production
make build

# Run tests
make test

# Clean build artifacts
make clean
```

This build guide ensures reliable, reproducible builds across all supported platforms while maintaining LibreAssistant's privacy-first architecture.
