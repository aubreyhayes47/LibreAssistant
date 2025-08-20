from typing import Any
import json
import pytest
from libreassistant.plugins import think_tank
from libreassistant.plugins.think_tank import ThinkTankPlugin


MOCK_ANALYSIS = {
    "summary": (
        "The objective is to improve education. Stakeholders should collaborate on this initiative.\n"
        "Argument: Improve education addresses an important societal need.; Investing in improve education can produce long-term benefits.; Improve education aligns with widely shared community values.\n"
        "Caveats: Limited resources could hamper efforts to improve education.; There may be unintended consequences when attempting to improve education."
    ),
    "analysis": {
        "goal": "Improve education",
        "executive": {
            "tasks": [
                "Assess the current state related to improve education.",
                "Develop a concrete plan to improve education.",
                "Implement the plan and monitor progress.",
            ]
        },
        "research": {
            "summary": "Preliminary surveys on improve education indicate that multiple approaches have been proposed in academic and policy literature.",
            "sources": ["https://example.org/research/improve_education"],
        },
        "devils_advocate": {
            "concerns": [
                "Limited resources could hamper efforts to improve education.",
                "There may be unintended consequences when attempting to improve education.",
            ]
        },
        "argument": {
            "points": [
                "Improve education addresses an important societal need.",
                "Investing in improve education can produce long-term benefits.",
                "Improve education aligns with widely shared community values.",
            ]
        },
        "communications": {
            "message": "The objective is to improve education. Stakeholders should collaborate on this initiative.",
            "audience": "general public",
        },
        "visualizer": {
            "description": "A bar chart visualizing stages to improve education.",
            "data": {
                "type": "bar",
                "labels": ["Plan", "Execute", "Review"],
                "values": [1, 2, 1],
            },
        },
    },
}


@pytest.fixture(autouse=True)
def mock_model_env(monkeypatch):
    monkeypatch.setenv("THINK_TANK_MODEL_RESPONSE", json.dumps(MOCK_ANALYSIS))
    yield
    monkeypatch.delenv("THINK_TANK_MODEL_RESPONSE", raising=False)


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
