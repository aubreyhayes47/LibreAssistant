"""Tests for libreassistant.config module."""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from libreassistant.config import (
    CONFIG_DIR,
    CONFIG_PATH,
    get_api_key,
    kms_mode,
    load_config,
    save_config,
    strip_control_chars,
)


# ---------------------------------------------------------------------------
# Fixture: save and restore sys.argv around every test
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def _restore_argv():
    """Ensure sys.argv is restored after tests that mock it."""
    original = sys.argv[:]
    yield
    sys.argv[:] = original


# ---------------------------------------------------------------------------
# 1. kms_mode()
# ---------------------------------------------------------------------------
class TestKmsMode:
    def test_returns_true_when_flag_present(self):
        sys.argv = ["libreassistant", "--kms"]
        assert kms_mode() is True

    def test_returns_true_when_flag_is_only_arg(self):
        sys.argv = ["--kms"]
        assert kms_mode() is True

    def test_returns_false_when_flag_absent(self):
        sys.argv = ["libreassistant"]
        assert kms_mode() is False

    def test_returns_false_for_empty_argv(self):
        sys.argv = []
        assert kms_mode() is False

    def test_returns_false_when_similar_flag(self):
        sys.argv = ["libreassistant", "--kms-extra"]
        assert kms_mode() is False

    def test_returns_true_among_other_flags(self):
        sys.argv = ["libreassistant", "--agent", "legal", "--kms"]
        assert kms_mode() is True


# ---------------------------------------------------------------------------
# 2. strip_control_chars()
# ---------------------------------------------------------------------------
class TestStripControlChars:
    def test_strips_null_byte(self):
        assert strip_control_chars("hello\x00world") == "helloworld"

    def test_strips_bell(self):
        assert strip_control_chars("hello\x07world") == "helloworld"

    def test_strips_backspace(self):
        assert strip_control_chars("hello\x08world") == "helloworld"

    def test_strips_escape(self):
        assert strip_control_chars("hello\x1bworld") == "helloworld"

    def test_does_not_strip_tab(self):
        assert strip_control_chars("hello\tworld") == "hello\tworld"

    def test_does_not_strip_newline(self):
        assert strip_control_chars("hello\nworld") == "hello\nworld"

    def test_does_not_strip_carriage_return(self):
        assert strip_control_chars("hello\rworld") == "hello\rworld"

    def test_strips_control_chars_keeps_normal_text(self):
        assert strip_control_chars("\x01\x02hello\x7f") == "hello"

    def test_empty_string(self):
        assert strip_control_chars("") == ""

    def test_none_returns_empty(self):
        assert strip_control_chars(None) == ""

    def test_no_control_chars_passthrough(self):
        assert strip_control_chars("plain text 123 !@#") == "plain text 123 !@#"

    def test_complex_ansi_escape(self):
        # Only the \x1b bytes are stripped; the remaining CSI params are printable
        assert strip_control_chars("\x1b[31mHello\x1b[0m") == "[31mHello[0m"

    def test_strips_vertical_tab(self):
        assert strip_control_chars("a\x0bb") == "ab"

    def test_strips_form_feed(self):
        assert strip_control_chars("a\x0cb") == "ab"

    def test_strips_del(self):
        assert strip_control_chars("a\x7fb") == "ab"

    def test_all_control_chars_stripped(self):
        ctrl = "".join(chr(i) for i in range(0x00, 0x20))
        result = strip_control_chars(ctrl)
        assert "\x09" in result   # tab kept
        assert "\x0a" in result   # newline kept
        assert "\x0d" in result   # carriage return kept
        assert "\x00" not in result
        assert "\x07" not in result
        assert "\x1b" not in result


# ---------------------------------------------------------------------------
# 3. get_api_key()
# ---------------------------------------------------------------------------
class TestGetApiKey:
    def test_returns_existing_key(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_key": "oc-test-key"}))
        with patch.object(type(CONFIG_PATH), "parent", tmp_path):
            with patch("libreassistant.config.CONFIG_PATH", cfg_file):
                assert get_api_key() == "oc-test-key"

    def test_returns_none_key_falls_through_to_prompt(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_key": None}))
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                with patch("libreassistant.config.getpass", return_value="oc-new-key"):
                    result = get_api_key()
                    assert result == "oc-new-key"

    def test_corrupt_config_file_prompts(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("not valid json{{{")
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                with patch("libreassistant.config.getpass", return_value="oc-recovered"):
                    result = get_api_key()
                    assert result == "oc-recovered"

    def test_missing_config_file_prompts(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                with patch("libreassistant.config.getpass", return_value="oc-first"):
                    result = get_api_key()
                    assert result == "oc-first"

    def test_saves_new_key_after_prompt(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                with patch("libreassistant.config.getpass", return_value="oc-saved"):
                    get_api_key()
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "oc-saved"

    def test_saved_key_file_permissions(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                with patch("libreassistant.config.getpass", return_value="oc-perm"):
                    get_api_key()
        assert oct(cfg_file.stat().st_mode)[-3:] == "600"


# ---------------------------------------------------------------------------
# 4. load_config()
# ---------------------------------------------------------------------------
class TestLoadConfig:
    def test_valid_json(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_key": "k", "search_provider": "google"}))
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg["api_key"] == "k"
        assert cfg["search_provider"] == "google"

    def test_missing_file_returns_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg == {"api_key": None, "search_provider": "duckduckgo", "search_api_key": None}

    def test_corrupt_json_returns_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("}{bad json{")
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg == {"api_key": None, "search_provider": "duckduckgo", "search_api_key": None}

    def test_empty_file_returns_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("")
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg == {"api_key": None, "search_provider": "duckduckgo", "search_api_key": None}

    def test_partial_config_merges_with_defaults(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"search_provider": "brave"}))
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg["search_provider"] == "brave"
        assert cfg["api_key"] is None
        assert cfg["search_api_key"] is None

    def test_unknown_keys_preserved(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"custom_key": "value"}))
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            cfg = load_config()
        assert cfg["custom_key"] == "value"
        assert cfg["api_key"] is None


# ---------------------------------------------------------------------------
# 5. save_config()
# ---------------------------------------------------------------------------
class TestSaveConfig:
    def test_writes_updates_to_file(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"api_key": "new-key"})
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "new-key"

    def test_atomic_write_creates_tmp_then_replaces(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"api_key": "atomic"})
        assert not (tmp_path / "config.tmp").exists()
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "atomic"

    def test_sets_permissions_600(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"api_key": "perm"})
        assert oct(cfg_file.stat().st_mode)[-3:] == "600"

    def test_merges_with_existing_config(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text(json.dumps({"api_key": "old", "search_provider": "google"}))
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"search_provider": "brave"})
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "old"
        assert saved["search_provider"] == "brave"

    def test_no_existing_file(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"api_key": "first"})
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "first"

    def test_corrupt_existing_file_ignored(self, tmp_path):
        cfg_file = tmp_path / "config.json"
        cfg_file.write_text("}{bad{")
        with patch("libreassistant.config.CONFIG_PATH", cfg_file):
            with patch("libreassistant.config.CONFIG_DIR", tmp_path):
                save_config({"api_key": "after-corrupt"})
        saved = json.loads(cfg_file.read_text())
        assert saved["api_key"] == "after-corrupt"
