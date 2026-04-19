import os
import sys
import threading
import time
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

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


@st.cache_resource
def load_detection_model() -> YOLO:
    return YOLO(MODEL_PATH)


MODEL_PREVIEW = load_detection_model()
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
st.sidebar.caption("Camera and uploaded clip detection")
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


def extract_detections(result, model: YOLO) -> list[dict[str, float | int | str]]:
    detections: list[dict[str, float | int | str]] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    for box in boxes:
        conf = float(box.conf[0])
        detected_label = model.names[int(box.cls[0])]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        detections.append(
            {
                "label": detected_label,
                "conf": conf,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            }
        )
    return detections


def draw_detections(frame, detections: list[dict[str, float | int | str]]) -> None:
    for detection in detections:
        conf = float(detection["conf"])
        detected_label = str(detection["label"])
        x1 = int(detection["x1"])
        y1 = int(detection["y1"])
        x2 = int(detection["x2"])
        y2 = int(detection["y2"])
        triggered = conf >= threshold
        _draw_box(frame, x1, y1, x2, y2, detected_label, conf, triggered)


def process_uploaded_video(
    video_bytes: bytes,
    confidence_threshold: float,
    imgsz: int,
    skip_frames: int,
    clip_stride: int,
    max_processed_frames: int,
) -> dict[str, object]:
    model = load_detection_model()
    label_frames = Counter()
    inference_times: list[float] = []

    with TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        input_path = temp_root / "input.mp4"
        output_path = temp_root / "annotated.mp4"
        input_path.write_bytes(video_bytes)

        capture = cv2.VideoCapture(str(input_path))
        if not capture.isOpened():
            raise RuntimeError("Could not open uploaded video.")

        source_fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 1280)
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 720)
        total_source_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        output_fps = max(source_fps / max(clip_stride, 1), 1.0)
        source_frame_index = 0
        processed_frame_index = 0
        cached_detections: list[dict[str, float | int | str]] = []

        output_container = av.open(str(output_path), mode="w")
        try:
            output_stream = output_container.add_stream("libx264", rate=round(output_fps))
        except av.codec.codec.UnknownCodecError:
            output_stream = output_container.add_stream("mpeg4", rate=round(output_fps))
        output_stream.width = width
        output_stream.height = height
        output_stream.pix_fmt = "yuv420p"

        progress = st.progress(0.0, text="Processing video clip...")
        status = st.empty()

        try:
            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                source_frame_index += 1
                if source_frame_index % max(clip_stride, 1) != 0:
                    if total_source_frames > 0:
                        progress.progress(
                            min(source_frame_index / total_source_frames, 1.0),
                            text=f"Sampling uploaded clip... source frame {source_frame_index}/{total_source_frames}",
                        )
                    continue

                processed_frame_index += 1
                if processed_frame_index > max_processed_frames:
                    break

                should_infer = (
                    not cached_detections
                    or processed_frame_index % max(skip_frames, 1) == 0
                )

                if should_infer:
                    inference_started = time.perf_counter()
                    result = model.track(
                        source=frame,
                        conf=confidence_threshold,
                        imgsz=imgsz,
                        persist=True,
                        verbose=False,
                        tracker="bytetrack.yaml",
                    )[0]
                    inference_times.append((time.perf_counter() - inference_started) * 1000)
                    cached_detections = extract_detections(result, model)

                draw_detections(frame, cached_detections)
                for label in {str(detection["label"]) for detection in cached_detections}:
                    label_frames[label] += 1

                overlay_text = (
                    f"clip frame {processed_frame_index}"
                    f" | imgsz {imgsz}"
                    f" | infer-skip {skip_frames}"
                    f" | sample {clip_stride}"
                )
                cv2.putText(
                    frame,
                    overlay_text,
                    (12, 28),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (0, 208, 132),
                    2,
                    cv2.LINE_AA,
                )
                video_frame = av.VideoFrame.from_ndarray(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                    format="rgb24",
                )
                for packet in output_stream.encode(video_frame):
                    output_container.mux(packet)

                if total_source_frames > 0:
                    progress.progress(
                        min(source_frame_index / total_source_frames, 1.0),
                        text=(
                            f"Processing video clip... source frame "
                            f"{source_frame_index}/{total_source_frames}, written {processed_frame_index}"
                        ),
                    )
                else:
                    progress.progress(0.0, text=f"Processing video clip... written {processed_frame_index} frames")
                if processed_frame_index % 10 == 0:
                    status.caption(
                        f"Written {processed_frame_index} frames | "
                        f"avg infer {sum(inference_times) / max(len(inference_times), 1):.1f} ms"
                    )
        finally:
            capture.release()
            for packet in output_stream.encode():
                output_container.mux(packet)
            output_container.close()

        progress.empty()
        status.empty()
        average_inference_ms = sum(inference_times) / max(len(inference_times), 1)
        return {
            "video_bytes": output_path.read_bytes(),
            "frame_count": processed_frame_index,
            "fps": output_fps,
            "source_fps": source_fps,
            "source_frame_count": total_source_frames,
            "average_inference_ms": average_inference_ms,
            "label_frames": dict(label_frames),
        }


class AerisProcessor(VideoTransformerBase):
    def __init__(self) -> None:
        self.model = load_detection_model()
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
            result = self.model.track(
                source=img,
                conf=threshold,
                imgsz=inference_size,
                persist=True,
                verbose=False,
                tracker="bytetrack.yaml",
            )[0]
            self._last_inference_ms = (time.perf_counter() - inference_started) * 1000
            self._cached_detections = extract_detections(result, self.model)

        draw_detections(img, self._cached_detections)

        for detection in self._cached_detections:
            conf = float(detection["conf"])
            detected_label = str(detection["label"])
            if should_infer and conf >= threshold and self._should_trigger(detected_label):
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

live_tab, upload_tab = st.tabs(["Live camera", "Upload clip"])

with live_tab:
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

with upload_tab:
    st.subheader("Upload clip")
    st.caption("Process a short video clip with the same model and settings used for live detection.")
    clip_stride = st.slider(
        "Sample every Nth source frame",
        min_value=1,
        max_value=12,
        value=4,
        step=1,
        key="clip_stride",
    )
    max_processed_frames = st.slider(
        "Max processed frames",
        min_value=30,
        max_value=300,
        value=120,
        step=10,
        key="max_processed_frames",
    )
    uploaded_video = st.file_uploader(
        "Video clip",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        accept_multiple_files=False,
    )
    if uploaded_video is not None:
        st.video(uploaded_video.getvalue())
        if st.button("Process clip", type="primary"):
            with st.spinner("Running detection on uploaded clip..."):
                processed = process_uploaded_video(
                    video_bytes=uploaded_video.getvalue(),
                    confidence_threshold=threshold,
                    imgsz=inference_size,
                    skip_frames=frame_skip,
                    clip_stride=clip_stride,
                    max_processed_frames=max_processed_frames,
                )
            st.success("Clip processed.")
            st.video(processed["video_bytes"], format="video/mp4")
            st.download_button(
                "Download processed clip",
                data=processed["video_bytes"],
                file_name="processed-trash-clip.mp4",
                mime="video/mp4",
            )
            st.markdown(
                f"Written frames: `{processed['frame_count']}`  \n"
                f"Source frames: `{processed['source_frame_count']}`  \n"
                f"Source FPS: `{processed['source_fps']:.1f}`  \n"
                f"Output FPS: `{processed['fps']:.1f}`  \n"
                f"Average inference: `{processed['average_inference_ms']:.1f} ms`"
            )
            label_frames = processed["label_frames"]
            if label_frames:
                ordered_labels = sorted(
                    label_frames.items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
                st.markdown("**Detected labels across clip**")
                for label, frame_hits in ordered_labels:
                    st.markdown(f"- `{label}` in `{frame_hits}` frames")
            else:
                st.info("No objects were detected in the uploaded clip.")

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
