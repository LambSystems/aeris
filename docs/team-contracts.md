# Team Contracts

This project now treats the Streamlit app as the primary product surface.

Source of truth:

```text
/backend/streamlit_app.py + /backend/app
```

---

## Shared Runtime Contract

Run two core processes:

```text
FastAPI:   http://localhost:8000
Streamlit: http://localhost:8507
```

Primary flow:

```text
camera -> Streamlit WebRTC -> local YOLO -> side-panel advice
```

---

## Backend / Integration

Owns:

- FastAPI app
- fixed environmental context
- sustainability advice endpoint
- vision bridge file
- app stability and run commands

Must keep stable:

```text
GET /context/fixed
GET /scan-frame/config
POST /scan-frame
POST /sustainability/detect
GET /vision/latest-detection
```

Must not do:

- trigger LLM calls every frame
- move core camera UX out of Streamlit
- break YOLO config or model-path handling

---

## Computer Vision

Owns:

- YOLO weights
- class quality
- confidence behavior
- realtime tracking quality

Current expected local classes:

```text
can
paper
bottle
```

Current preferred checkpoint:

```text
backend/models/trash-quick-v4-best.pt
```

Must prioritize:

- local YOLO `.pt` inference
- higher FPS and lower latency
- stable boxes across frames
- clear class naming without forced relabeling

---

## Product / Advice

Owns:

- framing of the sustainability recommendation
- what context matters
- what action wording feels specific and useful

Advice behavior:

1. Gemini if configured
2. Anthropic if configured
3. deterministic fallback otherwise

Must keep:

- concise context
- clear action
- compatibility with `can`, `paper`, and `bottle`

---

## Frontend Scope

React or browser-side UI work is not the primary runtime path right now.

If used at all, it is secondary and must not:

- replace Streamlit as the main app
- own live camera detection
- move YOLO inference away from the local backend stack
