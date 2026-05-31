# System Audit

Last updated: 2026-05-30

## Executive Summary

Aeris is portfolio-viable as a backend orchestration and AI integration project. The strongest story is not "we built an object detector"; it is that the repo connects live detection, environmental context, and resilient recommendation generation into one observable pipeline.

The main readiness gap was repo clarity. The codebase contains several UI experiments and older docs from hackathon iteration, while the current working runtime is Streamlit-first with FastAPI support and an optional React shell.

## Current Working System

Verified from code:

- `backend/streamlit_app.py` owns the primary live scanner, YOLO tracking, uploaded clip processing, side-panel context, and advice display.
- `backend/app/main.py` exposes the API surface for health, fixed context, scan-frame, sustainability advice, latest detection, and older async analysis.
- `backend/app/context/fixed_context_service.py` normalizes CASTNET, weather, air quality, alerts, risk flags, and source status.
- `backend/app/sustainability/adviser.py` handles Gemini/Anthropic provider selection, JSON parsing, cache keys, and deterministic fallback.
- `ui/` builds successfully and remains useful as an optional polished shell.

## Verification Baseline

Commands run during audit:

```powershell
python -m unittest discover -s tests
cd ui; npm run test
cd ui; npm run build
```

Results:

- Backend policy tests passed in the `aeris-backend` conda environment.
- Offline FastAPI contract tests cover health, fixed context shape, fallback sustainability advice, and latest detection shape.
- UI Vitest suite passed.
- UI production build passed.
- `python` is not directly on this PowerShell PATH; use Conda or a local virtual environment.
- UI test/build commands needed to run outside the Codex sandbox because sandboxed Vite/esbuild could not read `vite.config.ts`.

## Portfolio Strengths

- Clear pipeline boundary: detection, context, and recommendation are separate.
- Fallback-safe recommendation path: missing API keys or provider failures still produce advice.
- Cache-aware LLM usage: advice is not generated every frame.
- Real environmental data story: CASTNET is part of the runtime context, not only the pitch.
- Custom model record: `docs/trash-model.md` documents data prep, training iterations, model quality, and integration work.
- Demo-friendly runtime: Streamlit can show live camera, bounding boxes, advice, and uploaded video processing.

## Risks And Cleanup Targets

| Area | Risk | Recommended action |
| --- | --- | --- |
| UI folders | `frontend/`, `aeirs-ui/`, and `aeris ui/` are legacy workspaces | Move them under an archive folder or remove them after confirming no unique work remains |
| Model artifact availability | Preferred `trash-quick-v4-best.pt` is gitignored and may not exist after clone | Document download/placement path, or add a small release artifact link |
| UI text rendering | Some terminals render Streamlit's decorative Unicode poorly | Keep labels readable if the Streamlit UI is opened in constrained environments |
| Tests | Backend coverage is useful but still not exhaustive | Add integration checks for live Streamlit detection and real `/scan-frame` image uploads |
| Secrets | `.env` exists locally and must stay untracked | Keep `.env.example` current and avoid committing local secrets |
| Docs drift | Some older docs describe React as the primary runtime | Keep `readme.md` and `docs/architecture.md` canonical |

## Recommended Next Commits

1. Documentation and env examples: clarify current architecture, setup, team contributions, and audit status.
2. Streamlit code polish: keep UI labels professional and make constrained-environment rendering graceful.
3. API image-scan cleanup: add a fixture-backed `/scan-frame` upload test when model artifact availability is settled.
4. Legacy folder cleanup: archive old UI experiments after confirming no unique work remains.

## Recruiter Narrative

Use this framing:

```text
Aeris is a real-time environmental intelligence pipeline. The vision layer detects waste, the backend normalizes environmental context from CASTNET and live APIs, and the recommendation layer generates grounded advice with LLM providers, deterministic fallback, and caching.
```

For Piero's contribution:

```text
I worked mainly on backend orchestration: FastAPI endpoints, environmental context normalization, and the pipeline that converts structured detections into cached LLM-backed recommendations with deterministic fallback behavior.
```
