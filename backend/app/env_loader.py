"""Load local environment configuration for backend and Streamlit entrypoints."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


def load_app_env() -> None:
    backend_root = Path(__file__).resolve().parent.parent
    repo_root = backend_root.parent

    load_dotenv(repo_root / ".env")
    load_dotenv(backend_root / ".env")

    config_path = backend_root / "config.toml"
    if not config_path.is_file():
        return

    import tomllib

    with config_path.open("rb") as fh:
        cfg = tomllib.load(fh)

    for key, value in cfg.items():
        if isinstance(value, bool):
            os.environ[key] = "true" if value else "false"
        elif isinstance(value, (int, float)):
            os.environ[key] = str(value)
        elif isinstance(value, str):
            os.environ[key] = value
