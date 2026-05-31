# Aeris

Aeris is a real-time environmental intelligence system built for HackAugie, where it won Best Data Insight. It detects visible waste, normalizes local environmental context, and returns a practical sustainability recommendation that still works when LLM providers are unavailable.

Aeris is not production recycling infrastructure. The portfolio signal is the system design: a clear boundary between vision detections, environmental context, LLM-backed advice, deterministic fallback behavior, and cache-aware backend orchestration.

- Devpost: https://devpost.com/software/aeris-the-environmental-intelligence-system
- Demo video: https://www.youtube.com/watch?v=41eoB-4JUbs
- Architecture: [docs/architecture.md](docs/architecture.md)
- Readiness audit: [docs/system-audit.md](docs/system-audit.md)
- Primary portfolio angle: backend orchestration across vision, environmental data, LLM advice, fallback policy, and caching

## Review Paths

| If you are... | Start here |
| --- | --- |
| A recruiter or portfolio reviewer | This README, the demo video, and [docs/system-audit.md](docs/system-audit.md) |
| An engineer reviewing the system | [docs/architecture.md](docs/architecture.md), [docs/yolo-integration.md](docs/yolo-integration.md), and [tests/](tests/) |
| Trying to run it locally | The Quick Start below, then `python -m unittest discover -s tests` |
| Looking for model training context | [docs/trash-model.md](docs/trash-model.md) and `backend/scripts/` |
| Looking for hackathon provenance | [docs/hackaton-context.md](docs/hackaton-context.md) and `archive/legacy-ui/` |

## What It Does

Aeris answers one live question:

```text
What is this object, what local context matters, and what should someone do right now?
```

The current project-ready flow is:

```text
Camera or uploaded clip
  -> Streamlit WebRTC / upload processor
  -> local YOLO waste detector
  -> latest structured detection
  -> FastAPI environmental context layer
  -> Gemini or Anthropic advice
  -> deterministic fallback and cache
  -> sustainability recommendation in the UI
```

The custom detector focuses on:

- can
- paper
- bottle

The environmental context layer combines:

- CASTNET processed readings
- Open-Meteo weather
- Open-Meteo air quality
- weather.gov alerts
- derived risk flags

## Deterministic vs AI-Assisted

- Deterministic: environmental context normalization, risk flags, API contracts, cache behavior, and fallback recommendation policy.
- Model-based: YOLO waste detection for cans, paper, and bottles.
- AI-assisted: Gemini or Anthropic recommendation wording when provider keys are configured.
- Bounded: the LLM does not own object detection, environmental measurements, risk flags, or fallback behavior.

## System Boundary

Aeris is intentionally split into three boundaries:

| Boundary | Owner | Responsibility |
| --- | --- | --- |
| Vision layer | Streamlit + YOLO | Camera/video capture, inference, bounding boxes, latest detection |
| Context layer | FastAPI backend | Normalize CASTNET, weather, air quality, alerts, and risk flags |
| Recommendation layer | FastAPI + LLM/fallback | Turn detection + context into grounded action with cache and fallback |

The important engineering choice is that raw video is not sent to the reasoning layer. The recommendation path receives structured detections and environmental context, which keeps the pipeline debuggable and avoids calling an LLM on every frame.

## Repository Map

```text
backend/
  app/main.py                         FastAPI routes
  app/context/                        CASTNET/weather/air-quality context
  app/sustainability/adviser.py       Gemini/Anthropic/fallback advice cache
  app/cv/yolo_service.py              Image scan service path
  streamlit_app.py                    Primary live scanner and upload UI
  scripts/                            YOLO training, realtime, and dataset utilities

ui/
  src/pages/Index.tsx                 Optional React shell / Streamlit embed
  src/components/aeris/               Portfolio UI components
  src/vision/                         Browser/backend YOLO experiments

data/
  castnet/processed/                  Demo CASTNET profiles/readings
  sample_inputs/                      Demo scene fixtures

tests/                                Backend API and policy tests
scripts/                              Root-level backend smoke and data utilities
assets/                               Demo/reference assets

docs/
  architecture.md                     Current system design
  trash-model.md                      Custom model training record
  system-audit.md                     Portfolio-readiness audit

archive/legacy-ui/
  frontend/                           Earlier Vite/React experiment
  aeirs-ui/                           Earlier Next.js experiment
  aeris-ui-scratch/                   Scratch workspace notes only
```

Earlier UI experiments are archived under `archive/legacy-ui/` for provenance. The current maintained UI paths are `backend/streamlit_app.py` and, optionally, `ui/`.

## Quick Start

### 1. Backend Environment

From the repo root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If Python is managed through Conda:

```powershell
conda create -n aeris-backend python=3.12
conda activate aeris-backend
cd backend
pip install -r requirements.txt
```

### 2. Configure Optional Secrets

Copy the example file and fill only the keys you want to use:

```powershell
Copy-Item .env.example .env
```

Aeris works without LLM keys because the deterministic fallback still returns advice.

### 3. Run FastAPI

From the repo root:

```powershell
$env:PYTHONPATH="backend"
python -m uvicorn app.main:app --reload --app-dir backend --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/docs
```

### 4. Run Streamlit

From `backend/`:

```powershell
$env:YOLO_MODEL_PATH = (Resolve-Path ".\models\trash-quick-v4-best.pt").Path
$env:YOLO_IMGSZ="320"
$env:YOLO_FRAME_SKIP="2"
python -m streamlit run streamlit_app.py --server.address 127.0.0.1 --server.port 8507
```

Open:

```text
http://127.0.0.1:8507
```

If the custom checkpoint is not present, Streamlit falls back to bundled YOLO weights. The strongest documented checkpoint is `backend/models/trash-quick-v4-best.pt`; it is intentionally gitignored because model artifacts can be large.

## Optional React Shell

The Vite UI in `ui/` can run as a product shell around the Streamlit scanner or use experimental browser/backend scanning paths.

```powershell
cd ui
npm install
npm run dev
```

For the Streamlit embed path:

```powershell
$env:VITE_VISION_PROVIDER="streamlit-embed"
$env:VITE_STREAMLIT_URL="http://127.0.0.1:8507"
npm run dev
```

## Main API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Service check |
| `GET /context/fixed` | CASTNET + weather + air quality + risk flags |
| `GET /scan-frame/config` | Current local YOLO settings |
| `POST /scan-frame` | Scan one uploaded image with local YOLO |
| `POST /sustainability/detect` | Build advice for a structured detection |
| `GET /vision/latest-detection` | Latest detection written by Streamlit |
| `POST /analyze-scene` | Older async scene-analysis path |

## Verification

Backend policy smoke tests:

```powershell
python -m unittest discover -s tests
```

This includes offline API contract tests for the FastAPI boundary and backend policy tests for event/fallback behavior.

UI tests and build:

```powershell
cd ui
npm run test
npm run build
```

## Hackathon Tradeoffs

- Streamlit remains the primary live scanner because it was the fastest reliable way to connect camera input, YOLO inference, and backend recommendations during the hackathon.
- Model checkpoints are local artifacts and are intentionally gitignored; the documented path is `backend/models/trash-quick-v4-best.pt`.
- Legacy UI experiments are kept under `archive/legacy-ui/` for provenance, but the maintained demo paths are `backend/streamlit_app.py` and `ui/`.
- The recommendation layer favors a small, inspectable fallback path over broad autonomous-agent behavior.

## Team Contributions

- [@postigodev](https://github.com/postigodev): FastAPI layer, environmental context integration, recommendation pipeline, LLM/fallback/cache orchestration, and glue between Streamlit/YOLO detections and the rest of the system.
- [@shuja-waraich-03](https://github.com/shuja-waraich-03): AI integration, real-time synchronization between vision and reasoning, Gemini prompt structure, and live detection validation.
- [@kacytran1122](https://github.com/kacytran1122): Frontend work, React camera detection, landing page, responsive interaction design, and user experience polish.
- [@GALGALLOR](https://github.com/GALGALLOR): Computer vision pipeline, dataset preparation, YOLO fine-tuning, real-time inference performance, and Streamlit integration.

## Portfolio Notes

This repo is strongest when presented as a systems integration project rather than a generic object detector. The recruiter-facing story is:

```text
Aeris connects live computer vision, real environmental data, and resilient AI recommendations through a backend pipeline that is observable, cached, and fallback-safe.
```

See `docs/system-audit.md` for the current readiness audit and next cleanup targets.
