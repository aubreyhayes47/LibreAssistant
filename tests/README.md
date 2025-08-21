<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Tests

This directory contains the test suite for LibreAssistant.

## Layout

* Python tests live at the root of this folder (e.g., `test_cli.py`, `test_kernel.py`).
* Expert analysis modules have dedicated tests such as `test_experts_argumentation.py`,
  `test_experts_communications.py`, `test_experts_devils_advocate.py`,
  `test_experts_executive.py`, `test_experts_research.py`, and
  `test_experts_visualizer.py`.
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

### npm proxy warnings

If running `npm` commands produces a warning like `npm warn Unknown env config "http-proxy"`, clear any old proxy settings by running:

```bash
npm_config_http_proxy="" npm_config_https_proxy="" npm test
```

Setting the variables to empty strings removes the deprecated `http-proxy` configuration.

## Environment variables and mocks

Some tests rely on environment variables to inject test data:

* `THINK_TANK_MODEL_RESPONSE` – provides a mocked Think Tank analysis used by `tests/test_think_tank_plugin.py` and `tests/mcp/think_tank.test.ts`.
* `LIBRE_DB_PATH` and `LIBRE_DB_KEY` – temporary database path and encryption key for `tests/test_db_encryption.py`.
* `LA_MODELS_DIR` and `LA_DATASETS_DIR` – temporary directories for transparency tests in `tests/test_transparency.py`.

These variables are typically set by the tests themselves via monkeypatch but can be set manually when running individual tests.
