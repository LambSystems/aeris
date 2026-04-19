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

## Lovable

If Lovable is used, generate the actual split-screen demo UI from `docs/interface-concept.md`, then preserve `src/api.ts` and the response types so it can still connect to Piero's backend.

Tailwind is configured because Lovable will likely output Tailwind classes. The starter UI also includes plain CSS in `src/styles.css` so the app has a usable first screen immediately.
