import json
from pathlib import Path

from app.sustainability.schemas import YOLODetection

STATE_DIR = Path(__file__).resolve().parents[2] / ".tmp" / "vision"
LATEST_DETECTION_PATH = STATE_DIR / "latest_detection.json"


def write_latest_detection(detection: YOLODetection) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_path = LATEST_DETECTION_PATH.with_suffix(".tmp")
    tmp_path.write_text(detection.model_dump_json(), encoding="utf-8")
    tmp_path.replace(LATEST_DETECTION_PATH)


def read_latest_detection() -> YOLODetection | None:
    if not LATEST_DETECTION_PATH.exists():
        return None
    try:
        payload = json.loads(LATEST_DETECTION_PATH.read_text(encoding="utf-8"))
        return YOLODetection.model_validate(payload)
    except Exception:
        return None
