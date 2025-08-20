<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Transparency Endpoints

LibreAssistant provides endpoints for inspecting runtime behavior and deployed assets.

## `/api/v1/bom`

This endpoint returns a "Bill of Materials" describing the environment in which the
application is running. The response contains:

- `dependencies` – Python packages discovered via `importlib.metadata`, reported as
  `name==version` strings. This allows operators to verify the exact library versions
  loaded at runtime.
- `models` – files and directories in the models directory referenced by
  `LA_MODELS_DIR` (default `models/`). Hidden entries are excluded. Each item
  indicates a model artifact available to the application.
- `datasets` – files and directories in the datasets directory referenced by
  `LA_DATASETS_DIR` (default `datasets/`). Hidden entries are excluded. Each item
  represents a dataset available locally.

Use this endpoint to audit the dependencies and data sources bundled with an
instance and confirm that expected resources are present.

## `/api/v1/health`

This endpoint reports basic runtime metrics collected by the `HealthMonitor`.
The response includes:

- `status` – `"ok"` when no errors have been recorded, otherwise `"error"`.
- `uptime` – number of seconds the process has been running.
- `requests` – total number of HTTP requests observed since startup.
- `error_count` – cumulative number of error events.
- `errors` – up to 100 of the most recent error messages.

Interpreting the status allows administrators to quickly determine if the service
has encountered errors. Request counts and uptime can be used for basic traffic and
availability monitoring, while the error list surfaces recent failures.

## HealthMonitor internals

`HealthMonitor` is an in-memory tracker instantiated when the FastAPI application
is created. Middleware increments the request counter for every inbound request and
records errors when exceptions occur or responses have a status code of 500 or
higher. Errors are stored in a fixed-size queue, keeping only the 100 most recent
messages.

Calling `/api/v1/health` returns a snapshot of these values, allowing operators to
observe request rates, uptime, and whether any errors have been seen since startup.
