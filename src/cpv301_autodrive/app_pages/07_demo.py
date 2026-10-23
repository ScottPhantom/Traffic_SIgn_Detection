"""Slide 7 — simulation demo: D1 Vietnamese detector (default) and the E0 GTSRB baseline."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.views import render_d1_demo, render_simulator

slide_header(__file__)
model = st.segmented_control(
    "Model",
    ["D1 · biển Việt Nam (ảnh toàn cảnh)", "E0 · GTSRB (ảnh crop)"],
    default="D1 · biển Việt Nam (ảnh toàn cảnh)",
    required=True,
    key="demo_model",
)
if model.startswith("D1"):
    render_d1_demo()
else:
    st.caption(
        "Baseline E0 phân loại ảnh biển báo đã crop (GTSRB, 43 lớp Đức); không dùng được cho ảnh "
        "toàn cảnh Việt Nam."
    )
    render_simulator()
slide_footer(__file__)
