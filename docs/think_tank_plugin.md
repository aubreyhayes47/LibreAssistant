<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Think Tank Plugin

The `think_tank` plugin coordinates a collection of specialist agents through an MCP server to analyse a high-level goal and return an aggregated analysis. Each result is appended to a per-user dossier.

## Input Schema

```python
from pydantic import BaseModel

class ThinkTankInput(BaseModel):
    goal: str
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "think_tank",
        "user_id": "alice",
        "payload": {"goal": "Improve education"}
      }'
```

## Security Considerations

- Analyses are stored in `user_state["thinktank_dossier"]`; avoid submitting goals containing confidential information.
- The plugin interacts only with internal experts and does not read or write files or contact external networks by default.
