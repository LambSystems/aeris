import os
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import av
import cv2
import streamlit as st
from streamlit_webrtc import RTCConfiguration, VideoTransformerBase, webrtc_streamer
from ultralytics import YOLO

from app.env_loader import load_app_env

load_app_env()

from app.cv.pipeline import _draw_advice, _draw_box
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection

COOLDOWN_SECONDS = 10
DEFAULT_TRIGGER_THRESHOLD = 0.35
DEFAULT_INFERENCE_SIZE = 320
DEFAULT_FRAME_SKIP = 2
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
MODEL_NAME = Path(MODEL_PATH).name
MODEL_PREVIEW = YOLO(MODEL_PATH)
MODEL_LABELS = (
    [MODEL_PREVIEW.names[index] for index in sorted(MODEL_PREVIEW.names)]
    if isinstance(MODEL_PREVIEW.names, dict)
    else list(MODEL_PREVIEW.names)
)

st.set_page_config(
    page_title="Aeris Live Detection",
    page_icon="A",
    layout="wide",
)

st.sidebar.title("Aeris")
st.sidebar.caption("Live camera")
st.sidebar.markdown("---")

st.sidebar.subheader("Settings")
threshold = st.sidebar.slider(
    "Trigger confidence",
    min_value=0.10,
    max_value=1.00,
    value=DEFAULT_TRIGGER_THRESHOLD,
    step=0.05,
)
cooldown = st.sidebar.slider(
    "Cooldown (seconds)",
    min_value=5,
    max_value=60,
    value=COOLDOWN_SECONDS,
    step=5,
)
inference_size = st.sidebar.select_slider(
    "Inference size",
    options=[256, 320, 416, 512, 640],
    value=DEFAULT_INFERENCE_SIZE,
)
frame_skip = st.sidebar.slider(
    "Infer every Nth frame",
    min_value=1,
    max_value=6,
    value=DEFAULT_FRAME_SKIP,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Model classes")
for label in MODEL_LABELS:
    st.sidebar.markdown(f"- `{label}`")

st.sidebar.markdown("---")
advice_header = st.sidebar.empty()
advice_box = st.sidebar.empty()


class AerisProcessor(VideoTransformerBase):
    def __init__(self) -> None:
        self.model = YOLO(MODEL_PATH)
        self.castnet = load_mock_castnet()
        self.advice: SustainabilityAdvice | None = None
        self._lock = threading.Lock()
        self._last_triggered: dict[str, float] = {}
        self._frame_count = 0
        self._cached_detections: list[dict[str, float | int | str]] = []
        self._last_inference_ms = 0.0
        self._smoothed_fps = 0.0
        self._last_frame_at = time.perf_counter()

    def _should_trigger(self, obj_class: str) -> bool:
        return time.time() - self._last_triggered.get(obj_class, 0) >= cooldown

    def _fetch_advice(self, detection: YOLODetection) -> None:
        try:
            result = get_sustainability_advice(detection, self.castnet)
            with self._lock:
                self.advice = result
        except Exception as exc:
            print(f"Adviser error: {exc}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self._frame_count += 1

        should_infer = (
            not self._cached_detections
            or self._frame_count % max(frame_skip, 1) == 0
        )

        if should_infer:
            inference_started = time.perf_counter()
            results = self.model.track(
                source=img,
                conf=threshold,
                imgsz=inference_size,
                persist=True,
                verbose=False,
                tracker="bytetrack.yaml",
            )[0]
            self._last_inference_ms = (time.perf_counter() - inference_started) * 1000
            cached_detections: list[dict[str, float | int | str]] = []

            for box in results.boxes:
                conf = float(box.conf[0])
                detected_label = self.model.names[int(box.cls[0])]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cached_detections.append(
                    {
                        "label": detected_label,
                        "conf": conf,
                        "x1": x1,
                        "y1": y1,
                        "x2": x2,
                        "y2": y2,
                    }
                )

            self._cached_detections = cached_detections

        for detection in self._cached_detections:
            conf = float(detection["conf"])
            detected_label = str(detection["label"])
            x1 = int(detection["x1"])
            y1 = int(detection["y1"])
            x2 = int(detection["x2"])
            y2 = int(detection["y2"])
            triggered = conf >= threshold
            _draw_box(img, x1, y1, x2, y2, detected_label, conf, triggered)

            if should_infer and triggered and self._should_trigger(detected_label):
                self._last_triggered[detected_label] = time.time()
                detection_payload = YOLODetection(
                    object_class=detected_label,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{self._frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                )
                threading.Thread(
                    target=self._fetch_advice,
                    args=(detection_payload,),
                    daemon=True,
                ).start()

        with self._lock:
            if self.advice:
                _draw_advice(img, self.advice)

        now = time.perf_counter()
        instantaneous_fps = 1.0 / max(now - self._last_frame_at, 1e-6)
        self._last_frame_at = now
        if self._smoothed_fps == 0.0:
            self._smoothed_fps = instantaneous_fps
        else:
            self._smoothed_fps = (self._smoothed_fps * 0.85) + (instantaneous_fps * 0.15)

        cv2.putText(
            img,
            f"FPS {self._smoothed_fps:.1f} | infer {self._last_inference_ms:.0f} ms | imgsz {inference_size} | skip {frame_skip}",
            (12, 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 208, 132),
            2,
            cv2.LINE_AA,
        )

        return av.VideoFrame.from_ndarray(img, format="bgr24")


st.title("Live Detection")
st.caption(f"Model: {MODEL_NAME}")

ctx = webrtc_streamer(
    key="aeris-live",
    video_processor_factory=AerisProcessor,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    media_stream_constraints={
        "video": {
            "width": {"ideal": 1280},
            "height": {"ideal": 720},
            "frameRate": {"ideal": 30},
        },
        "audio": False,
    },
    async_processing=True,
)

if ctx.state.playing:
    while True:
        if ctx.video_processor:
            with ctx.video_processor._lock:
                advice = ctx.video_processor.advice

            if advice:
                advice_header.markdown("### Latest Detection")
                advice_box.markdown(
                    f"Detected: `{advice.object_detected}`  \n"
                    f"Confidence: {advice.confidence:.0%}\n\n"
                    f"Context\n\n{advice.context}\n\n"
                    f"Action\n\n> {advice.action}"
                )
            else:
                advice_header.markdown("### Waiting for detection")
                advice_box.markdown("_No object detected yet._")

        time.sleep(1)
