# Troubleshooting Guide

This guide helps resolve common issues when setting up or running LibreAssistant.

## Installation Issues

### Python Virtual Environment

**Problem**: Virtual environment not working

**Solutions**:
1. Make sure Python 3.10+ is installed: `python --version`
2. Create virtual environment explicitly:
   ```bash
   python -m venv .venv
   ```
3. On Windows, activate with: `.venv\Scripts\activate`
4. On Linux/macOS, activate with: `source .venv/bin/activate`
5. Verify activation: `which python` should show the `.venv` path

### Node.js Dependencies

**Problem**: `npm install` fails

**Solutions**:
1. Clear npm cache: `npm cache clean --force`
2. Delete node_modules: `rm -rf node_modules package-lock.json`
3. Update Node.js to latest LTS version
4. Run `npm install` again

### Rust/Tauri Issues

**Problem**: Tauri compilation fails

**Solutions**:
1. Update Rust: `rustup update`
2. Install required system dependencies:
   - **Windows**: Visual Studio Build Tools
   - **Linux**: `sudo apt install build-essential webkit2gtk-4.0-dev`
   - **macOS**: `xcode-select --install`
3. Clean build: `cd frontend/src-tauri && cargo clean`

## Runtime Issues

### Backend Connection Failed

**Problem**: Frontend can't connect to Python backend

**Solutions**:
1. Check Python virtual environment is activated
2. Verify all dependencies installed: `pip list`
3. Test backend manually:
   ```bash
   cd backend
   python main.py hello '{"name": "test"}'
   ```
4. Check backend logs for errors
5. Ensure UTF-8 encoding: set `PYTHONIOENCODING=utf-8`

### Database Initialization Failed

**Problem**: Database operations don't work

**Solutions**:
1. Initialize database manually:
   ```javascript
   await invoke('init_database');
   ```
2. Check write permissions in project directory
3. Delete existing database file and reinitialize
4. Verify SQLAlchemy dependencies installed

### Ollama Connection Issues

**Problem**: LLM chat doesn't work

**Solutions**:
1. Install Ollama: https://ollama.ai/
2. Start Ollama service: `ollama serve`
3. Pull a model: `ollama pull llama2`
4. Check Ollama is running on port 11434
5. Set correct Ollama host in `.env` file:
   ```
   OLLAMA_HOST=http://localhost:11434
   ```

## Development Issues

### Hot Reload Not Working

**Problem**: Changes don't appear during development

**Solutions**:
1. Stop and restart dev server: `npm run tauri:dev`
2. Clear browser cache if using web preview
3. Check file watchers aren't hitting system limits (Linux)
4. Verify files are being saved correctly

### Build Errors

**Problem**: Production build fails

**Solutions**:
1. Run development build first: `npm run tauri:dev`
2. Fix any TypeScript/Svelte errors: `npm run check`
3. Clear build cache: `rm -rf build dist`
4. Check disk space and permissions
5. Build step by step:
   ```bash
   npm run build      # Build frontend
   npm run tauri:build # Build Tauri app
   ```

### Import/Module Errors

**Problem**: Module not found or import errors

**Solutions**:
1. Check file paths are correct (case-sensitive on Linux/macOS)
2. Verify import statements use correct syntax
3. Check `package.json` has required dependencies
4. For Python modules, verify virtual environment activated
5. Update import paths in `jsconfig.json` if needed

## Platform-Specific Issues

### Windows

**Problem**: Command not found or permission errors

**Solutions**:
1. Use Git Bash or PowerShell instead of Command Prompt
2. Run as administrator if permission errors
3. Add Python to PATH environment variable
4. Install Visual Studio Build Tools for C++ compilation
5. Check Windows Defender isn't blocking files

### Linux

**Problem**: System dependencies missing

**Solutions**:
1. Install development tools:
   ```bash
   sudo apt update
   sudo apt install build-essential
   ```
2. Install webkit dependencies:
   ```bash
   sudo apt install webkit2gtk-4.0-dev libgtk-3-dev
   ```
3. Increase file watcher limits:
   ```bash
   echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
   sudo sysctl -p
   ```

### macOS

**Problem**: Compilation or signing issues

**Solutions**:
1. Install Xcode Command Line Tools:
   ```bash
   xcode-select --install
   ```
2. Accept Xcode license: `sudo xcodebuild -license accept`
3. Use Homebrew for dependencies if needed
4. Check macOS version compatibility with Tauri

## Performance Issues

### Slow Startup

**Problem**: Application takes long to start

**Solutions**:
1. Check available disk space (database needs space)
2. Disable unnecessary background processes
3. Use SSD storage if possible
4. Clear old log files and temporary data
5. Optimize database by running cleanup commands

### Memory Usage

**Problem**: High memory consumption

**Solutions**:
1. Clear chat history: `invoke('clear_chat_history')`
2. Clear browser history: `invoke('clear_browser_history')`
3. Clear conversation context: `invoke('clear_conversation_context')`
4. Restart application periodically
5. Check for memory leaks in browser dev tools

## Getting Help

### Debugging Steps

1. **Check logs**: Look in console output for error messages
2. **Test components**: Use the backend connection test in the UI
3. **Verify setup**: Run through SETUP.md instructions again
4. **Check versions**: Ensure all tools are correct versions
5. **Minimal reproduction**: Test with fresh clone

### Reporting Issues

When reporting a bug, include:

1. **System information**: OS, Python version, Node version
2. **Error messages**: Copy full error output
3. **Steps to reproduce**: Exact sequence that causes issue
4. **Expected vs actual behavior**: What should happen vs what does
5. **Logs**: Relevant console output or log files

### Community Resources

- **GitHub Issues**: https://github.com/aubreyhayes47/LibreAssistant/issues
- **Documentation**: README.md, API.md, SETUP.md
- **Contributing**: CONTRIBUTING.md for development guidelines

## Quick Fixes Checklist

Before seeking help, try these quick fixes:

- [ ] Restart the application
- [ ] Check virtual environment is activated
- [ ] Run `npm install` and `pip install -r backend/requirements.txt`
- [ ] Clear browser cache/storage
- [ ] Check all required services are running (Ollama)
- [ ] Verify file permissions
- [ ] Check available disk space
- [ ] Look for typos in configuration files
- [ ] Test with minimal/default configuration
- [ ] Check system firewall/antivirus settings
