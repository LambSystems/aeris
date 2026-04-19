from __future__ import annotations

import io
import time
from pathlib import Path

import cv2
import numpy as np
import streamlit as st
from PIL import Image, ImageDraw

from app.cv.yolo_service import (
    _default_confidence_threshold,
    _default_image_size,
    _ensure_runtime_dirs,
    display_label,
    _model_name,
    _run_yolo,
)


st.set_page_config(page_title="Aeris YOLO Live Check", layout="wide")

RAW_TEST_OBJECTS = [
    ("bottle", "maps directly to bottle"),
    ("cup", "maps directly to cup"),
    ("wine glass", "maps to glass_container"),
    ("potted plant", "maps to plant_pot"),
    ("scissors", "maps to metal_tool"),
    ("cell phone", "maps to electronics_case"),
    ("laptop", "maps to electronics_case"),
    ("keyboard", "maps to electronics_case"),
    ("remote", "maps to electronics_case"),
    ("suitcase", "maps to storage_bin"),
]


def _draw_result(image: Image.Image, result: object) -> Image.Image:
    rendered = image.copy()
    draw = ImageDraw.Draw(rendered)
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return rendered

    for box in boxes:
        raw_label = _raw_label(result.names, box)
        normalized = display_label(raw_label)
        if normalized is None:
            continue

        x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
        confidence = float(box.conf[0])
        label = f"{normalized} ({confidence:.2f})"
        draw.rectangle((x1, y1, x2, y2), outline="#00D084", width=3)
        text_box = (x1, max(y1 - 22, 0), min(x1 + 220, rendered.width), y1)
        draw.rectangle(text_box, fill="#00D084")
        draw.text((x1 + 4, max(y1 - 20, 0)), label, fill="black")

    return rendered


def _raw_label(names: dict[int, str] | list[str], box: object) -> str:
    class_id = int(box.cls[0])
    if isinstance(names, dict):
        return names.get(class_id, "unknown")
    return names[class_id] if class_id < len(names) else "unknown"


def _normalized_hits(result: object) -> list[tuple[str, str, float]]:
    hits: list[tuple[str, str, float]] = []
    boxes = getattr(result, "boxes", None)
    if boxes is None:
        return hits

    for box in boxes:
        raw_label = _raw_label(result.names, box)
        normalized = display_label(raw_label)
        if normalized is None:
            continue
        hits.append((normalized, raw_label, round(float(box.conf[0]), 4)))

    hits.sort(key=lambda hit: hit[2], reverse=True)
    return hits


def _scan_pil_image(image: Image.Image, confidence_threshold: float, image_size: int) -> tuple[object, Image.Image]:
    _ensure_runtime_dirs()
    rgb_image = image.convert("RGB")
    result = _run_yolo(rgb_image, confidence_threshold=confidence_threshold, image_size=image_size)
    return result, _draw_result(rgb_image, result)


def _capture_webcam_frame(camera_index: int) -> Image.Image | None:
    camera = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    try:
        ok, frame = camera.read()
    finally:
        camera.release()

    if not ok:
        return None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def _uploaded_image() -> Image.Image | None:
    uploaded_file = st.file_uploader(
        "Upload an image",
        type=["jpg", "jpeg", "png", "webp"],
        help="Good for quick still-image checks before you fine-tune anything.",
    )
    if uploaded_file is None:
        return None
    return Image.open(io.BytesIO(uploaded_file.getvalue())).convert("RGB")


def _camera_snapshot() -> Image.Image | None:
    snapshot = st.camera_input("Take a browser camera snapshot")
    if snapshot is None:
        return None
    return Image.open(io.BytesIO(snapshot.getvalue())).convert("RGB")


st.title("Aeris YOLO Live Check")
st.caption(f"Model: {_model_name()} | Stock checkpoint: 80 COCO classes | Curated aliases plus all stock classes")

with st.sidebar:
    st.subheader("Live Settings")
    confidence_threshold = st.slider(
        "Confidence threshold",
        min_value=0.05,
        max_value=0.95,
        value=float(_default_confidence_threshold()),
        step=0.05,
    )
    image_size = st.select_slider(
        "Image size",
        options=[320, 480, 640, 800, 960],
        value=int(_default_image_size()),
    )
    live_mode = st.toggle("Desktop webcam live mode", value=False)
    camera_index = st.number_input("Camera index", min_value=0, max_value=5, value=0, step=1)
    refresh_ms = st.slider("Live refresh (ms)", min_value=150, max_value=1500, value=500, step=50)

    st.subheader("Test These First")
    for raw_label, note in RAW_TEST_OBJECTS:
        st.write(f"- `{raw_label}`: {note}")

left_col, right_col = st.columns([1.6, 1.0])
image: Image.Image | None = None
source_label = "none"

with left_col:
    if live_mode:
        image = _capture_webcam_frame(int(camera_index))
        source_label = "desktop webcam"
        if image is None:
            st.error("Could not read from the selected webcam.")
    else:
        snapshot = _camera_snapshot()
        upload = _uploaded_image()
        image = snapshot or upload
        source_label = "browser snapshot" if snapshot is not None else "upload"

with right_col:
    st.subheader("What You Can Use Without Fine-Tuning")
    st.write("The stock model can show all of its built-in COCO classes, and Aeris still renames the curated ones when aliases exist:")
    st.write(
        "`bottle`, `cup`, `wine glass`, `potted plant`, `scissors`, "
        "`cell phone`, `laptop`, `keyboard`, `remote`, `suitcase`"
    )
    st.write("Those collapse into these Aeris labels:")
    st.write(
        "`bottle`, `cup`, `glass_container`, `plant_pot`, `metal_tool`, "
        "`electronics_case`, `storage_bin`"
    )

if image is not None:
    result, rendered = _scan_pil_image(image, confidence_threshold, image_size)
    hits = _normalized_hits(result)

    image_col, detections_col = st.columns([1.5, 1.0])
    with image_col:
        st.subheader(f"Live View ({source_label})")
        st.image(np.array(rendered), use_container_width=True)
    with detections_col:
        st.subheader("Detections")
        st.write(f"Inference time: `{getattr(result, 'speed', {}).get('inference', 0.0):.1f} ms`")
        if hits:
            st.dataframe(
                [
                    {"label": normalized, "raw_label": raw_label, "confidence": confidence}
                    for normalized, raw_label, confidence in hits
                ],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No currently mapped Aeris objects detected in this frame.")
else:
    st.info("Turn on live mode, take a camera snapshot, or upload an image to start testing.")

if live_mode:
    time.sleep(refresh_ms / 1000)
    st.rerun()
