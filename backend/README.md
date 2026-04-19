# Aeris Backend

FastAPI + Streamlit service that takes object detections from a YOLO pipeline and air quality data from CASTNET, then uses Claude (Anthropic) to generate concise sustainability advice.

---

## How It Works

```
YOLO Pipeline (teammate)
        │
        │  POST /sustainability/detect
        │  { object_class, confidence, bbox, frame_id, timestamp }
        ▼
┌─────────────────────────────────────┐
│         FastAPI  (main.py)          │
│                                     │
│  1. Receives YOLO detection JSON    │
│  2. Loads CASTNET air quality data  │
│     (mock now → real API later)     │
│  3. Calls get_sustainability_advice │
└──────────────────┬──────────────────┘
                   │
                   ▼
┌─────────────────────────────────────┐
│        adviser.py (LLM layer)       │
│                                     │
│  Builds prompt:                     │
│   - detected object + confidence    │
│   - ozone, sulfate, nitrate, CO     │
│                                     │
│  Calls Claude (claude-sonnet-4-6)   │
│                                     │
│  Parses JSON response into:         │
│   - context  (what + why)           │
│   - action   (what to do now)       │
└──────────────────┬──────────────────┘
                   │
                   ▼
        SustainabilityAdvice
        {
          object_detected,
          confidence,
          context,   ← one sentence: object, material, env impact
          action     ← one sentence: exactly what to do
        }
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Frontend UI       Streamlit
     (teammate)        (demo/dev)
```

---

## Folder Structure

```
backend/
├── app/
│   ├── main.py                    # FastAPI routes
│   ├── schemas.py                 # Shared Pydantic models (BoundingBox, etc.)
│   ├── sustainability/
│   │   ├── schemas.py             # YOLODetection, CASTNETReading, SustainabilityAdvice
│   │   ├── castnet_mock.py        # Mock CASTNET data — swap this for real API
│   │   └── adviser.py             # Prompt + Claude call + response parsing
│   └── cv/
│       └── yolo_service.py        # YOLO stub — replace with real pipeline output
└── streamlit_app.py               # Dev UI to test detections manually
```

---

## Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
ANTHROPIC_API_KEY=your_key_here
```

---

## Running

**API server:**
```bash
uvicorn app.main:app --reload
```
Runs at `http://localhost:8000` — interactive docs at `http://localhost:8000/docs`

**Streamlit demo UI:**
```bash
streamlit run streamlit_app.py
```
Runs at `http://localhost:8501` — lets you manually set detection inputs and see advice output.

---

## The Main Endpoint

### `POST /sustainability/detect`

This is the endpoint the YOLO pipeline calls when it detects an object with ≥90% confidence.

**Request body:**
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

**Response:**
```json
{
  "object_detected": "soda_can",
  "confidence": 0.94,
  "context": "A soda can was detected — aluminum takes over 80 years to decompose and the elevated ozone levels here accelerate surface oxidation.",
  "action": "Place it in the nearest blue recycling bin; aluminum cans are accepted at all municipal recycling facilities."
}
```

`bbox` is optional. All other fields are required.

---

## For Teammates

### YOLO teammate
Your pipeline should POST to `/sustainability/detect` whenever a detection exceeds 90% confidence. The expected JSON shape for `detection` is:

| Field | Type | Notes |
|---|---|---|
| `object_class` | string | e.g. `"soda_can"`, `"plastic_bottle"` |
| `confidence` | float (0–1) | Must be ≥ 0.90 to be meaningful |
| `frame_id` | string | Any identifier for the source frame |
| `timestamp` | string | ISO 8601 format |
| `bbox` | object or null | `{ x, y, width, height }` in pixels |

### Frontend teammate
Poll or receive the `SustainabilityAdvice` response from `/sustainability/detect`. Display:
- `context` — the environmental concern (shown as an info/warning)
- `action` — the directive (shown as a call-to-action)
- Show a loading state while the request is in flight (Claude call takes ~1–2s)

### CASTNET teammate
Replace `app/sustainability/castnet_mock.py` with a real API call. The function signature to match:

```python
def load_castnet(location: str | None = None) -> CASTNETReading:
    ...
```

`CASTNETReading` fields: `site_id`, `location`, `ozone_ppb`, `sulfate_ug_m3`, `nitrate_ug_m3`, `co_ppb`, `measurement_date`.

---

## Other Endpoints

These exist from an earlier version of the project and are still usable for testing:

| Endpoint | Description |
|---|---|
| `GET /health` | Service health check |
| `POST /analyze-scene` | Async agentic scene analysis (returns job ID) |
| `GET /analysis/latest` | Latest completed analysis result |
| `GET /analysis/{job_id}` | Poll a specific analysis job |
| `POST /demo/run` | Full demo run with fixture data |
| `POST /scan-frame` | Returns mock YOLO scene data |

---

## Quick Trash Training From Root Folders

If you have root-level folders like `paper/`, `can/`, and `bottle/`, build a YOLO dataset with:

```bash
cd backend
.venv\Scripts\python.exe scripts\prepare_trash_dataset.py
```

This creates:

```text
backend/datasets/trash_quick/
  images/train
  images/val
  labels/train
  labels/val
  data.yaml
```

Important: if an image does not have a same-name `.txt` YOLO label file beside it, the script creates a weak centered box covering most of the frame. That is fast for a hackathon run, but it is only a rough fallback.

## Modal Training

Install Modal locally:

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements-modal.txt
modal setup
```

Run the remote fine-tune:

```bash
cd backend
modal run scripts/modal_train_yolo.py --epochs 30 --imgsz 640 --batch 16 --patience 8 --run-name trash-quick
```

The current recommended path uses the annotated COCO export in `new_dataset/My First Project.coco`, converts it to YOLO format, then uploads and trains remotely.

The Modal app:

- builds the YOLO dataset locally from the annotated COCO export
- uploads it to the `aeris-yolo-trash-dataset` Volume
- trains `yolov8m.pt` on an `L4`
- saves checkpoints to the `aeris-yolo-trash-checkpoints` Volume

Inspect saved weights after training:

```bash
modal volume ls aeris-yolo-trash-checkpoints /runs/trash-quick/weights
```

Detailed notes for the current custom trash model live in:

```text
docs/trash-model.md
```
