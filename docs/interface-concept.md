# Interface Concept

## Purpose

This document describes the recommended Aeris UI for the HackAugie demo.

The interface should make the core product idea immediately obvious:

> live YOLO perception + CASTNET context -> asynchronous agentic protection decisions.

The UI should not feel like a generic dashboard, a chatbot, or a full 3D simulation. It should feel like a focused field-operator interface for sustainability decisions.

Chau may use **Lovable** to generate the first frontend pass. If so, Lovable should generate the actual demo interface described here, not a landing page or marketing site.

For exact frontend inputs/outputs, see `docs/team-contracts.md`.

---

## Design Goal

The UI has one job:

Help judges understand, in under one minute, that Aeris can keep scene perception live, detect exposed outdoor resources, and asynchronously recommend what to protect first based on environmental context.

The screen should always answer three questions:

1. What environmental context is active?
2. What objects is Aeris detecting?
3. What is the latest completed agentic recommendation?

---

## Recommended Layout

Use a single-screen split layout.

```text
+--------------------------------------------------------------+
| Aeris                                                        |
| Pollution-aware scene analyzer for outdoor resource protection|
+-------------------------------+------------------------------+
|                               | CASTNET Context              |
|  Live Scene / Camera View     | +--------------------------+ |
|                               | | Ozone Risk      High     | |
|  [camera or demo frame]       | | Deposition Risk Medium   | |
|                               | | Mode: Protect plants     | |
|  YOLO boxes on objects        | | and sensitive equipment  | |
|                               | +--------------------------+ |
|  seed tray                    |                              |
|  battery pack                 | Agent Status                 |
|  tarp                         | Reasoning over latest scene  |
|  storage bin                  |                              |
|                               | Latest Recommendation        |
|                               | 1. Protect seed tray first   |
|                               | 2. Move battery pack inside  |
|                               | 3. Use tarp if time allows   |
|                               |                              |
|                               | Agent Reasoning              |
|                               | CASTNET context and scene    |
|                               | objects indicate priority.   |
+-------------------------------+------------------------------+
```

---

## Lovable Prompt Direction

If using Lovable, the prompt should be direct and demo-specific:

```text
Build a single-screen React/Vite/Tailwind demo UI for Aeris, a pollution-aware scene analyzer for outdoor resource protection.

The screen should feel like an environmental operations console, not a marketing landing page. Use a split layout: a large live scene/camera panel on the left with YOLO-style detection boxes and object labels, and a right-side decision stack with CASTNET context, async agent status, latest protection recommendation, and a short explanation.

Use these visible sections:
- Header: Aeris, Pollution-aware scene analyzer for outdoor resource protection
- Live Scene panel with Start Watching, Analyze Scene, Use Demo Frame, and Rescan controls
- CASTNET Context panel showing Outdoor Garden Demo, Ozone Risk High, Deposition Risk Medium, Active Mode Protect Plants + Sensitive Equipment
- Agent Status panel showing Watching Scene, Objects Detected, Reasoning Over Latest Scene, Recommendation Updated, or Using Fallback Recommendation
- Latest Recommendation panel with ranked actions for seed tray, battery pack, and tarp
- Agent Reasoning panel with a short explanation

Use a calm field-operator visual style: deep neutral background, off-white panels, green context accents, amber priority accents, blue scan status accents, and clear readable typography.

Do not create a landing page. Do not add pricing, testimonials, auth, navigation-heavy pages, or generic AI chat UI.
```

After generation, replace hardcoded mock data with calls to the backend API.

---

## Left Side

The left side is the live scene scan area.

It should show:

- live camera feed or backup demo image
- YOLO detection boxes
- object labels
- confidence values if they do not clutter the view
- optional scan/source status

Example labels:

```text
seed_tray       94%
battery_pack    89%
metal_tool      84%
tarp            81%
storage_bin     78%
```

This is the "Aeris sees the scene" moment. It should stay responsive while the agent is reasoning.

---

## Right Side

The right side is the decision stack.

It should show:

- CASTNET-derived environmental context
- active risk mode
- agent reasoning state
- latest completed ranked actions
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

---

## Main Components

### Header

Recommended copy:

```text
Aeris
Pollution-aware scene analyzer for outdoor resource protection
```

### Live Scene Panel

States:

- watching
- detecting
- detections found
- reasoning in background
- fallback image loaded
- rescan complete

Controls:

```text
[ Start Watching ]
[ Analyze Scene ]
[ Use Demo Frame ]
[ Rescan ]
```

The camera/scene panel should not freeze while analysis is pending.

### CASTNET Context Panel

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

### Agent Status Panel

This panel prevents the UI from feeling frozen while the LLM is running.

States:

```text
Watching scene...
Objects detected
Reasoning over latest scene...
Recommendation updated
Using fallback recommendation
```

### Latest Recommendation Panel

This is the core output.

Example:

```text
1. Protect seed tray first
   Plant-sensitive resource under elevated ozone context

2. Move battery pack to storage
   Sensitive equipment exposed outdoors

3. Use tarp if time allows
   Protection-enabling object detected nearby
```

Each action should include:

- rank
- action verb
- target object
- short reason

### Agent Reasoning Panel

The explanation should be short enough to read during the pitch.

Example:

```text
Aeris recommends protecting the seed tray first because CASTNET-derived context indicates elevated plant-sensitive exposure. The battery pack ranks next because sensitive equipment is exposed, while the tarp can reduce exposure for nearby items.
```

Avoid long LLM-style paragraphs.

---

## Interaction Flow

The demo flow should feel almost theatrical:

1. The page loads with CASTNET context already visible.
2. The scene panel shows a live or fixture-backed camera view.
3. YOLO-style bounding boxes and labels appear.
4. The presenter clicks "Analyze Scene."
5. The agent status changes to "Reasoning over latest scene..."
6. The camera/scene panel continues updating.
7. The latest recommendation panel updates when the async job completes.
8. Optional: the presenter clicks "Rescan" after moving or removing an item.
9. The old recommendation stays visible while the new analysis is pending.
10. The recommendation updates again when reasoning completes.

This flow proves:

- environmental data is active
- scene perception is live
- recommendations are generated asynchronously from both inputs
- the output is practical
- the UI does not block on the LLM

The LLM should never block the live scene from rendering.

---

## Optional 3D Scene Map

React Three Fiber can be useful, but it should not be the primary interface.

Best use:

- a small secondary "Scene Map" panel below or beside the camera feed
- a simple table plane
- object markers placed by approximate x/y position
- priority color rings around objects

Recommended priority:

```text
2D live scan/recommend flow first
3D scene map second
full 3D interface never for MVP
```

---

## Mobile / Small Screen Layout

If the UI needs to run on a narrow screen, stack the panels vertically:

```text
Header
CASTNET Context
Live Scene Scan
Agent Status
Latest Recommendation
Agent Reasoning
```

Keep the scan panel large enough that boxes and labels remain readable.

---

## UI Success Criteria

The UI succeeds if a judge can immediately see:

- CASTNET context is visible and meaningful
- the scene view stays responsive
- YOLO-style detection identifies real resources
- agent status clearly shows async reasoning
- the recommendation list is concrete
- the explanation links environmental context to action

The UI fails if it looks like:

- only an object detector
- only an environmental dashboard
- a generic chatbot
- a decorative 3D demo without a clear decision layer

---

## Final Recommendation

Build the main interface as a polished 2D split-screen demo:

```text
Live scene scan on the left.
CASTNET context, async agent status, latest recommendation, and explanation on the right.
```

Add a small React Three Fiber scene map only after the core live scan/recommend flow is stable.

The interface should make the pipeline undeniable:

```text
live YOLO perception -> CASTNET context -> async agentic protection decisions
```
