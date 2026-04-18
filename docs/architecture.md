# Architecture

## Overview

Aeris is built around a simple core pipeline:

**Fixed Context + Dynamic Context -> Policy Engine -> Action Recommendations**

The system combines environmental exposure context derived from CASTNET with scene understanding from camera input, then produces ranked recommendations for what outdoor resources should be protected first.

---

## System Goals

The architecture is designed to satisfy five goals:

1. **Use CASTNET as a core input**
2. **Use scene understanding to analyze real visible resources**
3. **Rank actions deterministically**
4. **Use the LLM only for explanation, not core decision-making**
5. **Stay small enough to ship during the hackathon**

---

## High-Level Flow

```text
CASTNET-derived context
        +
 optional weather/context
        ↓
   Fixed Context
        +
camera feed → object detection / spatial estimation
        ↓
   Dynamic Context
        ↓
    Policy Engine
        ↓
Ranked Actions + Explanation
        ↓
        UI
````

---

## Core Architectural Components

### 1. Fixed Context Engine

The Fixed Context Engine is responsible for building a structured environmental exposure profile for the current location or demo setting.

Its job is to answer:

* what type of environmental stress matters here?
* how strong is that stress?
* what kinds of resources are likely to be vulnerable?

### Inputs

* processed CASTNET-derived data
* selected demo location / nearest CASTNET site
* optional weather or condition enrichments if available

### Outputs

* environmental mode
* risk summary
* vulnerability emphasis

### Example output

```json
{
  "location": "Demo Location",
  "castnet_site": "Example Site",
  "pollution_profile": {
    "ozone_risk": "high",
    "deposition_risk": "medium"
  },
  "risk_mode": "protect_plants_and_sensitive_equipment",
  "summary": "Elevated outdoor exposure conditions for plants and sensitive equipment."
}
```

---

### 2. Dynamic Context Engine

The Dynamic Context Engine is responsible for analyzing the visible scene and translating it into a structured scene state.

Its job is to answer:

* what objects are present?
* where are they approximately?
* are they reachable?
* which ones are exposed?
* which ones are protection-enabling objects?

### Inputs

* live camera frame or uploaded image
* object detector output
* optional spatial heuristics

### Outputs

* normalized object list
* confidence values
* rough spatial attributes

### Detection strategy

Primary:

* **YOLO**
* bounding-box and frame-position heuristics for approximate spatial reasoning

Optional stretch:

* **Boxer**, only if it is already stable and does not slow down integration

### Example output

```json
{
  "objects": [
    {
      "name": "seed_tray",
      "distance": 1.0,
      "reachable": true,
      "confidence": 0.94
    },
    {
      "name": "battery_pack",
      "distance": 1.8,
      "reachable": true,
      "confidence": 0.89
    },
    {
      "name": "metal_tool",
      "distance": 2.2,
      "reachable": true,
      "confidence": 0.85
    }
  ]
}
```

---

### 3. Policy Engine

The Policy Engine is the core decision layer.

It consumes Fixed Context and Dynamic Context, then ranks actions such as:

* protect first
* move next
* cover if time allows
* low priority

This component must be **deterministic** and should not depend on open-ended LLM reasoning.

### Why deterministic

For the hackathon demo, the project is stronger if the reasoning path is inspectable and grounded in explicit logic.

That makes the output:

* easier to debug
* easier to explain
* easier to trust
* more stable under demo pressure

### Core scoring logic

The engine should combine factors such as:

* environmental vulnerability of object type
* value of protecting the object
* distance or reachability cost
* urgency implied by current mode
* whether an item enables protection of others

### Example conceptual scoring

```text
priority_score =
  vulnerability_weight(object_type, risk_mode)
  + protection_value_weight(object_type)
  + enabling_weight(object_type)
  - distance_cost
  - handling_cost
```

### Example policy intuition

In `protect_plants_and_sensitive_equipment` mode:

* seed tray: very high priority
* battery pack: high priority
* tarp: high priority if it can protect multiple assets
* storage bin: high priority if it enables coverage/storage
* metal tools: medium priority
* water jug: lower priority
* irrelevant object: very low priority

---

### 4. Explanation Layer

The Explanation Layer converts structured recommendations into natural language.

This layer is where the LLM is used.

Its role is limited to:

* explaining ranked actions
* generating clean recommendation text
* optionally answering small follow-up questions

The LLM should **not** decide the ranking itself.

### Input to the LLM

* fixed context summary
* dynamic context summary
* policy engine output

### Output from the LLM

* short recommendation paragraph
* human-readable rationale

### Example explanation

> Current environmental conditions increase exposure risk for sensitive outdoor resources. Protect the seed tray first, then move the battery pack into storage. Cover the metal tools if time allows.

---

### 5. Frontend

The Frontend is a single-screen interface optimized for immediate judge comprehension.

Its job is to make the following visible at a glance:

* environmental context
* camera scene
* detected objects
* ranked actions
* explanation

### Recommended layout

```text
[ Camera / scene scan ]   [ Environmental Context ]
                          [ Top Actions ]
                          [ Why These Actions ]
```

### Core frontend responsibilities

* show input scene
* render bounding boxes / labels
* show fixed context card
* show ranked recommendations
* support “scan” and optional “rescan”

---

### 6. Backend API Layer

The Backend API Layer coordinates the application flow.

It should expose clean endpoints for:

* fixed context retrieval
* scene scan processing
* recommendation generation

The backend should own:

* schemas
* orchestration
* integration between CV, context, and ranking logic

---

## Data Flow

### Step 1 — Load Fixed Context

The frontend requests a CASTNET-informed environmental profile from the backend.

### Step 2 — Scan Scene

The frontend sends a frame or image reference to the backend or CV service.

### Step 3 — Build Dynamic Context

The CV pipeline detects objects and estimates enough spatial information for prioritization.

### Step 4 — Rank Actions

The backend passes fixed + dynamic context into the policy engine.

### Step 5 — Generate Explanation

The structured ranking is passed to the explanation layer.

### Step 6 — Render Results

The frontend displays recommendations and rationale.

---

## Component Responsibilities

### Frontend

* camera UI
* rendering detections
* displaying recommendations
* triggering scan / rescan

### Backend

* endpoint management
* schema validation
* service orchestration
* policy engine execution

### CV Module

* object detection
* normalization into dynamic context
* distance/reachability estimation

### Data Module

* CASTNET preprocessing
* environmental profile lookup
* location/site mapping

### LLM Module

* explanation only
* no core ranking logic

---

## Core Schemas

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
  "objects": [
    {
      "name": "string",
      "distance": 0.0,
      "reachable": true,
      "confidence": 0.0
    }
  ]
}
```

### Recommendation Output

```json
{
  "actions": [
    {
      "rank": 1,
      "action": "protect",
      "target": "seed_tray",
      "reason_tags": ["high_vulnerability", "high_priority", "reachable"]
    },
    {
      "rank": 2,
      "action": "move_to_storage",
      "target": "battery_pack",
      "reason_tags": ["sensitive_equipment", "moderate_distance"]
    }
  ],
  "explanation": "string"
}
```

---

## Detection and Spatial Reasoning Strategy

### Primary path: YOLO

YOLO is the primary path because it is faster to integrate, easier to test, and more reliable under hackathon time pressure.

Use YOLO to detect the small fixed object taxonomy, then add approximate spatial reasoning with:

* bounding-box size
* frame position
* scene heuristics
* optional lightweight depth cues if easy

### Important principle

Aeris does **not** require perfect 3D reconstruction.

It requires enough spatial information to support practical prioritization.

### Optional path: Boxer

Boxer can remain a stretch option if it becomes stable quickly, but it should not block the demo. The system contract should stay the same regardless of whether detections come from YOLO, Boxer, or a fixture.

---

## Architectural Constraints

To keep the project buildable within the hackathon:

* one scene only
* one core domain only
* small object taxonomy
* deterministic recommendation logic
* no complex forecasting pipeline
* no open-ended autonomous agent loop
* no large environmental simulation layer

This is an MVP+ architecture, not a full production system.

---

## Failure and Fallback Design

### If CASTNET processing is too heavy

Fallback to a preprocessed small environmental profile lookup table derived from CASTNET for the demo location(s).

### If YOLO is unstable

Fallback immediately to pre-captured demo-frame detections while keeping the same recommendation pipeline.

### If live camera is unstable

Allow image upload or fixed demo frames while keeping the same recommendation pipeline.

### If LLM explanation becomes brittle

Use template-based explanations generated from policy tags.

The demo must remain stable even if advanced components fail.

---

## Why This Architecture Works

This architecture is strong because it separates the system into interpretable layers:

* **Fixed Context** tells us what kind of environmental stress matters
* **Dynamic Context** tells us what resources are actually present
* **Policy Engine** decides what action matters most
* **LLM** makes the output readable

That separation makes Aeris:

* easier to build quickly
* easier to demo
* easier to defend technically
* easier to explain to judges

---

## One-Sentence Architecture Summary

**Aeris combines CASTNET-derived environmental context with scene understanding and a deterministic policy engine to recommend what outdoor resources should be protected first.**

