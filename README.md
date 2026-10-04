# CPV301 AutoDrive

Dự án local để đưa mô hình nhận diện 43 lớp biển báo GTSRB từ notebook nghiên cứu thành một sản phẩm có API, kiểm thử và các module mở rộng cho detection, behavior planning và simulator.

## Trạng thái hiện tại

- Đã tải notebook huấn luyện, notebook EDA, model HDF5, database log, dữ liệu raw/processed, kết quả EDA và tài liệu từ Google Drive.
- Model đang dùng: `models/VGG16_model.h5`, đầu vào RGB `32 x 32`, đầu ra Softmax 43 lớp.
- API hiện phục vụ **classification của ảnh biển đã crop**. Detection trong toàn cảnh, lane keeping, PID và CARLA chưa được nối vào runtime này.
- Tên artifact trên Drive là `VGG16_model.h5`. Tuy nhiên code notebook xây một CNN tuần tự lấy cảm hứng từ VGG với hai lớp convolution 32/64 filters; nó không gọi `keras.applications.VGG16` và không phải kiến trúc VGG16 nguyên bản.
- Đánh giá 12.630 ảnh GTSRB test đạt accuracy `86,82%`, macro-F1 `79,21%`; model **không hiệu quả cho giao thông Việt Nam** vì chưa có dữ liệu/đánh giá Việt Nam, chưa có detector và có lỗi augmentation đảo trái/phải. Xem `docs/initial_model_assessment.md`.

## Cài đặt bằng uv

Yêu cầu duy nhất: cài `uv` trên macOS/Linux. Python 3.12 và toàn bộ dependency được
khóa trong project; `uv run` sẽ tự tạo/cập nhật môi trường trước khi chạy lệnh. Notebook
gốc được huấn luyện bằng TensorFlow 2.20/Python 3.13; runtime local dùng Python 3.12 và
vẫn đọc được model Keras 3.

Thiết lập lần đầu, bao gồm kernel Jupyter riêng cho CPV301:

```bash
./scripts/bootstrap.sh
```

Hoặc đồng bộ thủ công:

```bash
./scripts/uv-project.sh sync --all-extras --all-groups
./scripts/uv-project.sh run cpv301 info
./scripts/uv-project.sh run pytest
```

JupyterLab, kernel, Matplotlib, pandas và công cụ test nằm trong nhóm `dev`; UV đồng bộ
nhóm này theo mặc định. Toàn bộ môi trường Python nằm trong một thư mục `.venv/` chuẩn;
script bootstrap đồng bộ dependency rồi đăng ký kernel `Python (CPV301 AutoDrive)`.

Ultralytics/PyTorch được để ngoài lockfile nền tảng cho tới milestone detection. Khi bắt
đầu milestone đó, thêm dependency bằng:

```bash
uv add --optional detector ultralytics
uv sync --extra detector
```

CARLA không được khóa trong `pyproject.toml` vì simulator và Python API của CARLA phụ thuộc phiên bản hệ điều hành/binary cụ thể. Chỉ thêm CARLA sau khi chốt môi trường simulator.

## Chạy Streamlit webapp

Entry point đơn giản nhất tự đồng bộ mọi dependency rồi mở webapp:

```bash
python main.py
```

Có thể đổi host/port hoặc chạy headless bằng cách chuyển tiếp tham số CLI:

```bash
python main.py --host 127.0.0.1 --port 8511
python main.py --headless
```

Lệnh shell tương đương:

```bash
./scripts/run-web.sh
```

Hoặc sau khi đã bootstrap:

```bash
uv run cpv301 web
```

Mặc định app chạy tại `http://127.0.0.1:8501`. App nhận một/nhiều ảnh hoặc webcam
snapshot, phân loại biển báo và hiển thị lệnh điều khiển xe mô phỏng. MVP hiện yêu cầu
ảnh biển đã crop; nó chưa phải detector tìm biển trong camera frame toàn cảnh.

## Chạy API

```bash
uv run cpv301 serve
```

Sau đó mở `http://127.0.0.1:8000/docs` hoặc kiểm tra:

```bash
curl http://127.0.0.1:8000/health
curl -F 'file=@/duong/dan/bien-bao.png' http://127.0.0.1:8000/v1/predict
```

Lệnh CLI cho một ảnh đã crop:

```bash
uv run cpv301 predict /duong/dan/bien-bao.png
```

Đánh giá lại toàn bộ GTSRB test và xuất artifact:

```bash
uv run cpv301 evaluate
```

`accepted=false` chỉ là cơ chế từ chối sơ bộ theo ngưỡng confidence cấu hình. Ngưỡng mặc định `0.50` chưa được calibration trên validation set và không được xem là kết quả open-set/OOD đã kiểm chứng.

## Cấu trúc

```text
Traffic_Sign_Detector/
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
