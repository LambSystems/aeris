# Aeris Backend

FastAPI service for the Aeris hackathon demo.

## Run

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

Swagger docs:

```text
http://localhost:8000/docs
```

## Core Endpoints

```text
GET  /health
GET  /context/demo
GET  /scan-frame/config
POST /scan-frame
POST /analyze-scene
GET  /analysis/latest
GET  /analysis/{job_id}
```

Compatibility/demo endpoints:

```text
GET  /scene/demo
GET  /scene/demo-after-move
POST /recommend
POST /demo/run
POST /scan
```

`/scan-frame` runs the live YOLO adapter when a frame upload is provided and falls back to the fixture scan when no frame is provided. `/scan` remains a fixture-backed compatibility endpoint.

`/analyze-scene` is the async agentic decision path. It returns a job id immediately while Gemini/OpenAI/fallback analysis runs in the background.

`/analysis/latest` returns the latest completed recommendation for polling UIs.

`/recommend` and `/demo/run` are compatibility helpers for local testing and fallback demos.

## Live YOLO Scan

`POST /scan-frame` accepts an optional multipart frame upload:

```text
frame: image file
image_width: original frame width
image_height: original frame height
confidence_threshold: optional 0-1 override
image_size: optional YOLO inference size, 320-1600
```

If no frame is provided, the endpoint returns the fixture-backed demo scan. Uploaded frames are decoded in memory, passed through YOLO, normalized into Aeris object labels, and discarded after the request.

Accepted frame content types:

```text
image/jpeg
image/png
image/webp
```

Frames larger than 8 MB are rejected. The frontend should send a compressed sampled frame, not a full video stream.

Optional environment variables:

```text
YOLO_MODEL_PATH=backend/.cache/yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.35
YOLO_IMAGE_SIZE=640
YOLO_INCLUDE_ALL_CLASSES=true
YOLO_LABEL_ALIASES_PATH=backend/app/cv/label_aliases.json
```

`GET /scan-frame/config` returns accepted image types, max frame size, the default confidence threshold, the model name, and label aliases.

## Backend Input / Output Contract

See `../docs/team-contracts.md` for the full team handoff contract.

Backend receives:

- sampled frame or fixture request for `/scan-frame`
- `DynamicContext` JSON for `/analyze-scene`
- optional `provider`: `gemini`, `openai`, or `template`

Backend returns:

- `FixedContext` from `/context/demo`
- `DynamicContext` from `/scan-frame`
- `AnalysisJobResponse` from `/analyze-scene`
- `RecommendationOutput` from `/analysis/{job_id}` when complete

Do not call the agent for every frame. `/scan-frame` should stay fast. `/analyze-scene` should start a background job and return immediately.

## YOLO Adapter Contract

Replace `app/cv/yolo_service.py` with real YOLO inference when ready, but keep this output shape:

```json
{
  "source": "yolo",
  "image_width": 920,
  "image_height": 460,
  "inference_ms": 72.4,
  "model_name": "yolov8n.pt",
  "scene_type": "outdoor",
  "scene_tags": ["outdoor_cues", "sustainability_items_visible"],
  "objects": [
    {
      "name": "bottle",
      "raw_label": "bottle",
      "category": "sustainability_item",
      "confidence": 0.94,
      "distance": 1.0,
      "reachable": true,
      "bbox": {
        "x": 92,
        "y": 112,
        "width": 190,
        "height": 126
      }
    }
  ]
}
```

Boxes must be in the same coordinate space as the sampled frame.

The default `yolov8n.pt` model can detect common COCO classes such as `bottle` and `cup`, but it does not have a dedicated `can` class. Use `YOLO_MODEL_PATH` plus `YOLO_LABEL_ALIASES_PATH` for reliable can, trash, wrapper, and bin detection from a custom/fine-tuned model.

By default Aeris keeps the curated aliases where they exist, but it also exposes the rest of the stock YOLO classes instead of filtering them out. Set `YOLO_INCLUDE_ALL_CLASSES=false` if you want mapped-only detections again.

## Quick Can / Bottle Fine-Tune

If you want better `can` and `bottle` detection, the fast path is to fine-tune the local `yolov8n.pt` checkpoint that is already cached in `backend/.cache/`.

Important: YOLO detection training needs bounding-box annotations, not just class folders. A folder like `/can` or `/bottle` is enough for classification, but not enough for object detection.

Expected dataset layout:

```text
backend/datasets/can_bottle/
  images/
    train/
      can_001.jpg
      bottle_001.jpg
    val/
      can_101.jpg
  labels/
    train/
      can_001.txt
      bottle_001.txt
    val/
      can_101.txt
```

Each label file must match the image filename and contain one YOLO box per line:

```text
<class_id> <x_center> <y_center> <width> <height>
```

Use these class ids:

```text
0 = can
1 = bottle
```

A starter dataset YAML lives at `backend/training/can_bottle.data.example.yaml`.

Run a short fine-tune:

```bash
cd backend
.venv\Scripts\python.exe scripts\train_yolo.py --data training\can_bottle.data.yaml --epochs 20 --batch 8 --device cpu
```

The script writes checkpoints under `backend/.cache/yolo-runs/` and prints the exact `YOLO_MODEL_PATH` to use when training finishes.

Then point the backend at the new weights:

```text
YOLO_MODEL_PATH=backend/.cache/yolo-runs/can-bottle-quick/weights/best.pt
```

## Streamlit Live Detector

For a fast local check before any fine-tuning, you can run a small Streamlit viewer that uses the same YOLO model and Aeris label normalization directly.

```bash
cd backend
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app supports:

- browser camera snapshots
- image uploads
- desktop webcam quick-refresh mode
- drawn boxes plus normalized Aeris labels

Best stock-model test objects right now:

```text
bottle
cup
wine glass
potted plant
scissors
cell phone
laptop
keyboard
remote
suitcase
```

Those currently map into these Aeris labels without custom training:

```text
bottle
cup
glass_container
plant_pot
metal_tool
electronics_case
storage_bin
```

## Realtime Webcam Detector

If you need boxes to follow objects continuously, use the local OpenCV loop instead of the snapshot-style API flow.

```bash
cd backend
.venv\Scripts\python.exe scripts\realtime_yolo.py --imgsz 320 --conf 0.25
```

This path is much faster because it:

- skips HTTP upload round-trips
- keeps the model loaded in one local process
- uses webcam frames directly
- uses YOLO tracking so boxes stay attached to moving objects

Useful flags:

```text
--imgsz 320         faster than 640 on CPU
--frame-skip 2      infer every other frame for smoother display
--show-raw          show non-Aeris YOLO classes too
--camera 1          switch webcams
```

For immediate responsiveness on CPU, start around:

```bash
.venv\Scripts\python.exe scripts\realtime_yolo.py --imgsz 320 --conf 0.25 --frame-skip 1
```

If that is still heavy, try:

```bash
.venv\Scripts\python.exe scripts\realtime_yolo.py --imgsz 256 --conf 0.25 --frame-skip 2
```
