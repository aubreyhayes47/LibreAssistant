<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# LibreAssistant

LibreAssistant is a free, open‑source assistant you can run entirely on your own
computer. It combines a small Python core with reviewable add‑on tools (called
plugins) and a web page you can style to your liking, so you stay in control of
what the assistant does and how it looks.

This guide introduces the project in plain language while keeping the technical
detail developers expect.

## What It Can Do

- **Talk to models you choose** – connect to well‑known cloud models or ones you
  host yourself and inspect every request and response.
- **Use built‑in plugins** – repeat messages with [Echo](docs/echo_plugin.md),
  read and write files through [File I/O](docs/file_io_plugin.md), gather ideas
  with [Think Tank](docs/think_tank_plugin.md), or search public legislation via
  the [Law](docs/law_api.md) plugin.
- **Apply network rules** – whitelist or block specific sites and protocols for
  each plugin.
- **Customise the interface** – switch between light, dark, or community themes
  and tailor the look of the web page.
- **Stay accessible** – full keyboard navigation, screen reader support, and
  [WCAG 2.1 AA compliance](docs/accessibility.md) for users with disabilities.
- **Stay transparent** – dashboards reveal system health and every component
  that participates in a request.

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [Python 3.10+](https://www.python.org/downloads/)
- [Node.js 20+](https://nodejs.org/en/download) for TypeScript components
- [httpx](https://www.python-httpx.org/) for local model HTTP access
- [pysqlcipher3](https://pypi.org/project/pysqlcipher3/) for encrypted SQLite.
  Building this package requires the [SQLCipher](https://www.zetetic.net/sqlcipher/)
  libraries on your system (for example, `libsqlcipher-dev` on Debian/Ubuntu).
  Without SQLCipher, installation of `pysqlcipher3` will fail and LibreAssistant
  will fall back to the standard `sqlite3` module without encryption.

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

### TypeScript Development and Testing

Install the JavaScript dependencies before running the TypeScript test suite or
compiling sources. These steps require **Node.js 20+**:

```sh
npm install
```

This command installs `ts-node`, `typescript`, and related packages. Run the
tests with:

```sh
npm test
```

Use your preferred TypeScript build tooling (for example, `npx tsc`) after the
dependencies are installed.

### Model Providers

LibreAssistant ships with adapters for both hosted and local models.  The
following environment variables control defaults and simple per-minute rate
limits.  A value of `0` disables throttling.

Additional configuration details and API key endpoints are documented in
[docs/providers.md](docs/providers.md).

| Provider | Variables |
| --- | --- |
| OpenAI | `OPENAI_MODEL`, `OPENAI_MAX_TOKENS`, `OPENAI_TEMPERATURE`, `OPENAI_RATE_LIMIT` |
| Local  | `LOCAL_URL`, `LOCAL_MODEL`, `LOCAL_MAX_TOKENS`, `LOCAL_TEMPERATURE`, `LOCAL_RATE_LIMIT` |

Set API keys via `POST /api/v1/providers/{name}/key`.

#### Local LLMs with Ollama

The local provider expects an HTTP endpoint compatible with
[Ollama](https://ollama.com/).  Install and start Ollama, then launch a model:

```sh
curl -fsSL https://ollama.com/install.sh | sh
ollama run llama2
```

By default the provider sends requests to `http://localhost:11434/api/generate`
and uses the model name `llama2`, matching Ollama's defaults.  Adjust any of
the `LOCAL_` variables to point at a different server or model.

## Using LibreAssistant

Open your browser to [http://localhost:8000](http://localhost:8000) to reach the
switchboard. It presents tabs for writing prompts, browsing plugins, reviewing
past activity, and editing your profile. Start a chat by typing a prompt and
selecting which model provider to use. Add API keys for new providers, apply
themes, or write your own plugins to extend the assistant.

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

### Search Government Data with the Law Plugin

```sh
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "law_by_keystone",
        "user_id": "alice",
        "payload": {
          "query": "education",
          "source": "govtrack",
          "output_format": "json",
          "output_path": "law"
        }
      }'
```

The law plugin connects to GovInfo, eCFR, CourtListener, Open States, and
GovTrack APIs and can export results in Markdown, HTML, JSON, plain text, or
XML with metadata about the query.

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

## Documentation Table of Contents

- [OVERVIEW.md](OVERVIEW.md) – background on the Model Context Protocol
- [ARCHITECTURE.md](ARCHITECTURE.md) – system flows and design goals
- [docs/configuration.md](docs/configuration.md) – environment variables and setup
- [docs/providers.md](docs/providers.md) – model provider settings
- [docs/api.md](docs/api.md) – REST API endpoints
- [docs/plugin-api.md](docs/plugin-api.md) – building and registering plugins
- [docs/echo_plugin.md](docs/echo_plugin.md) – Echo plugin usage
- [docs/file_io_plugin.md](docs/file_io_plugin.md) – File I/O plugin usage
- [docs/think_tank_plugin.md](docs/think_tank_plugin.md) – Think Tank plugin usage
- [docs/law_api.md](docs/law_api.md) – Law plugin API details
- [docs/data-vault.md](docs/data-vault.md) – consent workflow and storage details
- [docs/network-policy.md](docs/network-policy.md) – configuring server network policies
- [docs/transparency.md](docs/transparency.md) – audit and transparency features
- [docs/accessibility.md](docs/accessibility.md) – using LibreAssistant with assistive technologies
- [docs/bug-bash-guide.md](docs/bug-bash-guide.md) – organizing bug bash sessions with new users
- [docs/usability-walkthrough-guide.md](docs/usability-walkthrough-guide.md) – conducting user experience testing
- [CONTRIBUTING.md](CONTRIBUTING.md) – contribution guidelines
- [SECURITY.md](SECURITY.md) – security policies
- [CONSTITUTION.md](CONSTITUTION.md) – project principles
