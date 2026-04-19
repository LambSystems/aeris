import cv2
import numpy as np
from ultralytics import YOLO

from app.data import load_scene
from app.schemas import BoundingBox, DynamicContext, SceneObject

# Reference resolution the frontend canvas uses
CANVAS_W, CANVAS_H = 900, 480
CONF_THRESHOLD = 0.45

# COCO class names → our sustainability labels.
# Unmapped classes pass through as-is.
COCO_TO_SUSTAINABILITY: dict[str, str] = {
    "bottle": "soda_can",
    "cup":    "styrofoam_cup",
}

_model: YOLO | None = None


def _get_model() -> YOLO:
    global _model
    if _model is None:
        _model = YOLO("yolo11s.pt")
    return _model


def scan_demo_frame() -> DynamicContext:
    return load_scene("demo").model_copy(update={"source": "yolo_fixture"})


def scan_frame_from_bytes(image_bytes: bytes) -> DynamicContext:
    arr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return DynamicContext(objects=[], source="yolo_live")

    h, w = img.shape[:2]
    results = _get_model()(img, verbose=False)[0]

    objects: list[SceneObject] = []
    for box in results.boxes:
        conf = float(box.conf[0])
        if conf < CONF_THRESHOLD:
            continue

        coco_name = _get_model().names[int(box.cls[0])]
        obj_name = COCO_TO_SUSTAINABILITY.get(coco_name, coco_name)

        x1, y1, x2, y2 = box.xyxy[0].tolist()
        objects.append(SceneObject(
            name=obj_name,
            confidence=round(conf, 3),
            distance=1.0,
            reachable=True,
            bbox=BoundingBox(
                x=round(x1 / w * CANVAS_W, 1),
                y=round(y1 / h * CANVAS_H, 1),
                width=round((x2 - x1) / w * CANVAS_W, 1),
                height=round((y2 - y1) / h * CANVAS_H, 1),
            ),
        ))

    return DynamicContext(objects=objects, source="yolo_live")
