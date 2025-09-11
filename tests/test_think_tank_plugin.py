# Copyright (c) 2024 LibreAssistant contributors.
# Licensed under the MIT License.

from typing import Any
import json
import pytest
from libreassistant.plugins import think_tank
from libreassistant.plugins.think_tank import ThinkTankPlugin
from tests.test_env_setup import TestEnvironmentSetup


@pytest.fixture(autouse=True)
def mock_model_env(monkeypatch, tmp_path):
    """Set up comprehensive test environment for Think Tank plugin."""
    # Use the standardized test environment setup
    env_vars = TestEnvironmentSetup.setup_test_environment_variables(monkeypatch, tmp_path)
    yield env_vars
    # Cleanup is handled by monkeypatch automatically


def test_thinktank_records_dossier() -> None:
    plugin = ThinkTankPlugin()
    state: dict[str, Any] = {}
    payload = {"goal": "Improve education"}
    result = plugin.run(state, payload)
    assert "summary" in result
    dossier_entry = state["thinktank_dossier"][0]
    assert dossier_entry["goal"] == "Improve education"
    assert "tasks" in dossier_entry["executive"]
    assert dossier_entry["visualizer"]["data"]["type"] == "bar"


def test_thinktank_generates_realistic_summary() -> None:
    plugin = ThinkTankPlugin()
    result = plugin.run({}, {"goal": "Improve education"})
    summary = result["summary"]
    assert "Argument:" in summary
    assert "Caveats:" in summary
    analysis = result["analysis"]
    assert analysis["research"]["summary"].startswith(
        "Preliminary surveys on improve education"
    )
    assert isinstance(analysis["argument"]["points"], list)


def test_think_tank_integration(client) -> None:
    think_tank.register()
    response = client.post(
        "/api/v1/invoke",
        json={
            "plugin": "think_tank",
            "payload": {"goal": "Improve education"},
            "user_id": "alice",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data["result"]
    assert "Argument:" in data["result"]["summary"]
    entry = data["state"]["thinktank_dossier"][0]
    assert entry["goal"] == "Improve education"
    assert entry["visualizer"]["data"]["type"] == "bar"
