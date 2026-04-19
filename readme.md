# Aeris

**Aeris** is a live environmental scanner for hackathon demo use.

It shows a camera feed, detects recyclable waste with YOLO, combines the detection with CASTNET/weather context, and displays a concise sustainability recommendation.

Current source of truth for the demo:

```text
React UI (/ui)
  embeds Streamlit YOLO live vision
  polls FastAPI for latest detection + environmental context

Streamlit YOLO (/backend/streamlit_app.py)
  runs Gallo's YOLO model locally
  draws bounding boxes in real time
  writes the latest actionable detection to .tmp/vision/latest_detection.json

FastAPI (/backend/app/main.py)
  serves fixed environmental context
  exposes latest Streamlit detection
  generates sustainability advice with Gemini/Anthropic/fallback + cache
```

This is the stable demo path because browser ONNX YOLO was less smooth on this machine, while Streamlit + PyTorch CUDA can use the GPU.

---

## Current Demo Flow

```text
Camera
  -> Streamlit WebRTC
  -> YOLO .pt model on GPU
  -> bounding boxes inside iframe
  -> latest detection bridge file
  -> FastAPI GET /vision/latest-detection
  -> React sidebar Current Scan
  -> FastAPI POST /sustainability/detect
  -> React sidebar Recommendation

GPS/default location
  -> FastAPI GET /context/fixed
  -> CASTNET + Open-Meteo + weather.gov
  -> React Environmental Context + Risk Signals
```

Important: the iframe owns the live camera and boxes. React owns the product UI, environmental context, and recommendation cards.

---

## Quick Start

Run these in three separate terminals.

### 1. Backend API

```powershell
cd C:\Users\akuma\repos\aeris
conda activate aeris-backend
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --reload --app-dir backend
```

Backend:

```text
http://localhost:8000
```

Interactive API docs:

```text
http://localhost:8000/docs
```

### 2. Streamlit YOLO Vision

Balanced demo settings:

```powershell
cd C:\Users\akuma\repos\aeris\backend
conda activate aeris-backend
$env:AERIS_STREAMLIT_EMBED="1"
$env:YOLO_MODEL_PATH="C:\Users\akuma\repos\aeris\backend\models\trash-quick-v4-best.pt"
$env:YOLO_DEVICE="0"
$env:AERIS_CAMERA_WIDTH="960"
$env:AERIS_CAMERA_HEIGHT="540"
$env:YOLO_FRAME_SKIP="1"
$env:YOLO_IMGSZ="320"
python -m streamlit run streamlit_app.py --server.port 8501
```

More fluid fallback if the video feels heavy:

```powershell
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
$env:YOLO_FRAME_SKIP="2"
python -m streamlit run streamlit_app.py --server.port 8501
```

Streamlit:

```text
http://localhost:8501
```

### 3. React UI

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm run dev
```

Frontend:

```text
http://localhost:5173
```

Expected `ui/.env`:

```env
VITE_AERIS_API_BASE=http://localhost:8000
VITE_VISION_PROVIDER=streamlit-embed
VITE_STREAMLIT_URL=http://localhost:8501?embed=true
```

---

## Environment

Root `.env` may contain:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-haiku-4-5-20251001
```

Advice behavior:

1. Gemini if `GEMINI_API_KEY` exists.
2. Anthropic if `ANTHROPIC_API_KEY` exists.
3. Deterministic fallback if no LLM key works.
4. Per-session cache avoids repeated LLM calls for the same object/site/risk context.

---

## Repo Structure

```text
aeris/
  backend/
    app/
      main.py                    FastAPI endpoints
      vision_state.py            Streamlit -> FastAPI detection bridge
      context/                   fixed context: GPS, CASTNET, weather, alerts
      cv/                        backend YOLO/image helpers
      sustainability/            advice schemas, fallback, LLM adviser
    models/                      local YOLO weights, gitignored
    streamlit_app.py             live YOLO iframe app

  ui/
    src/
      pages/Index.tsx            main React demo shell
      components/aeris/          scanner/sidebar components
      lib/api.ts                 FastAPI client
      lib/types.ts               shared frontend types

  data/
    castnet/                     processed CASTNET artifacts

  docs/
    current-status.md            read this first after waking up
    architecture.md              current data flow
    stack.md                     chosen stack + alternatives
    team-contracts.md            owner input/output contracts
    demo.md                      demo runbook and script
    yolo-browser.md              browser YOLO experiment notes
```

---

## Main Endpoints

### `GET /health`

Sanity check.

### `GET /context/fixed?latitude=...&longitude=...`

Returns environmental context:

- nearest CASTNET site
- ozone/sulfate/nitrate/CO
- Open-Meteo weather
- Open-Meteo air quality
- weather.gov alerts
- risk flags and summary

### `GET /vision/latest-detection`

Returns the latest actionable detection written by Streamlit YOLO:

```json
{
  "object_class": "aluminum_can",
  "confidence": 0.84,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

### `POST /sustainability/detect`

Generates/caches the user-facing sustainability recommendation.

Request:

```json
{
  "latitude": 40.9478,
  "longitude": -90.3712,
  "detection": {
    "object_class": "aluminum_can",
    "confidence": 0.84,
    "frame_id": "frame_00123",
    "timestamp": "2026-04-19T06:30:00Z",
    "bbox": null
  }
}
```

Response:

```json
{
  "object_detected": "aluminum_can",
  "confidence": 0.84,
  "context": "An aluminum can was detected...",
  "action": "Place it in the nearest recycling bin...",
  "environment_summary": "Nearest CASTNET context is Bondville, IL...",
  "risk_flags": ["castnet_elevated_nitrate", "weather_alert_active"],
  "castnet_site": "Bondville, IL",
  "decision_source": "llm_gemini"
}
```

### `POST /scan-frame`

Backend image scan path. Still useful for testing and fallback, but not the current primary demo path.

---

## Team Handoff

### Piero - Backend / Integration

Owns:

- FastAPI app
- fixed context
- advice generation and cache
- Streamlit detection bridge
- runbook stability

Do now:

- keep `/context/fixed`, `/vision/latest-detection`, `/sustainability/detect` stable
- tune Streamlit env vars for FPS
- do not overbuild browser YOLO unless Streamlit collapses

### Gallo - CV

Owns:

- YOLO weights
- class quality for can, paper, bottle
- model path and confidence behavior

Current model path:

```text
backend/models/trash-quick-v4-best.pt
```

Expected labels:

```text
aluminum_can
paper
plastic_bottle
```

### Chau - Frontend

Owns:

- React UI in `/ui`
- sidebar polish
- demo screen UX

Current integration:

- iframe gets `http://localhost:8501?embed=true`
- API base is `http://localhost:8000`
- React should not directly call LLMs or own YOLO in the stable demo branch

### Shuja - Product/Data Story

Owns:

- sustainability framing
- CASTNET story
- judge narrative
- advice quality constraints

Current story:

```text
Same detected object + different environmental context = different recommendation.
```

---

## Known Tradeoffs

- Streamlit iframe is smoother and more accurate than browser ONNX on this machine, but it is visually embedded rather than native React video.
- Browser YOLO exists as an experiment, but ONNX Runtime Web was WASM/CPU-bound here and felt sticky.
- The recommendation is generated outside the iframe through a local bridge, so React can still show polished advice cards.
- Advice is not fake: it uses Gemini/Anthropic when keys are present, and deterministic fallback when not.

---

## Troubleshooting

### React shows detections in iframe but no recommendation

Check:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/vision/latest-detection
```

If `null`, Streamlit has not written an actionable detection yet. Make sure the detection is above threshold.

### Streamlit feels slow

Use lower camera constraints:

```powershell
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
$env:YOLO_FRAME_SKIP="2"
```

Restart Streamlit.

### GPU is not used

Check:

```powershell
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Then run Streamlit with:

```powershell
$env:YOLO_DEVICE="0"
```

### API context test

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/context/fixed?latitude=40.9478&longitude=-90.3712"
```

### Advice test

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/sustainability/detect `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"latitude":40.9478,"longitude":-90.3712,"detection":{"object_class":"aluminum_can","confidence":0.84,"frame_id":"manual_test","timestamp":"2026-04-19T06:30:00Z"}}'
```

---

## One-Line Pitch

**Aeris combines live YOLO waste detection with CASTNET-backed environmental context to tell people what to do with recyclable waste right now.**
