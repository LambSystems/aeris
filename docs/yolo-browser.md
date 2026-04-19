# Browser YOLO Experiment

Branch: `piero/yolo-browser`

This branch can run YOLOv8 in the browser from an exported ONNX model. If the browser model is missing or fails to load, the UI falls back to the existing backend `/scan-frame` endpoint.

## Expected files

```text
ui/public/models/yolo/best.onnx
ui/public/models/yolo/classes.json
```

`classes.json` can be either:

```json
["plastic_bottle", "aluminum_can"]
```

or:

```json
{ "names": ["plastic_bottle", "aluminum_can"] }
```

## Export Gallo's YOLOv8 weights

```powershell
yolo export model=C:\path\to\best.pt format=onnx imgsz=640 simplify=True opset=12
```

Copy the exported model:

```powershell
Copy-Item C:\path\to\best.onnx C:\Users\akuma\repos\aeris\ui\public\models\yolo\best.onnx
```

## Run

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm run dev
```

Open `http://localhost:5173`.

## Force backend fallback

Create `ui/.env`:

```env
VITE_VISION_PROVIDER=backend
```

Then restart Vite.
