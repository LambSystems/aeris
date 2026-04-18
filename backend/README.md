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
GET  /scene/demo
GET  /scene/demo-after-move
POST /recommend
POST /demo/run
POST /scan
```

`/scan` is currently a safe fixture-backed endpoint. Replace the stub in `app/cv/yolo_service.py` when YOLO is ready.

