<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# LibreAssistant
A FOSS alternative to next-gen AI assistants like Google Gemini and ChatGPT.

Continuous integration runs tests, Markdown style checks, and license header verification on every pull request.

## Features

- **Design System** – token-based CSS with Light, Dark, and High-Contrast themes plus accessible web components (primary button, input field, information card, modal dialog)
- **Main UI** – a tabbed layout with sections for Switchboard, Catalogue, Past Requests, and User Profile plus a six‑step onboarding flow
- **Switchboard & Providers** – request composer with twelve plugin slots, provider registry for cloud or local models, and an initial system prompt
- **Plugin Catalogue** – searchable list with enable/disable toggles
- **Past Requests** – history API and `<la-past-requests>` component to review plugin interactions
- **Personal Data Vault** – encrypted, consent-aware storage with export and deletion endpoints
- **Transparency Dashboards** – Bill of Materials and System Health endpoints with corresponding web components
- **Theme Marketplace** – browse, preview, rate, and install community themes from a dedicated repository; styles are sanitized server-side, loaded in sandboxed iframes, and served with a strict Content Security Policy

## Development

A Docker-based environment is provided for local development. Start the API with:

```sh
docker compose up --build
```

The service will be available at [http://localhost:8000](http://localhost:8000).

Install dependencies and run the test suite with:

```sh
python -m pip install -e .[dev]
pytest
```

Rebuild the theme catalog after adding or updating themes with:

```sh
python scripts/build_theme_catalog.py
```

### Model and Dataset Directories

The bill of materials endpoint inspects local directories to report installed artifacts. By default it scans `models/` and `datasets/` relative to the project root. These paths can be customized with environment variables:

```sh
export LA_MODELS_DIR=/path/to/models
export LA_DATASETS_DIR=/path/to/datasets
```

The endpoint returns empty lists when the configured directories are missing or contain no entries.

## Plugins

LibreAssistant ships with a simple `echo` plugin that returns the provided message and stores it in the user's state. It serves as a reference implementation for developing additional plugins.

See [docs/plugin-api.md](docs/plugin-api.md) for details on writing and registering plugins.
