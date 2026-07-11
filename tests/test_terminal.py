"""Tests for terminal tool execution, handle_terminal, and confirm_command edge cases."""

from unittest.mock import patch, MagicMock

import pytest

from libreassistant.tools.terminal import (
    _exec_command,
    _always_allow,
    confirm_command,
    handle_terminal,
    READ_ONLY_COMMANDS,
    _SHELL_OPS,
    set_sandbox_root,
    _validate_command_paths,
)
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


# ─── _exec_command tests ───────────────────────────────────────────────────────


class TestExecCommand:
    def test_successful_command(self):
        """echo hello should produce output containing 'hello'."""
        result = _exec_command("echo hello")
        assert "hello" in result

    def test_timeout_handling(self):
        """Commands exceeding 30s should return a timeout error string."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run",
            side_effect=__import__("subprocess").TimeoutExpired(
                cmd="sleep", timeout=30
            ),
        ):
            result = _exec_command("sleep 60")
        assert "timed out" in result

    def test_output_truncation_at_10kb(self):
        """Output exceeding 10KB should be truncated with a marker."""
        large_output = "x" * 15000
        mock_result = MagicMock()
        mock_result.stdout = large_output
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ):
            result = _exec_command("echo large")
        assert "[truncated at 10KB]" in result
        assert len(result) < 15000

    def test_shell_true_passes_string(self):
        """shell=True should pass the command as a string to subprocess.run."""
        mock_result = MagicMock()
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ) as mock_run:
            _exec_command("echo ok", use_shell=True)
            call_args = mock_run.call_args
            assert call_args[1]["shell"] is True
            assert call_args[0][0] == "echo ok"

    def test_shell_false_passes_list(self):
        """shell=False should pass the command as a list."""
        mock_result = MagicMock()
        mock_result.stdout = "ok"
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ) as mock_run:
            _exec_command(["echo", "ok"], use_shell=False)
            call_args = mock_run.call_args
            assert call_args[1]["shell"] is False
            assert call_args[0][0] == ["echo", "ok"]

    def test_nonzero_exit_code(self):
        """Non-zero exit code should include the code in output."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "something went wrong"
        mock_result.returncode = 1
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ):
            result = _exec_command("false")
        assert "exit code 1" in result
        assert "something went wrong" in result

    def test_empty_stdout_nonempty_stderr(self):
        """Stderr-only output should be returned."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = "warning: deprecated"
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ):
            result = _exec_command("cmd")
        assert "warning: deprecated" in result

    def test_both_empty_returns_no_output(self):
        """Both stdout and stderr empty should return the no-output marker."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        with patch(
            "libreassistant.tools.terminal.subprocess.run", return_value=mock_result
        ):
            result = _exec_command("cmd")
        assert result == "(no output)"


# ─── handle_terminal end-to-end tests ──────────────────────────────────────────


class TestHandleTerminal:
    def test_empty_command_returns_error(self):
        """Empty command string should return an error message."""
        assert handle_terminal({"command": ""}) == "Error: empty command"

    def test_whitespace_only_command_returns_error(self):
        """Whitespace-only command should be treated as empty after strip."""
        assert handle_terminal({"command": "   "}) == "Error: empty command"

    def test_command_rejected_by_user(self):
        """When user rejects, handler returns rejection string."""
        with patch("libreassistant.tools.terminal.confirm_command", return_value=False):
            assert (
                handle_terminal({"command": "rm -rf /"}) == "Command rejected by user."
            )

    def test_successful_execution(self):
        """Approved command should be executed and output returned."""
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command",
                return_value="hello world",
            ),
        ):
            result = handle_terminal({"command": "echo hello"})
        assert result == "hello world"

    def test_shell_false_valid_shlex(self):
        """shell=False with valid shlex syntax should execute as a list."""
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            handle_terminal({"command": "echo hello", "shell": False})
            mock_exec.assert_called_once_with(
                ["echo", "hello"], use_shell=False, cwd=None
            )

    def test_shell_false_invalid_shlex(self):
        """shell=False with unbalanced quotes should return a syntax error."""
        with patch("libreassistant.tools.terminal.confirm_command", return_value=True):
            result = handle_terminal({"command": "echo 'unclosed", "shell": False})
        assert "Invalid command syntax" in result

    def test_default_shell_is_true(self):
        """When shell key is absent, default should be True."""
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            handle_terminal({"command": "ls"})
            mock_exec.assert_called_once_with("ls", use_shell=True, cwd=None)


# ─── confirm_command edge-case bypasses ─────────────────────────────────────────


class TestConfirmCommandBypasses:
    def test_dollar_paren_subexpression_bypass(self):
        """Commands with $() are NOT detected as shell operators — they auto-approve
        if the base token is in READ_ONLY_COMMANDS. This is a known bypass."""
        assert confirm_command("echo $(whoami)") is True

    def test_backtick_subexpression_bypass(self):
        """Commands with backticks are NOT detected as shell operators — same bypass."""
        assert confirm_command("echo `whoami`") is True

    def test_embedded_newline_bypass(self):
        """Commands with embedded newlines bypass operator detection."""
        assert confirm_command("cat file\nevil") is True

    def test_shlex_split_empty_string(self):
        """shlex.split on empty string returns an empty list."""
        import shlex

        assert shlex.split("") == []

    def test_shlex_split_whitespace_only(self):
        """shlex.split on whitespace-only string returns an empty list."""
        import shlex

        assert shlex.split("   ") == []

    def test_command_with_only_spaces_as_base_token(self):
        """Command whose base token is empty (after shlex) should not match any
        read-only command and should prompt."""
        import shlex

        tokens = shlex.split("  ")
        base = tokens[0] if tokens else ""
        assert base == ""
        assert base not in READ_ONLY_COMMANDS

    def test_heredoc_operator_not_detected(self):
        """The << heredoc operator is not in _SHELL_OPS, so it won't trigger a prompt
        if the base command is read-only. This is a known limitation."""
        assert confirm_command("cat << EOF") is True


# ─── READ_ONLY_COMMANDS membership ──────────────────────────────────────────────


class TestReadOnlyCommandsMembership:
    def test_all_read_only_auto_approve(self):
        """Every command in READ_ONLY_COMMANDS auto-approves alone."""
        for cmd in READ_ONLY_COMMANDS:
            assert confirm_command(cmd) is True, f"{cmd} should auto-approve"

    def test_dangerous_commands_require_prompt(self):
        """Commands NOT in the set should trigger the prompt."""
        dangerous = ["rm", "cp", "mv", "sudo"]
        for cmd in dangerous:
            with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
                assert confirm_command(cmd) is False, f"{cmd} should prompt"

    def test_read_only_piped_to_dangerous_triggers_prompt(self):
        """A read-only command piped to a dangerous command should trigger the prompt
        because shell operators are present."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
            assert confirm_command("ls | rm -rf /") is False


# ─── _always_allow cache edge cases ────────────────────────────────────────────


class TestAlwaysAllowCache:
    def test_trailing_space_makes_different_entry(self):
        """Exact string matching means trailing space creates a new cache entry."""
        _always_allow.add("make test")
        assert confirm_command("make test") is True
        # "make test " is different from "make test" in the cache
        with patch("libreassistant.tools.terminal.user_prompt", return_value="n"):
            assert confirm_command("make test ") is False

    def test_cache_persists_across_calls(self):
        """Once cached, confirm_command returns True on subsequent calls without prompting."""
        with patch("libreassistant.tools.terminal.user_prompt", return_value="a"):
            assert confirm_command("npm install") is True
        # Second call should hit cache — no prompt needed
        assert confirm_command("npm install") is True

    def test_cache_cleared_by_fixture(self):
        """The autouse fixture clears the cache between tests — verify it starts empty."""
        assert len(_always_allow) == 0


# ─── Terminal sandbox tests ───────────────────────────────────────────────────


class TestTerminalSandbox:
    """Tests for filesystem sandbox enforcement in the terminal tool."""

    def setup_method(self):
        """Set sandbox before each test."""
        set_sandbox_root(None)

    def teardown_method(self):
        """Reset sandbox after each test."""
        set_sandbox_root(None)

    def test_validate_allows_relative_path(self):
        """Relative paths should always pass validation."""
        _validate_command_paths("cat file.txt")

    def test_validate_allows_path_inside_sandbox(self, tmp_path):
        """Absolute paths within the sandbox should pass."""
        set_sandbox_root(str(tmp_path))
        _validate_command_paths(f"cat {tmp_path}/file.txt")

    def test_validate_blocks_path_outside_sandbox(self, tmp_path):
        """Absolute paths outside the sandbox should raise PermissionError."""
        set_sandbox_root(str(tmp_path))
        with pytest.raises(PermissionError, match="outside sandbox"):
            _validate_command_paths("cat /etc/passwd")

    def test_validate_no_sandbox_allows_all(self):
        """Without a sandbox root, all paths should be allowed."""
        _validate_command_paths("cat /etc/passwd")

    def test_handle_terminal_blocks_outside_sandbox(self, tmp_path):
        """Commands with absolute paths outside sandbox should be rejected."""
        set_sandbox_root(str(tmp_path))
        with patch("libreassistant.tools.terminal.confirm_command", return_value=True):
            result = handle_terminal({"command": "cat /etc/passwd"})
        assert "Error" in result
        assert "outside sandbox" in result

    def test_handle_terminal_allows_inside_sandbox(self, tmp_path):
        """Commands with paths inside sandbox should execute normally."""
        set_sandbox_root(str(tmp_path))
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            handle_terminal({"command": f"cat {tmp_path}/file.txt"})
            # Should be called with cwd set to sandbox root
            call_kwargs = mock_exec.call_args
            assert call_kwargs[1]["cwd"] == str(tmp_path)

    def test_handle_terminal_sets_cwd(self, tmp_path):
        """When sandbox is set, cwd should be passed to _exec_command."""
        set_sandbox_root(str(tmp_path))
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            handle_terminal({"command": "ls"})
            call_kwargs = mock_exec.call_args
            assert call_kwargs[1]["cwd"] == str(tmp_path)

    def test_handle_terminal_no_cwd_without_sandbox(self):
        """Without sandbox, cwd should be None."""
        with (
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            handle_terminal({"command": "ls"})
            call_kwargs = mock_exec.call_args
            assert call_kwargs[1]["cwd"] is None

    def test_kms_bypasses_sandbox(self, tmp_path):
        """--kms mode should bypass sandbox path validation."""
        set_sandbox_root(str(tmp_path))
        with (
            patch("libreassistant.tools.terminal.kms_mode", return_value=True),
            patch("libreassistant.tools.terminal.confirm_command", return_value=True),
            patch(
                "libreassistant.tools.terminal._exec_command", return_value="ok"
            ) as mock_exec,
        ):
            result = handle_terminal({"command": "cat /etc/passwd"})
            assert "Error" not in result or "sandbox" not in result
            call_kwargs = mock_exec.call_args
            assert call_kwargs[1]["cwd"] is None

    def test_validate_blocks_symlink_escape(self, tmp_path):
        """Symlinks that resolve outside the sandbox should be blocked."""
        set_sandbox_root(str(tmp_path))
        # Create a symlink pointing outside sandbox
        link = tmp_path / "escape"
        link.symlink_to("/etc")
        with pytest.raises(PermissionError, match="outside sandbox"):
            _validate_command_paths(f"cat {link}/passwd")
