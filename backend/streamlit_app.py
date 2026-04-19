import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from app.sustainability.adviser import get_sustainability_advice
from app.sustainability.castnet_mock import load_mock_castnet
from app.sustainability.schemas import CASTNETReading, YOLODetection
from app.schemas import BoundingBox

OBJECT_CLASSES = [
    "soda_can",
    "plastic_bottle",
    "cardboard_box",
    "cigarette_butt",
    "plastic_bag",
    "food_wrapper",
    "glass_bottle",
    "styrofoam_cup",
]


st.set_page_config(
    page_title="Aeris — Sustainability Adviser",
    page_icon="🌿",
    layout="wide",
)

st.title("🌿 Aeris Sustainability Adviser")
st.caption("Detects environmental concerns from YOLO object detections and CASTNET air quality data.")

st.sidebar.header("Detection Input")
st.sidebar.subheader("YOLO Detection")

object_class = st.sidebar.selectbox("Object Class", OBJECT_CLASSES, index=0)
confidence = st.sidebar.slider("Confidence", min_value=0.90, max_value=1.00, value=0.94, step=0.01)
frame_id = st.sidebar.text_input("Frame ID", value="frame_042")
timestamp = st.sidebar.text_input("Timestamp", value=datetime.now().isoformat(timespec="seconds") + "Z")

st.sidebar.markdown("---")
st.sidebar.subheader("Bounding Box (optional)")
use_bbox = st.sidebar.checkbox("Include bounding box", value=True)
if use_bbox:
    col1, col2 = st.sidebar.columns(2)
    bbox_x = col1.number_input("x", value=120.0)
    bbox_y = col2.number_input("y", value=340.0)
    bbox_w = col1.number_input("width", value=80.0)
    bbox_h = col2.number_input("height", value=60.0)

st.sidebar.markdown("---")
st.sidebar.subheader("CASTNET Air Quality")
use_custom_castnet = st.sidebar.checkbox("Customize CASTNET data", value=False)

if use_custom_castnet:
    castnet_site = st.sidebar.text_input("Site ID", value="NE11")
    castnet_location = st.sidebar.text_input("Location", value="Boston, MA (urban periphery)")
    ozone_ppb = st.sidebar.number_input("Ozone (ppb)", value=54.2, step=0.1)
    sulfate = st.sidebar.number_input("Sulfate (µg/m³)", value=2.8, step=0.1)
    nitrate = st.sidebar.number_input("Nitrate (µg/m³)", value=1.6, step=0.1)
    co_ppb = st.sidebar.number_input("CO (ppb)", value=210.0, step=1.0)
    castnet_date = st.sidebar.text_input("Measurement Date", value="2026-04-18")
    castnet = CASTNETReading(
        site_id=castnet_site,
        location=castnet_location,
        ozone_ppb=ozone_ppb,
        sulfate_ug_m3=sulfate,
        nitrate_ug_m3=nitrate,
        co_ppb=co_ppb,
        measurement_date=castnet_date,
    )
else:
    castnet = load_mock_castnet()

col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Current Inputs")

    st.markdown("**YOLO Detection**")
    st.json({
        "object_class": object_class,
        "confidence": round(confidence, 2),
        "frame_id": frame_id,
        "timestamp": timestamp,
        **({"bbox": {"x": bbox_x, "y": bbox_y, "width": bbox_w, "height": bbox_h}} if use_bbox else {}),
    })

    st.markdown("**CASTNET Reading**")
    st.json(castnet.model_dump())

with col_right:
    st.subheader("Sustainability Advice")
    analyze = st.button("Analyze", type="primary", use_container_width=True)

    result_placeholder = st.empty()

    if analyze:
        detection = YOLODetection(
            object_class=object_class,
            confidence=confidence,
            frame_id=frame_id,
            timestamp=timestamp,
            bbox=BoundingBox(x=bbox_x, y=bbox_y, width=bbox_w, height=bbox_h) if use_bbox else None,
        )

        with result_placeholder.container():
            with st.spinner("Analyzing scene with Aeris..."):
                try:
                    advice = get_sustainability_advice(detection, castnet)
                    st.session_state["last_advice"] = advice
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
                    st.stop()

    if "last_advice" in st.session_state:
        advice = st.session_state["last_advice"]

        with result_placeholder.container():
            st.markdown(
                f"**Detected:** `{advice.object_detected}` &nbsp;|&nbsp; "
                f"**Confidence:** {advice.confidence:.0%}"
            )
            st.info(advice.context)
            st.success(advice.action)
