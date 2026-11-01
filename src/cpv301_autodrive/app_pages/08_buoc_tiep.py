"""Slide 8 — risks and next steps."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header
from cpv301_autodrive.project_status import MILESTONES

slide_header(__file__)

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown("#### :material/warning: Rủi ro đã biết")
        st.markdown(
            "- License và chủ sở hữu ảnh chưa được tác giả xác nhận (D-01: chấp nhận rủi ro).\n"
            "- Nhóm D-02 do AI suy luận: điểm test có thể lạc quan.\n"
            "- Val nhỏ (376 ảnh, 19 lớp) và lệch độ phân giải so với train/test.\n"
            "- 22 lớp chưa có test niêm phong: luôn ở trạng thái chưa kiểm chứng.\n"
            "- Chưa có ảnh ban đêm đã xác minh: hiệu năng đêm/mưa chưa biết."
        )
with right:
    with st.container(border=True):
        st.markdown("#### :material/rocket_launch: Bước tiếp theo")
        st.markdown(
            "1. Hoàn tất QA lần chạy thử khôi phục checkpoint trên Colab L4.\n"
            "2. Pilot detector D1 một seed (100 epoch), đánh giá trên val, đo latency.\n"
            "3. Ba seed, khóa ngưỡng trên val, đánh giá một lần trên test niêm phong.\n"
            "4. Đưa detector vào app: ảnh toàn cảnh → khung biển báo → hành vi mô phỏng."
        )

st.subheader("Lộ trình", anchor=False)
st.dataframe(
    [{"Mốc": code, "Trạng thái": status, "Phạm vi": scope} for code, scope, status in MILESTONES],
    hide_index=True,
    alt="Bảng milestone M0 đến M6",
)

slide_footer(__file__)
