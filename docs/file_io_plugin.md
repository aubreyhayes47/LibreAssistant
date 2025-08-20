<!-- Copyright (c) 2024 LibreAssistant contributors. Licensed under the MIT License. -->

# File I/O Plugin

The `file_io` plugin exposes basic filesystem operations through an MCP server. It allows reading, creating, updating, deleting, and listing files within a restricted directory.

## Input Schema

```python
from typing import Literal
from pydantic import BaseModel, model_validator

class FileIOInput(BaseModel):
    operation: Literal["read", "create", "update", "delete", "list"]
    path: str
    content: str | None = None
    confirm: bool | None = None

    @model_validator(mode="after")
    def _check_requirements(self):
        if self.operation in {"create", "update"} and self.content is None:
            raise ValueError("content required")
        if self.operation in {"update", "delete"} and not self.confirm:
            raise ValueError("confirm required")
        return self
```

## Examples

Create a new file:

```bash
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

List files in a directory:

```bash
curl -X POST http://localhost:8000/api/v1/invoke \
  -H "Content-Type: application/json" \
  -d '{
        "plugin": "file_io",
        "user_id": "alice",
        "payload": {"operation": "list", "path": "~/desktop"}
      }'
```

## Security Considerations

- Access is limited to the `~/desktop` directory via `ALLOWED_BASE_DIR` and validated with `os.path.realpath` to prevent path traversal.
- Destructive operations (`update`, `delete`) require an explicit `confirm` flag.
- Each operation is logged with `db.add_file_audit` for accountability.
