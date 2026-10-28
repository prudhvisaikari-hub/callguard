"""Policy engine: YAML rules + checklist + ML prefilter + LLM judge."""
import os, pathlib, re, time
from dataclasses import dataclass, asdict
import yaml
from .nlp import normalize, redact

PACK_DIR = pathlib.Path(__file__).parent / "packs"
WEIGHTS = {"high": 30, "medium": 15, "low": 5}
LLM_THRESHOLD = float(os.getenv("LLM_RISK_THRESHOLD", "0.3"))


def list_packs() -> list[str]:
    return sorted(p.stem for p in PACK_DIR.glob("*.yaml"))


def load_pack(name: str) -> dict:
    path = PACK_DIR / f"{name}.yaml"
    if not path.exists():
        raise KeyError(name)
    return yaml.safe_load(path.read_text())


@dataclass
class Flag:
    ts: str
    speaker: str
    severity: str
    issue: str
    fix: str
    quote: str
    source: str  # rule | dose_check | llm


class CallSession:
    def __init__(self, pack_name: str, llm=None, clf=None):
        self.pack_name = pack_name
        self.pack = load_pack(pack_name)
        self.llm, self.clf = llm, clf
        self.rules = [(re.compile(r["pattern"], re.I), r) for r in self.pack["rules"]]
        self.checks = [(re.compile(c["pattern"], re.I), c) for c in self.pack["checklist"]]
        self.done: dict[str, str] = {}
        self.flags: list[Flag] = []
        self.lines: list[dict] = []
        self.t0 = time.time()

    def _ts(self) -> str:
        s = int(time.time() - self.t0)
        return f"{s // 60:02d}:{s % 60:02d}"

    @property
    def score(self) -> int:
        return min(100, sum(WEIGHTS[f.severity] for f in self.flags))

    async def ingest(self, speaker: str, text: str) -> list[Flag]:
        ts, norm, clean = self._ts(), normalize(text), redact(text)
        self.lines.append({"ts": ts, "speaker": speaker, "text": clean})
        new: list[Flag] = []

        for rx, r in self.rules:
            if speaker not in r.get("speakers", [speaker]):
                continue
            if r.get("unless_done") in self.done:
                continue
            if rx.search(norm):
                new.append(Flag(ts, speaker, r["severity"], r["message"], r["fix"], clean, "rule"))

        order = self.pack.get("order")
        if order:
            m = re.search(rf"{re.escape(order['drug'])}\D{{0,20}}(\d+)\s*(?:mg|milligram)", norm)
            if m and int(m.group(1)) != order["dose_mg"]:
                new.append(Flag(ts, speaker, "high",
                                f"Dose mismatch: said {m.group(1)} mg, order says {order['dose_mg']} mg.",
                                "Re-check the order and read it back.", clean, "dose_check"))

        if not new and self.llm and self.llm.enabled:
            p = self.clf.risk(norm) if self.clf else 1.0
            if p >= LLM_THRESHOLD:
                for v in await self.llm.judge(self.pack, self.lines[-6:]):
                    new.append(Flag(ts, speaker, v["severity"], v.get("issue", "Possible violation"),
                                    v.get("fix", ""), clean, "llm"))

        for rx, c in self.checks:
            if c["id"] not in self.done and rx.search(norm):
                self.done[c["id"]] = ts

        self.flags += new
        return new

    def checklist(self) -> list[dict]:
        return [{"id": c["id"], "item": c["label"], "completed": c["id"] in self.done,
                 "at": self.done.get(c["id"])} for _, c in self.checks]

    def report(self) -> dict:
        done = len(self.done)
        s = self.score
        return {"pack": self.pack["name"], "duration": self._ts(), "risk_score": s,
                "verdict": "ESCALATE" if s >= 60 or any(f.severity == "high" for f in self.flags)
                           else "REVIEW" if s >= 15 else "CLEAR",
                "violations": [asdict(f) for f in self.flags], "checklist": self.checklist(),
                "coverage": f"{done}/{len(self.checks)} required items completed",
                "transcript": self.lines}


def summary_text(r: dict) -> str:
    miss = [c["item"] for c in r["checklist"] if not c["completed"]]
    s = (f"{r['verdict']}: {r['pack']} call ({r['duration']}). Risk {r['risk_score']}/100. "
         f"{len(r['violations'])} violation(s). {r['coverage']}.")
    if miss:
        s += " Missing: " + "; ".join(miss) + "."
    if r["violations"]:
        v = r["violations"][0]
        s += f" First issue at {v['ts']}: {v['issue']}"
    return s
