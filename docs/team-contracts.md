# Team Contracts

## Purpose

This document is the handoff contract for the team.

Each person should know:

- what they own
- what they receive as input
- what they must output
- which file or endpoint the next person depends on

The goal is to prevent integration confusion during the final hackathon sprint.

---

## System Contract Summary

```text
Frontend camera/demo frame
        |
        v
sampled frame or fixture request
        |
        v
CV / YOLO adapter
        |
        v
DynamicContext
        |
        v
Backend async analysis job
        |
        v
Agentic decision layer
        |
        v
RecommendationOutput
        |
        v
Frontend advice card
```

The camera stream should stay local and smooth. The backend returns detections and advice state whenever those are ready.

---

## Shared Schemas

These schema names are the integration boundary. Do not rename fields casually.

### `FixedContext`

Producer:

- Shuja / Data
- Piero / Backend

Consumer:

- Agentic decision layer
- Frontend context panel

Shape:

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

### `DynamicContext`

Producer:

- Gallo / CV
- fixture fallback

Consumer:

- Piero / Backend
- Shuja / Agent prompt/schema
- Chau / Frontend overlays

Shape:

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

### `RecommendationOutput`

Producer:

- Gemini agent
- OpenAI fallback
- local fallback policy

Consumer:

- Frontend advice card
- demo script

Shape:

```json
{
  "decision_source": "agentic_gemini",
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
  "explanation": "Aeris recommends protecting the seed tray first because CASTNET-derived context indicates elevated plant-sensitive exposure.",
  "missing_insights": []
}
```

Allowed `action` values:

- `protect_first`
- `move_to_storage`
- `cover_if_time_allows`
- `low_priority`

Allowed `decision_source` values:

- `agentic_gemini`
- `agentic_openai`
- `fallback_policy`

---

## Chau / Frontend Contract

### Owns

- React/Lovable UI
- camera or demo frame display
- box overlay rendering
- user controls
- polling analysis jobs
- advice card rendering

### Inputs

From backend:

- `GET /context/demo` -> `FixedContext`
- `POST /scan-frame` -> `DynamicContext`
- `POST /analyze-scene` -> `AnalysisJobResponse`
- `GET /analysis/{job_id}` -> `AnalysisJobResponse`
- `GET /analysis/latest` -> latest completed recommendation

Optional fallback:

- `GET /scene/demo`
- `POST /demo/run`

### Outputs

To backend:

For backend YOLO:

- sampled camera frame to `/scan-frame` once implemented with image upload

For fixture or browser-side detection:

- `DynamicContext` JSON to `/analyze-scene`

For MVP, if image upload is not ready, use fixture detections and send that `DynamicContext`.

### Must Do

- keep camera/video display smooth
- never block video on YOLO or LLM
- draw boxes from `bbox`
- show object labels and confidence
- show CASTNET context
- show agent status
- keep latest advice visible while a new job is pending
- poll analysis jobs until complete or failed
- keep demo-frame fallback working

### Must Not Do

- call Gemini/OpenAI directly from the browser
- expose API keys
- send every camera frame
- start a new detection request while the previous one is pending
- rename backend fields without telling Piero
- build a landing page instead of the demo screen

### Frontend State Checklist

```text
cameraStatus: idle | starting | live | fallback
detectionStatus: idle | detecting | detected | stale | failed
analysisStatus: idle | pending | complete | failed
environmentMode: indoor | outdoor
objects: SceneObject[]
latestAdvice: RecommendationOutput | null
```

---

## Gallo / CV Contract

### Owns

- YOLO model path
- label normalization
- confidence filtering
- bounding box output
- fixture fallback if live YOLO is unstable

### Inputs

From frontend/backend:

- sampled image frame
- image width
- image height

From data/team:

- object taxonomy

### Outputs

To backend/frontend:

- `DynamicContext`

Required object fields:

```json
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
```

### Label Normalization

Map detector labels to Aeris labels:

```text
potted plant / plant / seedling tray -> seed_tray or plant_pot
battery / power bank                -> battery_pack
tool / wrench / shovel              -> metal_tool
tarp / cloth / cover                -> tarp
box / bin                           -> storage_bin
bottle / jug                        -> water_jug
glove                               -> gloves
unknown                             -> misc_item
```

### Must Do

- return boxes in the same coordinate space as the sampled frame
- include confidence scores
- keep output schema stable
- keep fixture output available

### Must Not Do

- call LLMs
- decide sustainability advice
- block frontend work if live YOLO is not ready

---

## Piero / Backend Contract

### Owns

- FastAPI app
- schema definitions
- context loading
- scan-frame contract
- async analysis jobs
- latest recommendation state
- provider wrappers
- fallback policy

### Inputs

From frontend:

- frame sample or fixture request to `/scan-frame`
- `DynamicContext` to `/analyze-scene`
- optional provider choice: `gemini | openai | template`

From data:

- `data/castnet/processed/demo_profile.json`

From CV:

- normalized `DynamicContext`

### Outputs

To frontend:

- `FixedContext`
- `DynamicContext`
- `AnalysisJobResponse`
- `LatestAnalysisResponse`
- `RecommendationOutput`

### Primary Endpoints

```text
GET  /health
GET  /context/demo
POST /scan-frame
POST /analyze-scene
GET  /analysis/{job_id}
GET  /analysis/latest
```

### Fallback / Compatibility Endpoints

```text
GET  /scene/demo
GET  /scene/demo-after-move
POST /demo/run
POST /recommend
```

### Must Do

- keep `/scan-frame` fast
- keep `/analyze-scene` async
- keep latest completed recommendation available
- return pending/complete/failed status clearly
- fall back from Gemini to OpenAI to local fallback policy
- never require the frontend to wait on the LLM before rendering detections

### Must Not Do

- call the LLM on every frame
- store video frames unless necessary
- break fixture fallback
- expose provider-specific details in frontend contracts

---

## Shuja / Data + Agent Contract

### Owns

- CASTNET profile simplification
- agent prompt design
- output schema expectations
- fallback advice quality
- data story for judges

### Inputs

From data:

- CASTNET fields / processed profile

From backend:

- `FixedContext`
- `DynamicContext`
- allowed actions
- provider wrapper input

### Outputs

To backend:

- refined `demo_profile.json`
- agent prompt text / rules
- reason tags
- fallback advice templates if needed

To presentation:

- short explanation of why CASTNET changes advice
- Data Insight framing

### Must Do

- keep CASTNET visibly tied to advice
- keep prompts schema-bounded
- keep object/action vocabulary small
- make same object + different environmental context produce different advice

### Must Not Do

- ask the LLM to reason from raw video
- invent unsupported environmental claims
- overbuild CASTNET ingestion during MVP

---

## Event Trigger Contract

The event policy decides **when** to ask the agent, not what the final advice is.

Recommended triggers:

- user taps Analyze Scene
- object set changes meaningfully
- object remains stable for 2-3 sampled frames
- indoor/outdoor mode changes
- CASTNET/weather mode changes
- cooldown expires

Recommended cooldown:

```text
20 seconds per advice key
```

Example advice key:

```text
outdoor_high_ozone:seed_tray,battery_pack,tarp
```

---

## Coordinate Contract

Bounding boxes must be relative to the sampled image size.

If backend receives:

```json
{
  "image_width": 640,
  "image_height": 360
}
```

then boxes must use that same coordinate system.

Frontend scales them:

```text
display_x = bbox.x / image_width * displayed_video_width
display_y = bbox.y / image_height * displayed_video_height
```

Precaution:

- avoid `object-fit: cover` unless crop offsets are handled
- prefer `object-fit: contain` or match canvas/video dimensions exactly

---

## MVP Integration Rule

If anything is unstable, fall back in this order:

```text
live YOLO -> fixture detections
Gemini -> OpenAI -> fallback policy
camera -> demo frame
```

Do not block the demo on a single failing component.
