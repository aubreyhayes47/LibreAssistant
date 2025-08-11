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

## Transparency
- `GET /api/v1/bom` – list application dependencies and versions
- `GET /api/v1/health` – expose request counts and runtime metrics
