# Product

## Product Definition

**Aeris is a live environmental scanner that detects recyclable waste and tells the user what action to take.**

Current demo object set:

```text
aluminum can
plastic bottle
paper / crumpled paper
```

Current product loop:

```text
see object -> detect object -> add environmental context -> recommend action
```

---

## User Problem

People often see waste but do not know the best immediate action:

- recycle it?
- throw it away?
- handle it carefully?
- does outdoor context matter?

Aeris gives a short, practical answer while the user is looking at the object.

---

## Product Claim

Aeris is not only object detection.

It combines:

- live YOLO perception
- CASTNET regional environmental context
- weather/air-quality context
- LLM or deterministic advice

The important demo idea:

```text
same object + different environmental context = different recommendation
```

---

## Demo Experience

The user opens the Aeris UI and sees:

- live camera panel
- YOLO bounding boxes
- current detected object
- recommended action
- environmental context
- risk signals

The camera remains live while advice updates separately.

---

## Current Product Copy

One-line:

> Aeris sees recyclable waste live and gives environmentally aware disposal advice.

Pitch:

> Aeris combines YOLO object detection with CASTNET and weather context so people can take immediate, grounded sustainability actions when they encounter waste.

Judge explanation:

> The data is visible in the product. CASTNET/weather context appears in the interface and conditions the recommendation, instead of being hidden in a backend-only story.

---

## What Aeris Is Not

Aeris is not:

- a generic chat app
- a static recycling guide
- a landing page
- a per-frame LLM vision system
- a medical/health diagnosis tool
- a street-level air quality authority

---

## Current MVP Scope

In scope:

- live detection of can, paper, bottle
- environmental context panel
- advice card
- LLM provider when keys exist
- deterministic fallback when keys fail
- session cache for repeated advice

Out of scope:

- account system
- long-term user history
- database
- multi-user deployment
- full browser YOLO as primary path
- perfect mobile app packaging

---

## Success Criteria

The demo succeeds if judges can see:

1. an object detected live
2. environmental data loaded live
3. a recommendation generated from detection + context
4. the camera continuing while the advice exists independently
5. a clear sustainability action
