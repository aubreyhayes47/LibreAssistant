<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# Echo Plugin

The `echo` plugin returns a supplied message and records it in the user's state. It serves as a minimal reference implementation for building new plugins.

## Input Schema

```python
from pydantic import BaseModel

class EchoInput(BaseModel):
    message: str = ""
```

## Example

```bash
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "echo",
        "user_id": "alice",
        "payload": {"message": "hi"}
      }'
```

## Security Considerations

- The plugin stores the last echoed message in `user_state["last_message"]` and the per-user history. Avoid echoing sensitive information that should not persist.
- No external network or filesystem access is performed.
