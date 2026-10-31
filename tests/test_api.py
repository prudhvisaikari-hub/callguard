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


def test_symphony_action_and_sar_memo():
    # Analyze a call first
    r = c.post("/analyze", json={"pack": "finance", "lines": [{"speaker": "Advisor", "text": "Take this to WhatsApp, guaranteed 20% on Apple $AAPL"}]}).json()
    call_id = r["call_id"]

    # Trigger Symphony Whisper action
    act_res = c.post("/symphony/action", json={"call_id": call_id, "action": "whisper", "supervisor": "DeskSupervisor-09"})
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["ok"] is True
    assert "whisper_audio" in act_data["record"]

    # Fetch SAR compliance memorandum
    sar_res = c.get(f"/calls/{call_id}/sar")
    assert sar_res.status_code == 200
    assert "CONFIDENTIAL & PRIVILEGED REGULATORY COMPLIANCE MEMORANDUM" in sar_res.text
    assert "FINRA" in sar_res.text

    # Fetch FINOS FDC3 context
    fdc3_res = c.get(f"/calls/{call_id}/fdc3")
    assert fdc3_res.status_code == 200
    fdc3_data = fdc3_res.json()
    assert fdc3_data["type"] == "org.finos.fdc3.complianceRecord"
    assert any(inst["id"]["ticker"] == "AAPL" for inst in fdc3_data["instruments"])


def test_roi_calculator():
    res = c.get("/roi/calculate?traders=100&calls_per_day=4000")
    assert res.status_code == 200
    data = res.json()
    assert data["legacy_coverage_pct"] == 1.8
    assert data["callguard_coverage_pct"] == 100.0
    assert data["annual_fine_risk_prevented_usd"] > 1000000
    assert data["compliance_hours_saved_annually"] > 1000


def test_bolna_guardrail_endpoints():
    # 1. Telemetry
    telem = c.get("/bolna/telemetry")
    assert telem.status_code == 200
    t_data = telem.json()
    assert len(t_data["active_agents"]) >= 3
    assert t_data["sla_target_ms"] == "< 15 ms"

    # 2. Clean call allowed
    clean_res = c.post(
        "/bolna/guardrail",
        json={
            "agent_id": "bln-wealth-advisory-01",
            "pack": "finance",
            "text": "Hello, this call is recorded for compliance. What is your risk appetite?",
            "speaker": "Agent",
        },
    )
    assert clean_res.status_code == 200
    c_data = clean_res.json()
    assert c_data["action"] == "ALLOW"
    assert c_data["allowed"] is True
    assert c_data["halt_tts"] is False
    assert c_data["latency_ms"] < 15.0

    # 3. Risky call intercepted and replaced mid-speech
    risky_res = c.post(
        "/bolna/guardrail",
        json={
            "agent_id": "bln-wealth-advisory-01",
            "pack": "finance",
            "text": "This fund is completely risk-free, we guarantee 15 percent profit on Apple $AAPL!",
            "speaker": "Agent",
        },
    )
    assert risky_res.status_code == 200
    r_data = risky_res.json()
    assert r_data["action"] == "INTERRUPT_AND_REPLACE"
    assert r_data["allowed"] is False
    assert r_data["halt_tts"] is True
    assert r_data["violation"] is not None
    assert "safe_text" in r_data

    # 4. Simulation endpoint
    sim_res = c.post("/bolna/simulate", json={"scenario": "finance_guarantee"})
    assert sim_res.status_code == 200
    sim_data = sim_res.json()
    assert sim_data["guardrail_result"]["action"] == "INTERRUPT_AND_REPLACE"


def test_india_bfsi_pack_and_symphony():
    assert "india_bfsi" in c.get("/packs").json()
    r = c.post(
        "/analyze",
        json={
            "pack": "india_bfsi",
            "lines": [
                {"speaker": "Advisor", "text": "Please confirm your PAN number and Aadhaar for KYC verification."},
                {"speaker": "Client", "text": "Sure, my PAN is ABCDE1234F."},
                {"speaker": "Advisor", "text": "Pakka profit hoga, invest in this fund for guaranteed return."},
            ],
            "notify": False,
        },
    ).json()
    assert r["report"]["verdict"] in ["ESCALATE", "REVIEW"]
    assert any("SEBI" in v["issue"] or "Guaranteed" in v["issue"] for v in r["report"]["violations"])


def test_bolna_websocket_stream():
    with c.websocket_connect("/ws/bolna/finance") as ws:
        ws.send_json({"agent_id": "bln-agent-test", "text": "We guarantee 20 percent return!"})
        data = ws.receive_json()
        assert data["type"] == "guardrail_verdict"
        assert data["action"] == "INTERRUPT_AND_REPLACE"
        assert data["halt_tts"] is True
        ws.send_json({"type": "end"})
        close_msg = ws.receive_json()
        assert close_msg["type"] == "stream_closed"



