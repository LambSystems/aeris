# Local Dev Setup

This guide is the detailed companion to the README quick start. It keeps the reviewer path short while documenting the moving parts needed for a local Aeris demo.

## Maintained Local Paths

```text
backend/       FastAPI, Streamlit scanner, environmental context, advice pipeline
ui/            Optional Vite shell around the Streamlit scanner/backend paths
tests/         Offline backend API and policy tests
scripts/       Local dev and smoke-check helpers
data/          CASTNET/demo fixtures
assets/        Demo/reference assets
docs/          Architecture, model, and runbook notes
```

Legacy UI experiments live under `archive/legacy-ui/` for provenance only.

## Environment Files

Use the root `.env` as the primary local configuration file:

```powershell
Copy-Item .env.example .env
```

The backend loads root `.env` first, then `backend/.env` if present. Keep `backend/.env` and `ui/.env` only for local overrides. Do not commit real keys or local model paths.

Aeris can run without LLM keys because the recommendation layer has deterministic fallback behavior.

## Install Dependencies

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Or with Conda:

```powershell
conda create -n aeris-backend python=3.12
conda activate aeris-backend
cd backend
pip install -r requirements.txt
```

Optional React shell:

```powershell
cd ui
npm install
```

## One-Command Demo

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1
```

This starts:

```text
FastAPI:   http://127.0.0.1:8000/docs
Streamlit: http://127.0.0.1:8507
```

To also start the optional Vite shell:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev.ps1 -WithUi
```

That adds:

```text
React UI:  http://127.0.0.1:5173
```

If `backend/models/trash-quick-v4-best.pt` exists, the script uses it automatically. If not, the Streamlit app falls back according to the backend YOLO configuration.

If no Python virtual environment is active, the helper scripts prefer:

```powershell
conda run -n aeris-backend python
```

## Smoke Checks

Offline backend checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke.ps1
```

Backend plus UI checks:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\smoke.ps1 -WithUi
```

If FastAPI is already running, `smoke.ps1` also runs the HTTP smoke path in `scripts/smoke_backend.py`. Otherwise it skips live endpoint checks and reports that clearly.

## Manual Fallback Commands

FastAPI:

```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

Streamlit:

```powershell
cd backend
$env:YOLO_MODEL_PATH = (Resolve-Path ".\models\trash-quick-v4-best.pt").Path
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8507
```

Optional React shell:

```powershell
cd ui
$env:VITE_VISION_PROVIDER="streamlit-embed"
$env:VITE_STREAMLIT_URL="http://127.0.0.1:8507?embed=true"
npm run dev
```

## Troubleshooting

- If imports fail, confirm `PYTHONPATH=backend` is set or use `scripts/dev.ps1`.
- If the camera does not appear, confirm browser camera permissions and restart Streamlit.
- If detection is slow, set `YOLO_IMGSZ=320`, `YOLO_FRAME_SKIP=2`, and camera dimensions around `640x360`.
- If LLM keys are missing, the app should still return deterministic fallback advice.
- If the optional React shell cannot reach the scanner, confirm `VITE_STREAMLIT_URL` points at the active Streamlit port.
