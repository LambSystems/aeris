# Aeris Backend

FastAPI + Streamlit service that accepts object detections from YOLO, combines them with CASTNET air-quality context, and returns concise sustainability advice.

Shuja's updated context is the source of truth: the main product path is waste/object detection advice through `POST /sustainability/detect`.

---

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional `.env` in `backend/`:

```text
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

---

## Running

API server:

```bash
uvicorn app.main:app --reload
```

Runs at:

```text
http://localhost:8000
```

Interactive docs:

```text
http://localhost:8000/docs
```

Streamlit dev UI:

```bash
streamlit run streamlit_app.py
```

Runs at:

```text
http://localhost:8501
```

---

## Main Endpoint

### `POST /sustainability/detect`

This is the endpoint the YOLO pipeline or frontend calls when a detection is stable and confidence is at least `0.90`.

Request:

```json
{
  "detection": {
    "object_class": "soda_can",
    "confidence": 0.94,
    "frame_id": "frame_042",
    "timestamp": "2026-04-18T10:30:00Z",
    "bbox": { "x": 120, "y": 340, "width": 80, "height": 60 }
  }
}
```

Response:

```json
{
  "object_detected": "soda_can",
  "confidence": 0.94,
  "context": "A soda can was detected. Aluminum persists for decades if littered, and elevated ozone can add outdoor material stress.",
  "action": "Place it in the nearest recycling bin that accepts aluminum cans."
}
```

`bbox` is optional. All other fields are required.

---

## Sustainability Package

```text
app/sustainability/
  schemas.py
  castnet_mock.py
  adviser.py
```

Responsibilities:

- `schemas.py`: `YOLODetection`, `CASTNETReading`, `DetectionRequest`, `SustainabilityAdvice`
- `castnet_mock.py`: current mock CASTNET reading; replace with processed real CASTNET data
- `adviser.py`: prompt + provider call + response parsing

Planned backend hardening:

- deterministic CASTNET preprocessing through `scripts/process_castnet.py`
- deterministic fallback advice when no LLM key/network is available
- confidence/cooldown event policy for when not to call advice repeatedly

Processed CASTNET output is loaded from:

```text
data/castnet/processed/current_reading.json
```

Raw EPA ZIPs should stay local in `data/castnet/raw/` and are ignored by git.

---

## Other Endpoints

These remain from the earlier async scene-analysis version and are useful for compatibility/testing:

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check |
| `GET /context/demo` | Demo fixed context |
| `POST /scan-frame` | Fixture or uploaded-frame detection stub |
| `POST /analyze-scene` | Async agentic scene analysis |
| `GET /analysis/latest` | Latest completed analysis result |
| `GET /analysis/{job_id}` | Poll a specific analysis job |
| `POST /demo/run` | Full demo run with fixture data |
| `POST /recommend` | Direct fallback recommendation |

`/scan-frame` still accepts optional multipart field `file` and returns fixture detections until YOLO is fully wired.

---

## Local Checks

Compile backend:

```bash
python -m compileall app
```

From repo root, policy/fallback checks:

```bash
python scripts\test_backend_policy.py
```

With the API running, from repo root:

```bash
python scripts\smoke_backend.py
```
