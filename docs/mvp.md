# MVP+

## Goal

The goal of the Aeris MVP+ is to deliver one polished end-to-end demo that clearly shows:

1. **CASTNET-based environmental context**
2. **real scene understanding**
3. **ranked action recommendations**
4. **a clear sustainability use case**

The MVP+ is not meant to solve all of environmental adaptation. It is meant to demonstrate a strong, understandable, technically coherent product in a single focused scenario.

---

## Final MVP Definition

### Aeris MVP+
Aeris uses a **CASTNET-informed pollution exposure profile** plus **scene understanding** to recommend what outdoor resources should be **protected, moved, covered, or deprioritized first**.

For HackAugie, the product is scoped to:

- one domain: outdoor resource protection
- one demo scene
- one recommendation engine
- one primary environmental mode
- one clean user interface

---

## Demo Use Case

### Use Case
A user has a small outdoor or semi-outdoor setup containing exposed resources.

Aeris:
1. loads environmental exposure context
2. scans the scene
3. identifies resources
4. ranks the best next protective actions

### Example scene
- seed tray
- battery pack
- metal tool
- tarp
- storage bin
- water jug
- gloves
- one irrelevant item

### Example output
- Protect the seed tray first
- Move the battery pack into storage
- Cover the metal tools if time allows
- Leave the water jug for later

---

## Must-Have Features

These are required for the MVP+.

### 1. Fixed Context
The system must load a structured environmental profile derived from CASTNET.

At minimum, this profile should include:
- demo location
- CASTNET site or profile identifier
- pollution stress summary
- risk mode

### 2. Scene Understanding
The system must analyze a real scene and identify relevant resources.

Preferred:
- Boxer

Fallback:
- YOLO

The output must produce:
- object names
- confidence
- approximate distance or reachability signal

### 3. Deterministic Recommendation Engine
The system must rank actions in a stable and inspectable way.

At minimum, Aeris must output:
- top ranked action
- second action
- optional “if time allows” action
- short justification

### 4. UI
The demo must show:
- environmental context card
- scene scan panel
- visible detections
- ranked recommendations
- explanation text

### 5. Sustainability-Clear Output
The output must clearly preserve resources under environmental stress.

The recommendations should feel like:
- real protection actions
- resource preservation logic
- environmental adaptation decisions

---

## MVP+ Extras

These are desirable, but only after core functionality works.

### A. Rescan / Update
If a user moves one item, Aeris updates the recommendations.

### B. Missing Protection Insight
Example:
> No tarp detected. Protection options are limited.

### C. Two Protection Modes
If easy, support:

- `protect_plants_and_sensitive_equipment`
- `general_outdoor_protection`

### D. Better Explanation Layer
A slightly richer explanation that references:
- environmental mode
- object sensitivity
- reachability

---

## Non-Goals

These are explicitly out of scope.

- full environmental forecasting
- autonomous long-horizon planning
- route planning
- packing/travel logic
- evacuation logic
- healthcare workflows
- many scenes
- many user types
- full 3D world modeling
- perfect physical simulation
- production-ready dataset ingestion pipeline
- mobile deployment packaging unless trivial

---

## Success Criteria

The MVP+ is successful if a judge can immediately see:

### 1. Environmental Data Matters
The system is clearly driven by environmental context, not just object detection.

### 2. CASTNET Is Present
The product visibly uses a CASTNET-based environmental profile as part of the decision pipeline.

### 3. Scene Understanding Matters
The scene scan is not cosmetic. It changes what Aeris recommends.

### 4. The Output Is Actionable
The system does not just classify or label. It recommends what to do first.

### 5. The Sustainability Story Is Obvious
Aeris protects resources and reduces avoidable degradation.

---

## Locked Scope

### Domain
Outdoor resource protection under pollution-related environmental stress.

### Objects
Maximum of **7–8 objects** in the demo scene.

### Context Modes
Maximum of **2 modes**.

### Screens
One screen.

### Demo Loop
One simple scan -> recommend -> optional rescan flow.

---

## Core Taxonomy

### Primary objects
- `seed_tray`
- `battery_pack`
- `metal_tool`
- `tarp`
- `storage_bin`
- `water_jug`
- `gloves`

### Optional
- `plant_pot`
- `electronics_case`

### Low-priority dummy item
- `misc_item`

Keep the taxonomy small and stable.

---

## Environmental Modes

### Mode 1 — `protect_plants_and_sensitive_equipment`
Primary mode for the demo.

This mode prioritizes:
- plant-related resources
- sensitive electronics
- protection-enabling objects like tarps and bins

### Mode 2 — `general_outdoor_protection`
Optional secondary mode if time allows.

This mode uses more general resource-preservation logic.

---

## Recommendation Categories

The recommendation engine should output from this small action set:

- `protect_first`
- `move_to_storage`
- `cover_if_time_allows`
- `low_priority`

Keep the action vocabulary minimal and readable.

---

## Minimum Data Requirements

For the hackathon, Aeris does not need a full live environmental modeling pipeline.

It only needs:

- a small processed CASTNET-based profile
- enough environmental logic to produce a valid mode and summary
- a visible connection between CASTNET context and recommendations

This can be done through:
- a preprocessed lookup file
- a reduced dataset
- a small number of demo location profiles

---

## Minimum CV Requirements

The scene analyzer does not need perfect reconstruction.

It only needs enough signal to support:
- object identification
- approximate closeness/reachability
- visibly grounded recommendations

This means:
- Boxer is ideal
- YOLO fallback is acceptable
- approximate spatial reasoning is enough

---

## Recommendation Logic Requirements

The recommendation engine must be deterministic.

At minimum, scoring should account for:
- vulnerability under current environmental mode
- value of protecting the object
- distance/reachability penalty
- enabling value of protection tools like tarps or bins

### Example intuition
In plant-sensitive mode:

- seed tray should rank very high
- battery pack should rank high
- tarp/storage bin should gain value if they enable protection
- metal tool should rank medium
- water jug should rank lower
- irrelevant item should rank near zero

---

## Demo Requirements

The final demo must include:

### 1. Environmental Context View
A visible fixed-context panel showing:
- location
- CASTNET profile/site
- pollution summary
- active mode

### 2. Scene Scan
A visible scene containing the demo objects.

### 3. Detection Overlay
Bounding boxes or labels over visible resources.

### 4. Ranked Action List
At least top 3 actions.

### 5. Explanation
A short paragraph explaining why those actions were chosen.

### 6. Sustainability Interpretation
The recommendations must clearly preserve resources under environmental exposure.

---

## Polish Priorities

If core functionality works early, spend the remaining time on:

### Highest-value polish
- UI readability
- explanation clarity
- object detection stability
- consistent recommendation ranking
- one strong rescan moment

### Lower-value polish
- complex animations
- fancy voice mode
- multiple pages
- extra user settings

---

## Team Deliverables

### Chau
- final app screen
- camera and UI flow
- visual hierarchy and polish

### Gallo
- object detection pipeline
- Boxer integration or YOLO fallback
- normalized scene output

### Shuja
- CASTNET simplification
- fixed-context builder
- recommendation logic
- explanation prompt

### Piero
- backend API
- schemas
- orchestration between modules
- integration and stability

---

## Build Order

### Phase 1
- scaffold repo
- define schemas
- define object taxonomy
- define environmental modes

### Phase 2
- build fixed context
- build scene analyzer
- build recommendation logic

### Phase 3
- connect backend and frontend
- render detections and recommendations

### Phase 4
- improve explanation quality
- polish UI
- prepare demo assets

---

## Fallback Rules

### If Boxer is unstable
Switch to YOLO immediately.

### If live camera is unstable
Use uploaded image or pre-captured frame.

### If CASTNET pipeline becomes too heavy
Use a reduced preprocessed environmental profile file.

### If LLM output is unstable
Use template-generated explanations.

The system must always prioritize demo stability over technical purity.

---

## One-Sentence MVP+ Definition

**Aeris MVP+ is a CASTNET-driven sustainability demo that scans an outdoor scene and recommends what resources should be protected first under pollution-related environmental stress.**