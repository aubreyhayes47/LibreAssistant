# Codex Development Guide

This repository contains the LibreAssistant application with a Python backend and a Tauri/Svelte frontend. When making changes with Codex or other tooling, follow the steps below so tests and lint checks pass consistently.

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
