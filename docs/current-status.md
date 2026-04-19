# Current Status

This is the fastest handoff for the team after the overnight changes.

## TL;DR

The stable demo path is:

```text
React UI in /ui
  -> embeds Streamlit YOLO at http://localhost:8501?embed=true
  -> polls FastAPI for latest YOLO detection
  -> calls FastAPI for fixed context and advice

Streamlit in /backend
  -> owns the camera feed
  -> runs YOLO .pt weights with PyTorch CUDA
  -> draws boxes directly on the video
  -> writes the latest actionable detection to .tmp/vision/latest_detection.json

FastAPI in /backend/app
  -> reads latest Streamlit detection
  -> loads CASTNET/weather/air-quality context
  -> returns cached LLM/fallback recommendation
```

This branch favors demo stability over architectural purity. Browser YOLO was tested but felt slower/stickier than Streamlit + GPU.

---

## What Works

- FastAPI health, fixed context, and advice endpoints.
- CASTNET-backed fixed context for Bondville/Galesburg-like demo coordinates.
- Weather, air quality, and weather alerts through lightweight public APIs.
- YOLO live detection in Streamlit using Gallo's `.pt` model.
- Streamlit iframe embedded inside the React/Lovable UI.
- React sidebar displays environmental context.
- React sidebar can now display latest Streamlit detection and recommendation through `/vision/latest-detection`.
- Advice uses Gemini first when configured, Anthropic second, deterministic fallback always.
- Advice is cached by object/site/date/risk flags to avoid flooding the LLM.

---

## Current Branch Strategy

Main working demo branch:

```text
piero/iframe
```

Experimental branch:

```text
piero/yolo-browser
```

Do not switch the team to browser YOLO unless Streamlit becomes unusable. The browser version can run ONNX but was CPU/WASM-bound in testing.

---

## Files To Know

### Backend

```text
backend/app/main.py
```

FastAPI routes:

- `/health`
- `/context/fixed`
- `/vision/latest-detection`
- `/sustainability/detect`
- `/scan-frame`

```text
backend/app/vision_state.py
```

Tiny bridge between Streamlit and FastAPI. Streamlit writes latest actionable detection; FastAPI reads it.

```text
backend/streamlit_app.py
```

Live camera + YOLO + iframe embed CSS + latest detection publishing.

```text
backend/app/sustainability/adviser.py
```

LLM provider order, JSON prompt, cache, deterministic fallback handoff.

```text
backend/app/context/fixed_context_service.py
```

Combines GPS/default location with CASTNET, weather, air quality, and weather alerts.

### Frontend

```text
ui/src/pages/Index.tsx
```

Main UI. In `streamlit-embed` mode it embeds Streamlit and polls `/vision/latest-detection`.

```text
ui/src/components/aeris/DecisionPanel.tsx
```

Right sidebar: current scan, recommendation, environmental context, risk signals.

```text
ui/src/lib/api.ts
```

FastAPI client functions.

```text
ui/src/lib/types.ts
```

Frontend API types.

---

## Run Commands

Backend:

```powershell
cd C:\Users\akuma\repos\aeris
conda activate aeris-backend
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --reload --app-dir backend
```

Streamlit YOLO:

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

React:

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm run dev
```

---

## FPS Tuning

The main knobs are environment variables before starting Streamlit:

```powershell
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
$env:YOLO_FRAME_SKIP="2"
$env:YOLO_IMGSZ="320"
```

Tradeoff:

- lower camera size = smoother video, less visual detail
- higher `YOLO_FRAME_SKIP` = smoother video, boxes update less often
- higher `YOLO_IMGSZ` = better detection, slower inference

Recommended demo presets:

```text
Quality:  960x540, frame_skip 1, imgsz 320
Smooth:   640x360, frame_skip 2, imgsz 320
```

---

## Object Classes For Demo

The demo should focus on:

```text
aluminum_can
paper
plastic_bottle
```

Mapped backend sustainability classes:

```text
can / aluminum_can / soda_can -> aluminum_can
paper / cup                  -> paper
bottle                       -> plastic_bottle
```

---

## Integration Contracts

Streamlit writes:

```json
{
  "object_class": "aluminum_can",
  "confidence": 0.84,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

FastAPI exposes it:

```text
GET /vision/latest-detection
```

React turns it into:

```text
Current scan -> Recommendation
```

Advice request:

```text
POST /sustainability/detect
```

---

## What To Tell Judges

Short version:

> Aeris sees recyclable waste live, pulls environmental context from CASTNET and weather sources, then gives a practical action. The camera stays live because detection and advice are decoupled.

Dataset utility:

> The recommendation is not only based on the object. It is conditioned on local environmental context like CASTNET ozone/nitrate readings and weather alerts, so the same object can receive different advice in different conditions.

Technical tradeoff:

> LLM calls are event-based and cached. We do not call a model on every frame.

---

## Known Risks

- Streamlit iframe is not as clean as native React video, but it gives the best local YOLO performance right now.
- If Streamlit does not detect above threshold, React will not show a recommendation.
- If the GPU environment is not active, Streamlit can feel slow.
- Browser YOLO is not the current demo path.

---

## Test Checklist

1. `GET /health` returns ok.
2. `GET /context/fixed?...` returns CASTNET/weather.
3. Streamlit detects an object and draws a box.
4. `GET /vision/latest-detection` returns that object.
5. React sidebar shows Current Scan.
6. React sidebar shows Recommendation.
7. Move can/bottle/paper in camera and confirm the demo narrative still makes sense.
