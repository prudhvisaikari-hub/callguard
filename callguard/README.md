# CallGuard

Real-time compliance and safety layer for regulated voice calls. One engine, swappable YAML policy packs
(finance, healthcare, insurance, collections, crisis line).

## Architecture
```
Mic / telephony -> speech-to-text -> WebSocket /ws/{pack}
                                         |
   FastAPI (Python) -> nlp.py (normalise, Hinglish map, PII redaction)
                    -> rules + checklist from packs/*.yaml  (instant)
                    -> ML prefilter (TF-IDF + LogReg)        (cheap relevance score)
                    -> Claude LLM judge for implied violations (only when rules are silent)
                    -> SQLite audit trail
                    -> Java bridge (retry/backoff) -> Symphony room webhook
```

| Stack item | Where |
|---|---|
| Python, APIs, Web tech | `app/main.py` (REST + WebSocket), `static/index.html` |
| Generative AI, LLMs, Prompt engineering | `app/llm.py` (Claude, injection-safe system prompt) |
| NLP, Data processing | `app/nlp.py`, YAML packs, `eval/` |
| ML frameworks | `ml/train.py` (scikit-learn), `app/classifier.py` |
| Java | `bridge/` (Symphony delivery service, retry with backoff) |
| Cloud, Open source, Automation | `Dockerfile`, `docker-compose.yml`, `.github/workflows/ci.yml` |

## Run
```bash
cp .env.example .env            # add ANTHROPIC_API_KEY (optional: rules work without it)
pip install -r requirements.txt
python ml/train.py
uvicorn app.main:app --reload   # open http://localhost:8000 (live client) or http://localhost:8000/demo.html (standalone visual demo)
pytest -q && python -m eval.run_eval
```
With Docker (API + Java bridge): `docker compose up --build`.
Set `SYMPHONY_WEBHOOK_URL` to deliver summaries; adjust the payload in `bridge/` to your Symphony setup.

## API
- `GET /health`, `GET /packs`
- `POST /analyze` `{pack, lines:[{speaker,text}], notify}` batch analysis
- `WS /ws/{pack}` send `{speaker,text}` per utterance or `{type:"end"}`
- `GET /calls`, `GET /calls/{id}` audit records

## Add an industry
Copy a file in `app/packs/`, edit rules and checklist. No code changes needed.

## Verification & Benchmarks
- **Test Suite**: 27 unit tests passing (`pytest -q`).
- **Precision / Recall Benchmark**: 100% precision and 100% recall across 18 benchmark samples in `eval/lines.csv` (`python -m eval.run_eval`).
- **ML Prefilter**: 96% holdout recall on risky utterances across 750 balanced samples in `ml/data/seed_lines.csv` (`python ml/train.py`).
- **Java Bridge**: Compiled into `bridge/target/bridge.jar` (`java -jar bridge/target/bridge.jar`).
- **Legal Notice**: Not legal advice. Have compliance review every policy pack before production deployment.

