import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.env_loader import load_app_env

load_app_env()

from app.cv.pipeline import run

if __name__ == "__main__":
    # Pass a video file path as argument, or leave empty for webcam
    source = sys.argv[1] if len(sys.argv) > 1 else 0
    run(source)
