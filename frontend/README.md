# Aeris Frontend

Vite + React demo interface for Aeris.

## Run

```bash
cd frontend
npm install
npm run dev
```

The app runs at:

```text
http://localhost:5173
```

The frontend expects the backend at:

```text
http://localhost:8000
```

If the backend is not running, the app uses local mock data so Chau can keep iterating.

The intended live UI flow is:

1. keep the camera stream local and smooth
2. call `/scan-frame` for the latest YOLO/fixture detections
3. call `/analyze-scene` to start an async agentic recommendation job
4. poll `/analysis/{job_id}` or `/analysis/latest`
5. update the recommendation panel when a completed result is available

`/demo/run` still exists as a compatibility fallback for quick demos.

## Frontend Input / Output Contract

See `../docs/team-contracts.md` for the full team handoff contract.

Frontend owns:

- camera/demo frame display
- sampling frames, if backend YOLO is used
- drawing boxes and labels
- triggering analysis
- polling analysis jobs
- rendering latest advice

Frontend receives:

- `FixedContext` from `/context/demo`
- `DynamicContext` from `/scan-frame` or fixture/mock data
- `AnalysisJobResponse` from `/analyze-scene`
- `RecommendationOutput` from `/analysis/{job_id}`

Frontend sends:

- sampled frames to `/scan-frame` once image upload is wired, or
- `DynamicContext` JSON to `/analyze-scene`

Precautions:

- do not run Gemini/OpenAI in the browser
- do not expose API keys
- do not block the camera while analysis is pending
- do not send every frame
- do not start a new detection request while one is pending
- keep old boxes visible until new boxes arrive
- keep demo-frame/mock fallback working

## Lovable

If Lovable is used, generate the actual split-screen demo UI from `docs/interface-concept.md`, then preserve `src/api.ts` and the response types so it can still connect to Piero's backend.

Tailwind is configured because Lovable will likely output Tailwind classes. The starter UI also includes plain CSS in `src/styles.css` so the app has a usable first screen immediately.
