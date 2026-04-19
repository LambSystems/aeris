from app.data import load_scene
from app.schemas import DynamicContext


def scan_demo_frame() -> DynamicContext:
    """Temporary scan adapter.

    Replace this with YOLO inference when Gallo's pipeline is ready. Keep this
    endpoint fast; agentic reasoning should happen through /analyze-scene.
    """
    return load_scene("demo").model_copy(update={"source": "yolo_fixture"})


def detect_objects(
    image_bytes: bytes,
    filename: str | None = None,
    content_type: str | None = None,
) -> DynamicContext:
    """Run object detection for one sampled frame.

    Gallo should wire YOLO here and return the same DynamicContext shape.
    Until then, this preserves the frontend/backend contract by returning the
    fixture detections with a source that makes the fallback visible.
    """
    if not image_bytes:
        return scan_demo_frame()

    # TODO(Gallo): decode image_bytes, run YOLO, normalize labels, return boxes
    # in the sampled frame coordinate space.
    return scan_demo_frame().model_copy(update={"source": "upload_yolo_stub"})
