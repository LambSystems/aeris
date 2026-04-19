# Aeris Backend

The backend is now built around a Streamlit-first live camera app plus FastAPI support endpoints.

Primary path:

```text
Streamlit camera -> local YOLO model -> side-panel advice
```

Supporting path:

```text
FastAPI -> fixed environmental context, image scan endpoint, latest detection, sustainability advice
```

---

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional `backend/.env`:

```env
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-6
YOLO_MODEL_PATH=
YOLO_DEVICE=
YOLO_IMGSZ=320
YOLO_FRAME_SKIP=2
AERIS_CAMERA_WIDTH=640
AERIS_CAMERA_HEIGHT=360
```

---

## Run

API:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Streamlit:

```powershell
cd backend
$env:YOLO_MODEL_PATH = (Resolve-Path ".\models\trash-quick-v4-best.pt").Path
.venv\Scripts\python.exe -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8507
```

---

## Main Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Service check |
| `GET /context/fixed` | CASTNET + weather + air quality + risk flags |
| `GET /scan-frame/config` | Current local YOLO settings |
| `POST /scan-frame` | Scan one uploaded image with local YOLO |
| `POST /sustainability/detect` | Build advice for a detection |
| `GET /vision/latest-detection` | Latest detection written by Streamlit |
| `POST /analyze-scene` | Older async scene-analysis path |
| `GET /analysis/latest` | Latest async analysis result |
| `GET /analysis/{job_id}` | Async analysis status |

`POST /scan-frame` accepts multipart uploads using either `frame` or `file`.

---

## Custom YOLO Model

Current preferred local checkpoint:

```text
backend/models/trash-quick-v4-best.pt
```

Current custom classes:

```text
can
paper
bottle
```

The full training record lives in:

```text
docs/trash-model.md
```

That document covers:

- dataset annotation and preprocessing
- Modal training and checkpoint storage
- fine-tune history across `v2`, `v3`, and `v4`
- expected accuracy and limitations
- runtime integration into Streamlit and local testing

---

## Speed Notes

If live camera detection feels heavy, start here:

```powershell
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="2"
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
```

If the machine has CUDA available:

```powershell
$env:YOLO_DEVICE="0"
```

The Streamlit app keeps the camera stream as the primary surface and puts detections plus advice beside the video feed.
