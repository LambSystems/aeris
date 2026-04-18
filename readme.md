# Aeris

**Aeris** is a pollution-aware scene analyzer for outdoor sustainability.

It uses **CASTNET-based environmental exposure context** plus **scene understanding** to recommend what outdoor resources should be **protected, moved, covered, or deprioritized first** under pollution-related environmental stress.

Instead of stopping at environmental monitoring, Aeris turns environmental context into **real-world action**.

---

## Why Aeris

Environmental data often tells us **that** risk exists, but not **what to do next**.

Aeris closes that gap by combining two layers:

- **Fixed Context**: environmental exposure context derived from CASTNET and related conditions
- **Dynamic Context**: real-time scene understanding of visible outdoor resources

From there, Aeris ranks the **best next actions** for protecting resources in a real setup.

---

## Core Idea

Aeris answers:

> Given this environmental exposure context, and given the actual objects in front of me, what should I protect first?

Example output:

- Protect the seed tray first
- Move the battery pack into storage
- Cover the metal tools if time allows
- Leave the water jug for later

---

## Hackathon Demo Scope

For HackAugie, Aeris is focused on a single clear use case:

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

Aeris uses environmental context plus scene understanding to rank what should be protected first.

---

## How It Works

### 1. Fixed Context
Aeris loads environmental exposure context for the location.

This includes:
- CASTNET-informed pollution profile
- pollution stress mode
- risk summary for outdoor assets

### 2. Dynamic Context
Aeris scans the visible scene.

Using **YOLO** as the primary scene-understanding engine, with optional Boxer exploration only if time allows, it detects relevant objects and estimates enough spatial information to support prioritization.

### 3. Policy Engine
Aeris runs a deterministic ranking engine that weighs:
- environmental vulnerability of each object
- usefulness of protecting it
- approximate distance / reachability
- time-sensitive priority

### 4. Explanation Layer
An LLM converts the ranked output into a clean recommendation for the user.

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
- React / Next.js or Vite-based UI
- live camera view
- scene overlay
- recommendation panel

### Backend
- API service for context, scan results, and recommendations
- deterministic policy engine
- schema-based orchestration

### Computer Vision
- **YOLO** for primary object detection
- simple bounding-box heuristics for approximate reachability / distance
- **Boxer optional** only if it becomes stable without slowing the demo

### Data
- CASTNET-derived environmental context
- processed lookup/profile data for demo use

### LLM
- explanation layer only
- natural-language recommendation generation
- not the primary decision-maker

---

## MVP+

### Must-have
- CASTNET-based fixed context
- scene scan with object detections
- ranked action recommendations
- clean UI with visible rationale

### Nice-to-have
- re-scan after objects move
- missing protection insight
- two environmental modes

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

* keep the FastAPI contract stable
* wire YOLO output into `backend/app/cv/yolo_service.py`
* keep fixture fallback working
* keep deterministic policy ranking inspectable

### Chau / Frontend

* use `docs/interface-concept.md` as the source of truth
* Lovable can generate the first UI pass
* keep the app as a single demo screen
* replace mock data with backend API calls

### Gallo / CV

* prioritize YOLO over Boxer
* output the normalized scene schema used by the backend
* do not block the demo if live CV is unstable

### Shuja / Data + Policy

* refine CASTNET-derived profile data
* improve policy weights and reason tags
* keep explanations tied to deterministic policy output

---

## Status

HackAugie MVP+ in progress.

Current goal:

* deliver one polished end-to-end demo
* show CASTNET-based context
* show scene understanding
* show ranked protection decisions
* tell a clear sustainability story

---

## One-Line Pitch

**Aeris uses CASTNET environmental exposure data and scene understanding to tell users what outdoor resources to protect first under pollution-related stress.**
