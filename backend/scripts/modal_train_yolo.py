from __future__ import annotations

import json
from pathlib import Path

import modal


APP_NAME = "aeris-yolo-trash-train"
DATASET_VOLUME_NAME = "aeris-yolo-trash-dataset"
CHECKPOINT_VOLUME_NAME = "aeris-yolo-trash-checkpoints"
REMOTE_DATASET_ROOT = Path("/vol/dataset")
REMOTE_CHECKPOINT_ROOT = Path("/vol/checkpoints")
REMOTE_RUNS_ROOT = REMOTE_CHECKPOINT_ROOT / "runs"

app = modal.App(APP_NAME)
dataset_volume = modal.Volume.from_name(DATASET_VOLUME_NAME, create_if_missing=True)
checkpoint_volume = modal.Volume.from_name(CHECKPOINT_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("libgl1", "libglib2.0-0", "curl")
    .pip_install(
        "numpy==1.26.4",
        "ultralytics==8.3.49",
        "pillow==11.0.0",
        "pyyaml==6.0.2",
    )
)


def _resolve_latest_coco_export() -> Path:
    new_dataset_root = Path(__file__).resolve().parents[2] / "new_dataset"
    if not new_dataset_root.exists():
        raise RuntimeError(f"Dataset root not found at {new_dataset_root}")

    candidates = sorted(
        {
            annotation_path.parent.parent.resolve()
            for annotation_path in new_dataset_root.rglob("_annotations.coco.json")
        },
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    if not candidates:
        raise RuntimeError(f"No COCO export with _annotations.coco.json found under {new_dataset_root}")
    return candidates[0]


@app.function(
    image=image,
    gpu="L4",
    timeout=60 * 60,
    volumes={
        str(REMOTE_DATASET_ROOT): dataset_volume,
        str(REMOTE_CHECKPOINT_ROOT): checkpoint_volume,
    },
)
def train_yolo(
    epochs: int = 30,
    imgsz: int = 640,
    batch: int = 16,
    patience: int = 8,
    run_name: str = "trash-quick",
) -> dict[str, str]:
    from ultralytics import YOLO

    data_yaml = REMOTE_DATASET_ROOT / "trash_quick" / "data.yaml"
    if not data_yaml.exists():
        raise RuntimeError(f"Dataset config not found at {data_yaml}")
    trainable_data_yaml = Path("/tmp") / "trash_quick.data.yaml"
    data_lines = data_yaml.read_text(encoding="utf-8").splitlines()
    if not data_lines:
        raise RuntimeError(f"Dataset config is empty at {data_yaml}")
    data_lines[0] = f"path: {(REMOTE_DATASET_ROOT / 'trash_quick').as_posix()}"
    trainable_data_yaml.write_text("\n".join(data_lines) + "\n", encoding="utf-8")

    REMOTE_RUNS_ROOT.mkdir(parents=True, exist_ok=True)
    model = YOLO("yolov8m.pt")
    results = model.train(
        data=str(trainable_data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=patience,
        device=0,
        project=str(REMOTE_RUNS_ROOT),
        name=run_name,
        pretrained=True,
        exist_ok=True,
        verbose=True,
    )

    run_dir = Path(results.save_dir)
    best_weights = run_dir / "weights" / "best.pt"
    last_weights = run_dir / "weights" / "last.pt"
    summary = {
        "run_dir": str(run_dir),
        "best_weights": str(best_weights) if best_weights.exists() else "",
        "last_weights": str(last_weights) if last_weights.exists() else "",
        "data_yaml": str(trainable_data_yaml),
    }
    (run_dir / "training_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    checkpoint_volume.commit()
    return summary


@app.local_entrypoint()
def main(
    epochs: int = 30,
    imgsz: int = 640,
    batch: int = 16,
    patience: int = 8,
    run_name: str = "trash-quick",
) -> None:
    from prepare_roboflow_coco_dataset import build_dataset

    dataset_root = Path(__file__).resolve().parents[1] / "datasets" / "trash_coco_yolo"
    source_dir = _resolve_latest_coco_export()
    build_dataset(
        source_dir=source_dir,
        output_dir=dataset_root,
        train_ratio=0.85,
        seed=42,
    )
    data_yaml = dataset_root / "data.yaml"
    data_lines = data_yaml.read_text(encoding="utf-8").splitlines()
    if data_lines:
        data_lines[0] = "path: ."
        data_yaml.write_text("\n".join(data_lines) + "\n", encoding="utf-8")

    with dataset_volume.batch_upload(force=True) as batch_upload:
        batch_upload.put_directory(dataset_root, "/trash_quick")

    result = train_yolo.remote(
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        patience=patience,
        run_name=run_name,
    )

    print("Training finished.")
    print(json.dumps(result, indent=2))
    print("")
    print(f"Source dataset: {source_dir}")
    print(f"Dataset volume: {DATASET_VOLUME_NAME}")
    print(f"Checkpoint volume: {CHECKPOINT_VOLUME_NAME}")
    print("To inspect checkpoints later:")
    print(f"  modal volume ls {CHECKPOINT_VOLUME_NAME} /runs/{run_name}/weights")
