<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# LibreAssistant
A FOSS alternative to next-gen AI assistants like Google Gemini and ChatGPT.

Continuous integration runs tests, Markdown style checks, and license header verification on every pull request.

## Development

A Docker-based environment is provided for local development. Start the API with:

```sh
docker compose up --build
```

The service will be available at [http://localhost:8000](http://localhost:8000).

## Plugins

LibreAssistant ships with a simple `echo` plugin that returns the provided message and stores it in the user's state. It serves as a reference implementation for developing additional plugins.

See [docs/plugin-api.md](docs/plugin-api.md) for details on writing and registering plugins.
