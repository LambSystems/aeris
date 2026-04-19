# Aeris

**Aeris** detects environmental waste in real time and tells you exactly what to do about it.

A YOLO camera pipeline spots objects like litter or improperly disposed waste. That detection is combined with live air quality data from CASTNET, and Claude generates two lines of grounded sustainability advice: what the object is and why it matters, then exactly what the person should do right now.

---

## How It Works

```
Camera feed
    │
    ▼
YOLO Pipeline          ← Gallo
    │  object_class, confidence, bbox
    │
    ▼
POST /sustainability/detect    ← FastAPI backend (Piero / Shuja)
    │
    ├── Loads CASTNET air quality data   ← real API coming (Shuja)
    │   (ozone, sulfate, nitrate, CO)
    │
    └── Calls Claude (Anthropic)
            │
            ▼
        Two-line response:
        • context  — what it is, what it's made of, why it's a problem
        • action   — exactly what to do right now
            │
            ▼
    Frontend UI          ← Chau
    (loading → result)
```

---

## Repo Structure

```
aeris/
├── readme.md
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI routes
│   │   ├── schemas.py               # Shared Pydantic models
│   │   └── sustainability/
│   │       ├── schemas.py           # YOLODetection, CASTNETReading, SustainabilityAdvice
│   │       ├── castnet_mock.py      # Mock CASTNET data — swap for real API
│   │       └── adviser.py           # Prompt + Claude call + response parsing
│   └── streamlit_app.py             # Dev UI for testing detections manually
├── frontend/                        # React / Vite / Tailwind
├── data/
└── docs/
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create `backend/.env`:
```
ANTHROPIC_API_KEY=your_key_here
```

Run the API:
```bash
uvicorn app.main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (interactive API docs)
```

Run the Streamlit dev UI:
```bash
streamlit run streamlit_app.py
# → http://localhost:8501
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

The frontend falls back to mock data if the backend is not running.

---

## The Main API Contract

### `POST /sustainability/detect`

This is the single endpoint everything connects to.

**Request:**
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

Only fire this when YOLO confidence is ≥ 0.90. The call takes ~1–2 seconds (LLM round trip), so the frontend should show a loading state.

---

## Build Priorities by Role

### Gallo — Computer Vision
- YOLO detects objects in the camera feed
- When confidence ≥ 90%, POST the detection to `/sustainability/detect`
- Expected object classes include: `soda_can`, `plastic_bottle`, `cardboard_box`, `cigarette_butt`, `plastic_bag`, `food_wrapper`, `glass_bottle`, `styrofoam_cup`
- The full detection schema is in `backend/app/sustainability/schemas.py`

### Chau — Frontend
- On detection trigger: show a loading screen
- On response: display `context` (info/warning style) and `action` (call-to-action style)
- Backend at `http://localhost:8000` — full API docs at `/docs`
- Use the Streamlit app at port 8501 as a reference for what the output looks like

### Piero — Backend
- The core endpoint is `POST /sustainability/detect` in `app/main.py`
- Keep the FastAPI contract stable — other teammates depend on it
- The CASTNET mock is in `app/sustainability/castnet_mock.py`; wire the real API there when ready

### Shuja — Data / Agent
- Real CASTNET API replaces `castnet_mock.py` — match the `CASTNETReading` schema
- Prompt and LLM logic live in `app/sustainability/adviser.py`
- Claude model is `claude-sonnet-4-6`, temperature 0.4

---

## Tech Stack

| Layer | Tech |
|---|---|
| Computer Vision | YOLO |
| Backend | FastAPI, Python, Pydantic |
| LLM | Claude (Anthropic) via `claude-sonnet-4-6` |
| Environmental Data | CASTNET (Clean Air Status and Trends Network) |
| Frontend | React, Vite, TypeScript, Tailwind |
| Dev UI | Streamlit |

---

## Team

- **Chau** — Frontend
- **Gallo** — Data / Computer Vision
- **Shuja** — Agent / Data / LLM
- **Piero** — Backend / API

---

## One-Line Pitch

**Aeris uses YOLO object detection and CASTNET air quality data to give people two-line, grounded sustainability advice the moment they encounter waste.**
