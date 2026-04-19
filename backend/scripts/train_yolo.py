from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
CACHE_ROOT = BACKEND_ROOT / ".cache"
DEFAULT_MODEL_PATH = CACHE_ROOT / "yolov8n.pt"
DEFAULT_DATASET_PATH = BACKEND_ROOT / "training" / "can_bottle.data.example.yaml"
DEFAULT_PROJECT_PATH = CACHE_ROOT / "yolo-runs"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fine-tune a local YOLOv8 model on a small detection dataset."
    )
    parser.add_argument(
        "--data",
        type=Path,
        default=DEFAULT_DATASET_PATH,
        help="Path to a YOLO detection dataset YAML file.",
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL_PATH,
        help="Base model checkpoint to fine-tune.",
    )
    parser.add_argument("--epochs", type=int, default=20, help="Training epochs.")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size.")
    parser.add_argument(
        "--batch",
        type=int,
        default=8,
        help="Batch size. Lower this if you run out of memory.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=5,
        help="Early stopping patience in epochs.",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        help='Training device, for example "cpu", "0", or "0,1".',
    )
    parser.add_argument(
        "--project",
        type=Path,
        default=DEFAULT_PROJECT_PATH,
        help="Directory for training outputs.",
    )
    parser.add_argument(
        "--name",
        default="can-bottle-quick",
        help="Run name inside the project directory.",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=0,
        help="Dataloader workers. Keep 0 on Windows for the least drama.",
    )
    parser.add_argument(
        "--exist-ok",
        action="store_true",
        help="Allow reusing an existing output directory.",
    )
    return parser.parse_args()


def ensure_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    model_path = args.model.resolve()
    data_path = args.data.resolve()
    project_path = args.project.resolve()

    if not model_path.exists():
        raise SystemExit(f"Base model not found: {model_path}")
    if not data_path.exists():
        raise SystemExit(f"Dataset YAML not found: {data_path}")

    project_path.mkdir(parents=True, exist_ok=True)
    return model_path, data_path, project_path


def main() -> int:
    args = parse_args()
    model_path, data_path, project_path = ensure_paths(args)

    try:
        from ultralytics import YOLO
    except Exception as error:
        raise SystemExit(f"Could not import ultralytics: {error}") from error

    print(f"Fine-tuning from {model_path}")
    print(f"Using dataset {data_path}")
    print(f"Saving runs to {project_path / args.name}")

    model = YOLO(str(model_path))
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        device=args.device,
        project=str(project_path),
        name=args.name,
        workers=args.workers,
        exist_ok=args.exist_ok,
        pretrained=True,
        verbose=True,
    )

    run_dir = Path(results.save_dir)
    best_weights = run_dir / "weights" / "best.pt"
    last_weights = run_dir / "weights" / "last.pt"

    print("")
    print(f"Training finished. Run dir: {run_dir}")
    if best_weights.exists():
        print(f"Best weights: {best_weights}")
        print(f"Set YOLO_MODEL_PATH={best_weights} to use this model in the backend.")
    elif last_weights.exists():
        print(f"No best checkpoint found, but last weights exist: {last_weights}")
        print(f"Set YOLO_MODEL_PATH={last_weights} if you want to try it.")
    else:
        print("Training completed, but no checkpoint was found where expected.")

    print("")
    print("Reminder: YOLO detection training needs one label .txt file per image.")
    print("Each line must be: <class_id> <x_center> <y_center> <width> <height>")
    print("All coordinates must be normalized to 0-1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
