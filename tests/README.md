# Tests

This directory contains the test suite for LibreAssistant.

## Layout

* Python tests live at the root of this folder (e.g., `test_cli.py`, `test_kernel.py`).
* TypeScript tests for the Model Context Protocol (MCP) adapters live in `mcp/*.test.ts`.

## Running Python tests

Python tests use `pytest`. From the repository root:

```bash
pytest
```

## Running TypeScript tests

The TypeScript tests use Node's built-in test runner with `ts-node`. Install dependencies and run:

```bash
npm install
npm test
```

This executes all `*.test.ts` files under `tests/mcp`.

## Environment variables and mocks

Some tests rely on environment variables to inject test data:

* `THINK_TANK_MODEL_RESPONSE` – provides a mocked Think Tank analysis used by `tests/test_think_tank_plugin.py` and `tests/mcp/think_tank.test.ts`.
* `LIBRE_DB_PATH` and `LIBRE_DB_KEY` – temporary database path and encryption key for `tests/test_db_encryption.py`.
* `LA_MODELS_DIR` and `LA_DATASETS_DIR` – temporary directories for transparency tests in `tests/test_transparency.py`.

These variables are typically set by the tests themselves via monkeypatch but can be set manually when running individual tests.

