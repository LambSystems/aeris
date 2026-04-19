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

`/scan-frame` and `/scan` are currently safe fixture-backed endpoints. Replace the stub in `app/cv/yolo_service.py` when YOLO is ready.

`/analyze-scene` is the async agentic decision path. It returns a job id immediately while Gemini/OpenAI/fallback analysis runs in the background.

`/analysis/latest` returns the latest completed recommendation for polling UIs.

`/recommend` and `/demo/run` are compatibility helpers for local testing and fallback demos.
