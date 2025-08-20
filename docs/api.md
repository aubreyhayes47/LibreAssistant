<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# API Overview

LibreAssistant exposes a FastAPI service with endpoints for plugin invocation, user data management, provider integration, and transparency dashboards.

## Invocation
- `POST /api/v1/invoke` – invoke a registered plugin

## History
- `GET /api/v1/history/{user_id}` – return a user's past plugin invocations

## Audit
- `GET /api/v1/audit/file` – return file operation audit logs
- `GET /api/v1/audit/file/{user_id}` – return file operation logs for a user

## Personal Data Vault
- `POST /api/v1/vault/{user_id}` – store data
- `GET /api/v1/vault/{user_id}` – retrieve stored data
- `GET /api/v1/vault/{user_id}/export` – export stored data
- `DELETE /api/v1/vault/{user_id}` – delete stored data
- `POST /api/v1/consent/{user_id}` – set consent flag
- `GET /api/v1/consent/{user_id}` – get consent status

See [data-vault.md](data-vault.md) for consent workflow, storage format, key
rotation, and security implications.

## Provider Integration
- `POST /api/v1/providers/{name}/key` – configure an API key for a provider
- `POST /api/v1/generate` – generate a response using the specified provider

### Configuration

Environment variables define default model parameters and simple rate limits:

| Provider | Variables |
| --- | --- |
| OpenAI | `OPENAI_MODEL`, `OPENAI_MAX_TOKENS`, `OPENAI_TEMPERATURE`, `OPENAI_RATE_LIMIT` |
| Local  | `LOCAL_URL`, `LOCAL_MODEL`, `LOCAL_MAX_TOKENS`, `LOCAL_TEMPERATURE`, `LOCAL_RATE_LIMIT` |

API keys are supplied via the key endpoint above.  The local provider expects an
HTTP server such as [Ollama](https://ollama.com/) running at
`http://localhost:11434/api/generate` by default.  Install Ollama and launch a
model with `ollama run llama2`, or adjust the `LOCAL_` variables to point to a
different server or model.

## MCP Registry
- `GET /api/v1/mcp/servers` – list servers from the MCP registry and their
  consent status
- `POST /api/v1/mcp/consent/{name}` – set consent for an MCP server
- `GET /api/v1/mcp/consent/{name}` – get consent for an MCP server

Registry entries may include a `network` object describing `allow`, `deny`, and
`protocols` lists. A `defaultNetwork` policy applies to servers without explicit
rules. These settings control which hosts and protocols a server may access.

## Themes
- `GET /api/v1/themes/{theme_id}.css` – return sanitized CSS for a theme. The response is served with a strict `Content-Security-Policy` header.

## Transparency
- `GET /api/v1/bom` – list application dependencies, installed models, and datasets. The endpoint scans
  directories specified by `LA_MODELS_DIR` and `LA_DATASETS_DIR` (defaulting to `models/` and `datasets/`).
- `GET /api/v1/health` – expose request counts and runtime metrics
