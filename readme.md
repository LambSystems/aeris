# Aeris

**Aeris** detects environmental waste in real time and tells people exactly what to do about it.

A YOLO camera pipeline spots objects like litter or improperly disposed waste. The backend combines that detection with CASTNET air-quality context, then generates two concise lines of grounded sustainability advice: what the object is and why it matters, then the action the person should take right now.

Shuja's updated product context is the source of truth for this branch:

```text
YOLO detection -> CASTNET context -> sustainability advice
```

---

## How It Works

```text
Camera feed
    |
    v
YOLO Pipeline          <- Gallo
    |  object_class, confidence, bbox
    v
POST /sustainability/detect    <- FastAPI backend
    |
    +-- Loads CASTNET air-quality context
    |   ozone, sulfate, nitrate, CO
    |
    +-- Calls adviser layer
        Claude primary, deterministic fallback coming
            |
            v
        Two-line response:
        - context: what it is, what it is made of, why it is a problem
        - action: exactly what to do right now
            |
            v
    Frontend UI          <- Chau
```

---

## Repo Structure

```text
aeris/
  readme.md
  backend/
    app/
      main.py
      schemas.py
      sustainability/
        schemas.py
        castnet_mock.py
        adviser.py
    streamlit_app.py
  frontend/
  data/
  docs/
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API runs at:

```text
http://localhost:8000
```

Interactive docs:

```text
http://localhost:8000/docs
```

Optional `.env` in `backend/`:

```text
ANTHROPIC_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
```

### Streamlit Dev UI

```bash
cd backend
streamlit run streamlit_app.py
```

The Streamlit app runs at:

```text
http://localhost:8501
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at:

```text
http://localhost:5173
```

---

## Main API Contract

### `POST /sustainability/detect`

This is the primary endpoint for the updated product.

YOLO or the frontend should call this only when a detection is stable and confidence is at least `0.90`.

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

The response may take 1-2 seconds when an LLM provider is used, so the UI should show a loading state and keep the camera/detection view responsive.

---

## Build Priorities By Role

### Gallo - Computer Vision

- YOLO detects objects in the camera feed.
- When confidence is at least 90%, call `POST /sustainability/detect`.
- Expected object classes include `soda_can`, `plastic_bottle`, `cardboard_box`, `cigarette_butt`, `plastic_bag`, `food_wrapper`, `glass_bottle`, and `styrofoam_cup`.
- The detection schema lives in `backend/app/sustainability/schemas.py`.

### Chau - Frontend

- On detection trigger, show loading state.
- On response, display `context` as the environmental concern and `action` as the call to action.
- Backend base URL is `http://localhost:8000`.
- Use `http://localhost:8000/docs` for API docs.
- Streamlit at `http://localhost:8501` can be used as a reference output.

### Piero - Backend

- Keep `POST /sustainability/detect` stable.
- Process CASTNET data with `scripts/process_castnet.py`.
- Load `data/castnet/processed/current_reading.json` in the sustainability endpoint.
- Keep deterministic fallback advice so the demo does not depend fully on an LLM key/network.
- Keep older demo endpoints available only as compatibility helpers.

### Shuja - Data / Agent

- Product context, prompt direction, and sustainability framing are source of truth.
- Prompt and LLM logic live in `backend/app/sustainability/adviser.py`.
- CASTNET reading shape lives in `backend/app/sustainability/schemas.py`.

---

## Tech Stack

| Layer | Tech |
|---|---|
| Computer Vision | YOLO |
| Backend | FastAPI, Python, Pydantic |
| LLM | Claude primary for sustainability advice; Gemini/OpenAI compatibility remains |
| Environmental Data | CASTNET |
| Frontend | React, Vite, TypeScript, Tailwind |
| Dev UI | Streamlit |

---

## One-Line Pitch

**Aeris uses YOLO object detection and CASTNET air-quality data to give people two-line, grounded sustainability advice the moment they encounter waste.**
