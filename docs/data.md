# Data

## Purpose

The role of data in Aeris is not decorative. Data is the core of the product.

Aeris uses environmental context derived from **CASTNET** to determine what kind of pollution-related stress matters in a location. That context directly influences how the system ranks protective actions for outdoor resources.

In other words:

**CASTNET tells Aeris what matters environmentally.**  
**Scene understanding tells Aeris what is actually present.**  
**The asynchronous agentic decision layer connects the two.**

---

## Why CASTNET

CASTNET is the required dataset for this project and is also the best foundation for the sustainability framing we selected.

Aeris uses CASTNET because it provides environmental monitoring data related to:

- ozone
- sulfur-related pollutants
- nitrogen-related pollutants
- atmospheric deposition context
- rural and regional exposure patterns

That makes it a strong fit for a product focused on:

- pollution-related environmental stress
- outdoor resource vulnerability
- sustainability through protection and preservation

For the hackathon, CASTNET is the **Fixed Context backbone**.

---

## What CASTNET Does in Aeris

CASTNET is not used as a live object detector and not as a room-level trigger.

Instead, it is used to build a **location-level environmental exposure profile** that answers questions like:

- what environmental stress is important in this area?
- are plants especially vulnerable under this profile?
- should Aeris prioritize sensitive equipment as well?
- is this a higher-exposure context for outdoor resources?

This makes CASTNET part of the actual decision pipeline, not just the pitch.

---

## Fixed Context Data Model

The Fixed Context built from CASTNET should be lightweight and hackathon-friendly.

### Minimum fields
- location name
- CASTNET site or profile name
- ozone risk level
- deposition risk level
- risk mode
- short summary

### Example
```json id="17dbor"
{
  "location": "Demo Location",
  "castnet_site": "Example CASTNET Site",
  "pollution_profile": {
    "ozone_risk": "high",
    "deposition_risk": "medium"
  },
  "risk_mode": "protect_plants_and_sensitive_equipment",
  "summary": "Elevated ozone and outdoor exposure conditions for plants and sensitive equipment."
}
````

This is enough for the MVP+.

---

## Recommended Hackathon Data Strategy

Do **not** try to build a full CASTNET ingestion and analysis platform during the hackathon.

Instead, create a **small processed environmental profile layer** derived from CASTNET that can support the demo.

### Best strategy

Build a simplified processed file that maps one or a few demo locations to a compact environmental profile.

### Example output file

`data/processed/castnet_profiles.json`

This file can contain:

* site identifier
* site name
* region or demo label
* ozone risk bucket
* deposition risk bucket
* active risk mode
* one-line summary

This gives you a clear and honest way to say:

* the app uses CASTNET
* the environmental mode comes from data
* the agentic decision layer is data-informed

without spending too much of the hackathon on preprocessing complexity.

---

## Raw vs Processed Data

### Raw data

This is the original CASTNET dataset or downloaded files.

Suggested location:
`data/castnet/raw/`

### Processed data

This is the cleaned and reduced representation that Aeris actually uses in the app.

Suggested location:
`data/castnet/processed/`

### Why separate them

Separating raw and processed data makes the project cleaner and easier to explain.

It also helps in the README and judging narrative:

* raw data proves the project is grounded in the real dataset
* processed data powers the actual demo

---

## What to Extract from CASTNET

For the MVP+, you do not need the entire dataset.

You only need enough structure to create an environmental profile that supports your chosen demo mode.

### Best minimum extraction targets

* site name
* site location
* ozone-related signal or bucket
* sulfur/nitrogen or deposition-related signal or bucket
* a simplified environmental profile label

### Example simplification

Convert data into qualitative buckets such as:

* `low`
* `medium`
* `high`

Then map those to recommendation modes.

---

## Recommendation Modes from Data

For the hackathon, use **at most two environmental modes**.

### Mode 1 — `protect_plants_and_sensitive_equipment`

This is the main mode.

Use when:

* ozone-related stress is elevated
* or the environmental profile suggests higher sensitivity for plants and exposed equipment

### Mode 2 — `general_outdoor_protection`

Optional second mode.

Use when:

* the profile is less severe or more general
* and broad resource preservation is more appropriate than specific plant-sensitive prioritization

### Example mapping logic

```text id="sxsvku"
if ozone_risk == high:
    risk_mode = protect_plants_and_sensitive_equipment
else:
    risk_mode = general_outdoor_protection
```

Keep this very simple.

---

## How Data Affects Recommendations

The CASTNET-derived profile should influence the scoring system.

### Example idea

In `protect_plants_and_sensitive_equipment` mode:

* seed trays and plant resources get a strong priority boost
* batteries/electronics also get elevated protection value
* tarp and storage bin gain value as protection-enabling objects

In `general_outdoor_protection` mode:

* priorities are more evenly distributed across valuable exposed resources

This is where the data becomes part of the product logic.

---

## Dynamic Context Data

Dynamic Context is separate from CASTNET.

It comes from scene understanding and represents the visible setup.

### Example fields

* object name
* confidence
* distance
* reachability

### Example

```json id="buxmza"
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
    }
  ]
}
```

This data is then combined with the CASTNET-based Fixed Context.

---

## Final Combined Data Flow

### 1. Load processed CASTNET profile

Aeris loads a compact environmental exposure profile for the selected demo location.

### 2. Load scene state

Aeris scans the visible outdoor setup and creates a normalized object list.

### 3. Merge both layers

The backend combines:

* environmental mode
* object types
* distance/reachability
* object vulnerability

### 4. Rank actions

The agentic decision layer produces ranked recommendations, with fallback policy output available only as a safety net.

This is the core data pipeline.

---

## Suggested Files

```text id="6h19jd"
data/
├── castnet/
│   ├── raw/
│   │   └── ...
│   ├── processed/
│   │   ├── castnet_profiles.json
│   │   └── demo_profile.json
│   └── notes.md
└── sample_inputs/
    └── demo_scene.json
```

### File descriptions

#### `data/castnet/raw/`

Original dataset files or downloaded extracts.

#### `data/castnet/processed/castnet_profiles.json`

Compact environmental profiles used by the app.

#### `data/castnet/processed/demo_profile.json`

One clean demo-ready profile for the main presentation.

#### `data/castnet/notes.md`

Short explanation of how raw fields were simplified into app-level risk buckets.

---

## Suggested Processing Approach

For the hackathon, the processing pipeline should be simple and explicit.

### Recommended flow

1. inspect the relevant CASTNET fields
2. select one or a few locations/sites for the demo
3. derive simple risk buckets
4. create profile objects
5. store them as JSON for fast backend use

### Example app-level profile shape

```json id="q1dn1g"
{
  "site_id": "DEMO001",
  "site_name": "Demo CASTNET Profile",
  "location_label": "Outdoor Garden Demo",
  "ozone_risk": "high",
  "deposition_risk": "medium",
  "risk_mode": "protect_plants_and_sensitive_equipment",
  "summary": "Elevated ozone and environmental exposure conditions for outdoor plants and sensitive equipment."
}
```

This is enough for the MVP+ and much more reliable than overengineering.

---

## Data Constraints

### Constraint 1

The dataset must be visibly present in the system and in the narrative.

### Constraint 2

The app should not pretend CASTNET provides real-time object-level risk.

### Constraint 3

The processed environmental profile must remain understandable and inspectable.

### Constraint 4

The data logic must be simple enough to debug during the hackathon.

---

## Good Data Story for Judges

The clean story is:

* CASTNET gives Aeris environmental exposure context
* scene understanding reveals the real resources currently exposed
* Aeris combines the two to recommend what should be protected first

That keeps the dataset central, honest, and easy to explain.

---

## Non-Goals for Data Work

Do not try to:

* ingest all CASTNET history into a large analytics system
* train a custom environmental model
* build live forecasting from scratch
* overfit the product around hard-to-explain chemistry details

The goal is to use the dataset clearly, credibly, and effectively.

---

## Data Success Criteria

The data layer succeeds if:

1. Aeris clearly uses CASTNET-derived context
2. that context changes the recommendation mode
3. the mode changes what objects are prioritized
4. the link between data and action is obvious in the demo

---

## One-Sentence Summary

**Aeris uses a simplified CASTNET-derived environmental profile as Fixed Context, then combines it with real scene data to decide what outdoor resources should be protected first.**
