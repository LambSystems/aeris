# Architecture

## Current Demo Architecture

Aeris currently uses a split live-vision architecture:

```text
React product shell
  -> polished UI, sidebar, context, recommendation

Streamlit vision iframe
  -> camera access, YOLO inference, bounding boxes

FastAPI backend
  -> fixed context, latest detection bridge, advice generation
```

This is the stable hackathon demo path. It keeps YOLO running in the Python/GPU environment while preserving the more polished Lovable/React interface.

---

## Why This Shape

We tested three viable paths:

1. **React + backend YOLO polling**
   - Good integration.
   - Less smooth visually because frames travel through HTTP.

2. **React + browser YOLO ONNX**
   - Cleanest architecture.
   - Too sticky on this machine because ONNX Runtime Web was effectively WASM/CPU-bound.

3. **React + Streamlit YOLO iframe**
   - Best live YOLO performance locally.
   - Slightly less native visually.
   - Current chosen demo path.

The current priority is demo reliability and smooth-enough real-time perception.

---

## Runtime Flow

```text
Camera
  -> Streamlit WebRTC
  -> YOLO .pt model
  -> detection threshold / class normalization
  -> boxes drawn in Streamlit video
  -> latest actionable detection written to .tmp/vision/latest_detection.json

React
  -> embeds Streamlit iframe
  -> polls GET /vision/latest-detection
  -> renders Current Scan
  -> calls POST /sustainability/detect
  -> renders Recommendation

FastAPI
  -> loads fixed context through GET /context/fixed
  -> reads latest detection bridge file
  -> generates advice with LLM/cache/fallback
```

---

## Components

### React UI

Location:

```text
ui/
```

Responsibilities:

- render the demo product shell
- embed Streamlit at `VITE_STREAMLIT_URL`
- show current scan state
- show environmental context
- show recommendation
- poll backend, not LLM providers

Important file:

```text
ui/src/pages/Index.tsx
```

When `VITE_VISION_PROVIDER=streamlit-embed`, the UI uses `StreamlitEmbedPage`.

---

### Streamlit YOLO

Location:

```text
backend/streamlit_app.py
```

Responsibilities:

- request camera access
- run YOLO on frames
- draw bounding boxes
- filter actionable detections
- publish the latest detection for React/FastAPI

Config:

```powershell
$env:AERIS_STREAMLIT_EMBED="1"
$env:YOLO_MODEL_PATH="C:\Users\akuma\repos\aeris\backend\models\trash-quick-v4-best.pt"
$env:YOLO_DEVICE="0"
$env:AERIS_CAMERA_WIDTH="960"
$env:AERIS_CAMERA_HEIGHT="540"
$env:YOLO_FRAME_SKIP="1"
$env:YOLO_IMGSZ="320"
```

The Streamlit app should not own the polished recommendation UI in embed mode. It only owns live vision.

---

### Vision Bridge

Location:

```text
backend/app/vision_state.py
```

Purpose:

```text
Streamlit process -> local JSON file -> FastAPI endpoint -> React
```

File:

```text
.tmp/vision/latest_detection.json
```

Endpoint:

```text
GET /vision/latest-detection
```

This is intentionally simple. It avoids introducing Redis/WebSockets during the hackathon.

---

### FastAPI Backend

Location:

```text
backend/app/main.py
```

Primary endpoints:

```text
GET  /health
GET  /context/fixed
GET  /vision/latest-detection
POST /sustainability/detect
POST /scan-frame
```

Responsibilities:

- load fixed environmental context
- expose latest YOLO detection
- generate sustainability advice
- keep deterministic fallback working
- cache repeated advice

---

### Fixed Context

Fixed context combines:

- browser GPS or default coordinates
- nearest CASTNET reading
- Open-Meteo weather
- Open-Meteo air quality
- weather.gov alerts
- local risk flags

Endpoint:

```text
GET /context/fixed?latitude=40.9478&longitude=-90.3712
```

The UI should keep this visible because it proves the dataset is active.

---

### Advice Layer

Location:

```text
backend/app/sustainability/adviser.py
```

Provider order:

1. Gemini
2. Anthropic
3. deterministic fallback

The advice layer receives structured data only:

- detected object class
- confidence
- optional bbox
- fixed context
- CASTNET reading

It does not process raw video.

The cache key includes:

- object class
- CASTNET site
- measurement date
- risk flags

This prevents repeated LLM calls for the same demo state.

---

## Data Contracts

### Latest Detection

```json
{
  "object_class": "aluminum_can",
  "confidence": 0.84,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

### Fixed Context

```json
{
  "location": {
    "latitude": 40.9478,
    "longitude": -90.3712,
    "label": "40.9478,-90.3712",
    "source": "browser_gps"
  },
  "castnet": {
    "site_id": "BVL130",
    "location": "Bondville, IL",
    "ozone_ppb": 39.0,
    "sulfate_ug_m3": 0.68,
    "nitrate_ug_m3": 2.08,
    "co_ppb": 41.72,
    "measurement_date": "2026-04-15"
  },
  "risk_flags": ["castnet_elevated_nitrate", "weather_alert_active"],
  "summary": "Nearest CASTNET context is Bondville, IL..."
}
```

### Sustainability Advice

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

---

## Performance Model

Real-time perception and advice run at different speeds:

```text
YOLO/video: fast path, visible immediately in iframe
Advice: event-based path, cached, may take 1-3 seconds on first LLM call
Fixed context: loaded once per coordinate/session
```

We do not call an LLM on every frame.

---

## Fallbacks

If YOLO/Streamlit is slow:

- reduce camera resolution
- increase `YOLO_FRAME_SKIP`
- keep `YOLO_IMGSZ=320`

If LLM fails:

- deterministic fallback still returns advice

If Streamlit detection bridge fails:

- test `/vision/latest-detection`
- use `/sustainability/detect` manually for the pitch

If browser YOLO becomes necessary:

- see `docs/yolo-browser.md`
- treat it as experimental unless performance improves

---

## One-Sentence Architecture Summary

**Aeris embeds Python/GPU YOLO for live vision inside a React product shell, then uses FastAPI to combine latest detections with CASTNET/weather context and cached LLM-backed sustainability advice.**
