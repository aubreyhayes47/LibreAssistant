<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# API Overview

LibreAssistant exposes a FastAPI service with endpoints for plugin invocation, user data management, provider integration, and transparency dashboards.

## Invocation
- `POST /api/v1/invoke` – invoke a registered plugin

## History
- `GET /api/v1/history/{user_id}` – return a user's past plugin invocations

## Personal Data Vault
- `POST /api/v1/vault/{user_id}` – store data
- `GET /api/v1/vault/{user_id}` – retrieve stored data
- `GET /api/v1/vault/{user_id}/export` – export stored data
- `DELETE /api/v1/vault/{user_id}` – delete stored data
- `POST /api/v1/consent/{user_id}` – set consent flag
- `GET /api/v1/consent/{user_id}` – get consent status

## Provider Integration
- `POST /api/v1/providers/{name}/key` – configure an API key for a provider
- `POST /api/v1/generate` – generate a response using the specified provider

## Themes
- `GET /api/v1/themes/{theme_id}.css` – return sanitized CSS for a theme. The response is served with a strict `Content-Security-Policy` header.

## Transparency
- `GET /api/v1/bom` – list application dependencies, installed models, and datasets. The endpoint scans
  directories specified by `LA_MODELS_DIR` and `LA_DATASETS_DIR` (defaulting to `models/` and `datasets/`).
- `GET /api/v1/health` – expose request counts and runtime metrics
