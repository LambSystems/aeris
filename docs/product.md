# Product Overview

## Name

**Aeris**

## Tagline

**A pollution-aware scene analyzer that watches outdoor resources and recommends what to protect first.**

---

## Product Summary

Aeris is a sustainability-focused decision system that combines **CASTNET environmental exposure context**, **live YOLO scene perception**, and **asynchronous agentic reasoning** to help users protect outdoor resources under pollution-related stress.

It takes two main inputs:

- **Fixed Context**: environmental conditions derived from CASTNET-based pollution exposure data
- **Dynamic Context**: visible objects detected from a live or fixture-backed scene

An agentic reasoning layer then recommends what should be **protected, moved, covered, or deprioritized first**.

The camera/scene view should stay responsive while the agent reasons in the background.

---

## Problem

Environmental data often tells institutions that pollution-related risk exists, but it rarely helps people decide what to do with the real resources in front of them.

For small outdoor setups like:

- community gardens
- outdoor workstations
- field stations
- temporary storage areas
- semi-outdoor resource tables

there is no practical tool that says:

> given current environmental exposure conditions and this visible scene, what should I protect first?

---

## Solution

Aeris solves this by combining live perception with asynchronous reasoning.

### Step 1 - Understand Environmental Stress

Aeris uses CASTNET-derived context to understand what kind of pollution exposure matters in the location.

### Step 2 - Watch The Scene

YOLO detects visible outdoor resources in 2D and produces a structured scene snapshot.

### Step 3 - Reason Asynchronously

A Gemini-first agentic decision layer evaluates the latest snapshot and returns ranked protection actions.

### Step 4 - Update The User

The UI keeps the live scene visible and updates the recommendation panel when reasoning completes.

---

## Primary Use Case

### Outdoor Resource Protection

A user has an outdoor or semi-outdoor setup containing valuable or sensitive resources, and Aeris helps determine what to protect first under pollution-related environmental stress.

Example objects:

- seed tray
- battery pack
- metal hand tool
- tarp
- storage bin
- water jug
- gloves

Example output:

- Protect the seed tray first
- Move the battery pack into storage
- Use the tarp if time allows
- Leave the water jug for later

---

## Why This Is A Sustainability Product

Aeris is sustainability-focused because it helps:

- preserve outdoor resources under environmental stress
- reduce avoidable degradation
- extend the useful life of equipment and materials
- reduce replacement waste
- improve adaptation to pollution-related exposure

---

## Core Product Insight

> Environmental data should not stop at awareness. It should drive action.

Most environmental tools stop at dashboards or alerts. Most vision tools stop at detection. Aeris combines both and adds an asynchronous decision layer.

---

## User Flow

1. Load CASTNET context.
2. Keep scene/camera view active.
3. Detect visible objects with YOLO.
4. Start an async agentic analysis job.
5. Keep the latest recommendation visible while analysis is pending.
6. Update recommendations when the job completes.

---

## Product Inputs

### Fixed Context Inputs

- CASTNET-derived pollution profile
- regional exposure mode
- environmental stress summary

### Dynamic Context Inputs

- camera feed or demo frame
- YOLO detections
- approximate distance / reachability
- scene changes over time

---

## Product Outputs

Aeris outputs ranked recommendations such as:

- **Protect first**
- **Move to storage**
- **Cover if time allows**
- **Low priority**

Each recommendation should be grounded in:

- environmental context
- visible scene state
- the object's role and vulnerability
- the agentic reasoning output

---

## What Makes Aeris Different

Aeris is not just:

- an environmental dashboard
- an object detector
- a chatbot
- a static recommendation list

Its core value is:

```text
CASTNET context + live scene perception + async agentic reasoning -> prioritized real-world action
```

---

## One-Sentence Product Definition

**Aeris is a sustainability-focused scene analyzer that keeps YOLO perception live while asynchronously using CASTNET context and agentic reasoning to decide what outdoor resources should be protected first.**
