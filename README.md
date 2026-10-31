# CallGuard — In-Flight Voice Compliance on Symphony & Bolna
### 🏆 Y Combinator × Symphony Buildathon Entry (Symphony 2026 Voice AI Summit, Bengaluru)

> **"The In-Flight Guardrail for Wall Street Trading Desks & Autonomous Voice AI Agents."**  
> Every year, regulated institutions and lenders face **$3.2 Billion** in penalties for deceptive claims, coercive collection tactics, and unrecorded channels. Meanwhile, companies deploying autonomous Voice AI agents (via Bolna, etc.) risk catastrophic regulatory exposure if an AI bot hallucinates an illegal guarantee or abusive threat.  
> **CallGuard** monitors **100% of calls in-flight with &lt;15ms latency** — acting as a real-time safety layer for human reps and autonomous voice bots alike, whispering compliant rephrasings into rep earpieces and streaming interactive **Symphony MessageML alert cards** to supervisory rooms.

---

## 🏛️ System Architecture

```
  [Human Telephony / Mic]           [Bolna Autonomous Voice Agent]
            │                                    │
    PCM 16 kHz Audio                     HTTP/WS Candidate Utterance
            │                                    │
            ▼                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                       CallGuard Sub-15ms Core Engine                        │
│  1. Multilingual Normalization & Hinglish Idiom Parsing (nlp.py)            │
│  2. Automated PII Redaction (SSN, Aadhaar, Cards, Phones, Emails)           │
│  3. Sub-1ms Deterministic Policy Rules & Statutory Checklists               │
│  4. Clinical Prescription & Order Dose Verification                         │
│  5. Scikit-Learn ML Risk Prefilter (TF-IDF + LogisticRegression)            │
│  6. Claude LLM Fallback Judge (Asynchronous Implied Risk Evaluation)        │
│  7. Bolna Voice Bot Guardrail (Mid-Speech Audio Interception & TTS Halt)    │
│  8. FINOS FDC3 2.0 Desktop Interoperability & Cryptographic SAR Generator  │
│  9. Audit Trail Persistence (SQLite)                                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
 [Binaural Earpiece Whisper]                          [Enterprise Java Bridge]
  - Web Audio Synthetic Chime                          - 4-Attempt Exponential Backoff
  - Audio TTS Compliant Fix                            - Direct Symphony Room Bot
            │                                                     │
            ▼                                                     ▼
 Advisor / Trader Earpiece                        Symphony Room (#compliance-desk)
 (Remediates before hanging up)                   (Interactive MessageML Action Cards)
```

---

## 💡 The YC × Symphony Value Proposition

| Dimension | Legacy Compliance QA | CallGuard on Symphony & Bolna |
|---|---|---|
| **Coverage** | 1% – 2% sampled post-call | **100% of calls monitored in-flight** |
| **Intervention Speed** | 2 to 4 weeks post-call | **&lt; 15 ms instant earpiece whisper &amp; TTS halt** |
| **Autonomous Voice Bots** | Unmonitored hallucination risk | **Real-time Bolna guardrail middleware halts rogue speech** |
| **Supervision Desk** | Disconnected back-office audit | **1-Click Symphony Action Buttons** (*Whisper*, *Freeze Blotter*, *SAR Memo*) |
| **Interoperability** | Siloed standalone software | **FINOS FDC3 2.0 open standard across Symphony & Bloomberg** |
| **Fine Exposure** | Millions in retrospectively caught fines | **Preventative remediation before call termination** |

---

## 🚀 Key Features

### 1. Dual Ecosystem Synergy: Symphony + Bolna
- **Symphony 2.0 MessageML Action Cards**: Dispatches rich supervision cards with status badges (`tempo-bg-color--coral`, `tempo-bg-color--green`), financial cashtags (`$AAPL`, `$TSLA`), and interactive supervisory buttons (*Acknowledge*, *Trigger Whisper*, *Freeze Blotter*, *Generate SAR Memo*, *Broadcast FDC3*).
- **Bolna Voice AI Agent Middleware**: Real-time HTTP and WebSocket guardrail (`/bolna/guardrail`, `/ws/bolna/{pack}`) that intercepts autonomous voice bots mid-speech. When a bot hallucinates a prohibited promise, CallGuard halts the audio stream in &lt;10ms and injects approved statutory phrasing.
- **FINOS FDC3 2.0 Interoperability**: Standardized compliance record broadcast across Symphony Desktop, Bloomberg Terminal, FactSet, and OpenFin.
- **Official Form SAR Compliance Dossier**: Generates cryptographic SEC / FINRA / BSA Suspicious Activity Reports complete with SHA-256 integrity proofs.

### 2. Swappable Industry Policy Packs (YAML)
- 🏦 **Finance & Wealth**: Enforces `FINRA Rule 2210(d)(1)(D)` & `SEC Rule 206(4)-1`. Flags promised guarantees, pressure tactics, off-channel WhatsApp evasion, and CFTC spoofing.
- 🇮🇳 **India BFSI (SEBI & RBI Lending)**: Tailored for India's Voice AI Summit. Enforces `SEBI RIA 2013` (prohibiting assured returns) and `RBI Digital Lending Guidelines` (banning abusive debt recovery, unapproved contact access, and requiring Key Fact Statements).
- 🏥 **Healthcare & Clinical**: Enforces `HIPAA 45 CFR § 164.502` & `Joint Commission NPSG.02.03.01`. Blocks unverified PHI disclosure and verifies prescription dosages against clinical orders.
- 🛡️ **Insurance Sales**: Enforces `NAIC Model #275`. Flags deceptive "covers everything" claims and protects vulnerable consumers.
- ⚖️ **Debt Collection (FDCPA)**: Enforces `CFPB Regulation F` & `FDCPA 15 U.S.C. § 1692`. Catches abusive slurs, harassment, and police threats.
- 🆘 **Crisis Helpline**: Enforces `988 Lifeline Safety Protocols`. Tracks suicide cues, domestic violence disclosures, and location checks.

### 3. Ultra-Low Latency Multi-Stage Pipeline (&lt;15ms SLA)
- **Sub-1ms Deterministic Rules**: Instant regex and dosage verification.
- **Hinglish & Multilingual Normalizer**: Resolves Indian & colloquial idioms (*"pakka profit"*, *"turant invest karo"*, *"police bhejenge"*, *"dawa band kar do"*).
- **Automated PII Redaction**: Masks credit cards, SSNs, Aadhaar numbers, phone numbers, and emails before saving to transcripts or passing to models.
- **Scikit-Learn ML Prefilter**: TF-IDF + Logistic Regression trained on 750 balanced samples (**96% recall on risky lines, 93% accuracy**).
- **Claude LLM Judge**: Asynchronous fallback judge for implied or paraphrased violations.

### 4. Executive Telemetry Console
- Real-time HTML5 audio waveform oscilloscope canvas.
- Interactive **Symphony 2.0 Room Simulator Widget** displaying live incoming MessageML cards.
- **Supervision Target Switcher**: Toggle between **Human Advisory Desk** and **Autonomous Voice AI Agent (Bolna AI)**.
- 1-Click **"Simulate Call"** and **"Intercept Rogue Voice Bot"** demonstration modes.
- Interactive **Wall Street ROI & Regulatory Fine Avoidance Calculator**.
- Slide-over **Audit History Drawer** fetching past call records from SQLite.

---

## 🛠️ Quick Start

### 1. Run the Server
```powershell
# Activate environment
.\.venv\Scripts\Activate.ps1

# Start the CallGuard telemetry server & API
uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in Chrome or Edge to access the live compliance console.

### 2. Run Test Suite & Evaluation Benchmark
```powershell
# Run all 36 unit tests
pytest -q

# Run precision / recall benchmark across all policy packs
python -m eval.run_eval
```
*Result: `precision=1.00 recall=1.00 tp=11 fp=0 fn=0 tn=7` (100% precision and recall).*

### 3. Run the Java Symphony Bridge
```powershell
java -jar bridge/target/bridge.jar
```
Listens on port `8081` for audit summaries dispatched to Symphony with 4-attempt exponential backoff.

---

## 🌐 REST & WebSocket API Specification

| Endpoint | Protocol | Description |
|---|---|---|
| `GET /health` | HTTP | Service health, active STT engine, ML prefilter, and pack list |
| `GET /packs` | HTTP | Returns list of loaded YAML policy packs (finance, india_bfsi, healthcare, etc.) |
| `POST /analyze` | HTTP | Batch post-call QA analysis of full transcripts `{pack, lines, notify}` |
| `POST /bolna/guardrail` | HTTP | Sub-10ms in-flight compliance check for Bolna Voice Agents `{agent_id, pack, text}` |
| `GET /bolna/telemetry` | HTTP | Live telemetry of monitored autonomous Bolna Voice Agents |
| `POST /bolna/simulate` | HTTP | 1-Click simulation of an autonomous Bolna Voice Agent intercepted mid-speech |
| `WS /ws/bolna/{pack}` | WebSocket | Real-time streaming guardrail for Bolna Voice Agent pipelines |
| `POST /symphony/action` | HTTP | Process supervisory button clicks from Symphony cards (*Whisper*, *Freeze*, *SAR*) |
| `GET /calls/{id}/sar` | HTTP | Generate official SEC / FINRA / BSA Form SAR Cryptographic Memorandum |
| `GET /calls/{id}/fdc3` | HTTP | Return FINOS FDC3 2.0 context payload for Bloomberg / Symphony Desktop interop |
| `GET /roi/calculate` | HTTP | Dynamic Wall Street ROI & Regulatory Fine Avoidance Calculator |
| `GET /calls` | HTTP | Retrieve list of historical audited calls from SQLite |
| `GET /calls/{id}` | HTTP | Fetch detailed audit report by call ID |
| `WS /ws/{pack}` | WebSocket | Utterance-based text stream (`{speaker, text}`) |
| `WS /ws/audio/{pack}` | WebSocket | Streaming PCM 16 kHz audio chunk pipeline or browser speech fallback |

---

## 📁 Repository Layout

```
callguard-project/
├── .env                       # Environment configuration (Anthropic, Symphony webhook, ports)
├── .env.example               # Template environment configuration
├── .github/workflows/ci.yml   # GitHub Actions CI matrix (Python 3.12 + Java 17)
├── .gitignore                 # Ignore patterns for bytecode, databases, and artifacts
├── Dockerfile                 # Multi-stage production container
├── docker-compose.yml         # Container composition (API + Java Bridge)
├── pytest.ini                 # Pytest configuration
├── requirements.txt           # Python dependencies
├── README.md                  # This documentation
├── callguard.db               # SQLite audit persistence store
├── app/
│   ├── main.py                # FastAPI REST & WebSocket server
│   ├── engine.py              # Policy session, checklist, and scoring engine
│   ├── bolna.py               # Bolna Voice Agent in-flight guardrail & telemetry
│   ├── nlp.py                 # Normalization, Hinglish map, number parsing, PII redaction
│   ├── stt.py                 # Streaming STT (Deepgram, WebSpeech, Mock)
│   ├── llm.py                 # Claude LLM judge for implied violations
│   ├── classifier.py          # Scikit-learn risk prefilter loader
│   ├── store.py               # SQLite audit store
│   ├── symphony.py            # MessageML generator, FDC3 standard, SAR memo, Java bridge
│   └── packs/                 # YAML policy packs (finance, india_bfsi, healthcare, collections, etc.)
├── bridge/                    # Enterprise Java bridge with exponential backoff
│   ├── pom.xml
│   ├── Dockerfile
│   ├── src/main/java/ai/callguard/SymphonyBridge.java
│   └── target/bridge.jar      # Pre-compiled executable JAR
├── eval/                      # Benchmark scripts and validation lines
│   ├── lines.csv
│   └── run_eval.py
├── ml/                        # Training script, seed dataset, and serialized model
│   ├── train.py
│   ├── generate_data.py
│   ├── metrics.json
│   ├── risk_clf.joblib
│   └── data/seed_lines.csv
├── static/                    # Telemetry UI
│   ├── index.html             # Symphony 2.0 room feed & real-time telemetry console
│   ├── demo.html              # Standalone interactive client
│   └── pcm-worker.js          # 16 kHz PCM AudioWorklet processor
└── tests/                     # 36 comprehensive unit tests
    ├── conftest.py
    ├── test_api.py
    ├── test_engine.py
    ├── test_nlp.py
    └── test_stt.py
```
