# Đánh giá ban đầu model nhận diện biển báo

Ngày đánh giá: 2026-10-03 (Asia/Ho_Chi_Minh).

## Kết luận go/no-go

**NO-GO cho ứng dụng giao thông Việt Nam và điều khiển xe.** Model chỉ nên được giữ làm
baseline nghiên cứu GTSRB. Không nối dự đoán hiện tại với điều khiển xe thật hoặc tuyên bố
nhận diện được biển báo Việt Nam.

Tuy nhiên, bằng chứng không ủng hộ câu “model sai hoàn toàn” trên chính tập GTSRB. Khi chạy
đủ 12.630 ảnh test đã tải, model đạt accuracy `86,82%` và macro-F1 `79,21%`. Vấn đề là
hiệu năng này giảm mạnh ở một số lớp quan trọng, model quá tự tin khi sai và chưa có bằng
chứng tổng quát hóa sang Việt Nam hay camera toàn cảnh.

## Kết quả định lượng trên GTSRB test

| Chỉ số | Kết quả |
| --- | ---: |
| Số ảnh | 12.630 |
| Accuracy | 0,8682 |
| Macro-F1 | 0,7921 |
| Weighted-F1 | 0,8705 |
| Balanced accuracy | 0,7949 |
| Dự đoán sai | 1.665 |
| Dự đoán sai nhưng confidence >= 0,90 | 324 |
| Mean confidence | 0,9086 |
| Coverage tại threshold 0,50 | 0,9581 |
| Accuracy trên mẫu được threshold chấp nhận | 0,8910 |

Artifact định lượng:

- `results/evaluation/gtsrb_test_baseline/summary.json`
- `results/evaluation/gtsrb_test_baseline/per_class_metrics.csv`
- `results/evaluation/gtsrb_test_baseline/confusion_matrix.csv`
- `results/evaluation/gtsrb_test_baseline/high_confidence_mistakes.csv`

## Lỗi nghiêm trọng đã xác nhận

### 1. Augmentation làm sai nhãn trái/phải

Notebook dùng `horizontal_flip=True`. Phép lật ngang biến biển “rẽ phải” thành “rẽ trái”
hoặc “keep right” thành “keep left”, nhưng generator vẫn giữ nhãn cũ. Confusion matrix xác
nhận đúng kiểu lỗi này:

- 117 ảnh `Keep right` bị dự đoán thành `Keep left`.
- 86 ảnh `Turn right ahead` bị dự đoán thành `Turn left ahead`.
- 42 ảnh `Turn left ahead` bị dự đoán thành `Turn right ahead`.
- 36 ảnh `Keep left` bị dự đoán thành `Keep right`.

Đây là lỗi training pipeline cần loại bỏ trước khi train lại.

### 2. Hiệu năng theo lớp không đồng đều

Một số recall thấp trên chính GTSRB:

- `Dangerous curve to the right`: 30,00%.
- `Pedestrians`: 43,33%.
- `Slippery road`: 45,33%.
- `Double curve`: 47,78%.
- `Turn right ahead`: 48,10%.

Accuracy tổng thể vì thế che khuất rủi ro ở lớp ít mẫu hoặc lớp có ý nghĩa điều khiển.

### 3. Sai nhưng vẫn rất tự tin

Trong 1.665 dự đoán sai, 324 mẫu có confidence từ 90% trở lên. Vì vậy threshold Softmax
0,50 không phải cơ chế UNKNOWN/OOD đáng tin cậy và không đủ để bảo vệ behavior planner.

### 4. Model không xử lý camera toàn cảnh

Input của model là một biển báo đã crop ở kích thước 32×32. Nếu đưa nguyên camera frame
vào app, toàn bộ cảnh đường bị co thành 32×32 và model vẫn bắt buộc chọn một trong 43 lớp.
Hệ thống còn thiếu detector tìm bounding box trước bước classification.

### 5. Không có bằng chứng cho Việt Nam

Training/test hiện chỉ dùng GTSRB của Đức. Dự án chưa có:

- Dataset biển báo Việt Nam có provenance và label mapping đã duyệt.
- Test set Việt Nam độc lập.
- Tập unknown, non-sign và ảnh khó.
- Đánh giá full-scene/video theo điều kiện ngày, đêm, mưa, che khuất và motion blur.
- Detector, tracking, temporal voting hoặc safety validation.

Nhiều biển có ý nghĩa/hình thức khác nhau giữa hai hệ thống giao thông. Do đó metric GTSRB
không thể được suy diễn thành hiệu năng tại Việt Nam.

### 6. Artifact không phải VGG16 chuẩn

Tên file là `VGG16_model.h5`, nhưng notebook xây CNN nhỏ lấy cảm hứng từ VGG; không dùng
`keras.applications.VGG16`. Tên model cần được sửa trong lần train tiếp theo để tránh nhầm
lẫn provenance và kiến trúc.

## Hướng khắc phục bắt buộc

1. Đóng băng artifact hiện tại làm baseline; không ghi đè.
2. Loại bỏ horizontal flip và rà soát mọi augmentation có thể đổi nghĩa biển.
3. Sửa pipeline train/evaluate để chạy tái lập và không còn cảnh báo input hết dữ liệu.
4. Xây label taxonomy Việt Nam, mapping phần giao nhau với GTSRB và lớp UNKNOWN rõ ràng.
5. Thu thập/tạo split Việt Nam theo biển vật lý hoặc video, tránh rò rỉ frame liền kề.
6. Huấn luyện detector trên ảnh toàn cảnh rồi nối `detector -> crop -> classifier`.
7. Đánh giá riêng classifier, detector, OOD và video; chốt tiêu chí go/no-go trước khi nối
   behavior planner.

## Ranh giới bằng chứng

Kết quả trên chỉ chứng minh hiệu năng closed-set với ảnh crop GTSRB đã tải. Chưa có dữ liệu
Việt Nam trong project để đo trực tiếp mức sai tại Việt Nam, nên kết luận NO-GO dựa trên
thiếu phạm vi huấn luyện/đánh giá và các lỗi pipeline đã quan sát, không phải một con số
accuracy Việt Nam đã đo.
