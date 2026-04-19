# Team Contracts

This document tells each person what they own, what they receive, and what they output.

Current demo source of truth:

```text
/ui React shell + /backend Streamlit YOLO iframe + FastAPI advice/context
```

---

## Shared Runtime Contract

Run three processes:

```text
FastAPI:   http://localhost:8000
Streamlit: http://localhost:8501
React:     http://localhost:5173
```

React uses:

```env
VITE_AERIS_API_BASE=http://localhost:8000
VITE_VISION_PROVIDER=streamlit-embed
VITE_STREAMLIT_URL=http://localhost:8501?embed=true
```

---

## Piero - Backend / Integration

### Owns

- FastAPI app
- fixed environmental context
- sustainability advice endpoint
- LLM/fallback/cache behavior
- Streamlit-to-FastAPI detection bridge
- run commands and integration stability

### Inputs

From Streamlit:

```json
{
  "object_class": "aluminum_can",
  "confidence": 0.84,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

From React:

- GPS coordinates for `/context/fixed`
- latest detection forwarded to `/sustainability/detect`

From Shuja/data:

- sustainability framing
- CASTNET interpretation
- judge narrative constraints

### Outputs

To React:

```text
GET  /context/fixed
GET  /vision/latest-detection
POST /sustainability/detect
```

### Must Keep Stable

```text
GET /context/fixed?latitude=...&longitude=...
GET /vision/latest-detection
POST /sustainability/detect
```

### Must Not Do

- call LLMs every frame
- break deterministic fallback
- expose API keys to frontend
- change response field names without telling Chau

---

## Gallo - Computer Vision

### Owns

- YOLO weights
- class quality
- confidence behavior
- model handoff to `backend/models`

### Current Model

```text
backend/models/trash-quick-v4-best.pt
```

Model files are gitignored:

```text
backend/models/*.pt
backend/models/*.onnx
```

### Expected Demo Classes

```text
aluminum_can
paper
plastic_bottle
```

### Inputs

- webcam frames through Streamlit WebRTC
- environment variables:

```powershell
$env:YOLO_MODEL_PATH="C:\Users\akuma\repos\aeris\backend\models\trash-quick-v4-best.pt"
$env:YOLO_DEVICE="0"
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="1"
```

### Outputs

Streamlit draws boxes directly.

For backend/React bridge, actionable detections are normalized as:

```json
{
  "object_class": "plastic_bottle",
  "confidence": 0.87,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

### Must Do

- keep labels stable enough for mapping
- keep confidence threshold meaningful
- prioritize can, paper, bottle
- tell Piero if model class names change

### Must Not Do

- call LLMs
- decide sustainability advice
- overwrite UI/backend files during final integration without coordinating

---

## Chau - Frontend

### Owns

- React UI in `/ui`
- visual polish
- sidebar UX
- demo presentation screen

### Inputs

From FastAPI:

```text
GET /context/fixed
GET /vision/latest-detection
POST /sustainability/detect
```

From Streamlit:

```text
iframe src = http://localhost:8501?embed=true
```

### Outputs

Frontend renders:

- live iframe
- current scan
- recommendation
- environmental context
- risk signals

### Must Do

- keep UI in `/ui`
- keep `VITE_VISION_PROVIDER=streamlit-embed` for current demo
- do not call provider LLM APIs directly
- keep latest recommendation visible while a new one loads
- keep text readable on projector/screenshare

### Must Not Do

- move back to `/frontend` unless team agrees
- expose secrets in browser
- make a landing page instead of demo screen
- replace Streamlit vision path without testing FPS

---

## Shuja - Product / Data Story

### Owns

- product framing
- CASTNET relevance
- sustainability claim quality
- judge narrative
- advice constraints

### Inputs

From backend:

- fixed context summary
- CASTNET fields
- risk flags
- generated advice examples

### Outputs

To team:

- what the demo should say
- how CASTNET changes recommendations
- which claims are safe and understandable

### Must Do

- make the dataset role visible
- keep claims grounded
- keep same-object/different-context story clear

### Must Not Do

- imply raw video goes to LLM
- imply CASTNET gives exact street-level health diagnosis
- overcomplicate the demo story

---

## API Shapes

### `GET /vision/latest-detection`

Response:

```json
{
  "object_class": "aluminum_can",
  "confidence": 0.84,
  "bbox": null,
  "frame_id": "frame_00123",
  "timestamp": "2026-04-19T06:30:00Z"
}
```

May return `null` before the first detection.

### `POST /sustainability/detect`

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

### `GET /context/fixed`

Request:

```text
GET /context/fixed?latitude=40.9478&longitude=-90.3712
```

Response includes:

- `location`
- `castnet`
- `weather`
- `air_quality`
- `weather_alerts`
- `risk_flags`
- `summary`
- `source_status`

---

## Integration Rules

1. The camera should never wait for an LLM.
2. The LLM/advice layer sees structured detection data, not raw video.
3. Advice should be cached and event-based.
4. If Streamlit sees the object but React does not update, debug `/vision/latest-detection`.
5. If React has a detection but no advice, debug `/sustainability/detect`.
6. If context fails, the demo can still use deterministic fallback and CASTNET cached data.

---

## Final Demo Fallback Order

```text
Streamlit YOLO -> backend /scan-frame -> manual /sustainability/detect
Gemini -> Anthropic -> deterministic fallback
960x540 -> 640x360
frame_skip 1 -> frame_skip 2
```
