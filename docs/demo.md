# Demo

## Demo Goal

The Aeris demo must make five things immediately obvious:

1. **Aeris uses CASTNET-based environmental context**
2. **Aeris understands a real scene**
3. **Aeris identifies relevant outdoor resources**
4. **Aeris recommends what should be protected first**
5. **The product is clearly a sustainability tool**

The demo should feel like:

> environmental data + scene understanding -> practical protection decisions

---

## Demo Summary

Aeris analyzes a real outdoor or semi-outdoor setup and recommends what resources should be protected first under pollution-related environmental stress.

For the hackathon, the demo is intentionally focused on one scenario:

### **Outdoor resource protection under environmental exposure**

Aeris loads a CASTNET-informed environmental profile, scans a scene, and outputs ranked protective actions.

---

## Demo Scene

### Recommended setup
Use one simple table or workstation with **7–8 objects max**.

### Core scene objects
- seed tray
- battery pack
- metal hand tool
- tarp
- storage bin
- water jug
- gloves
- one irrelevant item

### Why this works
This setup gives the system a mix of:
- plant-sensitive resource
- sensitive equipment
- durable tool
- protection-enabling items
- lower-priority item
- irrelevant distraction

That makes the ranking visibly meaningful.

---

## Demo Narrative

### Short narrative
Aeris is given environmental exposure context from CASTNET. It then scans the visible setup and recommends which resources should be protected first to reduce avoidable degradation and preserve outdoor assets.

### Intended output feeling
It should feel like Aeris is not just detecting objects, but deciding:
- what matters most
- what should be acted on first
- what can wait

---

## Recommended Demo Flow

### Step 1 — Opening screen
Show the Aeris interface with a clear title and a visible environmental context panel.

The panel should include:
- location
- CASTNET site/profile
- pollution summary
- active risk mode

### Example displayed context
- Location: Outdoor Garden Demo
- CASTNET Profile: Demo Site
- Ozone Risk: High
- Deposition Risk: Medium
- Mode: Protect Plants and Sensitive Equipment

This anchors the dataset immediately.

---

### Step 2 — Explain the scenario
In one sentence, explain the setup:

> Aeris uses CASTNET-based environmental exposure data to understand what kind of outdoor stress matters here, then scans the visible setup to decide what should be protected first.

Do not spend too long here. Move quickly into the visual part.

---

### Step 3 — Scan the scene
Start the scene scan.

The user either:
- uses the live camera
- or loads the pre-captured demo image if needed

The scan should visibly produce:
- object labels
- bounding boxes
- identified resources

This is the “it sees the scene” moment.

---

### Step 4 — Show Dynamic Context result
Once the detections appear, the interface should clearly indicate the recognized items.

Example:
- seed tray detected
- battery pack detected
- metal tool detected
- tarp detected
- storage bin detected

Do not overload the interface. Judges just need to see that the scene has been understood.

---

### Step 5 — Show ranked actions
After the scan, Aeris should output a ranked list.

### Example
1. Protect the seed tray first
2. Move the battery pack into storage
3. Cover the metal tools if time allows

This is the core demo payoff.

---

### Step 6 — Show explanation
Display a short explanation paragraph.

### Example explanation
> Current environmental conditions increase exposure risk for sensitive outdoor resources. The seed tray is the highest priority because plant-sensitive assets are most vulnerable in the current mode. The battery pack should be moved next to reduce equipment exposure, while the metal tools are important but less urgent.

This is where the recommendation becomes legible.

---

### Step 7 — Optional rescan moment
If time allows and implementation is stable, move or remove one object and rescan.

Example:
- move the battery pack into the storage bin
- rescan the scene
- Aeris updates the recommendation order

This is a strong MVP+ moment because it proves the system is reacting to the real scene, not just replaying a static output.

---

## Demo Script Structure

### Demo timing target
Aim for a demo segment of **60–90 seconds** inside the full pitch.

---

### Script version
#### Opening
> This is Aeris, a pollution-aware scene analyzer for outdoor sustainability.

#### Context
> Aeris starts with Fixed Context from CASTNET-derived environmental exposure data. Here, the system sees elevated ozone-related stress and activates a protection mode focused on plants and sensitive equipment.

#### Scene scan
> Now we scan the actual outdoor setup. Aeris identifies the resources present in the scene and estimates enough spatial context to reason about what can be protected first.

#### Output
> Based on the environmental mode and the visible resources, Aeris recommends protecting the seed tray first, moving the battery pack into storage next, and covering the metal tools if time allows.

#### Sustainability close
> Instead of stopping at environmental monitoring, Aeris turns pollution exposure context into practical action that helps preserve outdoor resources and reduce avoidable degradation.

---

## Visual Requirements

The interface should always keep these visible:

### 1. Environmental context card
This proves the dataset matters.

### 2. Camera / image panel
This proves the system is grounded in a real scene.

### 3. Detection overlays
This proves scene understanding is active.

### 4. Ranked recommendation list
This proves the product outputs action, not just labels.

### 5. Explanation text
This proves the reasoning is understandable.

---

## Demo Layout

Recommended layout:

```text id="6l57hj"
[ Camera / Scene Panel ]     [ Environmental Context ]
                             [ Top Actions ]
                             [ Why These Actions ]
````

Keep this simple and readable.

---

## Demo Environment Guidance

### Best physical setup

A slightly outdoor or semi-outdoor table is ideal.

Examples:

* outside near a building
* near a garden area
* patio-like setup
* semi-outdoor campus space

If that is hard, a table staged to look like an outdoor resource station is acceptable.

### Important

What matters most is not perfect realism. What matters most is that the scene clearly communicates:

* exposed resources
* protection options
* different priorities

---

## Demo Asset Preparation

Before the final demo, prepare:

### 1. Main demo scene

The physical object arrangement that will be used live.

### 2. Backup scene image

A fallback image if the live camera becomes unstable.

### 3. Screenshot of the final output

Useful for slides and Devpost.

### 4. Backup recorded demo clip

Critical in case the live demo has any instability.

---

## Demo Failure Fallbacks

### If Boxer fails live

Use YOLO fallback without changing the story.

### If live camera fails

Switch to uploaded image / pre-captured frame.

### If LLM explanation fails

Use a template explanation from policy tags.

### If CASTNET live processing becomes awkward

Use the preprocessed demo profile and say clearly that the profile is derived from CASTNET.

The audience should never feel the system collapsed. Every advanced component must have a stable fallback.

---

## What Judges Should Remember

After the demo, judges should remember:

* Aeris uses environmental data, not just vision
* Aeris understands real outdoor resources
* Aeris helps users protect what matters first
* Aeris is about sustainability through preservation and adaptation

If those four land, the demo worked.

---

## Common Demo Mistakes to Avoid

### 1. Spending too long on the dataset

The dataset is important, but the demo should quickly show action.

### 2. Overexplaining chemistry

Do not get lost in technical pollutant details.

### 3. Showing only object detection

The value is in ranked action recommendations.

### 4. Making the recommendations too abstract

Use concrete verbs:

* protect
* move
* cover
* deprioritize

### 5. Overcrowding the scene

Use a small object set so the logic is easy to understand.

---

## Demo Success Criteria

The demo succeeds if:

* the context panel is visible and meaningful
* the scene scan works
* the top actions make intuitive sense
* the explanation is short and clean
* the sustainability angle is obvious without heavy justification

---

## One-Sentence Demo Summary

**In the Aeris demo, CASTNET-informed environmental context drives a scene-aware recommendation engine that tells the user what outdoor resources to protect first.**

