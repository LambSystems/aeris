from __future__ import annotations

import html
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
from app.context.schemas import EnvironmentalFixedContext
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

st.set_page_config(page_title="Aeris · Environmental Scanner", page_icon="🌿", layout="wide")


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

fixed_context = load_fixed_environment()


def _streamlit_public_url() -> str:
    return (os.getenv("AERIS_PUBLIC_STREAMLIT_URL") or "").strip() or "http://127.0.0.1:8507"


def _aeris_inject_styles() -> None:
    st.markdown(
        """
<style>
    :root {
      --aeris-bg: #e8eaef;
      --aeris-card: #ffffff;
      --aeris-border: #d8dce6;
      --aeris-text: #141722;
      --aeris-muted: #5a6270;
      --aeris-accent: #0a9b6b;
    }
    .stApp, [data-testid="stAppViewContainer"] {
      background: var(--aeris-bg) !important;
    }
    div[data-testid="stAppViewContainer"] > .main > div {
      max-width: 100% !important;
      width: 100% !important;
      padding-left: 0.75rem !important;
      padding-right: 0.75rem !important;
      padding-top: 0.5rem !important;
    }
    @media (min-width: 1200px) {
      div[data-testid="stAppViewContainer"] > .main > div {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
      }
    }
    footer { visibility: hidden; height: 0; }
    .block-container {
      padding-top: 0.25rem !important;
      padding-bottom: 0.5rem !important;
    }
    .aeris-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      flex-wrap: wrap;
      gap: 0.75rem;
      margin: 0 0 0.5rem 0;
    }
    .aeris-brand { display: flex; align-items: flex-start; gap: 0.55rem; }
    .aeris-brand-icon { font-size: 1.6rem; line-height: 1; filter: grayscale(0.1); }
    .aeris-brand-text h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      color: var(--aeris-text);
      font-family: system-ui, sans-serif;
    }
    .aeris-brand-text .aeris-sub {
      display: block;
      font-size: 0.65rem;
      font-weight: 600;
      letter-spacing: 0.16em;
      color: var(--aeris-muted);
      margin-top: 1px;
    }
    .aeris-pills { display: flex; flex-wrap: wrap; gap: 0.3rem; justify-content: flex-end; align-items: center; }
    .aeris-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      padding: 0.22rem 0.55rem;
      border-radius: 999px;
      font-size: 0.68rem;
      font-weight: 600;
      background: #fff;
      border: 1px solid var(--aeris-border);
      color: var(--aeris-muted);
      font-family: system-ui, sans-serif;
    }
    .aeris-pill-live span {
      display: inline-block;
      width: 6px; height: 6px; border-radius: 50%;
      background: #22c55e;
      margin-right: 2px;
    }
    .aeris-card {
      background: var(--aeris-card);
      border: 1px solid var(--aeris-border);
      border-radius: 12px;
      padding: 0.75rem 0.9rem;
      margin-bottom: 0.5rem;
      font-family: system-ui, sans-serif;
    }
    .aeris-card h3 {
      margin: 0 0 0.45rem 0;
      font-size: 0.65rem;
      font-weight: 700;
      letter-spacing: 0.14em;
      color: var(--aeris-muted);
    }
    .aeris-card .aeris-row {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
      margin-bottom: 0.35rem;
    }
    .aeris-detect { font-size: 1.05rem; font-weight: 700; color: var(--aeris-text); }
    .aeris-conf { font-size: 0.85rem; color: var(--aeris-muted); margin-top: 0.15rem; }
    .aeris-badge {
      flex-shrink: 0;
      font-size: 0.65rem;
      font-weight: 600;
      padding: 0.15rem 0.45rem;
      border-radius: 6px;
      background: #e8f4ff;
      color: #1d4ed8;
      border: 1px solid #bfdbfe;
    }
    .aeris-action-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
      margin-bottom: 0.4rem;
    }
    .aeris-action-head h3 { margin: 0; }
    .aeris-provider {
      font-size: 0.65rem;
      font-weight: 600;
      padding: 0.12rem 0.4rem;
      border-radius: 6px;
      background: #f3f4f6;
      color: #374151;
      border: 1px solid var(--aeris-border);
    }
    .aeris-action-body {
      font-size: 0.82rem;
      line-height: 1.45;
      color: var(--aeris-text);
    }
    .aeris-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.4rem;
      margin-top: 0.35rem;
    }
    .aeris-metric {
      background: #f8f9fb;
      border: 1px solid var(--aeris-border);
      border-radius: 8px;
      padding: 0.45rem 0.5rem;
    }
    .aeris-metric .lbl { font-size: 0.62rem; color: var(--aeris-muted); text-transform: uppercase; letter-spacing: 0.06em; }
    .aeris-metric .val { font-size: 0.88rem; font-weight: 700; color: var(--aeris-text); margin-top: 2px; }
    .aeris-alertbox {
      margin-top: 0.45rem;
      padding: 0.45rem 0.55rem;
      border-radius: 8px;
      background: #fff8ed;
      border: 1px solid #f5d78a;
      font-size: 0.78rem;
      font-weight: 600;
      color: #92400e;
    }
    .aeris-tags { display: flex; flex-wrap: wrap; gap: 0.3rem; margin-top: 0.35rem; }
    .aeris-tag {
      font-size: 0.68rem;
      font-weight: 600;
      padding: 0.2rem 0.45rem;
      border-radius: 6px;
      background: #fff7ed;
      color: #9a3412;
      border: 1px solid #fdba74;
    }
    .aeris-system {
      margin-top: 0.35rem;
      padding-top: 0.35rem;
      border-top: 1px solid var(--aeris-border);
      font-size: 0.62rem;
      color: var(--aeris-muted);
    }
    .aeris-system .lbl { font-weight: 700; letter-spacing: 0.12em; margin-right: 0.35rem; }
    .aeris-system code {
      font-size: 0.6rem;
      background: #f3f4f6;
      padding: 0.1rem 0.28rem;
      border-radius: 4px;
      margin-right: 0.2rem;
    }
    .aeris-footbar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 0.35rem;
      margin-top: 0.35rem;
      padding: 0.35rem 0.5rem;
      background: #f0f1f5;
      border-radius: 8px;
      border: 1px solid var(--aeris-border);
      font-size: 0.72rem;
      color: var(--aeris-muted);
    }
    div[data-testid="stTabs"] button { font-size: 0.8rem !important; }
</style>
        """,
        unsafe_allow_html=True,
    )


def _humanize_risk(flag: str) -> str:
    mapping = {
        "castnet_high_ozone": "High ozone",
        "castnet_moderate_ozone": "Moderate ozone",
        "castnet_elevated_sulfate": "Elevated sulfate",
        "castnet_elevated_nitrate": "Elevated nitrate",
        "rain_can_move_pollutants_to_stormwater": "Rain → stormwater",
        "wind_can_spread_litter": "Wind can spread litter",
        "particle_pollution_context": "Particle pollution",
        "modeled_ozone_elevated": "Modeled ozone elevated",
        "high_uv_plastic_degradation_context": "High UV (plastics)",
        "weather_alert_active": "Active weather alert",
    }
    return mapping.get(flag, flag.replace("_", " ").title())


def _adviser_badge(source: str) -> str:
    lowered = source.lower()
    if "anthropic" in lowered:
        return "Claude"
    if "gemini" in lowered:
        return "Gemini"
    return "Rules"


def _render_brand_header(fixed: EnvironmentalFixedContext) -> None:
    loc = html.escape(fixed.location.label)
    device_pill = "GPU" if torch.cuda.is_available() else "CPU"
    st.markdown(
        f"""
<div class="aeris-header">
  <div class="aeris-brand">
    <div class="aeris-brand-icon" aria-hidden="true">🌿</div>
    <div class="aeris-brand-text">
      <h1>Aeris</h1>
      <span class="aeris-sub">ENVIRONMENTAL SCANNER</span>
    </div>
  </div>
  <div class="aeris-pills">
    <span class="aeris-pill">Streamlit vision</span>
    <span class="aeris-pill">📍 {loc}</span>
    <span class="aeris-pill aeris-pill-live"><span></span>Live scan</span>
    <span class="aeris-pill">Embedded YOLO · {device_pill}</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


def _env_grid_html(fixed: EnvironmentalFixedContext) -> str:
    o3 = f"{fixed.castnet.ozone_ppb:.1f} ppb"
    no3 = f"{fixed.castnet.nitrate_ug_m3:.2f} µg/m³"
    pm = "—"
    if fixed.air_quality and fixed.air_quality.pm2_5_ug_m3 is not None:
        pm = f"{fixed.air_quality.pm2_5_ug_m3:.1f} µg/m³"
    wind = "—"
    if fixed.weather and fixed.weather.wind_speed_kmh is not None:
        wind = f"{fixed.weather.wind_speed_kmh:.0f} km/h"
    loc = html.escape(fixed.location.label)
    parts = [
        f'<div class="aeris-metric"><div class="lbl">Ozone</div><div class="val">{o3}</div></div>',
        f'<div class="aeris-metric"><div class="lbl">Nitrate</div><div class="val">{no3}</div></div>',
        f'<div class="aeris-metric"><div class="lbl">PM2.5</div><div class="val">{html.escape(pm)}</div></div>',
        f'<div class="aeris-metric"><div class="lbl">Wind</div><div class="val">{html.escape(wind)}</div></div>',
    ]
    grid = "".join(parts)
    alert_html = ""
    if fixed.weather_alerts:
        wa = fixed.weather_alerts[0]
        headline = html.escape((wa.headline or wa.event or "Weather alert")[:160])
        alert_html = f'<div class="aeris-alertbox">{headline}</div>'
    return f"""
<div class="aeris-card">
  <div class="aeris-row" style="margin-bottom:0.25rem">
    <h3 style="margin:0">ENVIRONMENTAL CONTEXT</h3>
    <span class="aeris-pill" style="font-size:0.62rem;padding:0.12rem 0.4rem">📍 {loc}</span>
  </div>
  <div class="aeris-grid">{grid}</div>
  {alert_html}
</div>
    """


def _risk_section_html(flags: list[str]) -> str:
    if not flags:
        return """
<div class="aeris-card">
  <h3>RISK SIGNALS</h3>
  <p style="margin:0;font-size:0.8rem;color:#5a6270">No elevated signals right now.</p>
</div>
        """
    tags = "".join(f'<span class="aeris-tag">{html.escape(_humanize_risk(f))}</span>' for f in flags)
    return f"""
<div class="aeris-card">
  <h3>RISK SIGNALS</h3>
  <div class="aeris-tags">{tags}</div>
</div>
    """


def _system_row_html(fixed: EnvironmentalFixedContext) -> str:
    keys = ["castnet", "weather", "air_quality", "weather_alerts"]
    chips = "".join(
        f"<code>{html.escape(key)}:{html.escape(fixed.source_status.get(key, '—'))}</code>"
        for key in keys
    )
    return f'<div class="aeris-system"><span class="lbl">SYSTEM</span>{chips}</div>'


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


_aeris_inject_styles()
_render_brand_header(fixed_context)

with st.expander("Scanner settings", expanded=False):
    s1, s2 = st.columns(2)
    with s1:
        threshold = st.slider(
            "Detection threshold",
            min_value=0.10,
            max_value=1.00,
            value=DEFAULT_TRIGGER_THRESHOLD,
            step=0.05,
        )
        cooldown = st.slider(
            "Advice cooldown (seconds)",
            min_value=3,
            max_value=45,
            value=COOLDOWN_SECONDS,
            step=1,
        )
        frame_skip = st.slider(
            "Infer every Nth frame",
            min_value=1,
            max_value=6,
            value=DEFAULT_FRAME_SKIP,
            step=1,
        )
    with s2:
        inference_size = st.select_slider(
            "Inference size",
            options=[256, 320, 416, 512, 640],
            value=DEFAULT_INFERENCE_SIZE,
        )
        camera_width = st.select_slider(
            "Camera width",
            options=[480, 640, 800, 960, 1280],
            value=DEFAULT_CAMERA_WIDTH,
        )
        camera_height = st.select_slider(
            "Camera height",
            options=[270, 360, 450, 540, 720],
            value=DEFAULT_CAMERA_HEIGHT,
        )
        camera_fps = st.select_slider(
            "Camera FPS",
            options=[15, 20, 24, 30],
            value=DEFAULT_CAMERA_FPS,
        )
    st.caption(f"Model file: `{MODEL_NAME}` · Device: `{YOLO_DEVICE}`")
    st.caption("Classes: " + ", ".join(f"`{str(l).lower()}`" for l in MODEL_LABELS))

video_col, side_col = st.columns([1.45, 0.82], gap="small")

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
        accel = "GPU" if torch.cuda.is_available() else "CPU"
        bar_left, bar_right = st.columns([5, 1])
        with bar_left:
            st.markdown(
                f'<div class="aeris-footbar">Live YOLO stream · {accel} via Streamlit · '
                f"<code>{html.escape(MODEL_NAME)}</code></div>",
                unsafe_allow_html=True,
            )
        with bar_right:
            st.link_button("Open stream ↗", _streamlit_public_url(), use_container_width=True)

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


def _scan_card_html(
    processor: AerisProcessor | None,
    fps: float,
    inference_ms: float,
    latest_detection: YOLODetection | None,
) -> str:
    badge = "Outdoor context active"
    if processor is None:
        return f"""
<div class="aeris-card">
  <div class="aeris-row">
    <div>
      <h3>CURRENT SCAN</h3>
      <div class="aeris-detect">Start the live camera</div>
      <div class="aeris-conf">Detection and advice appear here once the stream is running.</div>
    </div>
    <span class="aeris-badge">{html.escape(badge)}</span>
  </div>
</div>
        """
    if latest_detection is None:
        sub = f"Live pipeline · {fps:.0f} fps · {inference_ms:.0f} ms · imgsz {inference_size}"
        return f"""
<div class="aeris-card">
  <div class="aeris-row">
    <div>
      <h3>CURRENT SCAN</h3>
      <div class="aeris-detect">Scanning…</div>
      <div class="aeris-conf">{html.escape(sub)}</div>
    </div>
    <span class="aeris-badge">{html.escape(badge)}</span>
  </div>
</div>
        """
    label = html.escape(str(latest_detection.object_class).replace("_", " ").title())
    conf_pct = int(round(float(latest_detection.confidence) * 100))
    sub = f"Frame `{html.escape(latest_detection.frame_id)}` · {fps:.0f} fps · {inference_ms:.0f} ms"
    return f"""
<div class="aeris-card">
  <div class="aeris-row">
    <div>
      <h3>CURRENT SCAN</h3>
      <div class="aeris-detect">DETECTED OBJECT: {label}</div>
      <div class="aeris-conf">CONFIDENCE: {conf_pct}% · {sub}</div>
    </div>
    <span class="aeris-badge">{html.escape(badge)}</span>
  </div>
</div>
    """


def _advice_card_html(advice: SustainabilityAdvice | None, latest_detection: YOLODetection | None) -> str:
    if latest_detection is not None and advice is None:
        label = html.escape(str(latest_detection.object_class).replace("_", " ").title())
        return f"""
<div class="aeris-card">
  <div class="aeris-action-head">
    <h3>🌿 RECOMMENDED ACTION</h3>
    <span class="aeris-provider">…</span>
  </div>
  <div class="aeris-action-body" style="color:#5a6270">
    Fetching guidance for <strong>{label}</strong>…
  </div>
</div>
        """
    if advice is None or latest_detection is None:
        return """
<div class="aeris-card">
  <div class="aeris-action-head">
    <h3>🌿 RECOMMENDED ACTION</h3>
    <span class="aeris-provider">—</span>
  </div>
  <div class="aeris-action-body" style="color:#5a6270">
    Point the camera at objects in the frame. Advice refreshes after each confident detection
    (respecting your cooldown setting).
  </div>
</div>
        """
    provider = html.escape(_adviser_badge(advice.decision_source))
    body = html.escape(advice.action).replace("\n", "<br/>")
    ctx = html.escape(advice.context[:900] + ("…" if len(advice.context) > 900 else "")).replace("\n", "<br/>")
    return f"""
<div class="aeris-card">
  <div class="aeris-action-head">
    <h3>🌿 RECOMMENDED ACTION</h3>
    <span class="aeris-provider">{provider}</span>
  </div>
  <div class="aeris-action-body" style="margin-bottom:0.5rem;color:#5a6270;font-size:0.78rem">{ctx}</div>
  <div class="aeris-action-body">{body}</div>
</div>
    """


def render_side_panel(processor: AerisProcessor | None) -> None:
    fps = 0.0
    inference_ms = 0.0
    advice: SustainabilityAdvice | None = None
    latest_detection: YOLODetection | None = None

    if processor is not None:
        with processor._lock:
            advice = processor.advice
            latest_detection = processor.latest_detection
            fps = processor._smoothed_fps
            inference_ms = processor._last_inference_ms

    metrics_placeholder.markdown(
        _scan_card_html(processor, fps, inference_ms, latest_detection),
        unsafe_allow_html=True,
    )
    advice_placeholder.markdown(_advice_card_html(advice, latest_detection), unsafe_allow_html=True)

    merged_flags = sorted(set(fixed_context.risk_flags) | set(advice.risk_flags if advice else []))
    env_block = (
        _env_grid_html(fixed_context) + _risk_section_html(merged_flags) + _system_row_html(fixed_context)
    )
    env_placeholder.markdown(env_block, unsafe_allow_html=True)


if ctx and ctx.state.playing:
    while ctx.state.playing:
        render_side_panel(ctx.video_processor)
        time.sleep(1)
else:
    render_side_panel(None)
