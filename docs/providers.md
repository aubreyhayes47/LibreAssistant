<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Model Providers

LibreAssistant supports both hosted and local language models through adapter classes.  Each provider can be configured via environment variables and exposes an API endpoint for configuring API keys.  Simple per-minute rate limits guard against accidental overuse.

## Required Packages

- `httpx` – enables HTTP communication with locally hosted models.
- `pysqlcipher3` – provides encrypted SQLite storage for API keys.

## CloudProvider

The `CloudProvider` integrates with OpenAI's Chat Completions API.

### Environment Variables

- `OPENAI_MODEL` – model name (default `gpt-3.5-turbo`)
- `OPENAI_MAX_TOKENS` – maximum tokens to generate
- `OPENAI_TEMPERATURE` – sampling temperature
- `OPENAI_RATE_LIMIT` – requests allowed per minute (`0` disables)

### API Key Endpoint

Set the OpenAI API key via the REST API.  Keys are encrypted before storage.

```sh
POST /api/v1/providers/cloud/key
{"key": "sk-..."}
```

### Rate Limiting

The provider tracks request timestamps and raises an error when the limit is exceeded.  Adjust `OPENAI_RATE_LIMIT` to control throttling.

## LocalProvider

The `LocalProvider` sends prompts to a locally hosted model over HTTP (e.g. [Ollama](https://ollama.com/)).

### Environment Variables

- `LOCAL_URL` – endpoint of the local model API
- `LOCAL_MODEL` – model identifier
- `LOCAL_MAX_TOKENS` – maximum tokens to generate
- `LOCAL_TEMPERATURE` – sampling temperature
- `LOCAL_RATE_LIMIT` – requests allowed per minute (`0` disables)

### API Key Endpoint

Local models typically do not require authentication, but a key can be stored if needed:

```sh
POST /api/v1/providers/local/key
{"key": "optional-token"}
```

### Rate Limiting

Requests are throttled using the same per-minute mechanism as the cloud provider.  Configure the limit with `LOCAL_RATE_LIMIT`.

