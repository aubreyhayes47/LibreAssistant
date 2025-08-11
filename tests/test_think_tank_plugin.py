from libreassistant.plugins import think_tank
from libreassistant.plugins.think_tank import ThinkTankPlugin


def test_thinktank_records_dossier() -> None:
    plugin = ThinkTankPlugin()
    state = {}
    payload = {"goal": "Improve education"}
    result = plugin.run(state, payload)
    assert "summary" in result
    assert state["thinktank_dossier"][0]["goal"] == "Improve education"


def test_think_tank_integration(client) -> None:
    think_tank.register()
    response = client.post(
        "/api/v1/invoke",
        json={"plugin": "think_tank", "payload": {"goal": "Improve education"}, "user_id": "alice"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data["result"]
    assert data["state"]["thinktank_dossier"][0]["goal"] == "Improve education"
