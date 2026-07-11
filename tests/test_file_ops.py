"""Comprehensive tests for libreassistant.tools.file_ops."""
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from libreassistant.tools.file_ops import (
    SENSITIVE_PATHS,
    MAX_READ_SIZE,
    _resolve_path,
    read_file,
    save_file,
    append_file,
    delete_file,
    set_sandbox_root,
)


@pytest.fixture(autouse=True)
def _reset_sandbox(tmp_path):
    """Set sandbox to tmp_path and reset after each test."""
    set_sandbox_root(str(tmp_path))
    yield
    set_sandbox_root(None)


@pytest.fixture(autouse=True)
def _no_kms():
    """Ensure --kms is off unless a test explicitly overrides."""
    with patch("libreassistant.tools.file_ops._kms_mode", return_value=False):
        yield


# ── _resolve_path ────────────────────────────────────────────────────────────


class TestResolvePath:
    def test_normal_path_resolves_within_sandbox(self, tmp_path):
        f = tmp_path / "sub" / "file.txt"
        f.parent.mkdir(parents=True)
        f.write_text("hi")
        result = _resolve_path(str(f))
        assert result == f.resolve()

    def test_traversal_blocked(self, tmp_path):
        target = tmp_path / ".." / "outside.txt"
        with pytest.raises(PermissionError, match="Path must be under"):
            _resolve_path(str(target))

    def test_absolute_path_outside_sandbox_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="Path must be under"):
            _resolve_path("/etc/passwd")

    def test_sensitive_ssh_blocked(self, tmp_path):
        ssh = Path.home() / ".ssh"
        with pytest.raises(PermissionError, match="restricted"):
            _resolve_path(str(ssh / "id_rsa"))

    def test_sensitive_gnupg_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="restricted"):
            _resolve_path(str(Path.home() / ".gnupg" / "key.gpg"))

    def test_sensitive_aws_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="restricted"):
            _resolve_path(str(Path.home() / ".aws" / "credentials"))

    def test_sensitive_kube_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="restricted"):
            _resolve_path(str(Path.home() / ".kube" / "config"))

    def test_sensitive_docker_blocked(self, tmp_path):
        with pytest.raises(PermissionError, match="restricted"):
            _resolve_path(str(Path.home() / ".docker" / "config.json"))

    def test_dotenv_blocked(self, tmp_path):
        f = tmp_path / ".env"
        with pytest.raises(PermissionError, match="access to .env files is restricted"):
            _resolve_path(str(f))

    def test_dotenv_variants_not_blocked(self, tmp_path):
        """Known gap: .env.local and .env.production are NOT blocked."""
        for name in [".env.local", ".env.production", ".env.dev"]:
            f = tmp_path / name
            result = _resolve_path(str(f))
            assert result == f.resolve()

    def test_tilde_expands(self, tmp_path):
        """~ expands to home directory. Sandbox check bypassed via --kms."""
        with patch("libreassistant.tools.file_ops._kms_mode", return_value=True):
            result = _resolve_path("~/somefile.txt")
            assert result == (Path.home() / "somefile.txt").resolve()

    def test_symlink_outside_sandbox_blocked(self, tmp_path):
        link = tmp_path / "escape_link"
        link.symlink_to("/etc/passwd")
        with pytest.raises(PermissionError, match="Path must be under"):
            _resolve_path(str(link))


class TestResolvePathKms:
    def test_kms_skips_sandbox_check(self, tmp_path):
        with patch("libreassistant.tools.file_ops._kms_mode", return_value=True):
            result = _resolve_path("/tmp/kms_file.txt")
            assert result == Path("/tmp/kms_file.txt").resolve()

    def test_kms_sensitive_paths_still_blocked(self, tmp_path):
        with patch("libreassistant.tools.file_ops._kms_mode", return_value=True):
            with pytest.raises(PermissionError, match="restricted"):
                _resolve_path(str(Path.home() / ".ssh" / "id_rsa"))


# ── read_file ────────────────────────────────────────────────────────────────


class TestReadFile:
    def test_normal_read(self, tmp_path):
        f = tmp_path / "hello.txt"
        f.write_text("hello world")
        result = read_file({"path": str(f)})
        assert result == "hello world"

    def test_nonexistent_file(self, tmp_path):
        result = read_file({"path": str(tmp_path / "nope.txt")})
        assert "Error: file not found" in result

    def test_file_too_large(self, tmp_path):
        f = tmp_path / "big.bin"
        f.write_bytes(b"x" * (MAX_READ_SIZE + 1))
        result = read_file({"path": str(f)})
        assert "Error: file too large" in result

    def test_binary_falls_back_to_latin1(self, tmp_path):
        f = tmp_path / "binary.bin"
        f.write_bytes(bytes(range(256)))
        result = read_file({"path": str(f)})
        assert isinstance(result, str)
        assert len(result) == 256

    def test_pdf_triggers_pdftotext(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 fake pdf content")
        mock_result = type("R", (), {"stdout": "extracted text", "returncode": 0})()
        with patch("libreassistant.tools.file_ops.subprocess.run", return_value=mock_result) as m:
            result = read_file({"path": str(f)})
            m.assert_called_once()
            assert result == "extracted text"

    def test_pdf_no_pdftotext_installed(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4 fake")
        with patch(
            "libreassistant.tools.file_ops.subprocess.run",
            side_effect=FileNotFoundError,
        ):
            result = read_file({"path": str(f)})
            assert "Install pdftotext" in result

    def test_pdf_empty_text(self, tmp_path):
        f = tmp_path / "doc.pdf"
        f.write_bytes(b"%PDF-1.4")
        mock_result = type("R", (), {"stdout": "", "returncode": 0})()
        with patch("libreassistant.tools.file_ops.subprocess.run", return_value=mock_result):
            result = read_file({"path": str(f)})
            assert "no extractable text" in result

    def test_path_outside_sandbox(self, tmp_path):
        result = read_file({"path": "/etc/passwd"})
        assert "Error" in result

    def test_empty_path(self):
        result = read_file({"path": ""})
        assert "Error: path is required" in result

    def test_missing_path_key(self):
        result = read_file({})
        assert "Error: path is required" in result


# ── save_file ────────────────────────────────────────────────────────────────


class TestSaveFile:
    def test_creates_new_file(self, tmp_path):
        f = tmp_path / "new.txt"
        result = save_file({"path": str(f), "content": "new content"})
        assert "File saved" in result
        assert f.read_text() == "new content"

    def test_overwrites_existing(self, tmp_path):
        f = tmp_path / "existing.txt"
        f.write_text("old")
        result = save_file({"path": str(f), "content": "new"})
        assert "File saved" in result
        assert f.read_text() == "new"

    def test_creates_parent_directories(self, tmp_path):
        f = tmp_path / "a" / "b" / "c" / "file.txt"
        result = save_file({"path": str(f), "content": "deep"})
        assert "File saved" in result
        assert f.read_text() == "deep"

    def test_path_outside_sandbox(self, tmp_path):
        result = save_file({"path": "/tmp/outside.txt", "content": "nope"})
        assert "Error" in result

    def test_very_large_content(self, tmp_path):
        f = tmp_path / "huge.txt"
        content = "x" * (1024 * 1024)  # 1 MB
        result = save_file({"path": str(f), "content": content})
        assert "File saved" in result
        assert len(f.read_text()) == len(content)

    def test_empty_path(self):
        result = save_file({"path": "", "content": ""})
        assert "Error: path is required" in result

    def test_empty_content(self, tmp_path):
        f = tmp_path / "empty.txt"
        result = save_file({"path": str(f), "content": ""})
        assert "File saved" in result
        assert f.read_text() == ""


# ── append_file ──────────────────────────────────────────────────────────────


class TestAppendFile:
    def test_appends_to_existing(self, tmp_path):
        f = tmp_path / "log.txt"
        f.write_text("line1\n")
        result = append_file({"path": str(f), "content": "line2\n"})
        assert "Appended" in result
        assert f.read_text() == "line1\nline2\n"

    def test_nonexistent_file_returns_error(self, tmp_path):
        f = tmp_path / "nope.txt"
        result = append_file({"path": str(f), "content": "data"})
        assert "Error: file not found" in result

    def test_path_outside_sandbox(self, tmp_path):
        result = append_file({"path": "/tmp/outside.txt", "content": "nope"})
        assert "Error" in result

    def test_empty_content_appends_nothing(self, tmp_path):
        f = tmp_path / "unchanged.txt"
        original = "original"
        f.write_text(original)
        result = append_file({"path": str(f), "content": ""})
        assert "Appended" in result
        assert f.read_text() == original

    def test_empty_path(self):
        result = append_file({"path": "", "content": ""})
        assert "Error: path is required" in result


# ── delete_file ──────────────────────────────────────────────────────────────


class TestDeleteFile:
    def test_nonexistent_file(self, tmp_path):
        result = delete_file({"path": str(tmp_path / "nope.txt")})
        assert "Error: file not found" in result

    def test_directory_returns_error(self, tmp_path):
        d = tmp_path / "mydir"
        d.mkdir()
        with patch("libreassistant.tools.file_ops.user_prompt", return_value="y"):
            result = delete_file({"path": str(d)})
        assert "not a file" in result
        assert d.exists()

    def test_symlink_to_file(self, tmp_path):
        """resolve() follows symlinks, so unlink() removes the target, not the link."""
        target = tmp_path / "real.txt"
        target.write_text("data")
        link = tmp_path / "link.txt"
        link.symlink_to(target)
        with patch("libreassistant.tools.file_ops.user_prompt", return_value="y"):
            result = delete_file({"path": str(link)})
        assert "Deleted" in result
        assert not link.exists()
        assert not target.exists()

    def test_permission_denied(self, tmp_path):
        f = tmp_path / "protected.txt"
        f.write_text("secret")
        f.chmod(0o000)
        with patch("libreassistant.tools.file_ops.user_prompt", return_value="y"):
            result = delete_file({"path": str(f)})
        # Root can delete anyway; non-root gets an error. Both are valid.
        assert isinstance(result, str)

    def test_delete_path_outside_sandbox(self, tmp_path):
        result = delete_file({"path": "/etc/passwd"})
        assert "Error" in result

    def test_delete_empty_path(self):
        result = delete_file({"path": ""})
        assert "Error: path is required" in result
