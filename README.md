# CPV301 AutoDrive

Webapp local phân loại biển báo giao thông và mô phỏng phản ứng của xe.

## Chạy ứng dụng

Máy chỉ cần cài [`uv`](https://docs.astral.sh/uv/). Tại thư mục gốc của dự án, chạy đúng hai lệnh:

```bash
uv sync
python main.py
```

Sau đó mở [http://127.0.0.1:8501](http://127.0.0.1:8501). Nhấn `Ctrl+C` để dừng.

`main.py` tự khởi động toàn bộ webapp; không cần chạy thêm lệnh nào khác.

## Lưu ý

Phiên bản hiện tại dùng model `models/VGG16_model.h5` để phân loại 43 lớp GTSRB từ ảnh biển báo
đã được crop. Webapp chưa phát hiện biển báo trong ảnh toàn cảnh và chưa được xác thực cho giao
thông Việt Nam hoặc điều khiển xe thật.
