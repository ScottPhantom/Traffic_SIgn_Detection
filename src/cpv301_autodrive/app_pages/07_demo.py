"""Slide 7 — simulation demo with baseline E0."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.views import render_simulator

slide_header(__file__)
st.caption(
    "Baseline E0 phân loại ảnh biển báo đã crop (GTSRB, 43 lớp Đức). Detector Việt Nam sẽ thay "
    "thế bước này sau M4."
)
render_simulator()
slide_footer(__file__)
