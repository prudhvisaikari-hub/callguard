import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.stt import get_stt_provider, BrowserFallbackSTTProvider, DeepgramSTTProvider, MockSTTProvider

client = TestClient(app)


def test_stt_provider_factory():
    browser_prov = get_stt_provider("browser")
    assert isinstance(browser_prov, BrowserFallbackSTTProvider)
    assert browser_prov.is_available is True

    dg_no_key = DeepgramSTTProvider(api_key="")
    assert dg_no_key.is_available is False

    mock_prov = get_stt_provider("mock")
    assert isinstance(mock_prov, MockSTTProvider)
    assert mock_prov.is_available is True


def test_ws_audio_browser_fallback_mode():
    with client.websocket_connect("/ws/audio/finance?provider=browser") as ws:
        status = ws.receive_json()
        assert status["type"] == "provider_status"
        assert status["provider"] == "browser_fallback"

        # Client sends transcribed line from browser speech API
        ws.send_json({
            "type": "transcript",
            "speaker": "Advisor",
            "text": "This fund is completely risk-free",
        })
        msg1 = ws.receive_json()
        assert msg1["type"] == "transcript"
        assert msg1["text"] == "This fund is completely risk-free"

        msg2 = ws.receive_json()
        assert msg2["type"] == "update"
        assert any(f["severity"] == "high" for f in msg2["flags"])

        ws.send_json({"type": "end"})
        report_msg = ws.receive_json()
        assert report_msg["type"] == "report"
        assert report_msg["report"]["pack"] == "Finance"


def test_ws_audio_pcm_streaming_mock():
    with client.websocket_connect("/ws/audio/finance?provider=mock&channels=1&speaker=Advisor") as ws:
        status = ws.receive_json()
        assert status["type"] == "provider_status"
        assert status["available"] is True

        # Send raw 16kHz PCM bytes
        pcm_chunk = b"\x00\x00" * 1600  # 3200 bytes
        ws.send_bytes(pcm_chunk)

        trans_msg = ws.receive_json()
        assert trans_msg["type"] == "transcript"
        assert "risk-free" in trans_msg["text"]

        update_msg = ws.receive_json()
        assert update_msg["type"] == "update"
        assert update_msg["flags"]

        ws.send_json({"type": "end"})
        rep = ws.receive_json()
        assert rep["type"] == "report"
        assert rep["report"]["violations"]


def test_ws_audio_multichannel_mapping():
    with client.websocket_connect("/ws/audio/finance?channels=2&ch0=Advisor&ch1=Client&provider=browser") as ws:
        status = ws.receive_json()
        assert status["type"] == "provider_status"
        assert status["channels"] == 2
        assert status["speaker_mapping"]["0"] == "Advisor"
        assert status["speaker_mapping"]["1"] == "Client"
        ws.send_json({"type": "end"})
