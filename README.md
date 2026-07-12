# LibreAssistant

Local-first CLI AI assistant with tool calling, MCP server support, multi-agent profiles, and sandbox mode.

## Features

- **Tool-calling loop** — terminal, file I/O, web search, and web fetch with automatic retry
- **Multi-agent profiles** — built-in `default`, `legal`, and `code` profiles, or define your own in `~/.libreassistant/agents/`
- **MCP server support** — OAuth-authenticated services (CourtListener, Gmail, Drive, Calendar) and user-defined servers
- **Sandbox mode** — restrict file and terminal access to a directory with `--sandbox-root`
- **Background tasks** — delegate sub-tasks to specialist agents via `delegate_task` or `--exec-task`
- **Context compaction** — `/compact` trims or summarizes conversation history to stay within context limits
- **Skills** — load reusable instruction modules into context with `/<skill-name>`
- **Session persistence** — JSONL-based sessions with auto-save and named snapshots

## Quick Start

Requires Python 3.10+.

```bash
git clone https://github.com/aubreyhayes47/LibreAssistant.git
cd LibreAssistant
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

On first run, LibreAssistant prompts for an API key (any OpenAI-compatible endpoint). Set it via environment variable or let the interactive prompt save it to `~/.libreassistant/config.json`.

```bash
libre
```

Run from any directory. The terminal tool inherits your current working directory.

## CLI Arguments

| Flag | Description |
|------|-------------|
| `--kms` | Unrestricted mode — skip all command confirmations |
| `--agent NAME` | Start with a specific agent profile (default: `default`) |
| `--list-agents` | List available profiles and exit |
| `--no-terminal` | Disable the terminal/shell tool entirely |
| `--sandbox-root DIR` | Restrict file/terminal access to this directory |
| `--tutorial` | Start with the interactive tutorial loaded into context |
| `--exec MESSAGE` | Execute one turn with MESSAGE, print result, and exit |
| `--exec-task MESSAGE` | Submit MESSAGE as a background task, wait for result, and exit |
| `--timeout SECS` | Seconds to wait for `--exec-task` (default: 120) |

## Slash Commands

| Command | Description |
|---------|-------------|
| `/agent NAME` | Switch to a different agent profile |
| `/steer MSG` | Inject a message between tool-calling rounds |
| `/compact` | Compress context window (summarize + trim) |
| `/tasks` | List all background tasks |
| `/task ID [stop\|output]` | Task details and control |
| `/save NAME` | Save the current session |
| `/load NAME` | Load a saved session |
| `/sessions` | List saved sessions |
| `/new` | Start a new session (auto-saves current) |
| `/rm NAME` | Delete a saved session |
| `/skills` | List installed skill modules |
| `/mcp` | List connected MCP servers |
| `/setup [server]` | List servers or trigger OAuth for one |
| `/auth SERVER` | Alias for `/setup SERVER` |
| `/deauth SERVER` | Clear cached tokens for a server |
| `/help` | Show help |
| `/quit` | Quit (auto-saves) |

## Agent Profiles

Built-in profiles ship with curated system prompts and tool access:

| Profile | Purpose |
|---------|---------|
| `default` | General assistant with full tool access |
| `legal` | Legal research with CourtListener integration |
| `code` | Software development with file I/O and terminal |

Define custom profiles as JSON files in `~/.libreassistant/agents/`. User profiles with the same name override built-ins. Each profile controls:

- `system_prompt` — role instructions
- `tool_patterns` — glob patterns for allowed tools
- `max_context_chars` — context window budget (default: 120,000)
- `max_tool_rounds` — max tool calls per turn (default: 50)
- `compaction_mode` — `"trim"` or `"summarize"`
- `sandbox_root`, `allow_terminal`, `model` overrides

## MCP Servers

Built-in servers:

| Server | Transport | Auth |
|--------|-----------|------|
| CourtListener | HTTP | DCR-based OAuth |
| Google Gmail | HTTP | OAuth (env-gated) |
| Google Drive | HTTP | OAuth (env-gated) |
| Google Calendar | HTTP | OAuth (env-gated) |

Google servers require `LIBREASSISTANT_GOOGLE_CLIENT_ID` and `LIBREASSISTANT_GOOGLE_CLIENT_SECRET` environment variables.

Add custom servers in `~/.libreassistant/mcp_servers.json` (supports HTTP and stdio transports). Unauthenticated servers get a `setup_<name>` stub tool — run `/setup <server>` to complete the OAuth flow.

## Configuration

| Item | Location |
|------|----------|
| Config | `~/.libreassistant/config.json` |
| Sessions | `~/.libreassistant/sessions/*.jsonl` |
| Auto-save | `~/.libreassistant/last_session.jsonl` |
| Profiles | `~/.libreassistant/agents/*.json` |
| Skills | `~/.libreassistant/skills/*/SKILL.md` |
| MCP servers | `~/.libreassistant/mcp_servers.json` |

**API key** — set via `LIBRE_MODEL` env var for the model name, or configure in `config.json`. On first run, LibreAssistant prompts interactively and saves atomically with `chmod 600`.

**Environment variables:**

| Variable | Purpose |
|----------|---------|
| `LIBRE_MODEL` | Override the default LLM model |
| `LIBREASSISTANT_GOOGLE_CLIENT_ID` | Google OAuth client ID |
| `LIBREASSISTANT_GOOGLE_CLIENT_SECRET` | Google OAuth client secret |

## Context Compaction

Long conversations hit context limits. LibreAssistant handles this automatically during the tool-calling loop, or manually via `/compact`:

- **Trim mode** (default) — prunes large tool results and removes old tool call pairs
- **Summarize mode** — uses an LLM to produce a structured summary (Goal / Decisions / Progress / Open Items)

The system injects a recovery message when older context has been compacted, so the conversation remains coherent.

## Contributing

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
pytest
```

441 tests covering sessions, tool calling, MCP, profiles, and more. See `ARCHITECTURE.md` for detailed system documentation.

## License

[MIT](LICENSE) — Copyright 2026 aubreyhayes47
