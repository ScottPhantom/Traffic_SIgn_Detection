"""Slide 6 — model, D-05 acceptance gates, measured speed and training time."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.project_status import D1_STATUS
from cpv301_autodrive.views import render_d05_gates, render_speed_chart, render_train_time_chart

slide_header(__file__)
st.markdown(
    "Detector **YOLO11 54 lớp** tìm vị trí và đọc loại biển báo trong một lần chạy. Model được "
    "train bằng PyTorch/Ultralytics trong project riêng `detector/`, trên split WP36-R1; test "
    "được niêm phong cho lần đánh giá cuối."
)

st.subheader("Ngưỡng nghiệm thu D-05", anchor=False)
render_d05_gates()

st.subheader("Tốc độ suy luận đo được", anchor=False)
render_speed_chart()
st.subheader("Thời gian train", anchor=False)
render_train_time_chart()

st.info(D1_STATUS, icon=":material/pending:")
slide_footer(__file__)
