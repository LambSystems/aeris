# Stack

## Purpose

This document defines the fastest stack for shipping Aeris with live 2D perception and asynchronous agentic decisions.

The goal is:

- phone-style live camera experience
- YOLO object detection in 2D
- CASTNET environmental context
- Gemini-first agentic reasoning
- OpenAI fallback
- fixture/template fallback for demo safety

The UI should not wait for the LLM. It should keep showing the camera stream and latest detection state while the backend runs reasoning jobs in the background.

---

## Recommended Stack

### Frontend

Use:

- **Lovable** for first UI generation
- **Vite**
- **React**
- **TypeScript**
- **Tailwind CSS**

Why:

- fast phone-app-style interface
- easy camera stream / image fallback
- easy 2D overlay rendering
- compatible with Lovable output
- simple API polling for analysis jobs

Frontend responsibility:

- keep livestream smooth
- render detection boxes
- call analysis asynchronously
- poll latest recommendation
- never block the camera on reasoning

Avoid:

- landing page output from Lovable
- chat-first UI
- heavy navigation
- blocking UI state while LLM runs

---

### Backend

Use:

- **Python**
- **FastAPI**
- **Pydantic**
- **Uvicorn**

Why:

- native fit for YOLO/OpenCV/image processing
- clean schema contracts
- simple background task support
- easy provider wrappers for Gemini/OpenAI
- easy fixture fallback

Backend responsibility:

- load CASTNET fixed context
- normalize scene snapshots
- expose scan/analyze/latest APIs
- run async agentic reasoning jobs
- store latest completed recommendation in memory for the demo

Avoid:

- database setup
- auth
- queues unless absolutely needed
- calling LLMs on every video frame

---

### Computer Vision

Primary:

- **YOLO**
- 2D bounding boxes
- label normalization
- confidence filtering
- simple distance/reachability heuristics

Fallback:

- fixture-based normalized detections

Optional stretch:

- Boxer, only if it becomes stable without slowing the demo

YOLO should produce a normalized `DynamicContext` shape:

```json
{
  "source": "yolo",
  "objects": [
    {
      "name": "seed_tray",
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

---

### Agentic Decision Layer

Primary:

- **Gemini**

Secondary:

- **OpenAI**

Fallback:

- local template/fallback policy

The LLM should reason over structured data only:

- CASTNET context
- detected objects
- allowed actions
- strict output schema

It should not process raw video.

The agent decides:

- ranking
- action type
- target
- reason
- explanation

The fallback policy exists only for safety.

---

## API Contract

### Core Endpoints

```text
GET  /health
GET  /context/demo
POST /scan-frame
POST /analyze-scene
GET  /analysis/latest
GET  /analysis/{job_id}
```

### Compatibility / Demo Endpoints

```text
GET  /scene/demo
GET  /scene/demo-after-move
POST /demo/run
POST /recommend
```

The compatibility endpoints are useful for testing and fallback demos, but the primary live architecture should use `scan-frame`, `analyze-scene`, and `analysis/latest`.

---

## Endpoint Responsibilities

### `POST /scan-frame`

Fast perception path.

Returns latest YOLO detections or fixture detections. This endpoint must be fast.

### `POST /analyze-scene`

Async agentic decision path.

Accepts the latest scene snapshot and starts a reasoning job. Returns immediately with:

```json
{
  "job_id": "string",
  "status": "pending"
}
```

### `GET /analysis/{job_id}`

Returns job status:

```text
pending | complete | failed
```

If complete, includes recommendations.

### `GET /analysis/latest`

Returns the latest completed recommendation, if any.

The UI should keep rendering the live scene while polling this endpoint.

---

## Runtime Cadence

Do not call the agent for every frame.

Recommended cadence:

- camera stream: native browser/mobile frame rate
- YOLO snapshot: every 1-2 seconds or on user-triggered scan
- agent analysis: on user tap, meaningful object-set change, or stable scene
- latest recommendation polling: every 1 second while a job is pending

---

## Repo Structure

```text
aeris/
  frontend/
  backend/
    app/
      main.py
      schemas.py
      data.py
      analysis_store.py
      agent_decision.py
      fallback_policy.py
      cv/
        yolo_service.py
      llm/
        provider.py
        gemini.py
        openai_provider.py
        template.py
  data/
    castnet/
      processed/
    sample_inputs/
  docs/
```

---

## Package Choices

### Frontend

- `vite`
- `react`
- `typescript`
- `tailwindcss`
- `lucide-react`

Optional:

- `@react-three/fiber` and `three` only after the 2D live flow works

### Backend

- `fastapi`
- `uvicorn`
- `pydantic`
- `python-dotenv`
- `python-multipart`

Optional:

- Gemini SDK
- `openai`
- `opencv-python`
- `ultralytics`
- `pillow`

---

## Fallback Strategy

### If YOLO fails

Use fixture detections.

### If Gemini is slow

Keep latest completed recommendation visible and show pending state.

### If Gemini fails

Try OpenAI.

### If all LLM providers fail

Use local fallback policy/template output.

### If the frontend is not integrated yet

Use `/demo/run` for a single-call stable demo.

---

## Final Stack Summary

```text
Frontend: React + Vite + TypeScript + Tailwind, generated first with Lovable
Backend:  Python + FastAPI + Pydantic
CV:       YOLO primary, fixture fallback, Boxer optional stretch
Data:     Static CASTNET-derived JSON profiles
Agent:    Gemini primary, OpenAI fallback, template/fallback policy safety net
Runtime:  Live camera stays smooth; analysis runs asynchronously
Deploy:   Local demo first
```
