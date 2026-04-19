from __future__ import annotations

import argparse
import random
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIRS = ("paper", "can", "bottle")
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class SourceImage:
    class_name: str
    class_id: int
    image_path: Path
    label_path: Path | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a quick YOLO detection dataset from root-level class folders."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "backend" / "datasets" / "trash_quick",
        help="Destination directory for the generated YOLO dataset.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.8,
        help="Train split ratio per class.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for repeatable splits.",
    )
    parser.add_argument(
        "--box-width",
        type=float,
        default=0.92,
        help="Weak-label normalized box width when no label file exists.",
    )
    parser.add_argument(
        "--box-height",
        type=float,
        default=0.92,
        help="Weak-label normalized box height when no label file exists.",
    )
    parser.add_argument(
        "--classes",
        nargs="*",
        default=list(DEFAULT_SOURCE_DIRS),
        help="Root-level source folders to include.",
    )
    return parser.parse_args()


def gather_sources(class_names: list[str]) -> tuple[list[str], list[SourceImage]]:
    sources: list[SourceImage] = []

    for class_id, class_name in enumerate(class_names):
        source_dir = REPO_ROOT / class_name
        if not source_dir.is_dir():
            raise SystemExit(f"Missing source folder: {source_dir}")

        image_paths = sorted(
            path
            for path in source_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_SUFFIXES
        )
        if not image_paths:
            raise SystemExit(f"No images found in {source_dir}")

        for image_path in image_paths:
            label_path = image_path.with_suffix(".txt")
            sources.append(
                SourceImage(
                    class_name=class_name,
                    class_id=class_id,
                    image_path=image_path,
                    label_path=label_path if label_path.exists() else None,
                )
            )

    return class_names, sources


def build_split_map(
    class_names: list[str],
    sources: list[SourceImage],
    train_ratio: float,
    seed: int,
) -> dict[Path, str]:
    rng = random.Random(seed)
    split_map: dict[Path, str] = {}

    for class_name in class_names:
        class_sources = [source for source in sources if source.class_name == class_name]
        rng.shuffle(class_sources)
        if len(class_sources) == 1:
            train_cutoff = 1
        else:
            train_cutoff = max(1, min(len(class_sources) - 1, round(len(class_sources) * train_ratio)))

        for index, source in enumerate(class_sources):
            split_map[source.image_path] = "train" if index < train_cutoff else "val"

    return split_map


def _handle_remove_readonly(func, path, exc_info) -> None:
    _ = exc_info
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def ensure_layout(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir, onexc=_handle_remove_readonly)

    for split in ("train", "val"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def write_label_file(source: SourceImage, target_label_path: Path, box_width: float, box_height: float) -> None:
    if source.label_path is not None:
        shutil.copy2(source.label_path, target_label_path)
        return

    # Weak-label fallback: assume one centered object occupies most of the frame.
    target_label_path.write_text(
        f"{source.class_id} 0.5 0.5 {box_width:.4f} {box_height:.4f}\n",
        encoding="utf-8",
    )


def write_dataset(
    output_dir: Path,
    class_names: list[str],
    sources: list[SourceImage],
    split_map: dict[Path, str],
    box_width: float,
    box_height: float,
) -> None:
    for source in sources:
        split = split_map[source.image_path]
        target_image_path = output_dir / "images" / split / source.image_path.name
        target_label_path = output_dir / "labels" / split / f"{source.image_path.stem}.txt"
        shutil.copy2(source.image_path, target_image_path)
        write_label_file(source, target_label_path, box_width=box_width, box_height=box_height)

    names_block = "\n".join(f"  {index}: {name}" for index, name in enumerate(class_names))
    (output_dir / "data.yaml").write_text(
        "\n".join(
            [
                f"path: {output_dir.as_posix()}",
                "train: images/train",
                "val: images/val",
                "",
                "names:",
                names_block,
                "",
            ]
        ),
        encoding="utf-8",
    )


def print_summary(
    class_names: list[str],
    sources: list[SourceImage],
    split_map: dict[Path, str],
    output_dir: Path,
) -> None:
    print(f"Created dataset at {output_dir}")
    print(f"data.yaml: {output_dir / 'data.yaml'}")
    print("")
    for class_name in class_names:
        class_sources = [source for source in sources if source.class_name == class_name]
        train_count = sum(1 for source in class_sources if split_map[source.image_path] == "train")
        val_count = sum(1 for source in class_sources if split_map[source.image_path] == "val")
        provided_labels = sum(1 for source in class_sources if source.label_path is not None)
        weak_labels = len(class_sources) - provided_labels
        print(
            f"{class_name}: total={len(class_sources)} train={train_count} val={val_count} "
            f"provided_labels={provided_labels} weak_labels={weak_labels}"
        )


def build_dataset(
    output_dir: Path,
    class_names: list[str],
    train_ratio: float = 0.8,
    seed: int = 42,
    box_width: float = 0.92,
    box_height: float = 0.92,
) -> Path:
    resolved_output = output_dir.resolve()
    normalized_classes = [name.strip().lower() for name in class_names if name.strip()]
    if not normalized_classes:
        raise SystemExit("At least one class folder is required.")
    if not 0.5 <= train_ratio < 1:
        raise SystemExit("--train-ratio must be between 0.5 and 1.")
    if not 0 < box_width <= 1 or not 0 < box_height <= 1:
        raise SystemExit("--box-width and --box-height must be between 0 and 1.")

    normalized_classes, sources = gather_sources(normalized_classes)
    split_map = build_split_map(normalized_classes, sources, train_ratio=train_ratio, seed=seed)
    ensure_layout(resolved_output)
    write_dataset(
        resolved_output,
        class_names=normalized_classes,
        sources=sources,
        split_map=split_map,
        box_width=box_width,
        box_height=box_height,
    )
    print_summary(normalized_classes, sources, split_map, resolved_output)
    return resolved_output


def main() -> int:
    args = parse_args()
    build_dataset(
        output_dir=args.output,
        class_names=args.classes,
        train_ratio=args.train_ratio,
        seed=args.seed,
        box_width=args.box_width,
        box_height=args.box_height,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
