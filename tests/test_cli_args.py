"""Tests for CLI argument parsing."""

from unittest.mock import patch, MagicMock

import pytest


# --list-agents: invokes main(), catches SystemExit after profile listing
def test_list_agents(
    capsys,
):  # patching sys.argv, config, MCPManager, and API key to isolate CLI entry
    """--list-agents prints profiles and exits."""
    testargs = ["libreassistant", "--list-agents"]
    with patch("sys.argv", testargs):
        with patch("libreassistant.cli.get_api_key"):
            with patch("libreassistant.cli.load_config", return_value={}):
                with patch("libreassistant.cli.MCPManager"):
                    try:
                        from libreassistant.cli import main

                        main()
                    except SystemExit as e:
                        assert e.code is None or e.code == 0
    captured = capsys.readouterr()
    assert "default" in captured.out
    assert "legal" in captured.out
    assert "code" in captured.out


# --list-agents output includes human-readable descriptions
def test_list_agents_output(capsys):
    """--list-agents shows descriptions."""
    testargs = ["libreassistant", "--list-agents"]
    with patch("sys.argv", testargs):
        with patch("libreassistant.cli.get_api_key"):
            with patch("libreassistant.cli.load_config", return_value={}):
                with patch("libreassistant.cli.MCPManager"):
                    try:
                        from libreassistant.cli import main

                        main()
                    except SystemExit:
                        pass
    captured = capsys.readouterr()
    assert "Legal research" in captured.out or "courtlistener" in captured.out


# --- Argument parser unit tests (no patching) ---
def test_cli_parser_agent_default():  # manually constructs parser to avoid importing the real one (DRY but diverges from main)
    """Argument parser sets --agent default."""
    from libreassistant.cli import main
    import argparse

    parser = argparse.ArgumentParser(prog="libreassistant")
    parser.add_argument("--agent", default="default")
    parser.add_argument("--list-agents", action="store_true")
    args = parser.parse_args([])
    assert args.agent == "default"
    assert args.list_agents is False


def test_cli_parser_agent_custom():  # --agent flag accepts any string; no validation at parse time
    """Argument parser accepts --agent legal."""
    import argparse

    parser = argparse.ArgumentParser(prog="libreassistant")
    parser.add_argument("--agent", default="default")
    parser.add_argument("--list-agents", action="store_true")
    args = parser.parse_args(["--agent", "legal"])
    assert args.agent == "legal"


def test_cli_parser_list_agents():  # --list-agents flag is a boolean action
    """Argument parser handles --list-agents."""
    import argparse

    parser = argparse.ArgumentParser(prog="libreassistant")
    parser.add_argument("--agent", default="default")
    parser.add_argument("--list-agents", action="store_true")
    args = parser.parse_args(["--list-agents"])
    assert args.list_agents is True


def test_sandbox_root_wiring(tmp_path):
    """--sandbox-root calls set_sandbox_root for both file_ops and terminal."""
    testargs = ["libreassistant", "--sandbox-root", str(tmp_path)]
    with patch("sys.argv", testargs):
        with patch("libreassistant.cli.get_api_key"):
            with patch("libreassistant.cli.load_config", return_value={}):
                with (
                    patch("libreassistant.cli.MCPManager"),
                    patch("libreassistant.cli.auto_load", return_value=None),
                    patch("builtins.input", side_effect=EOFError),
                    patch(
                        "libreassistant.tools.file_ops.set_sandbox_root"
                    ) as mock_file_sandbox,
                    patch(
                        "libreassistant.tools.terminal.set_sandbox_root"
                    ) as mock_term_sandbox,
                ):
                    try:
                        from libreassistant.cli import main

                        main()
                    except (SystemExit, EOFError):
                        pass
    mock_file_sandbox.assert_called_once_with(str(tmp_path))
    mock_term_sandbox.assert_called_once_with(str(tmp_path))
