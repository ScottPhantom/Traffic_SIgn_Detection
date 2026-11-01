"""Slide 7 — still-image D1/S1 detectors and the E0 GTSRB baseline."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.review2_front_demo import render_review2_front_demo
from cpv301_autodrive.s1_demo import render_s1_demo
from cpv301_autodrive.views import render_d1_demo, render_simulator

slide_header(__file__)
model = st.segmented_control(
    "Model",
    [
        "D1 · YOLO11s 54 lớp (phát hiện + phân loại)",
        "S1 · YOLO11s 1 lớp (chỉ phát hiện)",
        "E0 · GTSRB (ảnh crop)",
        "Review 2 · video camera trước (thử nghiệm)",
    ],
    default="D1 · YOLO11s 54 lớp (phát hiện + phân loại)",
    required=True,
    key="demo_model",
)
if model.startswith("D1"):
    render_d1_demo()
elif model.startswith("S1"):
    render_s1_demo()
elif model.startswith("Review 2"):
    render_review2_front_demo()
else:
    st.caption(
        "Baseline E0 phân loại ảnh biển báo đã crop (GTSRB, 43 lớp Đức); không dùng được cho ảnh "
        "toàn cảnh Việt Nam."
    )
    render_simulator()
slide_footer(__file__)
