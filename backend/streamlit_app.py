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

from app.cv.pipeline import (
    COCO_TO_SUSTAINABILITY,
    CONFIDENCE_THRESHOLD,
    _draw_advice,
    _draw_box,
)
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection

COOLDOWN_SECONDS = 10

st.set_page_config(
    page_title="Aeris — Live Detection",
    page_icon="🌿",
    layout="wide",
)

# ── Sidebar ──────────────────────────────────────────────────────────────────

st.sidebar.title("🌿 Aeris")
st.sidebar.caption("Sustainability adviser · Live camera")
st.sidebar.markdown("---")

st.sidebar.subheader("Settings")
threshold = st.sidebar.slider(
    "Trigger confidence", min_value=0.50, max_value=1.00,
    value=CONFIDENCE_THRESHOLD, step=0.05,
)
cooldown = st.sidebar.slider(
    "Cooldown (seconds)", min_value=5, max_value=60,
    value=COOLDOWN_SECONDS, step=5,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Watching for")
for coco_class, sustain_class in COCO_TO_SUSTAINABILITY.items():
    st.sidebar.markdown(f"- `{coco_class}` → **{sustain_class}**")

st.sidebar.markdown("---")
advice_header = st.sidebar.empty()
advice_box = st.sidebar.empty()

# ── Video processor ───────────────────────────────────────────────────────────

class AerisProcessor(VideoTransformerBase):
    def __init__(self) -> None:
        self.model = YOLO("yolov8n.pt")
        self.castnet = load_mock_castnet()
        self.advice: SustainabilityAdvice | None = None
        self._lock = threading.Lock()
        self._last_triggered: dict[str, float] = {}
        self._frame_count = 0

    def _should_trigger(self, obj_class: str) -> bool:
        return time.time() - self._last_triggered.get(obj_class, 0) >= cooldown

    def _fetch_advice(self, detection: YOLODetection) -> None:
        try:
            result = get_sustainability_advice(detection, self.castnet)
            with self._lock:
                self.advice = result
        except Exception as e:
            print(f"Adviser error: {e}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self._frame_count += 1

        results = self.model(img, verbose=False)[0]

        for box in results.boxes:
            conf = float(box.conf[0])
            coco_name = self.model.names[int(box.cls[0])]
            sustain_class = COCO_TO_SUSTAINABILITY.get(coco_name)
            if sustain_class is None:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            triggered = conf >= threshold
            _draw_box(img, x1, y1, x2, y2, sustain_class, conf, triggered)

            if triggered and self._should_trigger(sustain_class):
                self._last_triggered[sustain_class] = time.time()
                detection = YOLODetection(
                    object_class=sustain_class,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{self._frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                )
                threading.Thread(
                    target=self._fetch_advice, args=(detection,), daemon=True
                ).start()

        with self._lock:
            if self.advice:
                _draw_advice(img, self.advice)

        return av.VideoFrame.from_ndarray(img, format="bgr24")


# ── Main area ─────────────────────────────────────────────────────────────────

st.title("Live Sustainability Detection")
st.caption("Point the camera at a bottle or cup. A green box appears at threshold; advice loads in the sidebar.")

ctx = webrtc_streamer(
    key="aeris-live",
    video_processor_factory=AerisProcessor,
    rtc_configuration=RTCConfiguration(
        {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
    ),
    media_stream_constraints={
        "video": {"width": {"ideal": 1280}, "height": {"ideal": 720}, "frameRate": {"ideal": 30}},
        "audio": False,
    },
    async_processing=True,
)

# ── Sidebar advice polling ────────────────────────────────────────────────────

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
