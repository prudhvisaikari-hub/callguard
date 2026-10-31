"""Measure precision/recall of the rule engine on labelled lines.  python -m eval.run_eval"""
import asyncio, csv, pathlib
from app.engine import CallSession


async def main():
    tp = fp = fn = tn = 0
    for r in csv.DictReader(open(pathlib.Path(__file__).parent / "lines.csv")):
        s = CallSession(r["pack"])
        got = bool(await s.ingest(r["speaker"], r["text"]))
        exp = r["expected"] == "flag"
        tp += got and exp; fp += got and not exp; fn += (not got) and exp; tn += (not got) and not exp
        if got != exp:
            print("MISS" if exp else "FALSE ALARM", "|", r["pack"], "|", r["text"])
    p = tp / (tp + fp) if tp + fp else 0
    rc = tp / (tp + fn) if tp + fn else 0
    print(f"precision={p:.2f} recall={rc:.2f} tp={tp} fp={fp} fn={fn} tn={tn}")


asyncio.run(main())
