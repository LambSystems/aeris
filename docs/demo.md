# Demo

## Demo Goal

The Aeris demo must make five things immediately obvious:

1. Aeris uses CASTNET-based environmental context
2. Aeris detects real outdoor resources in 2D
3. The camera/scene view stays live
4. Agentic reasoning runs asynchronously
5. The output is a practical sustainability recommendation

The demo should feel like:

> live perception + environmental context -> asynchronous protection decision

---

## Demo Summary

Aeris analyzes an outdoor or semi-outdoor setup and recommends what resources should be protected first under pollution-related environmental stress.

The system keeps the visual scene active while a Gemini-first agentic reasoning layer evaluates the latest YOLO scene snapshot.

---

## Demo Scene

Use one simple table or workstation with 7-8 objects max:

- seed tray
- battery pack
- metal hand tool
- tarp
- storage bin
- water jug
- gloves
- one irrelevant item

This gives the agent a mix of sensitive resources, protection enablers, lower-priority resources, and a distractor.

---

## Recommended Demo Flow

### Step 1 - Opening

Show the Aeris interface with:

- live scene/camera area
- CASTNET context panel
- empty/latest recommendation panel

Say:

> Aeris uses CASTNET-based environmental context and live scene perception to recommend what outdoor resources should be protected first.

### Step 2 - Environmental Context

Show:

- Location: Outdoor Garden Demo
- CASTNET Profile: Demo CASTNET Profile
- Ozone Risk: High
- Deposition Risk: Medium
- Mode: Protect Plants and Sensitive Equipment

This anchors the dataset immediately.

### Step 3 - Live Scene Perception

Run YOLO or fixture-backed detections.

The scene should show:

- bounding boxes
- labels
- confidence values

This is the "Aeris sees the scene" moment.

### Step 4 - Start Agentic Analysis

Trigger analysis from the latest scene snapshot.

The UI should show:

```text
Reasoning over latest scene...
```

The camera/scene view should keep running.

### Step 5 - Show Recommendation Update

When the async job completes, update the recommendation panel:

```text
1. Protect the seed tray first
2. Move the battery pack into storage
3. Use the tarp if time allows
```

This is the core payoff.

### Step 6 - Optional Rescan

Move or remove one item, then trigger another scene snapshot and analysis.

The UI should keep the old recommendation visible while the new one is pending, then replace it when complete.

---

## Demo Script

### Opening

> This is Aeris, a pollution-aware scene analyzer for outdoor sustainability.

### Context

> Aeris starts with CASTNET-derived environmental context. In this demo, elevated ozone activates a mode focused on plants and sensitive equipment.

### Scene Perception

> The scene view stays live while YOLO detects exposed outdoor resources in 2D.

### Async Reasoning

> Aeris sends the latest structured scene snapshot to an agentic reasoning layer. The LLM does not touch raw video, and the camera does not wait for the LLM.

### Output

> The recommendation updates when reasoning completes: protect the seed tray first, move the battery pack next, and use the tarp if time allows.

### Sustainability Close

> Instead of stopping at environmental monitoring, Aeris turns pollution exposure context into practical action that helps preserve outdoor resources and reduce avoidable degradation.

---

## Visual Requirements

Always keep these visible:

- environmental context
- scene/camera panel
- detection overlays
- analysis state
- latest ranked recommendation
- explanation

---

## Demo Failure Fallbacks

### If YOLO fails live

Use fixture detections from the backup demo image.

### If live camera fails

Use uploaded image or pre-captured frame.

### If Gemini is slow

Keep showing the live scene and latest completed recommendation.

### If Gemini fails

Try OpenAI.

### If all LLM providers fail

Use fallback policy/template output.

The audience should never feel the system collapsed.

---

## What Judges Should Remember

- Aeris uses real environmental data
- Aeris detects real resources
- Aeris uses agentic reasoning asynchronously
- Aeris tells users what to protect first
- Aeris is sustainability through preservation and adaptation

---

## One-Sentence Demo Summary

**In the Aeris demo, YOLO keeps scene perception live while CASTNET context and an asynchronous agentic reasoning layer recommend what outdoor resources to protect first.**
