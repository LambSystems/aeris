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
import torch
from streamlit_webrtc import RTCConfiguration, VideoTransformerBase, webrtc_streamer
from ultralytics import YOLO

from app.env_loader import load_app_env

load_app_env()

from app.cv.pipeline import COCO_TO_SUSTAINABILITY, _draw_advice, _draw_box
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_service import load_castnet
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection

COOLDOWN_SECONDS = 10
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_FRAME_SKIP = 1
DEFAULT_INFERENCE_SIZE = 320
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "yolov8n.pt")
MODEL_NAME = Path(MODEL_PATH).name
EMBED_MODE = os.getenv("AERIS_STREAMLIT_EMBED") == "1"
YOLO_DEVICE = os.getenv("YOLO_DEVICE") or ("0" if torch.cuda.is_available() else "cpu")

st.set_page_config(page_title="Aeris Live Vision", page_icon="A", layout="wide")

if EMBED_MODE:
    st.markdown(
        """
        <style>
          header, footer, [data-testid="stSidebar"], [data-testid="stToolbar"] {
            display: none !important;
          }
          .block-container {
            padding: 0.35rem 0.5rem 0.5rem !important;
            max-width: 100% !important;
          }
          [data-testid="stVerticalBlock"] {
            gap: 0.35rem !important;
          }
          iframe {
            border-radius: 12px;
          }
        </style>
        """,
        unsafe_allow_html=True,
    )

st.sidebar.title("Aeris")
st.sidebar.caption("Sustainability adviser · Live camera")
st.sidebar.markdown("---")

st.sidebar.subheader("Settings")
threshold = st.sidebar.slider(
    "Trigger confidence",
    min_value=0.10,
    max_value=1.00,
    value=DEFAULT_CONFIDENCE_THRESHOLD,
    step=0.05,
)
cooldown = st.sidebar.slider(
    "Cooldown (seconds)",
    min_value=5,
    max_value=60,
    value=COOLDOWN_SECONDS,
    step=5,
)
inference_size = st.sidebar.slider(
    "Inference size",
    min_value=320,
    max_value=640,
    value=DEFAULT_INFERENCE_SIZE,
    step=160,
)
frame_skip = st.sidebar.slider(
    "Infer every N frames",
    min_value=1,
    max_value=4,
    value=DEFAULT_FRAME_SKIP,
    step=1,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Watching for")
for raw_class, sustain_class in COCO_TO_SUSTAINABILITY.items():
    st.sidebar.markdown(f"- `{raw_class}` -> **{sustain_class}**")

st.sidebar.markdown("---")
advice_header = st.sidebar.empty()
advice_box = st.sidebar.empty()


@st.cache_resource
def load_detection_model(model_path: str) -> YOLO:
    return YOLO(model_path)


def raw_label(names: dict[int, str] | list[str], class_id: int) -> str:
    if isinstance(names, dict):
        return names.get(class_id, "unknown")
    return names[class_id] if class_id < len(names) else "unknown"


def plausible_box(frame_shape: tuple[int, int, int], x1: int, y1: int, x2: int, y2: int) -> bool:
    height, width = frame_shape[:2]
    box_w = max(0, x2 - x1)
    box_h = max(0, y2 - y1)
    if box_w <= 2 or box_h <= 2:
        return False
    area_ratio = (box_w * box_h) / (width * height)
    width_ratio = box_w / width
    height_ratio = box_h / height
    return area_ratio <= 0.75 and width_ratio <= 0.95 and height_ratio <= 0.95


class AerisProcessor(VideoTransformerBase):
    def __init__(self) -> None:
        self.model = load_detection_model(MODEL_PATH)
        self.castnet = load_castnet()
        self.advice: SustainabilityAdvice | None = None
        self._lock = threading.Lock()
        self._last_triggered: dict[str, float] = {}
        self._frame_count = 0
        self._last_inference_ms = 0.0

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

        should_infer = self._frame_count % frame_skip == 0
        boxes = []
        if should_infer:
            started_at = time.perf_counter()
            result = self.model.track(
                source=img,
                conf=0.05,
                imgsz=inference_size,
                persist=True,
                device=YOLO_DEVICE,
                verbose=False,
            )[0]
            self._last_inference_ms = (time.perf_counter() - started_at) * 1000
            boxes = list(result.boxes)

        for box in boxes:
            conf = float(box.conf[0])
            detected_name = raw_label(self.model.names, int(box.cls[0]))
            sustain_class = COCO_TO_SUSTAINABILITY.get(detected_name)
            if sustain_class is None:
                continue
            if conf < threshold:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            if not plausible_box(img.shape, x1, y1, x2, y2):
                continue

            _draw_box(img, x1, y1, x2, y2, sustain_class, conf, True)

            if self._should_trigger(sustain_class):
                self._last_triggered[sustain_class] = time.time()
                detection = YOLODetection(
                    object_class=sustain_class,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{self._frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                )
                threading.Thread(target=self._fetch_advice, args=(detection,), daemon=True).start()

        with self._lock:
            if self.advice and not EMBED_MODE:
                _draw_advice(img, self.advice)

        if not EMBED_MODE:
            cv2.putText(
                img,
                f"{MODEL_NAME} | infer {self._last_inference_ms:.0f} ms | imgsz {inference_size} | skip {frame_skip}",
                (12, 28),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (120, 255, 160),
                1,
            )
        return av.VideoFrame.from_ndarray(img, format="bgr24")


if not EMBED_MODE:
    st.title("Live Sustainability Detection")
    st.caption(f"Model: {MODEL_NAME}. Point the camera at a can, paper, or bottle.")

ctx = webrtc_streamer(
    key="aeris-live",
    video_processor_factory=AerisProcessor,
    rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
    media_stream_constraints={
        "video": {
            "width": {"ideal": 1280},
            "height": {"ideal": 720},
            "frameRate": {"ideal": 30, "max": 30},
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
                    f"**Detected:** `{advice.object_detected}` · "
                    f"**Confidence:** {advice.confidence:.0%}\n\n"
                    f"**Context**\n\n{advice.context}\n\n"
                    f"**Action**\n\n> {advice.action}"
                )
            else:
                advice_header.markdown("### Waiting for detection...")
                advice_box.markdown("_No object detected yet._")

        time.sleep(1)
