# Interface Concept

## Purpose

This document describes the recommended Aeris UI for the HackAugie demo.

The interface should make the core product idea immediately obvious:

> CASTNET environmental context + scene understanding -> ranked protection decisions.

The UI should not feel like a generic dashboard, a chatbot, or a full 3D simulation. It should feel like a focused field-operator interface for sustainability decisions.

Chau may use **Lovable** to generate the first frontend pass. If so, Lovable should generate the actual demo interface described here, not a landing page or marketing site.

---

## Design Goal

The UI has one job:

Help judges understand, in under one minute, that Aeris can look at an exposed outdoor setup and recommend what to protect first based on environmental context.

The screen should always answer three questions:

1. What environmental context is active?
2. What objects did Aeris see?
3. What should the user protect first?

---

## Recommended Layout

Use a single-screen split layout.

```text
+--------------------------------------------------------------+
| Aeris                                                        |
| Pollution-aware scene analyzer for outdoor resource protection|
+-------------------------------+------------------------------+
|                               | CASTNET Context              |
|  Scene / Camera View          | +--------------------------+ |
|                               | | Ozone Risk      High     | |
|  [image or camera frame]      | | Deposition Risk Medium   | |
|                               | | Mode: Protect plants     | |
|  bounding boxes on objects    | | and sensitive equipment  | |
|                               | +--------------------------+ |
|  seed tray                    |                              |
|  battery pack                 | Top Actions                  |
|  tarp                         | 1. Protect seed tray first   |
|  storage bin                  | 2. Move battery pack inside  |
|                               | 3. Use tarp if time allows   |
|                               |                              |
|                               | Why                          |
|                               | Current CASTNET-derived      |
|                               | conditions elevate risk for  |
|                               | plants and exposed equipment.|
+-------------------------------+------------------------------+
```

### Lovable Prompt Direction

If using Lovable, the prompt should be direct and demo-specific:

```text
Build a single-screen React/Vite/Tailwind demo UI for Aeris, a pollution-aware scene analyzer for outdoor resource protection.

The screen should feel like an environmental operations console, not a marketing landing page. Use a split layout: a large scene/camera panel on the left with detection boxes and object labels, and a right-side decision stack with CASTNET context, ranked protection actions, and a short explanation.

Use these visible sections:
- Header: Aeris, Pollution-aware scene analyzer for outdoor resource protection
- Scene Scan panel with Scan Scene, Use Demo Frame, and Rescan controls
- CASTNET Context panel showing Outdoor Garden Demo, Ozone Risk High, Deposition Risk Medium, Active Mode Protect Plants + Sensitive Equipment
- Top Actions panel with ranked actions for seed tray, battery pack, and tarp
- Why panel with a short explanation

Use a calm field-operator visual style: deep neutral background, off-white panels, green context accents, amber priority accents, blue scan status accents, and clear readable typography.

Do not create a landing page. Do not add pricing, testimonials, auth, navigation-heavy pages, or generic AI chat UI.
```

After generation, replace hardcoded mock data with calls to the backend API.

### Left Side

The left side is the scene scan area.

It should show:

- live camera feed or backup demo image
- detection boxes
- object labels
- confidence values if they do not clutter the view
- optional scan status

Example labels:

```text
seed_tray       94%
battery_pack    89%
metal_tool      84%
tarp            81%
storage_bin     78%
```

This is the "Aeris sees the scene" moment.

### Right Side

The right side is the decision stack.

It should show:

- CASTNET-derived environmental context
- active risk mode
- top ranked actions
- short explanation

This is the "Aeris turns data into action" moment.

---

## Visual Tone

The interface should feel like an environmental operations console.

Recommended tone:

- calm
- serious
- readable
- field-ready
- sustainability-focused
- technically credible

Avoid:

- playful game styling
- generic AI dashboard styling
- heavy glassmorphism
- full-screen gradients
- green-only palette
- chat-first UI

Suggested palette direction:

- deep neutral background
- off-white or light gray panels
- green accents for sustainability/context
- amber accents for priority/risk
- blue accents for scan/system state
- gray for low-priority objects

The UI should make resources and decisions feel important, not decorative.

---

## Main Components

### Header

The header should be short and direct.

Recommended copy:

```text
Aeris
Pollution-aware scene analyzer for outdoor resource protection
```

Avoid long onboarding text. The demo presenter will explain the concept verbally.

### Scene Panel

The scene panel is the visual anchor.

States:

- ready to scan
- scanning
- detections found
- fallback image loaded
- rescan complete

Required controls:

```text
[ Scan Scene ]
[ Use Demo Frame ]
[ Rescan ]
```

The backup path should feel normal. "Use Demo Frame" is better than "Fallback" because it sounds intentional.

### CASTNET Context Panel

This panel proves the dataset matters.

Recommended fields:

```text
CASTNET Profile
Outdoor Garden Demo

Ozone Risk
High

Deposition Risk
Medium

Active Mode
Protect Plants + Sensitive Equipment
```

This should be visible before the scan so judges understand that environmental context is part of the pipeline from the start.

### Ranked Actions Panel

This is the core output.

Use strong verbs and concise reasons.

Example:

```text
1. Protect seed tray first
   High plant vulnerability under current ozone profile

2. Move battery pack to storage
   Sensitive equipment, reachable, high protection value

3. Use tarp if time allows
   Protection-enabling object detected nearby
```

Each action should include:

- rank
- action verb
- target object
- short reason

Recommended action verbs:

- protect
- move
- cover
- deprioritize

### Explanation Panel

The explanation should be short enough to read during the pitch.

Example:

```text
Aeris prioritizes the seed tray because the CASTNET-derived profile indicates elevated plant-sensitive exposure. The battery pack ranks next because sensitive equipment degrades faster outdoors, while the tarp can reduce exposure for multiple nearby items.
```

Avoid long LLM-style paragraphs. The explanation should clarify the ranking, not replace it.

---

## Interaction Flow

The demo flow should feel almost theatrical:

1. The page loads with CASTNET context already visible.
2. The scene panel shows "Ready to scan."
3. The presenter clicks "Scan Scene."
4. Bounding boxes and labels appear.
5. The ranked action panel fills in.
6. The explanation appears.
7. Optional: the presenter clicks "Rescan" after moving or removing an item.
8. The recommendations update.

This flow proves:

- environmental data is active
- the scene is being analyzed
- recommendations are generated from both inputs
- the output is practical

---

## Optional 3D Scene Map

React Three Fiber can be useful, but it should not be the primary interface.

Best use:

- a small secondary "Scene Map" panel below or beside the camera feed
- a simple table plane
- object markers placed by approximate x/y position
- priority color rings around objects

Example:

```text
red / amber: protect first
blue: move to storage
green: protection-enabling object
gray: low priority
```

The 3D panel should help explain spatial reasoning. It should not become a separate simulated world.

Good 3D use:

- showing the seed tray as highest priority
- showing the tarp/storage bin as protection enablers
- showing rough reachability
- adding a memorable visual detail after the core flow works

Bad 3D use:

- full-screen immersive environment
- complex camera controls
- decorative objects unrelated to detections
- making the recommendation flow depend on 3D rendering

Recommended priority:

```text
2D scan/recommend flow first
3D scene map second
full 3D interface never for MVP
```

---

## Mobile / Small Screen Layout

If the UI needs to run on a narrow screen, stack the panels vertically:

```text
Header
CASTNET Context
Scene Scan
Top Actions
Explanation
```

Keep the scan panel large enough that boxes and labels remain readable.

---

## Demo Copy

Recommended presenter-aligned copy:

### Before Scan

```text
CASTNET-derived context is loaded. Aeris is ready to scan the outdoor setup.
```

### During Scan

```text
Analyzing visible resources...
```

### After Scan

```text
Recommendations generated from environmental context and detected objects.
```

### Rescan

```text
Scene updated. Priorities recalculated.
```

---

## UI Success Criteria

The UI succeeds if a judge can immediately see:

- CASTNET context is visible and meaningful
- the scene scan identifies real resources
- the recommendation list is concrete
- the explanation links environmental context to action
- the sustainability angle is obvious

The UI fails if it looks like:

- only an object detector
- only an environmental dashboard
- a generic chatbot
- a decorative 3D demo without a clear decision layer

---

## Final Recommendation

Build the main interface as a polished 2D split-screen demo:

```text
Scene scan on the left.
CASTNET context, ranked actions, and explanation on the right.
```

Add a small React Three Fiber scene map only after the core scan/recommend flow is stable.

The interface should make the pipeline undeniable:

```text
CASTNET context -> scene objects -> ranked protection decisions
```
