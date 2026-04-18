import json
from pathlib import Path
from typing import Any

from app.schemas import DynamicContext, FixedContext


REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = REPO_ROOT / "data"


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_demo_context() -> FixedContext:
    path = DATA_ROOT / "castnet" / "processed" / "demo_profile.json"
    return FixedContext.model_validate(_read_json(path))


def load_scene(scene: str = "demo") -> DynamicContext:
    filename = "demo_scene_after_move.json" if scene == "after_move" else "demo_scene.json"
    path = DATA_ROOT / "sample_inputs" / filename
    return DynamicContext.model_validate(_read_json(path))
