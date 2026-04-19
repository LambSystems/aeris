from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import cv2


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

DEFAULT_WORLD_MODEL = BACKEND_ROOT / ".cache" / "yolov8s-world.pt"

from app.cv.yolo_service import _default_confidence_threshold, _ensure_runtime_dirs, _load_model, display_label


BOX_COLOR = (0, 208, 132)
TEXT_COLOR = (15, 15, 15)
PANEL_COLOR = (0, 208, 132)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run live YOLO webcam detection with Aeris label normalization."
    )
    parser.add_argument("--camera", type=int, default=0, help="Webcam index.")
    parser.add_argument("--imgsz", type=int, default=320, help="Inference image size.")
    parser.add_argument(
        "--conf",
        type=float,
        default=float(_default_confidence_threshold()),
        help="Confidence threshold.",
    )
    parser.add_argument(
        "--show-raw",
        action="store_true",
        help="Show detections even when Aeris does not currently map the raw YOLO label.",
    )
    parser.add_argument(
        "--frame-skip",
        type=int,
        default=1,
        help="Run inference every Nth frame. Higher values increase display FPS on slower CPUs.",
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1280,
        help="Requested webcam width.",
    )
    parser.add_argument(
        "--height",
        type=int,
        default=720,
        help="Requested webcam height.",
    )
    parser.add_argument(
        "--world",
        action="store_true",
        help="Use YOLO-World with text prompts instead of the standard closed-set YOLO model.",
    )
    parser.add_argument(
        "--world-model",
        default=str(DEFAULT_WORLD_MODEL),
        help="YOLO-World checkpoint name or path.",
    )
    parser.add_argument(
        "--classes",
        default="trash,litter,garbage,trash bin,garbage bin,recycling bin,plastic bag,bottle,can,cup,paper cup,paper plate,tissue,wrapper,cardboard",
        help="Comma-separated class prompts for YOLO-World.",
    )
    return parser.parse_args()


def raw_label(names: dict[int, str] | list[str], box: object) -> str:
    class_id = int(box.cls[0])
    if isinstance(names, dict):
        return names.get(class_id, "unknown")
    return names[class_id] if class_id < len(names) else "unknown"


def draw_label(frame: object, label: str, x1: int, y1: int) -> None:
    (text_width, text_height), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
    top = max(y1 - text_height - 10, 0)
    cv2.rectangle(frame, (x1, top), (x1 + text_width + 10, top + text_height + 10), PANEL_COLOR, -1)
    cv2.putText(
        frame,
        label,
        (x1 + 5, top + text_height + 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        TEXT_COLOR,
        2,
        cv2.LINE_AA,
    )


def load_detection_model(args: argparse.Namespace) -> tuple[object, list[str] | None]:
    if not args.world:
        return _load_model(), None

    from ultralytics.models import YOLOWorld

    class_prompts = [value.strip() for value in args.classes.split(",") if value.strip()]
    model = YOLOWorld(args.world_model)
    if class_prompts:
        model.set_classes(class_prompts)
    return model, class_prompts


def main() -> int:
    args = parse_args()
    _ensure_runtime_dirs()

    capture = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    if not capture.isOpened():
        raise SystemExit(f"Could not open webcam index {args.camera}.")

    model, class_prompts = load_detection_model(args)
    frame_index = 0
    last_result = None
    last_inference_ms = 0.0
    smoothed_fps = 0.0
    started_at = time.perf_counter()

    print("Starting live YOLO. Press q to quit.")

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break

            frame_index += 1

            should_infer = last_result is None or frame_index % max(args.frame_skip, 1) == 0
            if should_infer:
                inference_started = time.perf_counter()
                if args.world:
                    results = model.predict(
                        source=frame,
                        conf=args.conf,
                        imgsz=args.imgsz,
                        verbose=False,
                    )
                else:
                    results = model.track(
                        source=frame,
                        conf=args.conf,
                        imgsz=args.imgsz,
                        persist=True,
                        verbose=False,
                        tracker="bytetrack.yaml",
                    )
                last_result = results[0]
                last_inference_ms = (time.perf_counter() - inference_started) * 1000

            if last_result is not None:
                names = last_result.names
                boxes = getattr(last_result, "boxes", None)
                if boxes is not None:
                    for box in boxes:
                        raw = raw_label(names, box).strip().lower().replace("_", " ")
                        normalized = display_label(raw)
                        if normalized is None and not args.show_raw:
                            continue

                        x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
                        confidence = float(box.conf[0])
                        track_id = None
                        if not args.world and getattr(box, "id", None) is not None:
                            track_id = int(box.id[0])

                        label_name = normalized or raw
                        if track_id is not None:
                            label = f"{label_name} #{track_id} {confidence:.2f}"
                        else:
                            label = f"{label_name} {confidence:.2f}"

                        cv2.rectangle(frame, (x1, y1), (x2, y2), BOX_COLOR, 2)
                        draw_label(frame, label, x1, y1)

            now = time.perf_counter()
            elapsed = max(now - started_at, 1e-6)
            instantaneous_fps = 1.0 / max(now - getattr(main, "_last_frame_time", now), 1e-6)
            main._last_frame_time = now  # type: ignore[attr-defined]
            smoothed_fps = instantaneous_fps if smoothed_fps == 0.0 else (smoothed_fps * 0.85) + (instantaneous_fps * 0.15)

            overlay_lines = [
                f"Model {'YOLO-World' if args.world else 'YOLO'}",
                f"FPS {smoothed_fps:.1f}",
                f"Inference {last_inference_ms:.1f} ms",
                f"imgsz {args.imgsz}",
                f"conf {args.conf:.2f}",
                f"frames {frame_index}",
                f"uptime {elapsed:.1f}s",
            ]
            if args.world and class_prompts:
                overlay_lines.append(f"prompts {len(class_prompts)}")

            overlay_y = 28
            for line in overlay_lines:
                cv2.putText(
                    frame,
                    line,
                    (12, overlay_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    BOX_COLOR,
                    2,
                    cv2.LINE_AA,
                )
                overlay_y += 26

            cv2.imshow("Aeris Realtime YOLO", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        capture.release()
        cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    sys.exit(main())
