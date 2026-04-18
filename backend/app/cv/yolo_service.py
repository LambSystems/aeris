from app.data import load_scene
from app.schemas import DynamicContext


def scan_demo_frame() -> DynamicContext:
    """Temporary scan adapter.

    Replace this with YOLO inference when Gallo's pipeline is ready. The return
    shape should stay identical so frontend/backend integration remains stable.
    """
    return load_scene("demo").model_copy(update={"source": "yolo_fixture"})

