# CPV301 AutoDrive — Product roadmap

Mục tiêu cuối: webapp mô phỏng xe và camera trước, nhận diện biển báo, duy trì trạng thái
xe và biểu diễn phản ứng của xe theo biển báo. Các kết quả an toàn trong app chỉ là mô phỏng.

## Ranh giới hệ thống

```text
Camera/frame
    -> detector tìm ROI biển báo
    -> CNN phân loại ROI thành 43 lớp GTSRB
    -> temporal voting/tracking
    -> behavior planner
    -> vehicle/lane simulator
    -> Streamlit dashboard
```

Model hiện tại mới đáp ứng khối **CNN phân loại ROI**. Webapp MVP dùng ảnh biển báo đã crop;
nó chưa chứng minh khả năng tìm biển báo trong một camera frame toàn cảnh.

## Backlog theo milestone

| ID | Milestone | Deliverable/tiêu chí hoàn thành | Trạng thái |
| --- | --- | --- | --- |
| CPV-001 | Reproducible UV | Một lệnh tự sync dependency; kernel riêng; test xanh | Hoàn thành |
| CPV-002 | Webapp shell | Streamlit chạy local, hiển thị pipeline và trạng thái model | Đã dựng MVP |
| CPV-003 | Image/camera classification | Upload nhiều ảnh hoặc webcam snapshot, dự đoán 43 lớp | Đã dựng MVP |
| CPV-004 | Behavior simulation | Stop/speed/turn/caution sinh lệnh và telemetry mô phỏng | Đã dựng MVP |
| CPV-005 | Classifier evaluation | Accuracy, macro-F1, per-class recall, confusion matrix trên test set | Hoàn thành baseline GTSRB |
| CPV-006 | Threshold calibration | Chọn ngưỡng trên validation; báo coverage/accepted accuracy | Tiếp theo |
| CPV-007 | Video journey | Đọc video/frame sequence, timeline, temporal voting và event log | Kế hoạch |
| CPV-008 | Full-scene detector | Dataset bounding box, detector -> crop -> CNN, báo mAP | Kế hoạch |
| CPV-009 | Lane/PID | Lane center, PID steering, kiểm thử trên video/simulator | Kế hoạch |
| CPV-010 | CARLA integration | Camera CARLA -> pipeline -> vehicle control; scenario tests | Kế hoạch |
| CPV-011 | Product hardening | Export model, latency test, Docker/deploy và user guide | Kế hoạch |

## Sprint tiếp theo đề xuất

Gate quản trị trước feature: review tracked-file policy và thiết lập initial Git baseline khi người
dùng yêu cầu. Repo đã được `git init` nhưng hiện chưa có commit hoặc remote nên chưa có lịch sử
recovery/review. Các tài liệu DOCX/PPTX/PDF thiếu khỏi `docs/` là do người dùng chủ động xóa và
không phải blocker.

1. Thực hiện CPV-006 trên `valid.p`. Ngưỡng hiện tại 0.50 chỉ là giá trị demo.
2. Tạo bộ đánh giá biển báo Việt Nam gồm ảnh crop, ảnh toàn cảnh, unknown và non-sign.
3. Sửa augmentation làm đảo trái/phải; huấn luyện lại một baseline có kiểm soát.
4. Chỉ nối behavior planner sau khi các lớp an toàn quan trọng đạt tiêu chí chấp nhận.

## Definition of done cho MVP local

- Một máy mới có `uv` có thể chạy `./scripts/run-web.sh` để tự cài dependency và mở app.
- App nhận ảnh PNG/JPEG/WebP hoặc webcam snapshot.
- App hiển thị nhãn, confidence, trạng thái accepted và hành vi xe mô phỏng.
- Có test cho preprocessing, API health và behavior rules.
- UI ghi rõ ảnh crop/classification không tương đương detector camera toàn cảnh.
