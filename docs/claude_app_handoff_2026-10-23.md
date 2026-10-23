# Bàn giao app D1 / CenterCam cho Claude — 2026-10-23

Owner yêu cầu giao lại toàn bộ việc phát triển `detector_d1.py` và `centercam.py` cho Claude;
Codex chuyển sang baseline detector một lớp + classifier trên Colab. Đây là commit cục bộ cho
phần app; không push và không gom các thay đổi dataset/environment/evaluation khác trong worktree.

## Phần bàn giao đã kiểm thử

- `src/cpv301_autodrive/centercam.py`: API vị trí trái/giữa/phải theo ba phần bằng nhau của ảnh,
  ranh giới giữa bao gồm x=1/3 và2/3; hướng đường Canny/Hough là ước lượng riêng.
- `src/cpv301_autodrive/detector_d1.py`: hash model/class map, box hợp lệ, lock predict dùng chung,
  hỗ trợ bảng và scene giữ ID; chặn mô phỏng lớp chưa kiểm chứng và lớp7/32/41 chưa đạt validation.
- `src/cpv301_autodrive/views.py`: sample/upload, EXIF transpose, cache primitive có giới hạn,
  xử lý lỗi checkpoint/model/PNG hỏng, overlay tham khảo. Ultralytics offline/autoinstall disabled.
- `tests/test_centercam.py`, `tests/test_detector_d1.py`: logic và app regressions.

QA độc lập PASS: `docs/review/d1_centercam_app_r1_independent_qa_record.md`
(`516ce460db90c97a9b64ba3a0ee76b8d47c94b5187eaa9e6e5b97ab13fadf0be`).
60 scoped tests PASS, Ruff/lock/diff/Graft PASS. Browser thật đã kiểm mẫu/upload, không có detection,
PNG hỏng, road overlay và E0↔D1. Bằng chứng chi tiết và giới hạn full-root regression:
`docs/review/d1_centercam_app_r1_implementation_record.md`,
`docs/review/d1_centercam_app_r1_validation_readback.md`.

## Claude làm tiếp

1. Đọc AGENTS/PROJECT_MEMORY, skill Streamlit, hồ sơ QA và diff trước khi sửa; bảo toàn các file
   đang dirty thuộc những workstream khác. Các source vừa được pin trong QA cần successor
   record khi thay đổi, không sửa hồ sơ QA cũ.
2. Xử lý Low L1: `places[place.pole_of or index]` chọn sai radius khi parent index=0; thay bằng
   kiểm tra `is not None`, thêm ca parent0/child khác radius và review lại phần scene.
3. Tiếp tục chất lượng UI, kiểm ảnh thực ngoài sample nếu Owner cung cấp. Vị trí trong ảnh không
   suy ra làn xe/hướng áp dụng/khoảng cách thật. Hướng đường còn là heuristic cần kiểm chứng riêng.
4. Khi Codex cung cấp model cascade và contract inference, tích hợp qua adapter riêng; không
   thay baseline54 lớp hoặc nhãn/class map âm thầm. Không dùng việc app chạy được để đổi NO-GO.
5. Giữ trọng số ngoài git, chỉ kiểm thử simulation. Không train từ nhiệm vụ app này.

App local lúc bàn giao: http://127.0.0.1:8599/demo, tab Codex được giữ mở. Trọng số local hiện tại
vẫn là pilot54 lớp `best.pt`, SHA5d5815a9…; chưa có cải thiện model qua training.

Các thay đổi PROJECT_MEMORY/product_roadmap hiện có chứa cả việc Claude khác, nên không được
gom toàn bộ vào commit app. Chi tiết app trong tài liệu này và hồ sơ QA là bản bàn giao độc lập.
