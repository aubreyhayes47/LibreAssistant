<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# MCP Servers

This directory contains sample servers for the [Model Context Protocol](../OVERVIEW.md).
Each server advertises a set of tools and resources and may require
environment variables to function.

| Server | Tools | Resources | Environment variables |
| ------ | ----- | --------- | --------------------- |
| `echo` | `echo_message` | `echo:last_message` | _None_ |
| `files` | `fs_read`, `fs_create`, `fs_update`, `fs_delete`, `fs_list` | _None_ | `MCP_FS_BASE_DIR` – root directory for file access |
| `law_by_keystone` | `generate_legal_summary` | `law:last_summary` | `MCP_FS_BASE_DIR`, `GOVINFO_API_KEY`, `OPENSTATES_API_KEY` |
| `think_tank` | `analyze_goal` | `thinktank:last_dossier` | `THINK_TANK_MODEL_RESPONSE`, `OPENAI_API_KEY`, `OPENAI_MODEL` |

See the [network policy guide](../docs/network-policy.md) for configuring
per-server egress restrictions.
