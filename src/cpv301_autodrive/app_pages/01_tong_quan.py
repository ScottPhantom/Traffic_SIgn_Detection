"""Slide 1 — project overview."""

import streamlit as st

from cpv301_autodrive.presentation import SLIDES, page_path, slide_footer, slide_header
from cpv301_autodrive.project_status import CURRENT_PHASE, GATE0, TRAINING_STATUS
from cpv301_autodrive.views import render_hero, render_pipeline

slide_header(__file__)
render_hero()

passed = sum(1 for _, _, status in GATE0 if status == "PASS")
with st.container(horizontal=True):
    st.metric("Khung hình DATASET01", "3.216", border=True)
    st.metric("Lớp biển báo train", "54", border=True)
    st.metric("Gate 0", f"{passed}/{len(GATE0)} PASS", border=True)
    st.metric("Huấn luyện", TRAINING_STATUS, border=True)
st.caption(f"Giai đoạn hiện tại: {CURRENT_PHASE}.")

render_pipeline()
st.warning(
    "Chưa có model Việt Nam đạt chuẩn: detector đang ở bước chạy thử trên Colab. Demo hiện dùng "
    "baseline E0, chỉ được đo trên ảnh "
    "crop GTSRB của Đức. Hành vi xe chỉ là mô phỏng, không điều khiển phương tiện thật.",
    icon=":material/warning:",
)

st.subheader("Nội dung trình bày", anchor=False)
with st.container(horizontal=True):
    for number, slide in enumerate(SLIDES[1:], start=2):
        with st.container(border=True, width=220):
            st.page_link(page_path(slide), label=f"{number}. {slide.title}", icon=slide.icon)
            st.caption(slide.subtitle)

slide_footer(__file__)
