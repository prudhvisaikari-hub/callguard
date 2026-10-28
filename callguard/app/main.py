"""CallGuard API.  uvicorn app.main:app --reload"""

# New imports for security, CORS, and rate limiting
from fastapi.security import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse
import os

import asyncio, json, pathlib, uuid
from typing import Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from . import store
from .classifier import load_classifier
from .engine import CallSession, list_packs
from .llm import LLMJudge
from .stt import get_stt_provider, STTProvider, AudioStreamSession
from .symphony import post_audit

app = FastAPI(title="CallGuard", version="1.0")

# CORS configuration (allow same origin for static UI)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter (10 requests per minute per IP)
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# API Key security (header auth for HTTP, query/header auth for WS)
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

def get_api_key(api_key: Optional[str] = Depends(api_key_header)):
    expected_key = os.getenv("CALLGUARD_API_KEY")
    # If no environment key is set, skip authentication (useful for testing)
    if not expected_key:
        return None
    if api_key == expected_key:
        return api_key
    raise HTTPException(status_code=401, detail="Invalid or missing API Key")

async def get_ws_api_key(websocket: WebSocket):
    expected_key = os.getenv("CALLGUARD_API_KEY")
    if not expected_key:
        return None
    key = websocket.headers.get("x-api-key") or websocket.query_params.get("api_key")
    if key == expected_key:
        return key
    await websocket.close(code=1008)
    raise WebSocketDisconnect(code=1008)

LLM, CLF = LLMJudge(), load_classifier()


class Line(BaseModel):
    speaker: str
    text: str


class AnalyzeRequest(BaseModel):
    pack: str
    lines: list[Line]
    notify: bool = False


def _session(pack: str) -> CallSession:
    try:
        return CallSession(pack, llm=LLM, clf=CLF)
    except KeyError:
        raise HTTPException(404, f"unknown pack '{pack}'. Available: {list_packs()}")


@app.get("/health")
@limiter.limit("20/minute")
def health(request: Request):
    stt_p = get_stt_provider()
    return {
        "ok": True,
        "llm": LLM.enabled,
        "ml_prefilter": CLF is not None,
        "stt": {"provider": stt_p.name, "available": stt_p.is_available},
        "packs": list_packs(),
    }


@app.get("/packs")
def packs():
    return list_packs()


@app.post("/analyze")
@limiter.limit("5/minute")
async def analyze(req: AnalyzeRequest, request: Request, api_key: str = Depends(get_api_key)):
    """Batch mode: analyse a full transcript (post-call QA or testing)."""
    s = _session(req.pack)
    for l in req.lines:
        await s.ingest(l.speaker, l.text)
    report, call_id = s.report(), uuid.uuid4().hex[:12]
    store.save(call_id, report)
    out = {"call_id": call_id, "report": report}
    if req.notify:
        out["symphony"] = await post_audit(call_id, report)
    return out


@app.websocket("/ws/{pack}")
# Rate limiting disabled for WebSocket endpoint
async def live(websocket: WebSocket, pack: str, api_key: Optional[str] = Depends(get_ws_api_key)):
    """Live mode. Client sends {speaker,text} per utterance, or {type:'end'}."""
    await websocket.accept()
    try:
        s = _session(pack)
    except HTTPException as e:
        await websocket.send_json({"type": "error", "detail": e.detail})
        return await websocket.close()
    call_id = uuid.uuid4().hex[:12]
    try:
        while True:
            msg = await websocket.receive_json()
            if msg.get("type") == "end":
                report = s.report()
                store.save(call_id, report)
                await websocket.send_json({"type": "report", "call_id": call_id, "report": report,
                                    "symphony": await post_audit(call_id, report)})
                return await websocket.close()
            new = await s.ingest(msg["speaker"], msg["text"])
            await websocket.send_json({"type": "update", "flags": [f.__dict__ for f in new],
                                "score": s.score, "checklist": s.checklist()})
    except WebSocketDisconnect:
        store.save(call_id, s.report())


@app.websocket("/ws/audio/{pack}")
async def live_audio(
    ws: WebSocket,
    pack: str,
    channels: int = 1,
    sample_rate: int = 16000,
    speaker: str = "Agent",
    ch0: str = "Agent",
    ch1: str = "Customer",
    provider: Optional[str] = None,
    api_key: Optional[str] = Depends(get_ws_api_key),
):
    """Streaming audio mode. Accepts 16 kHz PCM audio chunks or fallback text frames."""
    await ws.accept()
    try:
        s = _session(pack)
    except HTTPException as e:
        await ws.send_json({"type": "error", "detail": e.detail})
        return await ws.close()

    call_id = uuid.uuid4().hex[:12]
    channel_mapping = {0: ch0, 1: ch1} if channels > 1 else {0: speaker}
    stt_prov = get_stt_provider(provider)

    await ws.send_json({
        "type": "provider_status",
        "provider": stt_prov.name,
        "available": stt_prov.is_available,
        "channels": channels,
        "speaker_mapping": channel_mapping,
    })

    if not stt_prov.is_available or stt_prov.name == "browser_fallback":
        # Browser fallback mode: Web Speech API streams text frames to this socket
        try:
            while True:
                msg = await ws.receive_json()
                mtype = msg.get("type")
                if mtype == "end":
                    report = s.report()
                    store.save(call_id, report)
                    await ws.send_json({
                        "type": "report",
                        "call_id": call_id,
                        "report": report,
                        "symphony": await post_audit(call_id, report),
                    })
                    return await ws.close()
                elif mtype == "transcript" or "text" in msg:
                    spk = msg.get("speaker", channel_mapping.get(0, "Agent"))
                    txt = msg.get("text", "")
                    if txt:
                        new = await s.ingest(spk, txt)
                        await ws.send_json({
                            "type": "transcript",
                            "speaker": spk,
                            "text": txt,
                            "is_final": True,
                        })
                        await ws.send_json({
                            "type": "update",
                            "flags": [f.__dict__ for f in new],
                            "score": s.score,
                            "checklist": s.checklist(),
                        })
        except WebSocketDisconnect:
            store.save(call_id, s.report())
        return

    # Streaming STT provider active (e.g. Deepgram or Mock)
    try:
        stt_stream = await stt_prov.create_stream(
            sample_rate=sample_rate,
            channels=channels,
            channel_mapping=channel_mapping,
        )
    except Exception as e:
        await ws.send_json({"type": "error", "detail": f"Failed to initialize STT provider: {e}"})
        return await ws.close()

    stop_event = asyncio.Event()

    async def pump_transcripts():
        try:
            async for res in stt_stream.receive():
                if stop_event.is_set():
                    break
                if res.is_final:
                    new = await s.ingest(res.speaker, res.text)
                    await ws.send_json({
                        "type": "transcript",
                        "speaker": res.speaker,
                        "text": res.text,
                        "is_final": True,
                        "channel": res.channel,
                    })
                    await ws.send_json({
                        "type": "update",
                        "flags": [f.__dict__ for f in new],
                        "score": s.score,
                        "checklist": s.checklist(),
                    })
                else:
                    await ws.send_json({
                        "type": "transcript",
                        "speaker": res.speaker,
                        "text": res.text,
                        "is_final": False,
                        "channel": res.channel,
                    })
        except Exception:
            pass

    t_task = asyncio.create_task(pump_transcripts())

    try:
        while True:
            message = await ws.receive()
            if message["type"] == "websocket.disconnect":
                break

            if "bytes" in message and message["bytes"]:
                await stt_stream.send_audio(message["bytes"])
            elif "text" in message and message["text"]:
                try:
                    data = json.loads(message["text"])
                except Exception:
                    continue

                if data.get("type") == "end":
                    stop_event.set()
                    await stt_stream.finish()
                    await t_task
                    report = s.report()
                    store.save(call_id, report)
                    await ws.send_json({
                        "type": "report",
                        "call_id": call_id,
                        "report": report,
                        "symphony": await post_audit(call_id, report),
                    })
                    return await ws.close()
                elif data.get("type") == "speaker":
                    channel_mapping[0] = data["speaker"]
                elif data.get("type") == "transcript" or "text" in data:
                    spk = data.get("speaker", channel_mapping.get(0, "Agent"))
                    txt = data.get("text", "")
                    if txt:
                        new = await s.ingest(spk, txt)
                        await ws.send_json({
                            "type": "update",
                            "flags": [f.__dict__ for f in new],
                            "score": s.score,
                            "checklist": s.checklist(),
                        })
    except WebSocketDisconnect:
        pass
    finally:
        stop_event.set()
        await stt_stream.finish()
        t_task.cancel()
        store.save(call_id, s.report())


@app.get("/calls")
def calls():
    return store.recent()


@app.get("/calls/{call_id}")
def call(call_id: str):
    r = store.get(call_id)
    if not r:
        raise HTTPException(404, "call not found")
    return r


STATIC = pathlib.Path(__file__).resolve().parent.parent / "static"
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")

