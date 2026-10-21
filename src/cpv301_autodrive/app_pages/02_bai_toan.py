"""Slide 2 — problem and goal."""

import streamlit as st

from cpv301_autodrive.presentation import slide_footer, slide_header

slide_header(__file__)

left, right = st.columns(2, gap="large")
with left:
    with st.container(border=True):
        st.markdown("#### :material/report_problem: Vấn đề")
        st.markdown(
            "- Model hiện có (E0) học trên **GTSRB của Đức**: 43 lớp, ảnh đã crop sẵn 32×32.\n"
            "- Biển báo Việt Nam theo **QCVN 41:2024** có nhiều loại khác Đức: biển phụ, "
            "biển ghép xe máy, giới hạn chiều cao theo giá trị.\n"
            "- Ảnh thật là **toàn cảnh đường phố**: biển nhỏ, xa, bị che; khoảng 37 % biển "
            "chiếm dưới 0,1 % diện tích ảnh.\n"
            "- E0 không tìm được biển trong ảnh toàn cảnh, và chưa được kiểm chứng cho Việt Nam."
        )
with right:
    with st.container(border=True):
        st.markdown("#### :material/flag: Mục tiêu")
        st.markdown(
            "- Một **detector nhận diện biển báo Việt Nam trên ảnh toàn cảnh**: tìm vị trí và "
            "đọc loại biển cùng lúc.\n"
            "- Phục vụ **mô phỏng hỗ trợ lái**: kết quả biển báo dẫn tới hành vi xe mô phỏng.\n"
            "- Đánh giá trung thực: chia dữ liệu theo nhóm, test niêm phong, ngưỡng nghiệm thu "
            "được duyệt trước (D-05).\n"
            "- Thứ tự do chủ dự án đặt: **detector Việt Nam trước, prototype trong app sau**."
        )

st.subheader("Phạm vi", anchor=False)
with st.container(horizontal=True):
    with st.container(border=True):
        st.markdown(":green-badge[Trong phạm vi]")
        st.markdown("Ảnh/khung hình camera, 54 lớp biển VN, mô phỏng hành vi, giao diện Streamlit.")
    with st.container(border=True):
        st.markdown(":red-badge[Ngoài phạm vi]")
        st.markdown("Điều khiển xe thật, tuyên bố an toàn, triển khai công khai dữ liệu gốc.")

slide_footer(__file__)
