"""
YOLO detection pipeline with sustainability trigger.

Standard COCO does not have a "soda_can" class. We map COCO "bottle" (39)
as the demo stand-in. Swap COCO_TO_SUSTAINABILITY or use a custom model
trained on cans for production.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime

import cv2
from ultralytics import YOLO

from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection

CONFIDENCE_THRESHOLD = 0.70
COOLDOWN_SECONDS = 10

# Maps COCO class names → our sustainability object classes
COCO_TO_SUSTAINABILITY: dict[str, str] = {
    "bottle": "soda_can",
    "cup": "styrofoam_cup",
}


@dataclass
class PipelineState:
    advice: SustainabilityAdvice | None = None
    advice_timestamp: float = 0.0
    last_triggered: dict[str, float] = field(default_factory=dict)
    frame_count: int = 0


def _draw_box(frame, x1, y1, x2, y2, label: str, conf: float, triggered: bool) -> None:
    color = (0, 200, 80) if triggered else (200, 200, 200)
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    text = f"{label} {conf:.0%}"
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, text, (x1 + 2, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)


def _draw_advice(frame, advice: SustainabilityAdvice) -> None:
    h, w = frame.shape[:2]
    panel_y = h - 130
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, panel_y), (w, h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

    cv2.putText(
        frame,
        f"Detected: {advice.object_detected}  ({advice.confidence:.0%})",
        (12, panel_y + 22),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (100, 230, 120), 1,
    )

    for i, line in enumerate(_wrap(advice.context, max_chars=90)):
        cv2.putText(frame, line, (12, panel_y + 46 + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1)

    action_lines = _wrap(f"→ {advice.action}", max_chars=90)
    base_y = panel_y + 46 + len(_wrap(advice.context, 90)) * 20 + 6
    for i, line in enumerate(action_lines):
        cv2.putText(frame, line, (12, base_y + i * 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 200, 255), 1)


def _wrap(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = f"{current} {word}".strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _should_trigger(state: PipelineState, obj_class: str) -> bool:
    last = state.last_triggered.get(obj_class, 0)
    return time.time() - last >= COOLDOWN_SECONDS


def run(source: int | str = 0) -> None:
    """Run the pipeline. source=0 for webcam, or pass a video file path."""
    model = YOLO("yolov8n.pt")
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video source: {source}")

    state = PipelineState()
    castnet = load_mock_castnet()
    print(f"Pipeline running — watching for: {list(COCO_TO_SUSTAINABILITY.keys())}")
    print("Press Q to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        state.frame_count += 1
        results = model(frame, verbose=False)[0]

        triggered_this_frame: set[str] = set()

        for box in results.boxes:
            conf = float(box.conf[0])
            coco_name = model.names[int(box.cls[0])]
            sustain_class = COCO_TO_SUSTAINABILITY.get(coco_name)

            if sustain_class is None:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            triggered = conf >= CONFIDENCE_THRESHOLD

            _draw_box(frame, x1, y1, x2, y2, sustain_class, conf, triggered)

            if triggered and _should_trigger(state, sustain_class):
                state.last_triggered[sustain_class] = time.time()
                triggered_this_frame.add(sustain_class)

                detection = YOLODetection(
                    object_class=sustain_class,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{state.frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                    bbox=None,
                )

                print(f"  Triggered: {sustain_class} ({conf:.0%}) — calling adviser...")
                try:
                    state.advice = get_sustainability_advice(detection, castnet)
                    print(f"  → {state.advice.action}")
                except Exception as e:
                    print(f"  Adviser error: {e}")

        if state.advice:
            _draw_advice(frame, state.advice)

        cv2.imshow("Aeris — Sustainability Pipeline", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
