# Aeris

Aeris is a Streamlit-first environmental vision app. It runs a local YOLO model for live waste detection, pairs detections with CASTNET-backed environmental context, and shows immediate sustainability advice beside the video stream.

Current product direction:

```text
Streamlit owns the live camera, detections, and LLM/fallback advice experience.
FastAPI supports context, testing, and backend integration.
React is not the primary runtime path.
```

---

## Live Flow

```text
Camera
  -> Streamlit WebRTC
  -> local YOLO model
  -> realtime boxes and tracked objects
  -> latest detection written locally
  -> advice generated with Gemini / Anthropic / deterministic fallback
  -> answers shown beside the video
```

Fixed context comes from:

```text
CASTNET + Open-Meteo weather + Open-Meteo air quality + weather alerts
```

---

## Quick Start

### 1. Install backend dependencies

```powershell
cd C:\Users\webga\OneDrive\Documents\GitHub\aeris\backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run FastAPI

```powershell
cd C:\Users\webga\OneDrive\Documents\GitHub\aeris\backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### 3. Run Streamlit with the custom YOLO model

```powershell
cd C:\Users\webga\OneDrive\Documents\GitHub\aeris\backend
$env:YOLO_MODEL_PATH = (Resolve-Path ".\models\trash-quick-v4-best.pt").Path
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8507
```

Open:

```text
FastAPI:   http://127.0.0.1:8000/docs
Streamlit: http://127.0.0.1:8507
```

---

## What Is Running Where

### Streamlit

- owns the live camera experience
- runs the local YOLO checkpoint directly
- tracks objects across frames
- shows detections and advice beside the video
- supports uploaded clip processing

### FastAPI

- exposes `/context/fixed`
- exposes `/scan-frame` for uploaded-image scanning
- exposes `/sustainability/detect`
- exposes `/vision/latest-detection`

---

## Custom Model

Preferred checkpoint:

```text
backend/models/trash-quick-v4-best.pt
```

Current classes:

```text
can
paper
bottle
```

Full training and annotation notes:

```text
docs/trash-model.md
```

---

## Performance Defaults

For smoother live detection:

```powershell
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="2"
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
```

For GPU use:

```powershell
$env:YOLO_DEVICE="0"
```

---

## Notes

- YOLO stays local and is prioritized over browser-side inference.
- LLM-backed advice still runs in the Streamlit experience.
- The side panel is part of the main Streamlit app now, not an external UI dependency.
