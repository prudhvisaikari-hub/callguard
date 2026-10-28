"""Delivery of audit summaries to Symphony, via the Java bridge or a direct webhook."""
import os
import httpx
from .engine import summary_text


async def post_audit(call_id: str, report: dict) -> dict:
    payload = {"callId": call_id, "message": summary_text(report), "verdict": report["verdict"],
               "riskScore": report["risk_score"], "pack": report["pack"]}
    url = os.getenv("BRIDGE_URL") or os.getenv("SYMPHONY_WEBHOOK_URL")
    if not url:
        return {"delivered": False, "reason": "no BRIDGE_URL or SYMPHONY_WEBHOOK_URL configured", "payload": payload}
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.post(url, json=payload)
        return {"delivered": r.is_success, "status": r.status_code, "payload": payload}
    except Exception as e:
        return {"delivered": False, "reason": str(e), "payload": payload}
