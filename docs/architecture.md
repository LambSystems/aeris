# Architecture

## Current Shape

Aeris is currently Streamlit-first, with FastAPI as the context/recommendation backbone and React as an optional product shell.

```text
Streamlit live scanner
  -> camera or uploaded clip
  -> local YOLO checkpoint
  -> visible boxes and labels
  -> latest structured detection
  -> side-panel advice

FastAPI backend
  -> fixed environmental context
  -> image scan endpoint
  -> latest detection bridge
  -> LLM/fallback recommendation endpoint

Optional React shell
  -> embeds Streamlit
  -> polls FastAPI
  -> renders a polished operations-console view
```

This is different from a pure React camera app. YOLO remains in Python because that path was more reliable for a hackathon demo and is still the clearest portfolio architecture for the project.

## Core Boundary

The system boundary to preserve is:

```text
Vision produces structured detections.
Backend normalizes environmental context.
Recommendation layer consumes detection + context, not raw video.
```

That keeps the recommendation path small, testable, cacheable, and resilient.

## Runtime Flow

```text
Camera frame
  -> streamlit-webrtc
  -> Ultralytics YOLO
  -> detection threshold / label normalization
  -> bounding boxes drawn in Streamlit
  -> YOLODetection written to .tmp/vision/latest_detection.json
  -> advice request for object + CASTNET context
  -> cached LLM-backed advice or deterministic fallback
```

The optional React shell can poll:

```text
GET /vision/latest-detection
POST /sustainability/detect
GET /context/fixed
```

## Components

### Streamlit Scanner

Location:

```text
backend/streamlit_app.py
```

Responsibilities:

- request camera access through `streamlit-webrtc`
- load the configured YOLO checkpoint
- run live tracking or uploaded-clip processing
- draw detections directly on the video
- publish the latest actionable detection
- show current scan, environmental context, risk signals, and advice

Important runtime knobs:

```powershell
$env:YOLO_MODEL_PATH="backend\models\trash-quick-v4-best.pt"
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="2"
$env:YOLO_DEVICE="0"
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
```

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
- support image-scan and older async demo paths

### Environmental Context

Location:

```text
backend/app/context/
```

`load_fixed_context()` combines:

- default or browser-provided coordinates
- processed CASTNET reading
- Open-Meteo weather
- Open-Meteo air quality
- weather.gov alerts
- local risk flags

This layer returns an `EnvironmentalFixedContext` with `source_status` values so the UI can show when a source is live versus fallback.

### Advice Layer

Location:

```text
backend/app/sustainability/adviser.py
```

Provider behavior:

```text
AERIS_LLM_PROVIDER=gemini     -> Gemini only, then fallback
AERIS_LLM_PROVIDER=anthropic  -> Anthropic only, then fallback
AERIS_LLM_PROVIDER=auto       -> Gemini, Anthropic, then fallback
```

The cache key includes:

- detected object class
- CASTNET site id
- CASTNET measurement date
- risk flags

That prevents repeated model calls for the same object/context state.

### Optional React UI

Location:

```text
ui/
```

The Vite UI can:

- embed Streamlit with `VITE_VISION_PROVIDER=streamlit-embed`
- poll the latest Streamlit detection
- render context and recommendation panels
- exercise experimental browser/backend YOLO paths

This is useful for a polished portfolio shell, but the Streamlit app is the primary working runtime.

## Data Contracts

### Detection

```json
{
  "object_class": "can",
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
    "label": "Galesburg, IL",
    "source": "default_demo_location"
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
  "risk_flags": ["castnet_elevated_nitrate"],
  "summary": "Nearest CASTNET context is Bondville, IL..."
}
```

### Sustainability Advice

```json
{
  "object_detected": "can",
  "confidence": 0.84,
  "context": "A can was detected...",
  "action": "Place it in the nearest recycling bin...",
  "environment_summary": "Nearest CASTNET context is Bondville, IL...",
  "risk_flags": ["castnet_elevated_nitrate"],
  "castnet_site": "Bondville, IL",
  "decision_source": "llm_gemini"
}
```

## Failure Model

If weather or air-quality APIs fail, `source_status` records fallback/error status and the app still uses CASTNET context.

If LLM providers fail or keys are missing, `deterministic_fallback` still returns a recommendation.

If the Streamlit detection bridge fails, test `/vision/latest-detection` and use `/sustainability/detect` manually for a demo fallback.

If live inference is slow, lower camera size, increase `YOLO_FRAME_SKIP`, and keep `YOLO_IMGSZ=320`.

## One-Sentence Summary

Aeris keeps live perception in the Python vision layer, normalizes environmental context in FastAPI, and turns structured detections into cached, fallback-safe sustainability recommendations.
