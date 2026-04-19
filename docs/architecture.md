# Architecture

## Overview

Aeris is built around a live-perception plus asynchronous-reasoning pipeline:

```text
Live camera stream
        |
        v
YOLO 2D object detection
        |
        v
Stable scene snapshot
        |
        v
Async agentic decision job
        |
        v
Latest protection recommendation
```

The camera stream should never wait for the LLM. YOLO updates the visible scene state quickly, while Gemini/OpenAI reason asynchronously over the latest structured scene snapshot and CASTNET context.

---

## System Goals

The architecture is designed to satisfy six goals:

1. **Keep the phone-style camera stream smooth**
2. **Use YOLO for 2D object detection**
3. **Use CASTNET as the environmental context**
4. **Use an agentic LLM decision layer for ranking and recommendations**
5. **Keep all LLM output bounded by schemas and allowed actions**
6. **Preserve fixture/template fallbacks for demo safety**

The key principle:

> Real-time perception and agentic reasoning run at different speeds.

---

## High-Level Flow

```text
CASTNET-derived context
        |
        v
Fixed Context

Live camera stream
        |
        v
YOLO every N frames / seconds
        |
        v
Dynamic Context snapshot
        |
        v
POST /analyze-scene starts async agent job
        |
        v
Gemini primary / OpenAI fallback / template fallback
        |
        v
Latest Recommendation State
        |
        v
UI updates recommendation panel when complete
```

The UI can continue rendering the live camera and detection overlays while the agent is still reasoning.

---

## Core Architectural Components

### 1. Fixed Context Engine

The Fixed Context Engine loads a structured environmental exposure profile derived from CASTNET.

Its job is to answer:

- what environmental stress matters here?
- how strong is that stress?
- what resource categories should the agent care about?

### Inputs

- processed CASTNET-derived data
- selected demo location / nearest CASTNET site

### Outputs

- demo location
- CASTNET profile/site
- ozone risk
- deposition risk
- active risk mode
- short summary

### Example

```json
{
  "location": "Outdoor Garden Demo",
  "castnet_site": "Demo CASTNET Profile",
  "pollution_profile": {
    "ozone_risk": "high",
    "deposition_risk": "medium"
  },
  "risk_mode": "protect_plants_and_sensitive_equipment",
  "summary": "Elevated ozone and environmental exposure conditions for outdoor plants and sensitive equipment."
}
```

---

### 2. Live Perception Layer

The live perception layer is responsible for turning a camera frame into a normalized 2D scene snapshot.

Primary implementation:

- **YOLO**
- 2D bounding boxes
- confidence scores
- label normalization
- lightweight distance / reachability heuristics

Optional stretch:

- Boxer, only if stable without slowing the demo

The perception layer should run faster than the reasoning layer. It should update labels/boxes without waiting for the LLM.

### Output Shape

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

### 3. Scene State Builder

The Scene State Builder converts noisy detections into the snapshot used for reasoning.

It should:

- normalize labels into the fixed object taxonomy
- filter low-confidence detections
- estimate rough distance/reachability
- decide when the scene has changed meaningfully
- avoid triggering agent calls for every video frame

Recommended trigger rules:

- user taps **Analyze**
- object set changes meaningfully
- detection state stays stable across 2-3 YOLO snapshots
- at least 5-10 seconds have passed since the last reasoning job

This prevents the LLM from being called too often.

---

### 4. Agentic Decision Layer

The Agentic Decision Layer is the main recommendation engine.

It consumes:

- Fixed Context from CASTNET
- Dynamic Context from YOLO
- allowed object names
- allowed action vocabulary
- output schema

It returns:

- ranked actions
- target objects
- concise reasons
- explanation text

Primary provider:

- Gemini

Secondary provider:

- OpenAI

Fallback:

- template/fallback policy output

The LLM should make ranking decisions from structured scene state, not raw video.

### Bounded Output Schema

```json
{
  "actions": [
    {
      "rank": 1,
      "action": "protect_first",
      "target": "seed_tray",
      "reason": "Plant-sensitive resource under elevated ozone exposure."
    }
  ],
  "explanation": "Aeris recommends protecting the seed tray first because CASTNET-derived context indicates elevated plant-sensitive exposure."
}
```

Allowed actions:

- `protect_first`
- `move_to_storage`
- `cover_if_time_allows`
- `low_priority`

Allowed targets:

- only objects detected in the current scene snapshot

---

### 5. Fallback Policy Layer

The fallback policy is not the main product story.

Its job is to keep the demo alive if:

- Gemini is slow or unavailable
- OpenAI is unavailable
- network access fails
- the agent returns invalid JSON

The fallback policy may use simple local scoring and template explanations, but the UI/pitch should frame it as a safety fallback, not the core decision engine.

---

### 6. Frontend

The frontend should behave like a phone-style live scene analyzer:

- camera stream remains live
- YOLO boxes update independently
- recommendation panel shows latest completed decision
- pending agent jobs show a lightweight "reasoning..." state
- the UI never freezes while the LLM is running

Recommended visible states:

```text
Watching scene...
Objects detected
Reasoning over latest scene...
Recommendation updated
Using fallback recommendation
```

---

### 7. Backend API Layer

The backend owns:

- schemas
- CASTNET context loading
- YOLO scan adapter
- scene snapshot contracts
- async analysis jobs
- latest recommendation state
- provider abstraction
- fallback behavior

---

## API Flow

### Fast Perception Path

```text
POST /scan-frame
```

Returns the latest normalized YOLO detections quickly.

For the hackathon scaffold, this can return fixture detections until YOLO is wired.

### Async Reasoning Path

```text
POST /analyze-scene
```

Starts an asynchronous agentic reasoning job and immediately returns a `job_id`.

The camera UI should continue running.

### Polling Path

```text
GET /analysis/{job_id}
GET /analysis/latest
```

Returns pending, complete, or failed state.

The UI displays the latest completed recommendation when available.

---

## Core Schemas

See `docs/team-contracts.md` for the team handoff version of these schemas.

### Fixed Context

```json
{
  "location": "string",
  "castnet_site": "string",
  "pollution_profile": {
    "ozone_risk": "low|medium|high",
    "deposition_risk": "low|medium|high"
  },
  "risk_mode": "string",
  "summary": "string"
}
```

### Dynamic Context

```json
{
  "source": "yolo|fixture",
  "objects": [
    {
      "name": "string",
      "confidence": 0.0,
      "distance": 0.0,
      "reachable": true,
      "bbox": {
        "x": 0,
        "y": 0,
        "width": 0,
        "height": 0
      }
    }
  ]
}
```

### Analysis Job

```json
{
  "job_id": "string",
  "status": "pending|complete|failed",
  "recommendations": null
}
```

### Recommendation Output

```json
{
  "decision_source": "agentic_gemini|agentic_openai|fallback_policy",
  "actions": [
    {
      "rank": 1,
      "action": "protect_first",
      "target": "seed_tray",
      "score": null,
      "reason_tags": ["plant_sensitive", "high_ozone_context"],
      "reason": "Plant-sensitive resource under elevated ozone exposure."
    }
  ],
  "explanation": "string"
}
```

---

## Failure and Fallback Design

### If YOLO is unstable

Use fixture detections from a pre-captured demo frame.

### If live camera is unstable

Use a pre-captured demo image while preserving the same scene snapshot schema.

### If Gemini is slow

Keep the latest completed recommendation visible and show a pending reasoning state.

### If Gemini fails

Try OpenAI.

### If all LLM providers fail

Use fallback policy/template output.

### If no recommendation is ready

Show detections and a "reasoning over latest scene" state.

---

## Why This Architecture Works

This architecture resolves the core hackathon contradiction:

- live camera and YOLO perception need to feel real-time
- LLM reasoning will be slower and should be asynchronous
- the UI should never block on reasoning
- agentic decision-making remains the main story
- fallback logic keeps the demo stable

One-sentence architecture summary:

**Aeris keeps camera perception live with YOLO, then asynchronously uses CASTNET context and an agentic LLM decision layer to recommend what outdoor resources should be protected first.**
