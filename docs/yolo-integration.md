# YOLO Integration

## Owner

Gallo owns the YOLO adapter boundary:

- receive sampled image frames
- run object detection
- normalize detector labels into Aeris labels
- return `DynamicContext`

The CV layer must not call Gemini/OpenAI and must not decide protection advice.

## Backend Endpoint

```text
GET /scan-frame/config
```

Returns accepted image types, max frame size, default confidence threshold, model name, Aeris labels, and label aliases.

```text
POST /scan-frame
Content-Type: multipart/form-data
```

Fields:

```text
frame: JPEG, PNG, or WebP blob
image_width: original sampled frame width
image_height: original sampled frame height
confidence_threshold: optional 0-1 override
image_size: optional YOLO inference size, 320-1600
```

If no `frame` is sent, the endpoint returns the fixture scan so the demo remains usable.

## Output

The endpoint returns `DynamicContext`:

```json
{
  "source": "yolo",
  "image_width": 640,
  "image_height": 360,
  "inference_ms": 72.4,
  "model_name": "yolov8n.pt",
  "scene_type": "indoor",
  "scene_tags": ["indoor_cues", "sustainability_items_visible"],
  "raw_detections": [
    {
      "label": "bottle",
      "confidence": 0.91,
      "normalized_name": "bottle",
      "bbox": {
        "x": 120,
        "y": 80,
        "width": 180,
        "height": 210
      }
    }
  ],
  "objects": [
    {
      "name": "bottle",
      "raw_label": "bottle",
      "category": "sustainability_item",
      "confidence": 0.91,
      "distance": 1.4,
      "reachable": true,
      "bbox": {
        "x": 120,
        "y": 80,
        "width": 180,
        "height": 210
      }
    }
  ]
}
```

Boxes are always in the same coordinate space as `image_width` and `image_height`.
`objects` contains Aeris-relevant normalized detections. `raw_detections` contains the unfiltered YOLO labels for debugging detector behavior.

The current Aeris sustainability labels are:

```text
bottle
can
cardboard
cup
food_wrapper
glass_container
paper
plastic_bag
recycling_bin
trash
trash_bin
```

The original protection-resource labels are still supported:

```text
battery_pack
electronics_case
gloves
metal_tool
plant_pot
seed_tray
storage_bin
tarp
water_jug
```

Important YOLOv8n limitations:

- The default COCO model does not have a dedicated `can` class. It may detect a can as `bottle`, `cup`, or not detect it at all.
- Small or partially occluded bottles may only appear at very low confidence, even with larger `image_size`.

For reliable can/trash/bin detection, use a fine-tuned model via `YOLO_MODEL_PATH` and map its raw labels with `YOLO_LABEL_ALIASES_PATH`.

For the current Aeris custom trash model, training notes and expected accuracy are documented in:

```text
docs/trash-model.md
```

## Frontend Usage

Use `scanFrame` from `frontend/src/api.ts`:

```ts
import { scanFrame } from "./api";
import { captureVideoFrame } from "./cameraFrame";

const captured = await captureVideoFrame(video);
const dynamicContext = await scanFrame({
  frame: captured.frame,
  imageWidth: captured.imageWidth,
  imageHeight: captured.imageHeight,
  confidenceThreshold: 0.35,
});
```

Then send the returned `dynamicContext` to `/analyze-scene`. Do not send every frame. Sample only after user action, meaningful object changes, or a cooldown.

## Runtime Settings

```text
YOLO_MODEL_PATH=backend/.cache/yolov8n.pt
YOLO_CONFIDENCE_THRESHOLD=0.35
YOLO_IMAGE_SIZE=640
YOLO_LABEL_ALIASES_PATH=backend/app/cv/label_aliases.json
```

Runtime caches and downloaded model weights live under `backend/.cache/` by default and are ignored by git.

`YOLO_LABEL_ALIASES_PATH` should point to a JSON object that maps raw detector labels to Aeris labels:

```json
{
  "aluminum can": "can",
  "soda can": "can",
  "seed tray": "seed_tray",
  "powerbank": "battery_pack",
  "plastic cover": "tarp",
  "trash can": "trash_bin",
  "recycling bin": "recycling_bin",
  "food wrapper": "food_wrapper"
}
```

## Failure Behavior

- Missing frame: returns fixture scan with `source: "yolo_fixture"`.
- Invalid content type: returns HTTP `415`.
- Frame over 8 MB: returns HTTP `413`.
- YOLO/model runtime failure: returns fixture scan with `source: "yolo_unavailable_fixture"`.

The fixture fallback is deliberate. It keeps the demo stable without hiding invalid API usage from the frontend.
