# CPV301 AutoDrive

Dự án local để đưa mô hình nhận diện 43 lớp biển báo GTSRB từ notebook nghiên cứu thành một sản phẩm có API, kiểm thử và các module mở rộng cho detection, behavior planning và simulator.

## Trạng thái hiện tại

- Đã tải notebook huấn luyện, notebook EDA, model HDF5, database log, dữ liệu raw/processed, kết quả EDA và tài liệu từ Google Drive.
- Model đang dùng: `models/VGG16_model.h5`, đầu vào RGB `32 x 32`, đầu ra Softmax 43 lớp.
- API hiện phục vụ **classification của ảnh biển đã crop**. Detection trong toàn cảnh, lane keeping, PID và CARLA chưa được nối vào runtime này.
- Tên artifact trên Drive là `VGG16_model.h5`. Tuy nhiên code notebook xây một CNN tuần tự lấy cảm hứng từ VGG với hai lớp convolution 32/64 filters; nó không gọi `keras.applications.VGG16` và không phải kiến trúc VGG16 nguyên bản.
- Đánh giá 12.630 ảnh GTSRB test đạt accuracy `86,82%`, macro-F1 `79,21%`; model **không hiệu quả cho giao thông Việt Nam** vì chưa có dữ liệu/đánh giá Việt Nam, chưa có detector và có lỗi augmentation đảo trái/phải. Xem `docs/initial_model_assessment.md`.

## Chạy ứng dụng

Yêu cầu duy nhất là máy đã cài [`uv`](https://docs.astral.sh/uv/). Tại thư mục gốc của dự án, chạy đúng hai lệnh:

```bash
uv sync
python main.py
```

`uv sync` chuẩn bị môi trường và các thư viện cần thiết. `python main.py` khởi động toàn bộ webapp tại [http://127.0.0.1:8501](http://127.0.0.1:8501).

Không cần chạy API hoặc CLI riêng. Nhấn `Ctrl+C` trong Terminal để dừng ứng dụng.

Webapp nhận một hoặc nhiều ảnh và ảnh chụp từ webcam, sau đó phân loại biển báo và hiển thị lệnh điều khiển xe mô phỏng. MVP hiện yêu cầu ảnh biển đã crop; nó chưa phải detector tìm biển trong camera frame toàn cảnh.

## Cấu trúc

```text
Traffic_Sign_Detector/
├── main.py               # Điểm chạy duy nhất cho toàn bộ webapp
├── data/                 # raw ZIP và train/valid/test pickle; không commit Git
├── docs/                 # planning, slide và paper được export/tải từ Drive
├── models/               # model HDF5; không commit Git
├── notebooks/            # notebook gốc từ Drive
├── results/eda/          # kết quả EDA đã có
├── src/cpv301_autodrive/ # package, inference, API và CLI
├── tests/                # smoke/unit tests
├── pyproject.toml        # dependency và metadata cho uv
└── uv.lock               # lockfile tái lập môi trường
```

## Project memory và Graft

- `AGENTS.md` là contract bắt buộc cho agent làm việc trong repository.
- `PROJECT_MEMORY.md` là entry point ngắn cho trạng thái, quyết định, rủi ro và đường dẫn tới
  evidence chi tiết; đây không phải nhật ký chat.
- Source code đã được index cục bộ trong `graft/`. Trước khi đọc hoặc sửa code, agent phải dùng
  `graft check`, sau đó chọn `graft map`, `ask`, `grep`, `skeleton` hoặc `callers` theo loại câu hỏi.
- Sau thay đổi source, trạng thái bàn giao yêu cầu `graft build . && graft check .` thành công.

## Lộ trình idea-to-product

1. Xác nhận metric test của classifier và calibration ngưỡng từ validation set.
2. Tách code train/evaluate khỏi notebook thành pipeline tái lập được.
3. Huấn luyện detector biển báo trên dữ liệu có bounding box; nối detector -> crop -> classifier.
4. Thêm temporal voting/tracking và behavior planner.
5. Thêm lane keeping/PID, rồi mới tích hợp CARLA hoặc simulator đã chọn.

Backlog, tiêu chí hoàn thành và trạng thái từng milestone nằm trong
`docs/product_roadmap.md`. Nguồn Drive và checksum các artifact chính được ghi tại
`docs/drive_inventory.md`. Kiến trúc thực tế, log huấn luyện và ranh giới bằng chứng của
model được ghi tại `docs/model_provenance.md`.
