# Aeris UI

Clean React/Vite frontend for the Aeris demo. It is intentionally separate from the older `frontend/` app and Chau's `aeris ui/` scratch workspace so the team can integrate without merge-conflict pain.

## Contract

The UI consumes the backend only:

- `GET /health` to show API status.
- `GET /context/fixed?latitude=<lat>&longitude=<lng>` for location, weather, air quality, alerts, and CASTNET context.
- `POST /scan-frame` with multipart `file` for YOLO detections and bounding boxes.
- `POST /sustainability/detect` for the recommendation panel after a stable detection.

The UI does not run YOLO locally. It renders the webcam locally, samples compressed frames about every 700 ms, and draws returned backend boxes on top of the live video.

## Run

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm install
npm run dev
```

Open `http://localhost:5173`.

When demoing from a phone on the same Wi-Fi, run the backend with `--host 0.0.0.0`, open the UI with the laptop LAN IP, and the UI will call the backend on that same host:

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
npm run dev
```

Example browser URL: `http://192.168.1.25:5173`.

If the backend uses a different URL, create `.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```
