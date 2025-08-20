from pathlib import Path
import json

from libreassistant.plugins import file_io


def test_file_audit_logging_and_endpoint(client, tmp_path: Path) -> None:
    file_io.ALLOWED_BASE_DIR = str(tmp_path)
    file_io.register()
    log_file = Path("logs/file_io_audit.ndjson")
    if log_file.exists():
        log_file.unlink()
    path = tmp_path / "note.txt"
    resp = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "file_io",
            "payload": {"operation": "create", "path": str(path), "content": "hi"},
            "user_id": "alice",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == {"status": "created"}
    assert log_file.exists()
    lines = [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]
    assert len(lines) >= 2
    assert any(
        e["user_id"] == "alice" and e["action"] == "create" and e["path"] == str(path.resolve())
        for e in lines
    )
    resp_all = client.get("/api/v1/audit/file")
    assert resp_all.status_code == 200
    assert any(e["path"] == str(path.resolve()) for e in resp_all.json()["logs"])
    resp_user = client.get("/api/v1/audit/file/alice")
    assert resp_user.status_code == 200
    user_logs = resp_user.json()["logs"]
    assert user_logs and all(e["user_id"] == "alice" for e in user_logs)
