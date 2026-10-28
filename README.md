# CallGuard — Enterprise Real-Time Compliance &amp; Safety Layer

**CallGuard** is a real-time compliance and risk monitoring layer for high-stakes, regulated voice calls. It combines zero-latency regex policy packs, clinical and mathematical dosage read-back verifications, Hinglish/colloquial text normalization, automated PII redaction, an ML prefilter (TF-IDF + Logistic Regression), an optional Claude LLM judge for subtle implied violations, and a Java enterprise bridge with exponential backoff for Symphony chat room compliance alerts.

---

## 🏛️ System Architecture

```
Microphone / Telephony -> 16 kHz PCM Audio / Web Speech
                                 |
                     WebSocket /ws/audio/{pack}
                                 |
   ┌─────────────────────────────────────────────────────────────┐
   │                    FastAPI Core Engine                      │
   │  1. Text Normalization & Number-Word Conversion (nlp.py)    │
   │  2. Automated PII Redaction (SSN, Aadhaar, Cards, Phones)   │
   │  3. Deterministic Policy Rules & Mandatory Checklists       │
   │  4. Clinical Prescription & Order Dose Verification         │
   │  5. ML Risk Prefilter (TF-IDF + LogisticRegression)         │
   │  6. Claude LLM Judge (Implied Violations / Prompt-Shielded) │
   │  7. Audit Trail Persistence (SQLite)                        │
   └─────────────────────────────────────────────────────────────┘
                                 │
     Java Delivery Bridge (HTTP Server with Exponential Backoff)
                                 │
                      Symphony Webhook Room
```

---

## 🚀 Key Features

1. **Swappable Industry Policy Packs (YAML)**
   - 🏦 **Finance & Wealth**: Detects promised guarantees, pressure tactics, concentration risk; checks recording consent, risk disclosures, suitability appetite.
   - 🏥 **Healthcare & Clinical**: Enforces 2-identifier patient verification before PHI disclosure, dosage read-back verification against clinical orders (e.g., Metformin 500 mg).
   - 🛡️ **Insurance Sales**: Flags misleading "all-risk covered" claims, vulnerable customer coercion; monitors statutory free-look notices and exclusions.
   - ⚖️ **Debt Collection (FDCPA)**: Enforces Mini-Miranda disclosures; flags harassment, third-party threats, and abusive language.
   - 🆘 **Crisis Helpline**: Detects suicide cues, domestic violence disclosures; tracks location and safety verifications.

2. **Dual-Mode Streaming Speech-to-Text (STT)**
   - **Deepgram 16 kHz Linear16 PCM**: Streaming binary audio via `AudioWorklet` processor directly over WebSocket.
   - **Web Speech API Fallback**: In-browser client recognition with interim and final text frames.
   - **Multi-channel & Diarization**: Map channel 0 and 1 to Agent / Customer or Nurse / Patient.

3. **Multi-Stage Risk Detection Pipeline**
   - **Instant Rules**: Sub-millisecond regex & dosage validation.
   - **NLP & Hinglish Normalizer**: Translates colloquial phrases (*"pakka profit"*, *"turant invest karo"*, *"police bhejenge"*, *"dawa band kar do"*) and spoken numbers (*"eight fifty mg"* → `850 mg`).
   - **PII Redaction**: Masks credit cards, SSNs, Aadhaar numbers, phone numbers, and emails before saving to transcripts.
   - **ML Risk Prefilter**: Scikit-Learn TF-IDF + Logistic Regression trained on 750 balanced samples (96% recall on risky utterances, 93% accuracy).
   - **Claude LLM Judge**: Evaluates implied paraphrases only when rules are silent and ML score exceeds threshold (`LLM_RISK_THRESHOLD=0.3`).

4. **Modern Telemetry Web Console**
   - Live visualizer canvas with real-time waveform oscilloscope.
   - 1-click **"Play Demo Call"** simulation for every industry.
   - Risk telemetry dial (`CLEAR`, `REVIEW`, `ESCALATE`) and active policy checklist.
   - Inline violation alerts with compliant suggested fixes and Voice Whisper audio prompts.
   - Slide-over **Audit History Drawer** to inspect previous calls from SQLite.
   - Symphony room dispatch preview.

5. **Enterprise Java Bridge**
   - Java 17/21 HTTP service with 4-attempt exponential backoff (0.5s, 1s, 2s) forwarding audit records to Symphony chat rooms.

---

## 🛠️ Quick Start

### 1. Environment Setup
```powershell
# In callguard directory
cd callguard

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# (Optional) Add Anthropic key for LLM judge or Deepgram key for PCM STT in .env
Copy-Item .env.example .env
```

### 2. Train the ML Prefilter
```powershell
python ml/train.py
```
*Output: 96% validation recall on risky utterances, cross-validation metrics saved to `ml/metrics.json`.*

### 3. Run the Server
```powershell
uvicorn app.main:app --reload --port 8000
```
Open **`http://localhost:8000`** in Chrome/Edge to access the live compliance console, or **`http://localhost:8000/demo.html`** for the standalone interactive demo.

### 4. Run Test Suite & Evaluation Benchmark
```powershell
# Run all 27 unit tests
pytest -q

# Run precision / recall benchmark across all 5 industry packs
python -m eval.run_eval
```
*Result: `precision=1.00 recall=1.00 tp=11 fp=0 fn=0 tn=7` (100% precision and recall).*

### 5. Java Enterprise Bridge
```powershell
# Run the pre-compiled bridge jar
java -jar bridge/target/bridge.jar
```
Listens on port `8081` for audit summaries dispatched to Symphony.

---

## 🌐 REST & WebSocket API Specification

| Endpoint | Protocol | Description |
|---|---|---|
| `GET /health` | HTTP | Service health, active STT engine, ML prefilter, and pack list |
| `GET /packs` | HTTP | Returns list of loaded YAML policy packs |
| `POST /analyze` | HTTP | Batch post-call QA analysis of full transcripts `{pack, lines, notify}` |
| `GET /calls` | HTTP | Retrieve list of historical audited calls from SQLite |
| `GET /calls/{id}` | HTTP | Fetch detailed audit report by call ID |
| `WS /ws/{pack}` | WebSocket | Utterance-based text stream (`{speaker, text}`) |
| `WS /ws/audio/{pack}` | WebSocket | Streaming PCM 16 kHz audio chunk pipeline or browser speech fallback |

---

## 📁 Repository Layout

```
callguard-project/
├── app/                       # Root proxy package for top-level imports
├── callguard/
│   ├── app/
│   │   ├── main.py            # FastAPI REST & WebSocket server
│   │   ├── engine.py          # Policy session, checklist, and scoring engine
│   │   ├── nlp.py             # Normalization, Hinglish map, number parsing, PII redaction
│   │   ├── stt.py             # Streaming STT (Deepgram, WebSpeech, Mock)
│   │   ├── llm.py             # Claude LLM judge for implied violations
│   │   ├── classifier.py      # Scikit-learn risk prefilter loader
│   │   ├── store.py           # SQLite audit store
│   │   ├── symphony.py        # Webhook / bridge dispatcher
│   │   └── packs/             # YAML policy packs (finance, healthcare, insurance, etc.)
│   ├── bridge/                # Enterprise Java bridge with exponential backoff
│   │   ├── pom.xml
│   │   ├── src/main/java/ai/callguard/SymphonyBridge.java
│   │   └── target/bridge.jar  # Compiled executable JAR
│   ├── eval/                  # Benchmark scripts and validation lines
│   ├── ml/                    # Training script, seed dataset, and serialized model
│   ├── static/                # Luxury telemetry UI (index.html, demo.html, pcm-worker.js)
│   └── tests/                 # 27 comprehensive unit tests (API, STT, engine, NLP)
├── pytest.ini                 # Pytest configuration
└── README.md
```
