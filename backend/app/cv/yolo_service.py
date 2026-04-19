import os
from pathlib import Path
from typing import Any

from app.data import load_scene
from app.schemas import BoundingBox, DynamicContext, SceneObject


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = BACKEND_ROOT / "yolov8n.pt"
CONF_THRESHOLD = 0.20
COCO_TO_SUSTAINABILITY: dict[str, str] = {
    "bottle": "plastic_bottle",
    "cup": "styrofoam_cup",
    "wine glass": "glass_bottle",
    "vase": "glass_bottle",
    "bowl": "food_wrapper",
    "banana": "food_wrapper",
    "apple": "food_wrapper",
    "orange": "food_wrapper",
    "sandwich": "food_wrapper",
    "book": "cardboard_box",
    "backpack": "plastic_bag",
    "handbag": "plastic_bag",
    "suitcase": "plastic_bag",
}
ADVICE_CLASSES = {
    "soda_can",
    "plastic_bottle",
    "cardboard_box",
    "cigarette_butt",
    "plastic_bag",
    "food_wrapper",
    "glass_bottle",
    "styrofoam_cup",
}

_model: Any | None = None


def scan_demo_frame() -> DynamicContext:
    return load_scene("demo").model_copy(update={"source": "yolo_fixture"})


def detect_objects(
    image_bytes: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> DynamicContext:
    return scan_frame_from_bytes(image_bytes)


def scan_frame_from_bytes(
    image_bytes: bytes,
    include_raw: bool = False,
    confidence_threshold: float = CONF_THRESHOLD,
) -> DynamicContext:
    """Run YOLO on one uploaded image, falling back safely if CV is unavailable."""
    if not image_bytes:
        return scan_demo_frame()

    try:
        cv2, np = _load_cv_modules()
        img = _decode_image(cv2, np, image_bytes)
        if img is None:
            return DynamicContext(objects=[], source="yolo_live")

        h, w = img.shape[:2]
        model = _get_model()
        results = model(img, verbose=False)[0]

        objects: list[SceneObject] = []
        for box in results.boxes:
            conf = float(box.conf[0])
            if conf < confidence_threshold:
                continue

            coco_name = model.names[int(box.cls[0])]
            obj_name = COCO_TO_SUSTAINABILITY.get(coco_name, coco_name)
            if not include_raw and obj_name not in ADVICE_CLASSES:
                continue
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            objects.append(
                SceneObject(
                    name=obj_name,
                    confidence=round(conf, 3),
                    distance=1.0,
                    reachable=True,
                    bbox=BoundingBox(
                        x=round(x1, 1),
                        y=round(y1, 1),
                        width=round(x2 - x1, 1),
                        height=round(y2 - y1, 1),
                    ),
                )
            )

        return DynamicContext(
            objects=objects,
            source="yolo_live_raw" if include_raw else "yolo_live",
            frame_width=w,
            frame_height=h,
        )
    except Exception:
        return scan_demo_frame().model_copy(update={"source": "yolo_unavailable_fallback"})


def _load_cv_modules() -> tuple[Any, Any]:
    import cv2
    import numpy as np

    return cv2, np


def _decode_image(cv2: Any, np: Any, image_bytes: bytes) -> Any:
    arr = np.frombuffer(image_bytes, np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def _get_model() -> Any:
    global _model
    if _model is None:
        from ultralytics import YOLO

        model_path = os.environ.get("AERIS_YOLO_MODEL") or str(DEFAULT_MODEL_PATH)
        _model = YOLO(model_path)
    return _model
