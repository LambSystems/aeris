# Aeris

**Aeris** is a pollution-aware scene analyzer for outdoor sustainability.

It uses **CASTNET-based environmental exposure context**, **live YOLO scene perception**, and an **asynchronous agentic reasoning layer** to recommend what outdoor resources should be **protected, moved, covered, or deprioritized first** under pollution-related environmental stress.

Instead of stopping at environmental monitoring, Aeris turns environmental context into **real-world action**.

---

## Why Aeris

Environmental data often tells us **that** risk exists, but not **what to do next**.

Aeris closes that gap by combining three layers:

- **Fixed Context**: environmental exposure context derived from CASTNET
- **Live Perception**: YOLO-based 2D detection of visible outdoor resources
- **Agentic Decisioning**: asynchronous Gemini/OpenAI reasoning over the latest structured scene snapshot

From there, Aeris updates the **best next actions** for protecting resources without blocking the camera stream.

---

## Core Idea

Aeris answers:

> Given this environmental exposure context, and given the actual objects in front of me, what should I protect first?

Example output:

- Protect the seed tray first
- Move the battery pack into storage
- Use the tarp if time allows
- Leave the water jug for later

---

## Hackathon Demo Scope

For HackAugie, Aeris is focused on one clear use case:

### Outdoor resource protection under environmental stress

The demo scene contains a small outdoor or semi-outdoor setup such as:

- seed tray
- battery pack
- metal tool
- tarp
- storage bin
- water jug
- gloves
- one irrelevant object

Aeris uses environmental context plus live scene perception to trigger an asynchronous recommendation about what should be protected first.

---

## How It Works

### 1. Fixed Context

Aeris loads environmental exposure context for the location.

This includes:

- CASTNET-informed pollution profile
- pollution stress mode
- risk summary for outdoor assets

### 2. Live Perception

Aeris keeps the scene/camera view responsive while YOLO detects visible resources in 2D.

The YOLO adapter returns a structured scene snapshot with:

- object names
- confidence
- bounding boxes
- approximate distance / reachability

### 3. Agentic Decision Layer

Aeris starts an asynchronous reasoning job over:

- CASTNET context
- detected objects
- approximate distance / reachability
- allowed protection actions

Gemini is the primary provider, OpenAI is the fallback, and local template/fallback policy output keeps the demo stable if providers fail.

---

## Why This Fits Sustainability

Aeris is a sustainability project because it focuses on:

- protecting outdoor resources from pollution-related stress
- reducing avoidable degradation
- extending the useful life of materials and equipment
- reducing unnecessary replacement and waste
- turning environmental monitoring into practical environmental adaptation

---

## Tech Stack

### Frontend

- Lovable first UI pass
- React / Vite / TypeScript / Tailwind
- live camera view
- 2D detection overlay
- async recommendation panel

### Backend

- FastAPI service for context, scan snapshots, async analysis jobs, and latest recommendations
- Gemini/OpenAI provider wrappers
- fixture and fallback policy safety paths
- schema-based orchestration

### Computer Vision

- **YOLO** for primary object detection
- simple bounding-box heuristics for approximate reachability / distance
- **Boxer optional** only if it becomes stable without slowing the demo

### Data

- CASTNET-derived environmental context
- processed lookup/profile data for demo use

### Agent

- Gemini-first agentic decision layer
- OpenAI fallback
- local template/fallback policy safety net

---

## MVP+

### Must-have

- CASTNET-based fixed context
- live or fixture-backed YOLO detections
- async agentic recommendations
- clean UI with visible analysis state

### Nice-to-have

- rescan after objects move
- missing protection insight
- two environmental modes
- small 3D scene map

---

## Team

- **Chau** - Frontend
- **Gallo** - Data / Computer Vision
- **Shuja** - Agentic / Data / Policy Logic
- **Piero** - Backend / API

---

## Repo Structure

```text
aeris/
|-- README.md
|-- docs/
|   |-- product.md
|   |-- architecture.md
|   |-- mvp.md
|   |-- data.md
|   |-- demo.md
|   |-- stack.md
|   `-- interface-concept.md
|-- frontend/
|-- backend/
`-- data/
```

---

## Quick Start

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend:

```text
http://localhost:8000
```

API docs:

```text
http://localhost:8000/docs
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend:

```text
http://localhost:5173
```

The frontend falls back to mock data if the backend is not running.

---

## Build Priorities

### Piero / Backend

- keep the FastAPI contract stable
- wire YOLO output into `backend/app/cv/yolo_service.py`
- keep fixture fallback working
- keep async analysis jobs stable
- keep fallback policy available only as a safety net

### Chau / Frontend

- use `docs/interface-concept.md` as the source of truth
- Lovable can generate the first UI pass
- keep the app as a single demo screen
- keep livestream smooth while analysis jobs run
- poll latest recommendation instead of blocking UI on LLM response

### Gallo / CV

- prioritize YOLO over Boxer
- output the normalized scene schema used by the backend
- do not block the demo if live CV is unstable

### Shuja / Data + Agent

- refine CASTNET-derived profile data
- improve agent prompt/schema and fallback logic
- keep recommendations tied to structured scene state

---

## Status

HackAugie MVP+ in progress.

Current goal:

- deliver one polished end-to-end demo
- show CASTNET-based context
- show live scene perception
- show async agentic protection decisions
- tell a clear sustainability story

---

## One-Line Pitch

**Aeris uses CASTNET environmental exposure data, live YOLO scene perception, and asynchronous agentic reasoning to tell users what outdoor resources to protect first under pollution-related stress.**
