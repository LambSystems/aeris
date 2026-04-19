"""Load `.env` then optional root-level string keys from `config.toml` into the process environment."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_app_env() -> None:
    backend_root = Path(__file__).resolve().parent.parent
    load_dotenv(backend_root / ".env")
    config_path = backend_root / "config.toml"
    if not config_path.is_file():
        return
    import tomllib

    with config_path.open("rb") as fh:
        cfg = tomllib.load(fh)
    for key, value in cfg.items():
        if isinstance(value, str):
            os.environ[key] = value
