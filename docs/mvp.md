# MVP+

## Goal

The Aeris MVP+ should deliver one polished end-to-end demo that clearly shows:

1. **CASTNET-based environmental context**
2. **live 2D scene perception with YOLO**
3. **asynchronous agentic recommendations**
4. **a clear sustainability use case**

The MVP+ is not a full environmental adaptation platform. It is a focused demo showing that Aeris can watch an outdoor setup, detect resources, and asynchronously recommend what should be protected first.

---

## Final MVP Definition

Aeris uses a **CASTNET-informed pollution exposure profile** plus **YOLO scene perception** to create a structured snapshot of visible outdoor resources. An **agentic reasoning layer** then uses that snapshot to recommend what should be **protected, moved, covered, or deprioritized first**.

For HackAugie, the product is scoped to:

- one domain: outdoor resource protection
- one demo scene
- one live or fixture-backed YOLO perception path
- one asynchronous agentic decision path
- one clean phone-style interface

---

## Demo Use Case

A user has a small outdoor or semi-outdoor setup containing exposed resources.

Aeris:

1. loads environmental exposure context
2. keeps the camera/scene view live
3. detects visible resources with YOLO
4. creates a stable scene snapshot
5. starts an async agentic reasoning job
6. updates the recommendation when reasoning completes

Example scene:

- seed tray
- battery pack
- metal tool
- tarp
- storage bin
- water jug
- gloves
- one irrelevant item

Example output:

- Protect the seed tray first
- Move the battery pack into storage
- Use the tarp if time allows
- Leave the water jug for later

---

## Must-Have Features

### 1. Fixed Context

The system must load a structured environmental profile derived from CASTNET.

At minimum:

- demo location
- CASTNET site/profile identifier
- ozone risk
- deposition risk
- active risk mode
- short summary

### 2. Live 2D Scene Perception

The system must analyze a scene and identify relevant resources.

Primary:

- YOLO
- bounding boxes
- object labels
- confidence values

Fallback:

- fixture detections from a backup demo image

The output must produce:

- object names
- confidence
- approximate distance or reachability
- optional bounding box

### 3. Async Agentic Recommendation Engine

The main recommendation path should be an LLM-based agentic decision layer.

Primary:

- Gemini

Fallback:

- OpenAI
- local template/fallback policy if providers fail

The agent must be bounded:

- only rank detected objects
- only use allowed action types
- return structured JSON
- avoid raw video reasoning

### 4. UI

The demo must show:

- live or simulated camera scene
- visible detection overlays
- environmental context card
- current reasoning state
- latest completed recommendation
- explanation text

### 5. Sustainability-Clear Output

The recommendations must clearly preserve resources under environmental stress.

---

## MVP+ Extras

Only after the core flow works:

- rescan/update after an object moves
- missing protection insight
- second environmental mode
- richer agent explanation
- small 3D scene map

---

## Non-Goals

- full environmental forecasting
- database persistence
- auth
- calling the LLM on every video frame
- full 3D world modeling
- perfect physical simulation
- production-ready CASTNET ingestion
- mobile packaging unless trivial

---

## Success Criteria

The MVP+ is successful if a judge can immediately see:

1. CASTNET context is visible and meaningful
2. YOLO/scene perception identifies real resources
3. camera/scene UI stays responsive
4. agentic reasoning updates recommendations asynchronously
5. recommendations are concrete and sustainability-focused

---

## Locked Scope

### Domain

Outdoor resource protection under pollution-related environmental stress.

### Objects

Maximum of 7-8 objects in the demo scene.

### Context Modes

Start with one mode:

- `protect_plants_and_sensitive_equipment`

Optional second mode:

- `general_outdoor_protection`

### Screens

One screen.

### Demo Loop

```text
live scene -> YOLO detections -> analyze scene -> latest recommendation
```

---

## Core Taxonomy

Primary objects:

- `seed_tray`
- `battery_pack`
- `metal_tool`
- `tarp`
- `storage_bin`
- `water_jug`
- `gloves`

Optional:

- `plant_pot`
- `electronics_case`

Low-priority dummy:

- `misc_item`

---

## Recommendation Categories

The agent should choose from:

- `protect_first`
- `move_to_storage`
- `cover_if_time_allows`
- `low_priority`

Keep action vocabulary minimal and readable.

---

## Team Deliverables

### Chau

- phone-style live scene UI
- detection overlays
- current analysis/pending state
- latest recommendation display
- Lovable first pass if useful

### Gallo

- YOLO detection pipeline
- label normalization
- normalized scene output
- fixture fallback

### Shuja

- CASTNET profile simplification
- agent prompt/schema
- fallback policy support
- explanation quality

### Piero

- FastAPI backend
- async analysis job contract
- schemas
- provider wrappers
- latest recommendation state
- integration stability

---

## Build Order

### Phase 1

- backend contracts
- fixtures
- context endpoint
- scan-frame endpoint
- async analysis job endpoint

### Phase 2

- YOLO adapter
- Gemini/OpenAI provider stubs
- fallback policy
- latest recommendation state

### Phase 3

- frontend live scene UI
- detection overlay integration
- async analysis polling
- recommendation panel

### Phase 4

- demo hardening
- backup frame
- recorded clip
- README/setup polish

---

## Fallback Rules

### If YOLO is unstable

Use fixture detections from the backup demo frame.

### If live camera is unstable

Use uploaded image or pre-captured frame.

### If Gemini is slow

Keep the latest completed recommendation visible.

### If Gemini fails

Try OpenAI.

### If all LLM providers fail

Use fallback policy/template output.

The system must always prioritize demo stability over technical purity.

---

## One-Sentence MVP+ Definition

**Aeris MVP+ is a CASTNET-driven sustainability demo that keeps scene perception live with YOLO and asynchronously uses an agentic reasoning layer to recommend what outdoor resources should be protected first.**
