from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)


def test_health_and_packs():
    assert c.get("/health").json()["ok"]
    assert "finance" in c.get("/packs").json()


def test_analyze_roundtrip():
    r = c.post("/analyze", json={"pack": "finance", "lines": [{"speaker": "Advisor", "text": "guaranteed returns"}]}).json()
    assert r["report"]["violations"]
    assert c.get(f"/calls/{r['call_id']}").status_code == 200


def test_unknown_pack():
    assert c.post("/analyze", json={"pack": "nope", "lines": []}).status_code == 404


def test_websocket_flow():
    with c.websocket_connect("/ws/finance") as ws:
        ws.send_json({"speaker": "Advisor", "text": "this is a sure thing"})
        assert ws.receive_json()["flags"]
        ws.send_json({"type": "end"})
        assert ws.receive_json()["type"] == "report"


def test_calls_listing_and_not_found():
    res = c.get("/calls")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    not_found = c.get("/calls/unknown_id_000")
    assert not_found.status_code == 404

