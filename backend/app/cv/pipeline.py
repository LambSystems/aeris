"""Lightweight OpenCV pipeline helpers for local YOLO demos."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import cv2
from ultralytics import YOLO

from app.context.fixed_context_service import load_fixed_context
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection


CONFIDENCE_THRESHOLD = 0.35
COOLDOWN_SECONDS = 10
WATCHED_LABELS = {"can", "paper", "bottle"}


@dataclass
class PipelineState:
    advice: SustainabilityAdvice | None = None
    advice_timestamp: float = 0.0
    last_triggered: dict[str, float] = field(default_factory=dict)
    frame_count: int = 0


def _normalize_label(label: str) -> str:
    return label.strip().lower().replace("_", " ")


def _model_path() -> str:
    env_path = os.getenv("YOLO_MODEL_PATH")
    if env_path:
        return env_path

    backend_root = Path(__file__).resolve().parents[2]
    preferred = backend_root / "models" / "trash-quick-v4-best.pt"
    if preferred.exists():
        return str(preferred)
    return str(backend_root / "yolov8n.pt")


def _draw_box(frame, x1, y1, x2, y2, label: str, conf: float, triggered: bool) -> None:
    color = (0, 200, 80) if triggered else (200, 200, 200)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text = f"{label} {conf:.0%}"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, text, (x1 + 2, max(12, y1 - 4)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)


def _draw_advice(frame, advice: SustainabilityAdvice) -> None:
    h, w = frame.shape[:2]
    panel_y = max(0, h - 130)
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, panel_y), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(
        frame,
        f"Detected: {advice.object_detected} ({advice.confidence:.0%})",
        (12, panel_y + 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (100, 230, 120),
        1,
    )

    for index, line in enumerate(_wrap(advice.context, max_chars=90)):
        cv2.putText(
            frame,
            line,
            (12, panel_y + 46 + index * 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (220, 220, 220),
            1,
        )

    action_lines = _wrap(f"Action: {advice.action}", max_chars=90)
    base_y = panel_y + 46 + len(_wrap(advice.context, 90)) * 20 + 6
    for index, line in enumerate(action_lines):
        cv2.putText(
            frame,
            line,
            (12, base_y + index * 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (80, 200, 255),
            1,
        )


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word
    if current:
        lines.append(current)
    return lines


def _should_trigger(state: PipelineState, obj_class: str) -> bool:
    return time.time() - state.last_triggered.get(obj_class, 0.0) >= COOLDOWN_SECONDS


def run(source: int | str = 0) -> None:
    """Run a local webcam/file demo using the current YOLO model."""

    model = YOLO(_model_path())
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source: {source}")

    fixed_context = load_fixed_context()
    state = PipelineState()

    print(f"Pipeline running with {_model_path()}")
    print(f"Watching for: {sorted(WATCHED_LABELS)}")
    print("Press q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        state.frame_count += 1
        result = model.track(source=frame, conf=0.10, imgsz=320, persist=True, verbose=False)[0]

        for box in result.boxes:
            conf = float(box.conf[0])
            raw_name = model.names[int(box.cls[0])]
            label = _normalize_label(raw_name)
            if label not in WATCHED_LABELS:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            triggered = conf >= CONFIDENCE_THRESHOLD
            _draw_box(frame, x1, y1, x2, y2, label, conf, triggered)

            if triggered and _should_trigger(state, label):
                state.last_triggered[label] = time.time()
                detection = YOLODetection(
                    object_class=label,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{state.frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                    bbox=None,
                )
                try:
                    state.advice = get_sustainability_advice(
                        detection=detection,
                        castnet=fixed_context.castnet,
                        fixed_context=fixed_context,
                    )
                except Exception as error:
                    print(f"Adviser error: {error}")

        if state.advice:
            _draw_advice(frame, state.advice)

        cv2.imshow("Aeris Live YOLO", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
