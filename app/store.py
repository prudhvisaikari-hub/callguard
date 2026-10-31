"""SQLite audit store."""
import json, os, sqlite3, time

DB = os.getenv("DB_PATH", "callguard.db")


def _conn():
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS calls(id TEXT PRIMARY KEY, created REAL, pack TEXT, verdict TEXT, report TEXT)")
    return c


def save(call_id: str, report: dict):
    with _conn() as c:
        c.execute("INSERT OR REPLACE INTO calls VALUES(?,?,?,?,?)",
                  (call_id, time.time(), report["pack"], report["verdict"], json.dumps(report)))


def get(call_id: str):
    with _conn() as c:
        row = c.execute("SELECT report FROM calls WHERE id=?", (call_id,)).fetchone()
    return json.loads(row[0]) if row else None


def recent(limit: int = 20):
    with _conn() as c:
        rows = c.execute("SELECT id, created, pack, verdict FROM calls ORDER BY created DESC LIMIT ?", (limit,)).fetchall()
    return [{"id": r[0], "created": r[1], "pack": r[2], "verdict": r[3]} for r in rows]


def record_action(call_id: str, action_item: dict) -> dict:
    """Record a supervisory action taken on a call."""
    rep = get(call_id)
    if not rep:
        rep = {"pack": "finance", "verdict": "REVIEW", "risk_score": 50, "violations": []}
    if "actions" not in rep:
        rep["actions"] = []
    rep["actions"].append(action_item)
    save(call_id, rep)
    return rep

