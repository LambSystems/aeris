# Stack

## Purpose

This document defines the most efficient stack for shipping Aeris within the remaining hackathon window.

The goal is not to choose the most impressive production stack. The goal is to choose the stack that gives the team the best chance of delivering:

- one working end-to-end demo
- visible CASTNET-based context
- real or fallback scene understanding
- deterministic ranked recommendations
- a clean UI
- stable submission artifacts

For this project, efficiency means:

- fewer languages across the app
- simple local setup
- clear API contracts
- fast frontend/backend integration
- stable demo fallbacks
- minimal infrastructure

---

## Recommended Stack

### Frontend

Use:

- **Vite**
- **React**
- **TypeScript**
- **Tailwind CSS**
- **Lovable** for the first UI scaffold

Why:

- fastest path to a polished single-screen demo
- simple local dev server
- easy camera or image-upload UI
- easy rendering of detection overlays
- no App Router or deployment complexity needed for the hackathon
- Lovable can quickly generate the first interface pass for Chau to refine

Avoid:

- multi-page routing
- heavy state management
- complex animation libraries
- server-side rendering
- letting Lovable generate a marketing landing page instead of the actual demo screen

Frontend should stay as a single screen:

```text
[ Scene / Camera Panel ]   [ Environmental Context ]
                           [ Ranked Actions ]
                           [ Explanation ]
```

---

### Backend

Use:

- **Python**
- **FastAPI**
- **Pydantic**
- **Uvicorn**

Why:

- fastest path if CV, data processing, and model integration are Python-native
- clean typed request/response schemas through Pydantic
- simple API scaffolding
- easy image upload support
- easy integration with YOLO, OpenCV, notebooks, and data scripts
- easy for Piero to own API contracts and orchestration

Avoid:

- database setup
- authentication
- queues
- microservices
- serverless deployment complexity
- large framework setup

The backend should be a local API service, not a production platform.

### Why FastAPI over Express

Express is still a viable choice if the team wants TypeScript everywhere. For Aeris, FastAPI is the more efficient backend choice because the riskiest integrations are likely to be Python-side:

- CV inference
- image processing
- CASTNET preprocessing
- data fixtures
- LLM SDK calls

Using FastAPI avoids extra cross-language glue between a Node API and Python CV/data scripts.

The frontend can stay TypeScript while the backend stays Python. That split is acceptable because the API boundary is small and schema-driven.

---

### Data Layer

Use:

- static JSON files
- small processed CASTNET-derived profile
- sample scene fixtures

Recommended files:

```text
data/
  castnet/
    processed/
      demo_profile.json
      castnet_profiles.json
    notes.md
  sample_inputs/
    demo_scene.json
    demo_scene_after_move.json
```

Why:

- fastest way to make CASTNET visibly operational
- easy to inspect during judging
- easy for backend to load
- avoids losing hours to ingestion or database work

The data story should be honest:

> Aeris uses a compact environmental profile derived from CASTNET as Fixed Context for the demo.

Avoid:

- full CASTNET ingestion
- live environmental APIs
- database migrations
- complex data science notebooks in the demo path

---

### Computer Vision

Primary:

- **YOLO**
- simple bounding-box and frame-position heuristics

Fallback:

- fixture-based normalized scene output if live CV integration is unstable

Optional stretch:

- **Boxer**, only if it becomes stable quickly and does not slow down the core demo

The backend contract should not depend on the CV implementation. CV only needs to produce this shape:

```json
{
  "objects": [
    {
      "name": "seed_tray",
      "confidence": 0.94,
      "distance": 1.0,
      "reachable": true,
      "bbox": {
        "x": 120,
        "y": 80,
        "width": 180,
        "height": 120
      }
    }
  ]
}
```

Why:

- backend and frontend can integrate before CV is final
- Gallo can swap YOLO, Boxer, or fixture output behind the same contract
- demo remains stable if live detection fails

Avoid:

- making CV block the frontend/backend
- training custom models
- full 3D reconstruction
- complex depth estimation

---

### Interface Mode

See `docs/interface-concept.md` for the detailed UI direction.

Primary UI:

- 2D camera or image panel
- bounding boxes
- labels
- recommendation cards
- CASTNET context panel

Optional polish:

- **React Three Fiber**
- **Three.js**

Why 2D first:

- the demo only needs to prove scene understanding and prioritized action
- 2D overlays are faster to build and easier to debug
- judges will understand bounding boxes immediately
- a 3D interface can distract from the CASTNET + recommendation story

When React Three Fiber makes sense:

- if the team already has a stable 3D scene ready
- if the 3D view clearly improves spatial understanding
- if it can be done without blocking scan/recommendation integration
- if it remains a supporting visualization, not the primary demo risk

Best compromise:

- ship the core UI as 2D
- optionally add a small 3D "scene map" panel that places detected objects on a simple table plane using approximate positions
- use color and object markers to show priority, not a full simulated environment

Avoid:

- making 3D required for the main flow
- spending hours on camera controls or lighting
- building a decorative 3D scene that does not improve the recommendation story

---

### Recommendation Engine

Use:

- deterministic Python policy module in the backend
- simple weight tables
- explicit reason tags

Why:

- easy to debug
- easy to explain to judges
- stable under demo pressure
- aligns with the architecture docs

Recommended scoring model:

```text
score =
  vulnerability_weight
  + protection_value
  + enabling_value
  - distance_penalty
  - unreachable_penalty
```

The engine should return:

- ranked actions
- scores
- reason tags
- short explanation input

Avoid:

- using an LLM to decide rankings
- complex optimization logic
- hard-to-explain scoring

---

### Explanation Layer

Primary path:

- template-generated explanation from policy output

Optional path:

- LLM rewrite through an `LLMProvider` wrapper after the template path works

Preferred LLM provider:

- **Gemini**

Secondary provider:

- **OpenAI**

Why:

- the demo cannot depend on a flaky external call
- template explanations are enough for judges
- the LLM can be framed as polish, not core logic
- Gemini is a good first option for the hackathon context
- a provider wrapper lets the team switch models without changing policy logic or API responses

Recommended provider interface:

```text
LLMProvider.generateExplanation(input) -> string
```

Recommended implementations:

```text
GeminiProvider
OpenAIProvider
TemplateProvider
```

Recommended fallback order:

```text
Gemini -> OpenAI -> TemplateProvider
```

Recommended template:

```text
Current CASTNET-derived conditions indicate {risk_mode_label}. Aeris ranked {top_target} first because it is {reason}. Next, {second_target} should be {second_action}. {third_target} is lower priority or should be handled if time allows.
```

Avoid:

- making the LLM call required
- sending raw images to the LLM
- letting the LLM change action ordering
- coupling backend routes directly to one vendor SDK

---

### Deployment

For the hackathon demo:

- run locally
- record a backup demo video
- keep a known-good screenshot

Recommended local commands:

```text
frontend: npm run dev
backend:  uvicorn app.main:app --reload
```

Optional after core demo works:

- deploy frontend to Vercel
- deploy backend only if trivial

Avoid:

- spending core build time on deployment issues
- requiring cloud services for the live demo

Completion is worth more than infrastructure polish for HackAugie.

---

## API Contract

Piero should prioritize a stable backend contract.

### Required Endpoints

```text
GET  /health
GET  /context/demo
GET  /scene/demo
GET  /scene/demo-after-move
POST /recommend
POST /demo/run
```

### Optional Endpoint

```text
POST /scan
```

Only add `/scan` once CV integration has a reliable path.

---

## Endpoint Responsibilities

### `GET /health`

Confirms the backend is running.

Example:

```json
{
  "ok": true,
  "service": "aeris-api"
}
```

### `GET /context/demo`

Returns the demo CASTNET-derived Fixed Context.

### `GET /scene/demo`

Returns the normalized scene fixture for the main demo.

### `GET /scene/demo-after-move`

Returns a second normalized scene fixture for the optional rescan moment.

### `POST /recommend`

Accepts Fixed Context and Dynamic Context, then returns ranked recommendations.

### `POST /demo/run`

Returns the complete demo payload in one call:

```json
{
  "fixed_context": {},
  "dynamic_context": {},
  "recommendations": {}
}
```

This is the live-demo safety endpoint.

---

## Repo Structure

Recommended structure:

```text
aeris/
  frontend/
    src/
      App.tsx
      api.ts
      components/
  backend/
    app/
      main.py
      schemas.py
      policy.py
      explanations.py
      data.py
      llm/
        provider.py
        gemini.py
        openai_provider.py
        template.py
  data/
    castnet/
      processed/
        demo_profile.json
        castnet_profiles.json
      notes.md
    sample_inputs/
      demo_scene.json
      demo_scene_after_move.json
  docs/
```

This keeps ownership clean:

- Chau owns `frontend/`
- Piero owns `backend/`
- Shuja owns data/profile/policy support
- Gallo owns CV output normalization

---

## Package Choices

### Frontend Packages

Use:

- `vite`
- `react`
- `typescript`
- `tailwindcss`

Optional:

- `lucide-react` for icons
- `@react-three/fiber` and `three` only if the optional scene map is added after the core UI works

Avoid unless already installed:

- large UI kits
- charting libraries for the core app
- animation frameworks

### Backend Packages

Use:

- `fastapi`
- `uvicorn`
- `pydantic`
- `python-dotenv`

Optional:

- `google-generativeai` or the current Gemini SDK available to the team
- `openai`
- `opencv-python`
- `ultralytics`
- `pillow`
- `python-multipart` if image upload is needed

Avoid:

- Prisma
- databases
- auth libraries
- background job libraries
- external API clients in the critical path

---

## Data Visualization

The Data Insight requirement needs at least one clear visualization or dashboard.

Most efficient option:

- add a simple frontend mini-chart or compact visual card showing the CASTNET-derived risk profile

Recommended visualization:

```text
Ozone Risk:      High
Deposition Risk: Medium
Active Mode:     Protect Plants and Sensitive Equipment
```

If time allows, make this a small bar visualization in the UI or pitch slide.

Avoid:

- building a separate analytics dashboard
- spending hours on chart libraries
- overexplaining atmospheric chemistry

---

## Fallback Strategy

The stack should support graceful degradation.

### If CV fails

Use `GET /scene/demo` and keep the same recommendation pipeline.

### If live camera fails

Use a pre-captured scene image and fixture detections.

### If CASTNET processing is incomplete

Use `demo_profile.json` and explain that it is a processed CASTNET-derived profile.

### If LLM explanation fails

Use `explanations.py` template output.

### If integration becomes unstable

Use `POST /demo/run` as the single frontend call.

---

## What Not To Build

Do not build these during the hackathon unless everything else is already finished:

- login or user accounts
- database persistence
- multi-location search
- production deployment pipeline
- full CASTNET ingestion service
- custom model training
- autonomous agents
- complex mobile packaging
- multi-page application
- advanced LLM chat

These do not materially improve the 3-minute pitch.

---

## Build Order

### 1. Backend contract

Create schemas, fixtures, health endpoint, context endpoint, and recommendation endpoint.

### 2. Policy engine

Implement deterministic ranking with reason tags and template explanations.

### 3. Frontend integration

Render the context, scene, detections, recommendations, and explanation.

If Lovable is used, start from the UI described in `docs/interface-concept.md` and generate the actual demo screen first. Replace mocked data with backend calls once Piero's API contract is stable.

### 4. CV integration

Wire YOLO output into the normalized scene schema. Keep fixture detections available for demo safety. Add Boxer only if the core demo is already stable.

### 5. Demo hardening

Add fixture fallback, rescan fixture, backup screenshot, and README setup instructions.

---

## Final Stack Summary

The fastest reliable stack is:

```text
Frontend: React + Vite + TypeScript + Tailwind
Backend:  Python + FastAPI + Pydantic
Data:     Static CASTNET-derived JSON profiles
CV:       YOLO primary, fixture fallback, Boxer optional stretch
Policy:   Deterministic Python scoring module
LLM:      Gemini first, OpenAI second, template fallback through LLMProvider
3D UI:    Optional React Three Fiber polish only after 2D flow works
Deploy:   Local demo first, optional Vercel only after core works
```

This stack gives Aeris the best chance to ship a complete, judge-readable demo by the HackAugie deadline.
