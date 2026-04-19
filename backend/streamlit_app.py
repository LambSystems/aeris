from __future__ import annotations

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
import torch
from streamlit_webrtc import RTCConfiguration, VideoTransformerBase, webrtc_streamer
from ultralytics import YOLO

from app.context.fixed_context_service import load_fixed_context
from app.env_loader import load_app_env
from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.schemas import SustainabilityAdvice, YOLODetection
from app.vision_state import write_latest_detection


load_app_env()

if torch.cuda.is_available():
    torch.backends.cudnn.benchmark = True
    try:
        torch.set_float32_matmul_precision("high")
    except Exception:
        pass


def _default_model_path() -> str:
    backend_root = Path(__file__).resolve().parent
    candidates = [
        backend_root / "models" / "trash-quick-v4-best.pt",
        backend_root / "models" / "trash-quick-v3-best.pt",
        backend_root / "models" / "trash-quick-v2-best.pt",
        backend_root / "yolov8n.pt",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return str(backend_root / "yolov8n.pt")


COOLDOWN_SECONDS = int(os.getenv("AERIS_ADVICE_COOLDOWN", "10"))
DEFAULT_TRIGGER_THRESHOLD = float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.35"))
DEFAULT_FRAME_SKIP = int(os.getenv("YOLO_FRAME_SKIP", "1"))
DEFAULT_INFERENCE_SIZE = int(os.getenv("YOLO_IMGSZ", "256"))
DEFAULT_CAMERA_WIDTH = int(os.getenv("AERIS_CAMERA_WIDTH", "480"))
DEFAULT_CAMERA_HEIGHT = int(os.getenv("AERIS_CAMERA_HEIGHT", "270"))
DEFAULT_CAMERA_FPS = int(os.getenv("AERIS_CAMERA_FPS", "20"))
MODEL_PATH = os.getenv("YOLO_MODEL_PATH", _default_model_path())
MODEL_NAME = Path(MODEL_PATH).name
YOLO_DEVICE = os.getenv("YOLO_DEVICE") or ("0" if torch.cuda.is_available() else "cpu")
USE_HALF_PRECISION = bool(torch.cuda.is_available() and YOLO_DEVICE != "cpu")

st.set_page_config(page_title="Aeris Live Vision", page_icon="A", layout="wide")


@st.cache_resource(show_spinner=False)
def load_detection_model(model_path: str) -> YOLO:
    model = YOLO(model_path)
    try:
        model.fuse()
    except Exception:
        pass
    return model


@st.cache_resource(show_spinner=False)
def load_fixed_environment():
    return load_fixed_context()


MODEL_PREVIEW = load_detection_model(MODEL_PATH)
MODEL_LABELS = (
    [MODEL_PREVIEW.names[index] for index in sorted(MODEL_PREVIEW.names)]
    if isinstance(MODEL_PREVIEW.names, dict)
    else list(MODEL_PREVIEW.names)
)

st.sidebar.title("Aeris")
st.sidebar.caption("Streamlit-first live sustainability detection")
st.sidebar.markdown("---")
st.sidebar.subheader("Realtime settings")

threshold = st.sidebar.slider(
    "Detection threshold",
    min_value=0.10,
    max_value=1.00,
    value=DEFAULT_TRIGGER_THRESHOLD,
    step=0.05,
)
cooldown = st.sidebar.slider(
    "Advice cooldown (seconds)",
    min_value=3,
    max_value=45,
    value=COOLDOWN_SECONDS,
    step=1,
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
camera_width = st.sidebar.select_slider(
    "Camera width",
    options=[480, 640, 800, 960, 1280],
    value=DEFAULT_CAMERA_WIDTH,
)
camera_height = st.sidebar.select_slider(
    "Camera height",
    options=[270, 360, 450, 540, 720],
    value=DEFAULT_CAMERA_HEIGHT,
)
camera_fps = st.sidebar.select_slider(
    "Camera FPS",
    options=[15, 20, 24, 30],
    value=DEFAULT_CAMERA_FPS,
)

st.sidebar.markdown("---")
st.sidebar.subheader("Model classes")
for label in MODEL_LABELS:
    st.sidebar.markdown(f"- `{str(label).lower()}`")

fixed_context = load_fixed_environment()


def normalize_label(raw_label: str) -> str:
    return raw_label.strip().lower().replace("_", " ")


def extract_detections(result, model: YOLO) -> list[dict[str, float | int | str]]:
    detections: list[dict[str, float | int | str]] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return detections

    for box in boxes:
        conf = float(box.conf[0])
        detected_label = normalize_label(str(model.names[int(box.cls[0])]))
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        track_id = int(box.id[0]) if getattr(box, "id", None) is not None else -1
        detections.append(
            {
                "label": detected_label,
                "conf": conf,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
                "track_id": track_id,
            }
        )

    detections.sort(key=lambda item: float(item["conf"]), reverse=True)
    return detections


def draw_detections(frame, detections: list[dict[str, float | int | str]]) -> None:
    for detection in detections:
        detected_label = str(detection["label"])
        x1 = int(detection["x1"])
        y1 = int(detection["y1"])
        x2 = int(detection["x2"])
        y2 = int(detection["y2"])
        color = (0, 0, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        text = detected_label
        (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (x1, max(0, y1 - th - 6)), (x1 + tw + 6, y1), color, -1)
        cv2.putText(
            frame,
            text,
            (x1 + 3, max(12, y1 - 4)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )


def run_tracking_pass(model: YOLO, frame, confidence_threshold: float, imgsz: int):
    return model.track(
        source=frame,
        conf=max(confidence_threshold * 0.6, 0.10),
        imgsz=imgsz,
        persist=True,
        device=YOLO_DEVICE,
        verbose=False,
        tracker="bytetrack.yaml",
        half=USE_HALF_PRECISION,
        max_det=12,
    )[0]


def process_uploaded_video(
    video_bytes: bytes,
    confidence_threshold: float,
    imgsz: int,
    skip_frames: int,
    clip_stride: int,
    max_processed_frames: int,
) -> dict[str, object]:
    model = load_detection_model(MODEL_PATH)
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
                            text=f"Sampling uploaded clip... frame {source_frame_index}/{total_source_frames}",
                        )
                    continue

                processed_frame_index += 1
                if processed_frame_index > max_processed_frames:
                    break

                should_infer = not cached_detections or processed_frame_index % max(skip_frames, 1) == 0
                if should_infer:
                    inference_started = time.perf_counter()
                    result = run_tracking_pass(
                        model=model,
                        frame=frame,
                        confidence_threshold=confidence_threshold,
                        imgsz=imgsz,
                    )
                    inference_times.append((time.perf_counter() - inference_started) * 1000)
                    cached_detections = extract_detections(result, model)

                visible_detections = [d for d in cached_detections if float(d["conf"]) >= confidence_threshold]
                draw_detections(frame, visible_detections)
                for label in {str(detection["label"]) for detection in visible_detections}:
                    label_frames[label] += 1

                overlay_text = (
                    f"frame {processed_frame_index} | imgsz {imgsz} | "
                    f"skip {skip_frames} | sample {clip_stride}"
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
                video_frame = av.VideoFrame.from_ndarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB), format="rgb24")
                for packet in output_stream.encode(video_frame):
                    output_container.mux(packet)

                if total_source_frames > 0:
                    progress.progress(
                        min(source_frame_index / total_source_frames, 1.0),
                        text=f"Processing clip... source {source_frame_index}/{total_source_frames}, written {processed_frame_index}",
                    )
                if processed_frame_index % 10 == 0:
                    status.caption(
                        f"Written {processed_frame_index} frames | "
                        f"avg inference {sum(inference_times) / max(len(inference_times), 1):.1f} ms"
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
        self.model = load_detection_model(MODEL_PATH)
        self.fixed_context = fixed_context
        self.advice: SustainabilityAdvice | None = None
        self.latest_detection: YOLODetection | None = None
        self._lock = threading.Lock()
        self._last_triggered: dict[str, float] = {}
        self._frame_count = 0
        self._cached_detections: list[dict[str, float | int | str]] = []
        self._last_inference_ms = 0.0
        self._smoothed_fps = 0.0
        self._last_frame_at = time.perf_counter()

    def _should_trigger(self, obj_class: str) -> bool:
        return time.time() - self._last_triggered.get(obj_class, 0.0) >= cooldown

    def _fetch_advice(self, detection: YOLODetection) -> None:
        try:
            result = get_sustainability_advice(
                detection=detection,
                castnet=self.fixed_context.castnet,
                fixed_context=self.fixed_context,
            )
            with self._lock:
                self.advice = result
        except Exception as exc:
            print(f"Adviser error: {exc}")

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        img = frame.to_ndarray(format="bgr24")
        self._frame_count += 1

        should_infer = not self._cached_detections or self._frame_count % max(frame_skip, 1) == 0
        if should_infer:
            inference_started = time.perf_counter()
            result = run_tracking_pass(
                model=self.model,
                frame=img,
                confidence_threshold=threshold,
                imgsz=inference_size,
            )
            self._last_inference_ms = (time.perf_counter() - inference_started) * 1000
            self._cached_detections = extract_detections(result, self.model)

        visible_detections = [detection for detection in self._cached_detections if float(detection["conf"]) >= threshold]
        draw_detections(img, visible_detections)

        for detection_data in visible_detections:
            conf = float(detection_data["conf"])
            detected_label = str(detection_data["label"])
            if should_infer and self._should_trigger(detected_label):
                self._last_triggered[detected_label] = time.time()
                detection = YOLODetection(
                    object_class=detected_label,
                    confidence=round(conf, 4),
                    frame_id=f"frame_{self._frame_count:05d}",
                    timestamp=datetime.now().isoformat(timespec="seconds") + "Z",
                )
                write_latest_detection(detection)
                with self._lock:
                    self.latest_detection = detection
                threading.Thread(target=self._fetch_advice, args=(detection,), daemon=True).start()
                break

        now = time.perf_counter()
        instantaneous_fps = 1.0 / max(now - self._last_frame_at, 1e-6)
        self._last_frame_at = now
        if self._smoothed_fps == 0.0:
            self._smoothed_fps = instantaneous_fps
        else:
            self._smoothed_fps = (self._smoothed_fps * 0.85) + (instantaneous_fps * 0.15)
        return av.VideoFrame.from_ndarray(img, format="bgr24")


st.title("Aeris Live Vision")
st.caption(f"Model: {MODEL_NAME} | Device: {YOLO_DEVICE}")

video_col, side_col = st.columns([1.65, 1.0], gap="large")

with side_col:
    metrics_placeholder = st.empty()
    advice_placeholder = st.empty()
    env_placeholder = st.empty()

with video_col:
    live_tab, upload_tab = st.tabs(["Live camera", "Upload clip"])

    with live_tab:
        ctx = webrtc_streamer(
            key="aeris-live",
            video_processor_factory=AerisProcessor,
            rtc_configuration=RTCConfiguration({"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}),
            media_stream_constraints={
                "video": {
                    "width": {"ideal": camera_width},
                    "height": {"ideal": camera_height},
                    "frameRate": {"ideal": camera_fps, "max": camera_fps},
                },
                "audio": False,
            },
            async_processing=True,
        )

    with upload_tab:
        st.caption("Process a short clip with the same local YOLO model.")
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
                label_frames = processed["label_frames"]
                st.markdown(
                    f"Written frames: `{processed['frame_count']}`  \n"
                    f"Source frames: `{processed['source_frame_count']}`  \n"
                    f"Source FPS: `{processed['source_fps']:.1f}`  \n"
                    f"Output FPS: `{processed['fps']:.1f}`  \n"
                    f"Average inference: `{processed['average_inference_ms']:.1f} ms`"
                )
                if label_frames:
                    st.markdown("**Detected labels across clip**")
                    for label, frame_hits in sorted(label_frames.items(), key=lambda item: item[1], reverse=True):
                        st.markdown(f"- `{label}` in `{frame_hits}` frames")
                else:
                    st.info("No objects were detected in the uploaded clip.")


def render_side_panel(processor: AerisProcessor | None) -> None:
    if processor is None:
        metrics_placeholder.markdown("### Realtime status\nStart the camera to begin detection.")
        advice_placeholder.markdown("### Advice\n_No advice yet._")
        env_placeholder.markdown(
            "### Environmental context\n"
            f"{fixed_context.summary}\n\n"
            f"- CASTNET site: `{fixed_context.castnet.location}`\n"
            f"- Risk flags: `{', '.join(fixed_context.risk_flags) if fixed_context.risk_flags else 'none'}`"
        )
        return

    with processor._lock:
        advice = processor.advice
        latest_detection = processor.latest_detection
        fps = processor._smoothed_fps
        inference_ms = processor._last_inference_ms

    metrics_placeholder.markdown(
        "### Realtime status\n"
        f"- FPS: `{fps:.1f}`\n"
        f"- Inference: `{inference_ms:.0f} ms`\n"
        f"- Model: `{MODEL_NAME}`\n"
        f"- Image size: `{inference_size}`\n"
        f"- Frame skip: `{frame_skip}`\n"
        f"- Camera: `{camera_width}x{camera_height}` at `{camera_fps}` fps"
    )

    if advice and latest_detection:
        advice_placeholder.markdown(
            "### Advice\n"
            f"**Detected:** `{latest_detection.object_class}` at {latest_detection.confidence:.0%}\n\n"
            f"**Context**\n\n{advice.context}\n\n"
            f"**Action**\n\n> {advice.action}\n\n"
            f"**Source:** `{advice.decision_source}`"
        )
    else:
        advice_placeholder.markdown("### Advice\n_Waiting for a confident detection._")

    env_placeholder.markdown(
        "### Environmental context\n"
        f"{fixed_context.summary}\n\n"
        f"- CASTNET site: `{fixed_context.castnet.location}`\n"
        f"- Risk flags: `{', '.join(fixed_context.risk_flags) if fixed_context.risk_flags else 'none'}`"
    )


if ctx and ctx.state.playing:
    while ctx.state.playing:
        render_side_panel(ctx.video_processor)
        time.sleep(1)
else:
    render_side_panel(None)
