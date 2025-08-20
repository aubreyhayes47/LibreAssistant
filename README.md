<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# LibreAssistant

LibreAssistant is an open‑source AI assistant you can run locally. It pairs a
Python microkernel with auditable plugins and a themeable web interface so you
stay in control of every request.

This guide focuses on getting you up and running and showcasing creative ways to
use the built‑in tools.

## Highlights

- **Chat with models you trust** – point LibreAssistant at local or cloud
  providers and inspect every request.
- **Do more with plugins** – read and write files, analyse goals, or integrate
  your own tools.
- **Transparent by design** – dashboards reveal system health and every
  component that participates in a request.
- **Customisable UI** – switch between light, dark, or community themes.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/en/download) for TypeScript components

### Clone and Launch

```sh
git clone https://github.com/LibreAssistant/LibreAssistant.git
cd LibreAssistant
docker compose up --build
```

Visit [http://localhost:8000](http://localhost:8000) to open the switchboard
interface.

### Optional: Python Development Setup

Install the Python dependencies using the lock file before working on the core
microkernel or running tests:

```sh
uv pip sync uv.lock
python -m pip install -e .[dev]
```

If you modify dependencies, regenerate the lock file with:

```sh
uv pip compile pyproject.toml -o uv.lock
```

## First Steps in the UI

The switchboard presents tabs for composing requests, browsing plugins, viewing
past activity, and updating your profile. Start a conversation by entering a
prompt in the request tab and choosing a model provider.

## Example Requests

### Brainstorm with the Think Tank Plugin

```sh
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "think_tank",
        "user_id": "alice",
        "payload": {"goal": "Improve education"}
      }'
```

### Save a Note with the File I/O Plugin

```sh
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "file_io",
        "user_id": "alice",
        "payload": {
          "operation": "create",
          "path": "~/desktop/note.txt",
          "content": "hello"
        }
      }'
```

## Customise and Extend

- **Add providers** – set API keys at
  `/api/v1/providers/{name}/key` to use cloud models.
- **Pick a theme** – apply a community style from
  `/api/v1/themes/{name}.css` or design your own.
- **Write plugins** – see [docs/plugin-api.md](docs/plugin-api.md) for a guide
  to building and registering new tools.

## Architecture Overview

Under the hood, LibreAssistant uses a Python microkernel with plugins that may
delegate to TypeScript MCP servers. History, audit logs, and transparency
dashboards track each request so you can inspect how outputs were produced.

## Further Reading

- [docs/api.md](docs/api.md) – REST API endpoints
- [ARCHITECTURE.md](ARCHITECTURE.md) – system flows and design goals
- [OVERVIEW.md](OVERVIEW.md) – background on the Model Context Protocol
