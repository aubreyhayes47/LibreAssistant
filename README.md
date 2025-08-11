<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# LibreAssistant
A FOSS alternative to next-gen AI assistants like Google Gemini and ChatGPT.

Continuous integration runs tests, Markdown style checks, and license header verification on every pull request.

## Features

- **Design System** – CSS design tokens and accessible web components (primary button, input field, information card, modal dialog)
- **Main UI** – a tabbed layout with sections for Switchboard, Catalogue, Past Requests, and User Profile plus a six‑step onboarding flow
- **Switchboard & Providers** – request composer with twelve plugin slots, provider registry for cloud or local models, and an initial system prompt
- **Plugin Catalogue** – searchable list with enable/disable toggles
- **Past Requests** – history API and `<la-past-requests>` component to review plugin interactions
- **Personal Data Vault** – encrypted, consent-aware storage with export and deletion endpoints
- **Transparency Dashboards** – Bill of Materials and System Health endpoints with corresponding web components
- **Theme Marketplace** – browse and install community themes sourced from a dedicated repository

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

## Plugins

LibreAssistant ships with a simple `echo` plugin that returns the provided message and stores it in the user's state. It serves as a reference implementation for developing additional plugins.

See [docs/plugin-api.md](docs/plugin-api.md) for details on writing and registering plugins.
