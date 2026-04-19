from app.data import load_scene
from app.schemas import DynamicContext


def scan_demo_frame() -> DynamicContext:
    """Temporary scan adapter.

    Replace this with YOLO inference when Gallo's pipeline is ready. Keep this
    endpoint fast; agentic reasoning should happen through /analyze-scene.
    """
    return load_scene("demo").model_copy(update={"source": "yolo_fixture"})
