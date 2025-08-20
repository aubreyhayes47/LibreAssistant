# Audit logs

This directory stores runtime audit logs in newline-delimited JSON (NDJSON) format.
Each line represents an `AuditEntry` emitted by the MCP client. Logs rotate when
the file exceeds 5 MB, renaming the current file to `audit.ndjson.1`.
