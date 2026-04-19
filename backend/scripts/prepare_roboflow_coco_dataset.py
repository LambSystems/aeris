from __future__ import annotations

import argparse
import json
import random
import shutil
import stat
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_DIR = REPO_ROOT / "new_dataset" / "My First Project.coco"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "backend" / "datasets" / "trash_coco_yolo"

CLASS_NAME_OVERRIDES = {
    "can": "can",
    "paper": "paper",
    "water bottle": "bottle",
}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


@dataclass(frozen=True)
class ImageRecord:
    image_id: int
    file_name: str
    width: int
    height: int
    split: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Roboflow COCO export into a YOLO training dataset."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="Path to the Roboflow COCO export directory.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Destination directory for the YOLO dataset.",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.85,
        help="Train split ratio when only one split exists in the source export.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed used for synthetic train/val splits.",
    )
    return parser.parse_args()


def _handle_remove_readonly(func, path, exc_info) -> None:
    _ = exc_info
    Path(path).chmod(stat.S_IWRITE)
    func(path)


def ensure_layout(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir, onexc=_handle_remove_readonly)

    for split in ("train", "val", "test"):
        (output_dir / "images" / split).mkdir(parents=True, exist_ok=True)
        (output_dir / "labels" / split).mkdir(parents=True, exist_ok=True)


def normalized_class_name(raw_name: str) -> str:
    key = raw_name.strip().lower().replace("-", " ")
    key = " ".join(key.split())
    return CLASS_NAME_OVERRIDES.get(key, key.replace(" ", "_"))


def discover_split_dirs(source_dir: Path) -> list[Path]:
    split_dirs = []
    for child in source_dir.iterdir():
        if child.is_dir() and (child / "_annotations.coco.json").exists():
            split_dirs.append(child)
    if not split_dirs:
        raise SystemExit(f"No COCO split folders found in {source_dir}")
    return sorted(split_dirs)


def load_coco_annotations(annotation_path: Path) -> dict:
    return json.loads(annotation_path.read_text(encoding="utf-8"))


def build_category_map(split_dirs: list[Path]) -> tuple[dict[int, int], list[str]]:
    raw_categories: dict[int, str] = {}
    used_category_ids: set[int] = set()

    for split_dir in split_dirs:
        coco = load_coco_annotations(split_dir / "_annotations.coco.json")
        raw_categories.update({category["id"]: category["name"] for category in coco["categories"]})
        used_category_ids.update(annotation["category_id"] for annotation in coco["annotations"])

    normalized_names: list[str] = []
    category_id_map: dict[int, int] = {}

    for category_id in sorted(used_category_ids):
        normalized = normalized_class_name(raw_categories[category_id])
        if normalized not in normalized_names:
            normalized_names.append(normalized)
        category_id_map[category_id] = normalized_names.index(normalized)

    return category_id_map, normalized_names


def synthetic_split(records: list[ImageRecord], train_ratio: float, seed: int) -> dict[int, str]:
    rng = random.Random(seed)
    by_class_presence: dict[str, list[ImageRecord]] = defaultdict(list)
    assignments: dict[int, str] = {}

    for record in records:
        by_class_presence["all"].append(record)

    shuffled = list(by_class_presence["all"])
    rng.shuffle(shuffled)
    cutoff = max(1, min(len(shuffled) - 1, round(len(shuffled) * train_ratio)))
    for index, record in enumerate(shuffled):
        assignments[record.image_id] = "train" if index < cutoff else "val"
    return assignments


def convert_bbox_xywh_to_yolo(bbox: list[float], width: int, height: int) -> tuple[float, float, float, float]:
    x, y, box_width, box_height = [float(value) for value in bbox]
    center_x = (x + box_width / 2) / width
    center_y = (y + box_height / 2) / height
    normalized_width = box_width / width
    normalized_height = box_height / height
    return center_x, center_y, normalized_width, normalized_height


def build_dataset(source_dir: Path, output_dir: Path, train_ratio: float = 0.85, seed: int = 42) -> Path:
    resolved_source = source_dir.resolve()
    resolved_output = output_dir.resolve()
    split_dirs = discover_split_dirs(resolved_source)
    category_id_map, class_names = build_category_map(split_dirs)
    ensure_layout(resolved_output)

    all_records: list[ImageRecord] = []
    split_payloads: list[tuple[str, dict, Path]] = []
    for split_dir in split_dirs:
        coco = load_coco_annotations(split_dir / "_annotations.coco.json")
        split_name = split_dir.name.lower()
        split_payloads.append((split_name, coco, split_dir))
        for image in coco["images"]:
            all_records.append(
                ImageRecord(
                    image_id=int(image["id"]),
                    file_name=str(image["file_name"]),
                    width=int(image["width"]),
                    height=int(image["height"]),
                    split=split_name,
                )
            )

    has_explicit_val_or_test = any(record.split in {"val", "valid", "validation", "test"} for record in all_records)
    synthetic_assignments = synthetic_split(all_records, train_ratio=train_ratio, seed=seed) if not has_explicit_val_or_test else {}

    image_counts_by_split: dict[str, int] = defaultdict(int)
    annotation_counts_by_class: dict[str, int] = defaultdict(int)

    for split_name, coco, split_dir in split_payloads:
        images_by_id = {
            int(image["id"]): ImageRecord(
                image_id=int(image["id"]),
                file_name=str(image["file_name"]),
                width=int(image["width"]),
                height=int(image["height"]),
                split=split_name,
            )
            for image in coco["images"]
        }
        annotations_by_image: dict[int, list[dict]] = defaultdict(list)
        for annotation in coco["annotations"]:
            category_id = int(annotation["category_id"])
            if category_id not in category_id_map:
                continue
            annotations_by_image[int(annotation["image_id"])].append(annotation)

        for image_id, record in images_by_id.items():
            destination_split = split_name
            if destination_split in {"valid", "validation"}:
                destination_split = "val"
            if destination_split == "train" and synthetic_assignments:
                destination_split = synthetic_assignments[image_id]

            image_path = split_dir / record.file_name
            if image_path.suffix.lower() not in IMAGE_SUFFIXES:
                continue

            destination_image_path = resolved_output / "images" / destination_split / image_path.name
            destination_label_path = resolved_output / "labels" / destination_split / f"{image_path.stem}.txt"
            shutil.copy2(image_path, destination_image_path)

            label_lines: list[str] = []
            for annotation in annotations_by_image.get(image_id, []):
                yolo_class_id = category_id_map[int(annotation["category_id"])]
                class_name = class_names[yolo_class_id]
                annotation_counts_by_class[class_name] += 1
                center_x, center_y, box_width, box_height = convert_bbox_xywh_to_yolo(
                    annotation["bbox"],
                    width=record.width,
                    height=record.height,
                )
                label_lines.append(
                    f"{yolo_class_id} {center_x:.6f} {center_y:.6f} {box_width:.6f} {box_height:.6f}"
                )

            destination_label_path.write_text("\n".join(label_lines) + ("\n" if label_lines else ""), encoding="utf-8")
            image_counts_by_split[destination_split] += 1

    names_block = "\n".join(f"  {index}: {name}" for index, name in enumerate(class_names))
    (resolved_output / "data.yaml").write_text(
        "\n".join(
            [
                "path: .",
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

    print(f"Converted COCO dataset from {resolved_source}")
    print(f"Created YOLO dataset at {resolved_output}")
    print(f"data.yaml: {resolved_output / 'data.yaml'}")
    print("")
    for split_name in ("train", "val", "test"):
        if image_counts_by_split.get(split_name):
            print(f"{split_name}: {image_counts_by_split[split_name]} images")
    print("")
    for class_name in class_names:
        print(f"{class_name}: {annotation_counts_by_class[class_name]} annotations")

    return resolved_output


def main() -> int:
    args = parse_args()
    build_dataset(
        source_dir=args.source,
        output_dir=args.output,
        train_ratio=args.train_ratio,
        seed=args.seed,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
