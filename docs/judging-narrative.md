# Judging Narrative

## Purpose

This document explains how Aeris should be framed to judges.

Aeris should not be pitched as "an AI that detects objects."

It should be pitched as:

> **a system that turns environmental monitoring and live scene perception into real-world protection decisions**

---

## Core Judge Message

**Aeris uses CASTNET environmental exposure data, live YOLO scene perception, and asynchronous agentic reasoning to decide what outdoor resources should be protected first.**

That sentence contains:

- the dataset
- the visual system
- the agentic decision layer
- the action output
- the sustainability angle

---

## Problem Framing

Environmental monitoring data exists, but it rarely becomes actionable resource-level decisions for people managing real outdoor setups.

There is a missing last mile between:

- environmental awareness
- live visible conditions
- resource protection

Without that action layer, valuable resources stay exposed longer than they should, degrade faster, and are replaced more often than necessary.

---

## Why This Is Sustainability

Aeris helps preserve resources under environmental stress.

It supports sustainability through:

- preservation
- adaptation
- reduced avoidable degradation
- reduced replacement waste

Short answer:

> It is sustainability because it helps preserve real resources and reduce replacement waste under environmental stress.

---

## Technical Novelty Narrative

Pitch Aeris as a layered system:

### 1. Fixed Context

CASTNET-derived environmental context tells Aeris what kind of pollution-related stress matters.

### 2. Live Perception

YOLO detects what outdoor resources are actually visible.

### 3. Scene Snapshot

The system converts detections into a structured object list with labels, confidence, boxes, and rough reachability.

### 4. Async Agentic Decision

Gemini/OpenAI reason over the latest structured snapshot and CASTNET context to produce ranked protection actions.

### 5. Fallback Safety

If providers fail, local fallback policy/template output keeps the demo stable.

This shows:

- real dataset use
- computer vision
- agentic reasoning
- schema-bounded AI
- demo resilience

---

## Why CASTNET Matters

CASTNET is not decorative.

CASTNET provides the environmental exposure profile that tells the agent what kind of resource protection logic should matter in this location.

Short answer:

> CASTNET is the fixed environmental context that drives the protection mode.

---

## Why Not Just A Dashboard?

Dashboards tell you that risk exists.

Aeris watches the actual scene and tells you what to protect first.

---

## Why Not Just Object Detection?

Object detection alone only tells you what is there.

Aeris combines what is there with environmental context and asynchronous agentic reasoning to decide what matters first.

---

## Why The LLM?

The LLM is the agentic decision layer, but it is bounded.

It receives:

- structured CASTNET context
- structured scene detections
- allowed object list
- allowed action list
- output schema

It does not reason from raw video, and it does not block the live camera stream.

---

## Strongest Differentiators

1. Real dataset integration
2. Live scene perception
3. Asynchronous agentic recommendations
4. Actionable sustainability output
5. Stable fallback path

---

## The 30-Second Pitch

> **Aeris is a pollution-aware scene analyzer for outdoor sustainability. It uses CASTNET environmental exposure data to understand what kind of pollution stress matters, keeps scene perception live with YOLO, and asynchronously uses an agentic reasoning layer to recommend what outdoor resources should be protected first. Instead of stopping at environmental monitoring or object detection, Aeris turns environmental context into practical protection decisions that help preserve materials, tools, and plant resources.**

---

## What To Repeat Often

- CASTNET-driven context
- live YOLO scene perception
- asynchronous agentic reasoning
- protect outdoor resources
- turn monitoring into action
- reduce avoidable degradation

---

## Final Positioning Statement

**Aeris is not just an environmental dashboard and not just a vision demo. It is a sustainability-focused decision system that uses CASTNET exposure context, live YOLO perception, and asynchronous agentic reasoning to turn environmental risk into practical resource-protection actions.**
