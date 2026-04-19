# Stack

## Current Chosen Stack

The stack is optimized for shipping a stable hackathon demo quickly:

```text
Frontend: React + Vite + TypeScript + Tailwind + shadcn-style components
UI seed:  Lovable-generated project in /ui, then manually integrated
Vision:   Streamlit WebRTC + Ultralytics YOLO .pt
Backend:  Python + FastAPI + Pydantic
Data:     CASTNET processed data + Open-Meteo + weather.gov alerts
Advice:   Gemini first, Anthropic second, deterministic fallback, in-memory cache
Runtime:  Local demo, three processes
```

---

## Why Not Only React For Vision

React is still the product UI. But the stable vision demo uses Streamlit because:

- Gallo's model is a YOLO `.pt` model, not a browser-ready model.
- PyTorch CUDA can use the local NVIDIA GPU.
- Streamlit WebRTC can draw boxes smoothly without HTTP frame roundtrips.
- Browser ONNX was tested and felt sticky on this machine.

The React app embeds Streamlit and handles everything around it:

- header/status
- environmental context
- current scan
- recommendation
- risk signals

---

## Frontend Stack

Use:

- `ui/`
- Vite
- React
- TypeScript
- Tailwind
- shadcn-style primitives
- `lucide-react`

Important files:

```text
ui/src/pages/Index.tsx
ui/src/components/aeris/DecisionPanel.tsx
ui/src/components/aeris/RecommendationCard.tsx
ui/src/lib/api.ts
ui/src/lib/types.ts
ui/src/index.css
```

Current mode:

```env
VITE_VISION_PROVIDER=streamlit-embed
VITE_STREAMLIT_URL=http://localhost:8501?embed=true
VITE_AERIS_API_BASE=http://localhost:8000
```

Frontend must not:

- call Gemini/Anthropic/OpenAI directly
- own API keys
- send every camera frame in the current demo path
- block the UI while advice is loading

---

## Vision Stack

Use:

- Python
- Streamlit
- `streamlit-webrtc`
- Ultralytics YOLO
- PyTorch CUDA
- OpenCV drawing helpers

Primary model:

```text
backend/models/trash-quick-v4-best.pt
```

Expected demo classes:

```text
aluminum_can
paper
plastic_bottle
```

Config knobs:

```powershell
$env:YOLO_DEVICE="0"
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="1"
$env:AERIS_CAMERA_WIDTH="960"
$env:AERIS_CAMERA_HEIGHT="540"
```

Performance presets:

```text
Quality: 960x540, frame_skip 1, imgsz 320
Smooth:  640x360, frame_skip 2, imgsz 320
```

---

## Backend Stack

Use:

- Python
- FastAPI
- Pydantic
- Uvicorn
- `python-multipart`
- public HTTP APIs for weather context

Important files:

```text
backend/app/main.py
backend/app/vision_state.py
backend/app/context/fixed_context_service.py
backend/app/sustainability/adviser.py
backend/app/sustainability/fallback_advice.py
backend/app/cv/yolo_service.py
backend/streamlit_app.py
```

Backend owns:

- context loading
- schema stability
- advice provider order
- advice fallback
- latest detection bridge
- API docs

---

## LLM Stack

Provider priority:

1. Gemini
2. Anthropic
3. deterministic fallback

Root `.env`:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

The LLM receives structured data:

- object class
- confidence
- fixed environmental context
- CASTNET reading

The LLM does not receive raw video.

Advice is cached by:

- object class
- CASTNET site
- CASTNET measurement date
- active risk flags

---

## Data Stack

Use:

- processed CASTNET files in `data/castnet`
- nearest-site selection
- Open-Meteo weather
- Open-Meteo air quality
- weather.gov alerts

The product claim is not "we have a dataset in the repo."

The claim is:

```text
Dataset/live environmental context changes the recommendation.
```

---

## API Contract

Primary live-demo endpoints:

```text
GET  /health
GET  /context/fixed
GET  /vision/latest-detection
POST /sustainability/detect
```

Useful fallback/testing endpoints:

```text
POST /scan-frame
GET  /context/demo
GET  /scene/demo
POST /demo/run
POST /recommend
POST /analyze-scene
GET  /analysis/latest
GET  /analysis/{job_id}
```

The async analysis endpoints remain in the repo, but they are not the current primary demo path.

---

## Browser YOLO Status

Browser YOLO is documented in:

```text
docs/yolo-browser.md
```

Status:

- ONNX export works.
- ONNX Runtime Web loads but was slow/sticky.
- It may improve with WebGPU or a smaller/custom browser model.
- Do not make it the main path unless tested live on the demo machine.

---

## Final Stack Summary

```text
React UI for product polish
Streamlit YOLO for live GPU vision
FastAPI for context/advice
CASTNET + weather APIs for environmental evidence
Gemini/Anthropic/fallback for advice
Local JSON bridge for hackathon-safe integration
```
