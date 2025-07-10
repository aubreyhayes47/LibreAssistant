# Development Setup Guide

This guide provides detailed instructions for setting up LibreAssistant for development on different platforms.

## Prerequisites

### Required Software

1. **Rust** (latest stable)
   - Install from [rustup.rs](https://rustup.rs)
   - Verify: `rustc --version`

2. **Node.js** (18+ recommended)
   - Install from [nodejs.org](https://nodejs.org)
   - Verify: `node --version` and `npm --version`

3. **Python** (3.10 or higher)
   - Install from [python.org](https://python.org)
   - Verify: `python --version` (or `python3 --version` on Unix systems)

4. **Git**
   - Install from [git-scm.com](https://git-scm.com)
   - Verify: `git --version`

### Platform-Specific Requirements

#### Windows
- Install Visual Studio Build Tools or Visual Studio Community
- Ensure you have the C++ build tools component

#### Linux
- Install build essentials: `sudo apt install build-essential`
- Install webkit2gtk: `sudo apt install webkit2gtk-4.0-dev`

#### macOS
- Install Xcode Command Line Tools: `xcode-select --install`

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/aubreyhayes47/LibreAssistant.git
cd LibreAssistant
```

### 2. Python Backend Setup

#### Option A: Automatic Setup (Linux/macOS)

```bash
./setup.sh
source .venv/bin/activate
```

#### Option B: Manual Setup (All Platforms)

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 3. Frontend Setup

```bash
cd frontend
npm install
cd ..
```

## Development Workflow

### 1. Start Development Server

```bash
# Activate Python environment first
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\activate     # Windows

# Start Tauri development server
cd frontend
npm run tauri:dev
```

### 2. Build for Production

```bash
cd frontend
npm run tauri:build
```

### 3. Run Tests

**Python Backend:**
```bash
cd backend
python -m pytest
```

**Code Quality Checks:**
```bash
cd backend
black .
ruff --fix .
```

**Frontend Checks:**
```bash
cd frontend
npm run check
```

## Troubleshooting

### Common Issues

1. **Python virtual environment not activated**
   - Always activate the virtual environment before running Python commands
   - Check with: `which python` (should show .venv path)

2. **Node dependencies out of date**
   - Delete `node_modules` and `package-lock.json`
   - Run `npm install` again

3. **Rust compilation errors**
   - Update Rust: `rustup update`
   - Clean build: `cargo clean` in `frontend/src-tauri/`

4. **Python import errors**
   - Ensure you're in the correct directory
   - Check that all dependencies are installed: `pip list`

### Platform-Specific Issues

#### Windows
- Use Git Bash or PowerShell, not Command Prompt
- Ensure Python is in your PATH
- Install Visual Studio Build Tools if compilation fails

#### Linux
- Install missing system dependencies: `sudo apt install webkit2gtk-4.0-dev libgtk-3-dev libsoup2.4-dev`

#### macOS
- Install Xcode Command Line Tools
- Use Homebrew for system dependencies if needed

## Development Tools

### Recommended VS Code Extensions

- Rust Analyzer
- Svelte for VS Code
- Python
- Python Docstring Generator
- Prettier - Code formatter
- GitLens

### Configuration Files

- `.env` in `backend/` for environment variables
- `frontend/src-tauri/tauri.conf.json` for Tauri configuration
- `backend/pyproject.toml` and `requirements.txt` for Python dependencies
- `frontend/package.json` for Node.js dependencies

## Next Steps

After successful setup:

1. Start the development server with `npm run tauri:dev`
2. Test the backend connection using the UI
3. Run the test suite to ensure everything works
4. Check the CONTRIBUTING.md for development guidelines
