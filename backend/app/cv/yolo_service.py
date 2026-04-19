import os
import time
from functools import lru_cache
from io import BytesIO
from pathlib import Path
from typing import Any

from app.data import load_scene
from app.schemas import BoundingBox, DynamicContext, RawDetection, SceneObject

BACKEND_ROOT = Path(__file__).resolve().parents[2]
CACHE_ROOT = BACKEND_ROOT / ".cache"
DEFAULT_CONFIDENCE_THRESHOLD = 0.35
DEFAULT_IMAGE_SIZE = 640
DEFAULT_MODEL_PATH = CACHE_ROOT / "yolov8n.pt"
DEFAULT_INCLUDE_ALL_CLASSES = True
MAX_FRAME_BYTES = 8 * 1024 * 1024
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
FIXTURE_WIDTH = 920
FIXTURE_HEIGHT = 460

LABEL_ALIASES: dict[str, str] = {}

SUSTAINABILITY_LABELS = {
    "bottle",
    "can",
    "cardboard",
    "cup",
    "food_wrapper",
    "glass_container",
    "paper",
    "plastic_bag",
    "recycling_bin",
    "trash",
    "trash_bin",
}

PROTECTION_LABELS = {
    "battery_pack",
    "electronics_case",
    "gloves",
    "metal_tool",
    "plant_pot",
    "seed_tray",
    "storage_bin",
    "tarp",
    "water_jug",
}

RELEVANT_LABELS = SUSTAINABILITY_LABELS | PROTECTION_LABELS | {"misc_item"}

INDOOR_EVIDENCE_LABELS = {
    "bed",
    "book",
    "chair",
    "couch",
    "dining table",
    "keyboard",
    "laptop",
    "microwave",
    "mouse",
    "oven",
    "refrigerator",
    "remote",
    "sink",
    "toaster",
    "toilet",
    "tv",
}

OUTDOOR_EVIDENCE_LABELS = {
    "bench",
    "bicycle",
    "bird",
    "bus",
    "car",
    "dog",
    "fire hydrant",
    "motorcycle",
    "parking meter",
    "potted plant",
    "stop sign",
    "traffic light",
    "truck",
}


def scan_demo_frame() -> DynamicContext:
    """Return the stable fixture-backed scan used when live frame input is absent."""
    return load_scene("demo").model_copy(
        update={
            "source": "yolo_fixture",
            "image_width": FIXTURE_WIDTH,
            "image_height": FIXTURE_HEIGHT,
            "inference_ms": 0.0,
            "model_name": "fixture",
        }
    )


def yolo_config() -> dict[str, Any]:
    """Return static adapter settings without loading the YOLO model."""
    return {
        "accepted_content_types": sorted(ALLOWED_CONTENT_TYPES),
        "max_frame_bytes": MAX_FRAME_BYTES,
        "default_confidence_threshold": _default_confidence_threshold(),
        "default_image_size": _default_image_size(),
        "model_name": _model_name(),
        "include_all_classes": _include_all_classes(),
        "aeris_labels": _aeris_labels(),
        "label_aliases": _label_aliases(),
    }


def scan_frame_bytes(
    image_bytes: bytes,
    image_width: int | None = None,
    image_height: int | None = None,
    confidence_threshold: float | None = None,
    image_size: int | None = None,
) -> DynamicContext:
    """Run YOLO over an uploaded frame and return Aeris-normalized detections.

    Frames are decoded in memory and are not persisted. If the local YOLO model
    cannot be loaded, Aeris keeps the demo stable by returning the fixture scan.
    """
    if not image_bytes:
        return scan_demo_frame()
    if len(image_bytes) > MAX_FRAME_BYTES:
        return scan_demo_frame().model_copy(update={"source": "yolo_frame_too_large_fixture"})

    try:
        started_at = time.perf_counter()
        image = _decode_image(image_bytes)
        decoded_width, decoded_height = image.size
        output_width = image_width or decoded_width
        output_height = image_height or decoded_height
        result = _run_yolo(image, confidence_threshold, image_size)
        objects = _result_to_scene_objects(
            result=result,
            decoded_width=decoded_width,
            decoded_height=decoded_height,
            output_width=output_width,
            output_height=output_height,
        )
        raw_detections = _result_to_raw_detections(
            result=result,
            decoded_width=decoded_width,
            decoded_height=decoded_height,
            output_width=output_width,
            output_height=output_height,
        )
        return DynamicContext(
            source="yolo",
            objects=objects,
            image_width=output_width,
            image_height=output_height,
            inference_ms=round((time.perf_counter() - started_at) * 1000, 2),
            model_name=_model_name(),
            scene_type=_infer_scene_type(result),
            scene_tags=_scene_tags(result, objects),
            raw_detections=raw_detections,
        )
    except Exception:
        return scan_demo_frame().model_copy(update={"source": "yolo_unavailable_fixture"})


def _decode_image(image_bytes: bytes) -> Any:
    _ensure_runtime_dirs()

    from PIL import Image

    image = Image.open(BytesIO(image_bytes))
    return image.convert("RGB")


def _run_yolo(
    image: Any,
    confidence_threshold: float | None = None,
    image_size: int | None = None,
) -> Any:
    model = _load_model()
    threshold = confidence_threshold if confidence_threshold is not None else _default_confidence_threshold()
    imgsz = image_size if image_size is not None else _default_image_size()
    results = model.predict(image, conf=threshold, imgsz=imgsz, verbose=False)
    return results[0]


@lru_cache(maxsize=1)
def _load_model() -> Any:
    _ensure_runtime_dirs()

    from ultralytics import YOLO

    return YOLO(_model_path())


def _model_path() -> str:
    return os.getenv("YOLO_MODEL_PATH", str(DEFAULT_MODEL_PATH))


def _model_name() -> str:
    return Path(_model_path()).name


def _default_confidence_threshold() -> float:
    return float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", DEFAULT_CONFIDENCE_THRESHOLD))


def _default_image_size() -> int:
    return int(os.getenv("YOLO_IMAGE_SIZE", DEFAULT_IMAGE_SIZE))


def _include_all_classes() -> bool:
    value = os.getenv("YOLO_INCLUDE_ALL_CLASSES")
    if value is None:
        return DEFAULT_INCLUDE_ALL_CLASSES
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _ensure_runtime_dirs() -> None:
    matplotlib_dir = CACHE_ROOT / "matplotlib"
    yolo_config_dir = CACHE_ROOT / "ultralytics"
    torch_home = CACHE_ROOT / "torch"

    for path in (matplotlib_dir, yolo_config_dir, torch_home):
        path.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("MPLCONFIGDIR", str(matplotlib_dir))
    os.environ.setdefault("YOLO_CONFIG_DIR", str(yolo_config_dir))
    os.environ.setdefault("TORCH_HOME", str(torch_home))


def _result_to_scene_objects(
    result: Any,
    decoded_width: int,
    decoded_height: int,
    output_width: int,
    output_height: int,
) -> list[SceneObject]:
    names = result.names
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    scale_x = output_width / decoded_width
    scale_y = output_height / decoded_height
    scene_objects: list[SceneObject] = []

    for box in boxes:
        raw_label = _raw_label(names, box)
        normalized_label = display_label(raw_label)
        if normalized_label is None:
            continue

        confidence = round(float(box.conf[0]), 4)
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        bbox = BoundingBox(
            x=round(x1 * scale_x, 2),
            y=round(y1 * scale_y, 2),
            width=round((x2 - x1) * scale_x, 2),
            height=round((y2 - y1) * scale_y, 2),
        )
        distance = _estimate_distance(bbox, output_width, output_height)

        scene_objects.append(
            SceneObject(
                name=normalized_label,
                confidence=confidence,
                distance=distance,
                reachable=distance <= 2.5,
                bbox=bbox,
                raw_label=raw_label,
                category=_object_category(normalized_label),
            )
        )

    return _dedupe_objects(scene_objects)


def _result_to_raw_detections(
    result: Any,
    decoded_width: int,
    decoded_height: int,
    output_width: int,
    output_height: int,
) -> list[RawDetection]:
    names = result.names
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    scale_x = output_width / decoded_width
    scale_y = output_height / decoded_height
    raw_detections: list[RawDetection] = []

    for box in boxes:
        raw_label = _raw_label(names, box)
        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        raw_detections.append(
            RawDetection(
                label=raw_label,
                confidence=round(float(box.conf[0]), 4),
                normalized_name=display_label(raw_label),
                bbox=BoundingBox(
                    x=round(x1 * scale_x, 2),
                    y=round(y1 * scale_y, 2),
                    width=round((x2 - x1) * scale_x, 2),
                    height=round((y2 - y1) * scale_y, 2),
                ),
            )
        )

    return raw_detections


def _raw_label(names: dict[int, str] | list[str], box: Any) -> str:
    class_id = int(box.cls[0])
    if isinstance(names, dict):
        return names.get(class_id, "unknown")
    return names[class_id] if class_id < len(names) else "unknown"


def _raw_labels(result: Any) -> list[str]:
    names = result.names
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return []

    return [_raw_label(names, box).strip().lower().replace("_", " ") for box in boxes]


def _infer_scene_type(result: Any) -> str:
    raw_labels = set(_raw_labels(result))
    indoor_hits = raw_labels & INDOOR_EVIDENCE_LABELS
    outdoor_hits = raw_labels & OUTDOOR_EVIDENCE_LABELS

    if indoor_hits and not outdoor_hits:
        return "indoor"
    if outdoor_hits and not indoor_hits:
        return "outdoor"
    if indoor_hits and outdoor_hits:
        return "mixed"
    return "unknown"


def _scene_tags(result: Any, objects: list[SceneObject]) -> list[str]:
    raw_labels = set(_raw_labels(result))
    tags: list[str] = []

    if raw_labels & INDOOR_EVIDENCE_LABELS:
        tags.append("indoor_cues")
    if raw_labels & OUTDOOR_EVIDENCE_LABELS:
        tags.append("outdoor_cues")
    if any(scene_object.name in SUSTAINABILITY_LABELS for scene_object in objects):
        tags.append("sustainability_items_visible")
    if any(scene_object.name in {"trash_bin", "recycling_bin", "storage_bin"} for scene_object in objects):
        tags.append("collection_container_visible")
    if not objects and raw_labels:
        tags.append("detections_filtered_as_irrelevant")

    return tags


def normalize_label(raw_label: str) -> str | None:
    return raw_label.strip().lower().replace("_", " ")


def display_label(raw_label: str) -> str | None:
    normalized = normalize_label(raw_label)
    if normalized:
        return normalized
    if _include_all_classes():
        return raw_label.strip().lower().replace("_", " ")
    return None


def _object_category(aeris_label: str) -> str:
    if aeris_label in SUSTAINABILITY_LABELS:
        return "sustainability_item"
    if aeris_label in PROTECTION_LABELS:
        return "protection_resource"
    return "other"


def _aeris_labels() -> list[str]:
    return sorted(RELEVANT_LABELS)


@lru_cache(maxsize=1)
def _label_aliases() -> dict[str, str]:
    return dict(LABEL_ALIASES)


def _estimate_distance(bbox: BoundingBox, image_width: int, image_height: int) -> float:
    image_area = max(image_width * image_height, 1)
    box_area = max(bbox.width * bbox.height, 1)
    area_ratio = min(box_area / image_area, 1)
    vertical_position = min((bbox.y + bbox.height) / max(image_height, 1), 1)

    size_distance = 3.0 - (area_ratio * 8.0)
    vertical_adjustment = (1.0 - vertical_position) * 0.7
    return round(min(max(size_distance + vertical_adjustment, 0.5), 3.5), 2)


def _dedupe_objects(objects: list[SceneObject]) -> list[SceneObject]:
    best_by_name: dict[str, SceneObject] = {}
    for scene_object in objects:
        existing = best_by_name.get(scene_object.name)
        if existing is None or scene_object.confidence > existing.confidence:
            best_by_name[scene_object.name] = scene_object

    return sorted(best_by_name.values(), key=lambda scene_object: scene_object.confidence, reverse=True)
