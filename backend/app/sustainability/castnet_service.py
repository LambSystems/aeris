import json
from pathlib import Path
from typing import Any

from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import CASTNETReading


REPO_ROOT = Path(__file__).resolve().parents[3]
PROCESSED_READING_PATH = REPO_ROOT / "data" / "castnet" / "processed" / "current_reading.json"


def load_castnet(location: str | None = None) -> CASTNETReading:
    """Load the processed CASTNET reading used by the sustainability endpoint."""
    if PROCESSED_READING_PATH.exists():
        with PROCESSED_READING_PATH.open("r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)
        return CASTNETReading.model_validate(data)

    return load_mock_castnet()
