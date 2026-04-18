# Product Overview

## Name
**Aeris**

## Tagline
**A pollution-aware scene analyzer that recommends what outdoor resources to protect first.**

---

## Product Summary

Aeris is a sustainability-focused decision system that combines **environmental exposure context** with **real-time scene understanding** to help users protect outdoor resources under pollution-related stress.

It takes two kinds of input:

- **Fixed Context**: environmental conditions derived from CASTNET-based pollution exposure data
- **Dynamic Context**: the real objects currently visible in an outdoor or semi-outdoor setup

Aeris then recommends what should be **protected, moved, covered, or deprioritized first**.

The goal is to turn environmental monitoring into **practical action**.

---

## Problem

Environmental data often tells institutions that pollution-related risk exists, but it rarely helps ordinary people decide what to do with the real resources in front of them.

For small outdoor setups like:

- community gardens
- outdoor workstations
- field stations
- temporary storage areas
- semi-outdoor resource tables

there is no practical tool that says:

> given current environmental exposure conditions, what should I protect first?

This creates a last-mile problem between:

- **environmental awareness**
- and
- **resource-level action**

As a result, materials, tools, electronics, and plant resources are more likely to remain exposed, degrade faster, and require replacement sooner than necessary.

---

## Solution

Aeris solves this by combining environmental context with scene analysis.

### Step 1 — Understand environmental stress
Aeris uses CASTNET-derived context to understand what kind of pollution exposure matters in the location.

### Step 2 — Understand the real scene
Aeris scans a visible setup and identifies relevant outdoor resources.

### Step 3 — Recommend the next best actions
Aeris ranks what should be protected first based on:

- environmental vulnerability
- resource type
- spatial accessibility
- protection value
- time-sensitive prioritization

This allows Aeris to move from:

> “there is pollution-related risk in this environment”

to:

> “protect this first, then move this, then cover this if time allows”

---

## Primary Use Case

### Outdoor Resource Protection

Aeris is designed around a focused hackathon use case:

A user has an outdoor or semi-outdoor setup containing valuable or sensitive resources, and Aeris helps determine what to protect first under pollution-related environmental stress.

### Example objects
- seed tray
- battery pack
- metal hand tool
- tarp
- storage bin
- water jug
- gloves

### Example output
- Protect the seed tray first
- Move the battery pack into storage
- Cover the metal tools if time allows
- Leave the water jug for later

---

## Why This Is a Sustainability Product

Aeris is directly sustainability-coded because it focuses on:

- protecting outdoor resources
- reducing avoidable degradation
- extending the lifespan of materials and equipment
- reducing waste from premature replacement
- improving adaptation to environmental stress

It is not a healthcare app and not a generic productivity assistant.

It is a sustainability tool because it helps users respond to environmental conditions in a way that preserves real-world resources.

---

## Core Product Insight

Aeris is built on a simple but powerful idea:

> Environmental risk should not stop at awareness.
> It should drive action.

Most systems in this space stop at one of two points:

- they show environmental data
- or they detect objects in a scene

Aeris combines both and adds a decision layer.

That means it does not just answer:

- what is the pollution context?
- what objects are present?

It answers:

- what matters most in this scene right now?
- what should the user do first?

---

## User Flow

### 1. Load environmental context
The system loads a CASTNET-informed environmental profile for the demo location.

### 2. Scan the scene
The user scans a real outdoor or semi-outdoor setup using the camera.

### 3. Build scene state
Aeris identifies relevant objects and estimates enough spatial information to support prioritization.

### 4. Rank actions
A policy engine decides what to protect first.

### 5. Explain recommendations
Aeris presents a short natural-language explanation of the recommended actions.

---

## Product Inputs

### Fixed Context Inputs
- CASTNET-derived pollution profile
- regional exposure mode
- environmental stress summary

### Dynamic Context Inputs
- camera feed
- object detections
- approximate distance / reachability
- scene changes over time

---

## Product Outputs

Aeris outputs ranked recommendations such as:

- **Protect first**
- **Move next**
- **Cover if time allows**
- **Low priority**

Each recommendation should be grounded in:

- the environmental context
- the visible scene
- the object’s role and vulnerability

---

## What Makes Aeris Different

Aeris is not just:

- a dashboard
- a detector
- a chatbot
- an environmental alert viewer

Its core value is that it converts:

**environmental context + scene state -> prioritized real-world action**

That decision layer is the product.

---

## Scope for HackAugie

For the hackathon, Aeris is intentionally scoped to:

- one domain: outdoor resource protection
- one demo scene
- one environmental context pipeline
- one recommendation engine
- one clean UI

This keeps the product understandable, demoable, and technically achievable within the time limit.

---

## Success Criteria

The product succeeds if a judge can immediately understand:

1. Aeris uses environmental context grounded in CASTNET
2. Aeris understands the visible scene
3. Aeris recommends what should be protected first
4. The recommendations feel practical and scene-aware
5. The project clearly preserves resources under environmental stress

---

## One-Sentence Product Definition

**Aeris is a sustainability-focused scene analyzer that uses CASTNET-based pollution exposure context to decide what outdoor resources should be protected first.**