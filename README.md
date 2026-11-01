# CPV301 AutoDrive — ứng dụng demo

Bản phát hành gọn cho demo nhận diện biển báo trên ảnh, video camera trước và mô phỏng hành vi. Mã nguồn của mỗi chức năng đang dùng nằm trong `src/cpv301_autodrive/`; hồ sơ thí nghiệm/QA đầy đủ vẫn ở nhánh nghiên cứu `codex/yolo11n-dual-track-r1`. Đây là hệ thống **mô phỏng**, chưa đạt tiêu chí nghiệm thu D-05 và không điều khiển xe thật.

## Clone và khởi động

Yêu cầu Python 3.12 và [uv](https://docs.astral.sh/uv/). Để chỉ tải bản phát hành hiện hành, dùng nhánh mặc định với lịch sử nông:

```bash
git clone --depth 1 --single-branch https://github.com/ScottPhantom/Traffic_SIgn_Detection.git
cd Traffic_SIgn_Detection
```

Từ thư mục gốc:

```bash
uv sync --locked --no-dev
uv run --no-sync cpv301 web
```

Mở `http://127.0.0.1:8501`. Có thể dùng `python main.py` để cài môi trường đã khóa và mở app bằng một lệnh. Muốn chạy kiểm tra mã: `uv sync --locked`, rồi `uv run ruff check src tests` và `uv run pytest -q`.

App khởi động được khi chưa có trọng số. Các tab D1, S1, Cascade và E0 sẽ báo rõ phần model còn thiếu. Trọng số và dữ liệu ảnh/video **không nằm trong Git**; cần nhận bản riêng tư từ chủ dự án, giữ đúng tên và SHA-256 dưới đây. Không tải trọng số tự động từ nguồn khác, vì chúng không tương đương checkpoint đã đánh giá.

| Chức năng | Đường dẫn trong checkout | SHA-256 |
| --- | --- | --- |
| D1 YOLO11s-54 | `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/weights/best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| S1 YOLO11s-1 | `results/experiments/cascade_classifier_improvement_r1/latency_input_r1/s1_best.pt` | `30d1d6e0162c4da54ef3c2c1b31f6bbc25f0ea2fa9e76090190addff1307d218` |
| Cascade detector | `models/pretrained/review2_cascade_b0_r1/detector_best.pt` | `30d1d6e0162c4da54ef3c2c1b31f6bbc25f0ea2fa9e76090190addff1307d218` |
| Cascade classifier | `models/pretrained/review2_cascade_b0_r1/classifier_best.pt` | `e4d96b8b2a42a96b0338df7f6fc39fa62f7a466bd94d3a90ef59122791e54e98` |

`models/VGG16_model.h5` là baseline GTSRB E0 riêng tư (43 lớp), không phải VGG16 chuẩn. Người dùng có thể tải ảnh riêng để thử D1/S1 khi có trọng số. Clip PHENIKAA Mini và các ảnh mẫu validation cũng không được phân phối trong Git; tab tương ứng báo thiếu dữ liệu thay vì tự tải hoặc mở tập test niêm phong.

## Bản đồ mã hiện hành

| Chức năng | Module |
| --- | --- |
| Điều hướng Streamlit | `web_app.py`, `app_pages/`, `views.py` |
| YOLO11s-54 và CenterCam | `detector_d1.py`, `centercam.py` |
| YOLO11s-1 | `detector_s1.py`, `s1_demo.py` |
| Dynamic Threshold | `dynamic_threshold.py`, `dynamic_threshold_comparison.py` |
| Video Review 2 | `review2_front_demo.py`, `review2_upload_video.py`, `review2_temporal.py`, `review2_temporal_overlay.py`, `review2_behavior.py` |
| DATASET01 | `dataset01_authority.py` và `dataset01_renderer.py` |

Các tên module phát hành là tên ổn định. Mã huấn luyện, notebook, chứng cứ QA theo phiên bản và kết quả thí nghiệm ở nhánh nghiên cứu; chúng không được gộp thành logic runtime thứ hai. `docs/review/generated/` ở đây chỉ chứa bản dữ liệu công khai mà app đọc trực tiếp, gồm class map 54 lớp và bằng chứng split/đồ thị đã pin.

## Giới hạn kết quả

Dynamic Threshold là xử lý sau dự đoán, không thay trọng số YOLO. Policy đang dùng chưa chứng minh cải thiện độ chính xác trên validation độc lập. Tracking/video là heuristic cho demo; nhãn biển và hành vi xe chưa được chứng nhận an toàn. Không sử dụng clip riêng tư hoặc tập test niêm phong để chọn model/ngưỡng.
