# Demo Runbook

## Demo Goal

Make judges understand this in under 30 seconds:

```text
Aeris sees recyclable waste live, uses environmental context, and gives a practical action.
```

The visual proof is:

- live camera with YOLO box
- environmental context panel
- recommendation card that changes from detection + context

---

## Demo Objects

Use only the classes the model is expected to handle well:

```text
aluminum can
plastic bottle
paper / crumpled paper / napkin
```

Keep the scene simple. One object at a time is better than a cluttered scene.

---

## Run Order

### Terminal 1 - FastAPI

```powershell
cd C:\Users\akuma\repos\aeris
conda activate aeris-backend
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --reload --app-dir backend
```

### Terminal 2 - Streamlit YOLO

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

### Terminal 3 - React

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## Pre-Demo Checklist

1. `http://localhost:8000/health` returns ok.
2. `http://localhost:5173` loads the Aeris UI.
3. Browser allows camera access.
4. Streamlit iframe shows the camera.
5. YOLO draws a box around can/bottle/paper.
6. Right sidebar shows fixed context.
7. Right sidebar changes from "Waiting for detection" to the detected object.
8. Recommendation card fills in after the first actionable detection.

Manual checks:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
Invoke-RestMethod -Uri "http://localhost:8000/context/fixed?latitude=40.9478&longitude=-90.3712"
Invoke-RestMethod -Uri http://localhost:8000/vision/latest-detection
```

---

## Recommended Demo Script

### Opening

> This is Aeris, a live environmental scanner. It detects recyclable waste and uses local environmental context to tell people what to do right now.

### Dataset Moment

Point to the environmental context panel.

> The sidebar is not static filler. It is built from CASTNET context plus live weather and air-quality sources. That context affects the recommendation.

### Vision Moment

Hold up the can/bottle/paper.

> The vision model is running live. The box and label come from YOLO, not a pre-baked screenshot.

### Advice Moment

Point to the recommendation.

> We do not call an LLM every frame. YOLO detects continuously, then an event-based/cached advice layer turns the latest structured detection into a short action.

### Close

> Aeris connects perception, environmental data, and practical sustainability behavior in one live workflow.

---

## What To Show

Best sequence:

1. Start with empty/waiting state.
2. Hold up aluminum can until YOLO detects it.
3. Let recommendation appear.
4. Briefly mention CASTNET/weather values.
5. Swap to bottle or paper if time allows.

Avoid:

- cluttered background
- multiple objects at once
- moving object too fast
- discussing browser YOLO unless asked

---

## If It Feels Slow

Restart Streamlit with:

```powershell
$env:AERIS_CAMERA_WIDTH="640"
$env:AERIS_CAMERA_HEIGHT="360"
$env:YOLO_FRAME_SKIP="2"
$env:YOLO_IMGSZ="320"
python -m streamlit run streamlit_app.py --server.port 8501
```

Say, if asked:

> We can tune the vision cadence independently from the UI. The video and advice paths are decoupled.

---

## If Recommendation Does Not Appear

Check latest detection:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/vision/latest-detection
```

If `null`:

- the model has not passed threshold yet
- hold object more steadily
- check Streamlit terminal

If detection exists, test advice:

```powershell
Invoke-RestMethod `
  -Uri http://localhost:8000/sustainability/detect `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"latitude":40.9478,"longitude":-90.3712,"detection":{"object_class":"aluminum_can","confidence":0.84,"frame_id":"manual_test","timestamp":"2026-04-19T06:30:00Z"}}'
```

---

## If GPU Is Not Used

Check:

```powershell
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Expected:

```text
cuda_available True
NVIDIA GeForce RTX 5050 Laptop GPU
```

Streamlit must be restarted after changing PyTorch/GPU setup.

---

## Judge Talking Points

- CASTNET is visibly used in the right panel.
- Weather and air quality add fixed context.
- YOLO gives live object perception.
- The LLM is event-based and cached, not called per frame.
- The system has deterministic fallback, so it does not collapse if an LLM key/network fails.

---

## One-Sentence Demo Summary

**Aeris embeds live YOLO vision in a React interface, then uses FastAPI to combine the latest detection with CASTNET/weather context and produce a practical sustainability recommendation.**
