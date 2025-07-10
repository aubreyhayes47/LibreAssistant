# LibreAssistant Development Guide

⚠️ **Project Status**: LibreAssistant is currently in proof-of-concept state with basic functionality implemented.

This repository contains the LibreAssistant application with a Python backend and a Tauri/Svelte frontend. When making changes with Codex or other tooling, follow the steps below so tests and lint checks pass consistently.

## Current Implementation State

- ✅ **Python Backend**: CLI-based command processing
- ✅ **SQLite Database**: Basic operations with SQLAlchemy models  
- ✅ **Tauri Frontend**: Svelte 4 with native command integration
- ✅ **LLM Integration**: Ollama client for local AI processing
- ✅ **Web Scraping**: Basic content extraction with Playwright

## Next Development Phase

See the [Implementation Roadmap](docs/IMPLEMENTATION_ROADMAP.md) for the complete development plan:

1. **Phase 1.1**: Enhanced database operations and migrations
2. **Phase 1.2**: FastAPI backend architecture 
3. **Phase 1.3**: Session management and user state
4. **Phase 1.4**: Svelte 5 migration with modern reactive patterns

## Setup

Run `./setup.sh` once in a fresh environment to install Python and Node dependencies.

## Formatting and Linting

- Python code is formatted with **Black** and linted with **Ruff**.
- Run these from the `backend` directory:
  ```bash
  black --check .
  ruff .
  ```

## Testing

- Backend tests use `pytest`:
  ```bash
  cd backend
  python -m pytest
  ```
- Frontend type checking:
  ```bash
  cd ../frontend
  npm run check
  ```

Always run the formatting, lint, and test commands before committing.
