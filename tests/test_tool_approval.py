"""Tests for tool approval flow: confirm_command, prompt hook, and delete_file confirmation."""
from unittest.mock import patch, MagicMock

import pytest

from libreassistant.tools.terminal import confirm_command, _always_allow, READ_ONLY_COMMANDS
from libreassistant import prompt


@pytest.fixture(autouse=True)
def _reset_always_allow():
    """Clear the always-allow cache between tests to prevent cross-test contamination."""
    _always_allow.clear()
    yield
    _always_allow.clear()


@pytest.fixture(autouse=True)
def _reset_prompt_hook():
    """Clear the prompt hook between tests."""
    prompt.set_prompt_hook(None)
    yield
    prompt.set_prompt_hook(None)


# --- confirm_command: auto-approval paths ---
class TestConfirmAutoApprove:
    def test_read_only_single_command(self):
        """ls alone should be auto-approved (no prompt)."""
        assert confirm_command("ls") is True

    def test_read_only_with_path(self):
        """cat /path/to/file should be auto-approved."""
        assert confirm_command("cat /path/to/file") is True

    def test_all_read_only_commands(self):
        """Every command in READ_ONLY_COMMANDS should auto-approve when used alone."""
        for cmd in READ_ONLY_COMMANDS:
            assert confirm_command(cmd) is True, f"{cmd} should auto-approve"

    def test_kms_mode_skips_all(self):
        """With --kms active, even dangerous commands are approved."""
        with patch("libreassistant.tools.terminal.kms_mode", return_value=True):
            assert confirm_command("rm -rf /") is True

    def test_always_allow_cache(self):
        """Commands previously approved with 'always' should be auto-approved."""
        _always_allow.add("make test")
        assert confirm_command("make test") is True


# --- confirm_command: prompt paths ---
class TestConfirmPrompt:
    def test_operators_trigger_prompt(self):
        """Shell operators like |, &&, > should trigger the prompt even for read-only bases."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
            assert confirm_command("ls | grep foo") is False

    def test_non_read_only_triggers_prompt(self):
        """Non-read-only commands should always prompt."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
            assert confirm_command("make test") is False

    def test_prompt_approve_once(self):
        """Answering 'y' should return True and NOT cache the command."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="y"):
            assert confirm_command("make test") is True
            assert "make test" not in _always_allow

    def test_prompt_approve_always(self):
        """Answering 'a' should return True and cache the command."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="a"):
            assert confirm_command("make test") is True
            assert "make test" in _always_allow

    def test_prompt_reject(self):
        """Answering 'n' should return False."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
            assert confirm_command("make test") is False

    def test_prompt_empty_answer_rejects(self):
        """Empty input should be treated as rejection."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value=""):
            assert confirm_command("make test") is False


# --- prompt module ---
class TestPromptModule:
    def test_user_prompt_with_hook(self):
        """When a hook is registered, user_prompt should call it."""
        hook = MagicMock(return_value="y")
        prompt.set_prompt_hook(hook)
        result = prompt.user_prompt("Allow? ")
        hook.assert_called_once_with("Allow? ")
        assert result == "y"

    def test_user_prompt_without_hook(self):
        """Without a hook, user_prompt falls back to builtins.input."""
        with patch("builtins.input", return_value="n\n"):
            result = prompt.user_prompt("Allow? ")
        assert result == "n"

    def test_set_prompt_hook_clears(self):
        """Passing None clears the hook."""
        prompt.set_prompt_hook(lambda t: "y")
        prompt.set_prompt_hook(None)
        assert prompt._hook is None


# --- delete_file: uses prompt hook ---
class TestDeleteFileApproval:
    def test_delete_file_uses_user_prompt(self):
        """delete_file should call user_prompt for confirmation, not raw input."""
        import tempfile, os
        from libreassistant.tools.file_ops import delete_file, set_sandbox_root

        set_sandbox_root(tempfile.gettempdir())
        tmp = os.path.join(tempfile.gettempdir(), "test_delete_prompt.txt")
        try:
            with open(tmp, "w") as f:
                f.write("test")
            with patch("libreassistant.tools.file_ops.user_prompt", return_value="y") as mock_prompt:
                result = delete_file({"path": tmp})
                mock_prompt.assert_called_once()
                assert "Deleted" in result
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
            set_sandbox_root(None)

    def test_delete_file_cancel(self):
        """delete_file should cancel when user answers 'n'."""
        import tempfile, os
        from libreassistant.tools.file_ops import delete_file, set_sandbox_root

        set_sandbox_root(tempfile.gettempdir())
        tmp = os.path.join(tempfile.gettempdir(), "test_delete_cancel.txt")
        try:
            with open(tmp, "w") as f:
                f.write("test")
            with patch("libreassistant.tools.file_ops.user_prompt", return_value="n"):
                result = delete_file({"path": tmp})
                assert "cancelled" in result
                assert os.path.exists(tmp)  # file should NOT be deleted
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
            set_sandbox_root(None)

    def test_delete_file_kms_skips_prompt(self):
        """delete_file should skip the prompt in --kms mode."""
        import tempfile, os
        from libreassistant.tools.file_ops import delete_file, set_sandbox_root

        set_sandbox_root(tempfile.gettempdir())
        tmp = os.path.join(tempfile.gettempdir(), "test_delete_kms.txt")
        try:
            with open(tmp, "w") as f:
                f.write("test")
            with patch("libreassistant.tools.file_ops._kms_mode", return_value=True):
                with patch("libreassistant.tools.file_ops.user_prompt") as mock_prompt:
                    result = delete_file({"path": tmp})
                    mock_prompt.assert_not_called()
                    assert "Deleted" in result
                    assert not os.path.exists(tmp)
        finally:
            set_sandbox_root(None)
