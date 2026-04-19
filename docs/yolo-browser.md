# Browser YOLO Experiment

Branch:

```text
piero/yolo-browser
```

Status:

```text
Experimental, not current demo path.
```

The browser YOLO path can load an exported ONNX model, but testing showed it was less smooth than Streamlit + PyTorch CUDA on the demo machine. Keep this as a fallback or future improvement.

---

## Why It Is Not The Main Path

Pros:

- native React camera
- no iframe
- cleaner architecture
- no Python vision server needed

Cons observed:

- ONNX Runtime Web used WASM/CPU path in testing
- UI felt sticky
- large boxes/class instability appeared with the custom model
- Gallo's source model is `.pt`, so conversion/postprocessing adds risk

The current main path is:

```text
React UI + Streamlit iframe + PyTorch CUDA YOLO
```

---

## Expected Browser Files

```text
ui/public/models/yolo/best.onnx
ui/public/models/yolo/classes.json
```

Expected demo classes:

```json
["aluminum_can", "paper", "plastic_bottle"]
```

Some code may also accept:

```json
{ "names": ["aluminum_can", "paper", "plastic_bottle"] }
```

---

## Export YOLOv8 Weights To ONNX

From repo root:

```powershell
conda activate aeris-backend
yolo export model=backend\models\trash-quick-v4-best.pt format=onnx imgsz=640 simplify=True opset=12
```

Copy:

```powershell
Copy-Item backend\models\trash-quick-v4-best.onnx ui\public\models\yolo\best.onnx
```

If `yolo` is unavailable:

```powershell
python -m ultralytics export model=backend\models\trash-quick-v4-best.pt format=onnx imgsz=640 simplify=True opset=12
```

---

## Force Browser YOLO

In `ui/.env`:

```env
VITE_AERIS_API_BASE=http://localhost:8000
VITE_VISION_PROVIDER=browser-yolo
```

Then restart Vite:

```powershell
cd C:\Users\akuma\repos\aeris\ui
npm run dev
```

---

## Force Stable Streamlit Path

In `ui/.env`:

```env
VITE_AERIS_API_BASE=http://localhost:8000
VITE_VISION_PROVIDER=streamlit-embed
VITE_STREAMLIT_URL=http://localhost:8501?embed=true
```

This is the recommended path for the current demo.

---

## If Reviving Browser YOLO

Before switching the team:

1. Confirm model loads.
2. Confirm boxes are correctly scaled.
3. Confirm classes are not random.
4. Confirm FPS feels better than Streamlit.
5. Confirm recommendation still appears in React.
6. Test on the actual demo machine, not only Gallo's machine.

Potential improvements:

- use a smaller model
- use WebGPU execution provider if available
- lower input size
- run inference less often while keeping camera at native FPS
- smooth labels with short-term memory

---

## Recommendation

Do not spend final demo time on browser YOLO unless the Streamlit path fails. The browser path is promising, but Streamlit + GPU is currently more reliable.
