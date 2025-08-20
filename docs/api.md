<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# API Overview

LibreAssistant exposes a FastAPI service with endpoints for plugin invocation, user data management, provider integration, and transparency dashboards.

## Invocation
- `POST /api/v1/invoke` – invoke a registered plugin

  ```bash
  curl -X POST http://localhost:8000/api/v1/invoke \
    -H "Content-Type: application/json" \
    -d '{"plugin":"echo","user_id":"alice","payload":{"text":"hi"}}'
  ```

  ```json
  {
    "result": {"text": "hi"},
    "state": {"history": []}
  }
  ```

## History
- `GET /api/v1/history/{user_id}` – return a user's past plugin invocations

  ```bash
  curl http://localhost:8000/api/v1/history/alice
  ```

  ```json
  {
    "history": [
      {"plugin": "echo", "payload": {"text": "hi"}, "granted": true}
    ]
  }
  ```

## Audit
- `GET /api/v1/audit/file` – return file operation audit logs

  ```bash
  curl http://localhost:8000/api/v1/audit/file
  ```

  ```json
  {
    "logs": [
      {
        "user_id": "alice",
        "action": "read",
        "path": "/tmp/example.txt",
        "timestamp": "2024-01-01T00:00:00Z"
      }
    ]
  }
  ```

- `GET /api/v1/audit/file/{user_id}` – return file operation logs for a user

  ```bash
  curl http://localhost:8000/api/v1/audit/file/alice
  ```

  ```json
  {
    "logs": [
      {
        "action": "read",
        "path": "/tmp/example.txt",
        "timestamp": "2024-01-01T00:00:00Z"
      }
    ]
  }
  ```

## Personal Data Vault
- `POST /api/v1/vault/{user_id}` – store data

  ```bash
  curl -X POST http://localhost:8000/api/v1/vault/alice \
    -H "Content-Type: application/json" \
    -d '{"data":{"email":"alice@example.com"}}'
  ```

  ```json
  { "status": "ok" }
  ```

  Error cases:
  - `403` if consent not granted.

- `GET /api/v1/vault/{user_id}` – retrieve stored data

  ```bash
  curl http://localhost:8000/api/v1/vault/alice
  ```

  ```json
  { "data": { "email": "alice@example.com" } }
  ```

  Error cases:
  - `403` if consent not granted.

- `GET /api/v1/vault/{user_id}/export` – export stored data

  ```bash
  curl http://localhost:8000/api/v1/vault/alice/export
  ```

  ```json
  { "data": { "email": "alice@example.com" } }
  ```

  Error cases:
  - `403` if consent not granted.

- `DELETE /api/v1/vault/{user_id}` – delete stored data

  ```bash
  curl -X DELETE http://localhost:8000/api/v1/vault/alice
  ```

  ```json
  { "status": "deleted" }
  ```

  Error cases:
  - `403` if consent not granted.

- `POST /api/v1/consent/{user_id}` – set consent flag

  ```bash
  curl -X POST http://localhost:8000/api/v1/consent/alice \
    -H "Content-Type: application/json" \
    -d '{"consent": true}'
  ```

  ```json
  { "status": "ok" }
  ```

  Error cases:
  - `400` if `consent` field missing.

- `GET /api/v1/consent/{user_id}` – get consent status
  ```bash
  curl http://localhost:8000/api/v1/consent/alice
  ```

  ```json
  { "consent": true }
  ```

See [data-vault.md](data-vault.md) for consent workflow, storage format, key
rotation, and security implications.

  ```bash
  curl http://localhost:8000/api/v1/consent/alice
  ```

  ```json
  { "consent": true }
  ```

## Provider Integration
- `POST /api/v1/providers/{name}/key` – configure an API key for a provider

  ```bash
  curl -X POST http://localhost:8000/api/v1/providers/openai/key \
    -H "Content-Type: application/json" \
    -d '{"key":"sk-..."}'
  ```

  ```json
  { "status": "ok" }
  ```

  Error cases:
  - `400` if `key` field missing.

- `POST /api/v1/generate` – generate a response using the specified provider

  ```bash
  curl -X POST http://localhost:8000/api/v1/generate \
    -H "Content-Type: application/json" \
    -d '{"provider":"openai","prompt":"Hello"}'
  ```

  ```json
  { "result": "Hi!" }
  ```

  Error cases:
  - `404` if provider not found.
  - `400` for invalid prompt or configuration.

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
- `GET /api/v1/mcp/servers` – list servers from the MCP registry and their consent status

  ```bash
  curl http://localhost:8000/api/v1/mcp/servers
  ```

  ```json
  { "servers": [ { "name": "echo", "consent": true } ] }
  ```

- `POST /api/v1/mcp/consent/{name}` – set consent for an MCP server

  ```bash
  curl -X POST http://localhost:8000/api/v1/mcp/consent/echo \
    -H "Content-Type: application/json" \
    -d '{"consent": false}'
  ```

  ```json
  { "status": "ok" }
  ```

  Error cases:
  - `400` if `consent` field missing.
  - `404` if server not found.

- `GET /api/v1/mcp/consent/{name}` – get consent for an MCP server

  ```bash
  curl http://localhost:8000/api/v1/mcp/consent/echo
  ```

  ```json
  { "consent": false }
  ```

Registry entries may include a `network` object describing `allow`, `deny`, and
`protocols` lists. A `defaultNetwork` policy applies to servers without explicit
rules. These settings control which hosts and protocols a server may access.

## Themes
- `GET /api/v1/themes/{theme_id}.css` – return sanitized CSS for a theme. The response is served with a strict `Content-Security-Policy` header.

  ```bash
  curl http://localhost:8000/api/v1/themes/dark.css
  ```

  ```css
  body { background: #000; color: #fff; }
  ```

  Error cases:
  - `404` if theme not found.

## Transparency
- `GET /api/v1/bom` – list application dependencies, installed models, and datasets. The endpoint scans directories specified by `LA_MODELS_DIR` and `LA_DATASETS_DIR` (defaulting to `models/` and `datasets/`).

  ```bash
  curl http://localhost:8000/api/v1/bom
  ```

  ```json
  {
    "dependencies": ["fastapi", "uvicorn"],
    "models": [],
    "datasets": []
  }
  ```

- `GET /api/v1/health` – expose request counts and runtime metrics

  ```bash
  curl http://localhost:8000/api/v1/health
  ```

  ```json
  {
    "requests": 42,
    "uptime": 3600
  }
  ```
