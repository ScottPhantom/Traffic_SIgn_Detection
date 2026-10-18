# D-05 — Ngưỡng nghiệm thu, latency và số seed cho detector VN (ĐỀ XUẤT)

Trạng thái: `PROPOSAL_AWAITING_OWNER_DECISION` · Ngày: 2026-10-18
Thay thế cho track detector: `docs/review/experiment_acceptance_template.md` (template giữ nguyên,
các bundle D05-A/B/C dùng lại ở đây).

Ưu tiên của owner: có **detector nhận diện biển báo VN trên ảnh toàn cảnh** trước (M1 → M4,
experiment D1); classifier crop (E1–E4) và prototype để sau. Detector YOLO tự phân lớp nên track
detector là track nghiệm thu chính. Đây là **ngưỡng nghiên cứu cho mô phỏng**, không phải ngưỡng
an toàn, không cho phép điều khiển xe thật.

## 1. Dữ kiện đã kiểm (VERIFIED, split WP36-R1)

| Dữ kiện | Giá trị | Hệ quả |
| --- | --- | --- |
| Val | 376 ảnh, 560 box, chỉ **19 lớp** có box; 9 lớp có ≥ 20 box | Val chỉ đủ cho chỉ số gộp; không đặt gate theo lớp trên val |
| Test niêm phong | 903 ảnh, 2.315 box, 32 lớp; 22 lớp có ≥ 20 box | Gate theo lớp chỉ áp cho lớp có ≥ 20 box test |
| Lớp không có test | 22 lớp (D-04 + lớp 38) | Không nằm trong gate; luôn "chưa kiểm chứng" |
| Box nhỏ | ≈ 37 % box < 0,1 % diện tích ảnh | Phải báo AP-small; ảnh đầu vào nên ≥ 1280 px |
| Lệch split | Ảnh dọc và ảnh bucket DARK chỉ có ở val; 1920×1080 chỉ ở train/test | Báo kết quả theo độ phân giải |
| Phần cứng | Apple M1 Pro, 16 GB, GPU 16 nhân (MPS); repo chưa có PyTorch | M1 phải thêm PyTorch/Ultralytics vào lock (cần duyệt đổi dependency) |

## 2. Quyết định cần owner duyệt (khuyến nghị in đậm)

### Q1 — Bundle seed

| Lựa chọn | Seed | Dùng cho | Chi phí ước lượng trên M1 Pro |
| --- | --- | --- | --- |
| D05-A | 1 | Pilot chạy thử, không được promote | 1 lần train |
| **D05-B (khuyến nghị)** | **pilot 1 seed → ứng viên cuối 3 seed** | Chọn model trên val, đánh giá test một lần | ≈ 4 lần train |
| D05-C | 5 | Ứng viên nghiên cứu cuối | ≈ 6 lần train, nhiều giờ/lần |

Seed cố định: `20261018, 20261019, 20261020`. Gate tính trên **trung bình 3 seed**, báo kèm độ lệch chuẩn.

### Q2 — Gate detector trên test niêm phong (đánh giá cuối, chạy một lần)

| Chỉ số | **Đề xuất (D05-B)** | Ghi chú |
| --- | --- | --- |
| mAP50 (class-aware, trung bình trên 32 lớp có box test) | **≥ 0,60** | Chỉ số chính |
| mAP50-95 | **≥ 0,40** | |
| Recall phát hiện biển (bỏ qua lớp, IoU 0,5, tại ngưỡng confidence chọn trên val) | **≥ 0,85** | Cho hỗ trợ lái: bỏ sót biển là lỗi nặng nhất |
| Recall từng lớp **quan trọng** (danh sách Q3) có ≥ 20 box test | **≥ 0,70** mỗi lớp | Lớp nào trượt → hệ thống không dùng lớp đó cho hành vi mô phỏng |
| Recall từng lớp khác có ≥ 20 box test | **≥ 0,50** mỗi lớp | Trượt → lớp bị đánh dấu "chưa đạt", không fail toàn gate |
| False positive / ảnh (trên toàn bộ ảnh test) | **≤ 0,30** | Có ít ảnh nền (chỉ 0544) nên đo trên ảnh có biển |
| AP-small, kết quả theo độ phân giải, 10 lớp có < 20 box test | **chỉ báo cáo**, không gate | Support quá ít để làm gate |
| Khoảng tin cậy 95 % | **bootstrap theo nhóm D-02** trên test | Ảnh cùng nhóm không độc lập |

Gate tổng PASS khi mAP50, mAP50-95, recall phát hiện và FP/ảnh đều đạt, và **mọi lớp quan trọng
có support đều đạt**. Lớp thường trượt không làm fail gate nhưng bị loại khỏi hành vi mô phỏng.

### Q3 — Danh sách lớp quan trọng cho hỗ trợ lái (10 lớp, đều có ≥ 20 box test)

**0 W.224 người đi bộ cắt ngang (95) · 2 P.102 cấm đi ngược chiều (94) · 7 P.123a cấm rẽ trái (53) ·
32 P.123b cấm rẽ phải (71) · 13 W.245a đi chậm (131) · 22 W.221b gồ giảm tốc (31) · 45 I.407a
đường một chiều (70) · 39/40/41 P.127 tốc độ tối đa 60/80/40 km/h (206/143/83).**
(Số trong ngoặc = box test.) P.127 50 km/h (lớp 38) quan trọng nhưng không có test → chưa kiểm chứng.

### Q4 — Dùng val như thế nào

- Chọn model/epoch/kích thước ảnh: theo **mAP50-95 gộp trên val, trung bình theo seed**.
- Ngưỡng confidence và NMS: chọn trên val để recall phát hiện ≥ 0,85 với FP/ảnh nhỏ nhất; khóa
  trước khi mở test.
- 13 lớp không có val (9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50) không được dùng để chọn
  model hay ngưỡng (G0.7).
- Được phép **một lần hiệu chỉnh gate sau pilot**: nếu pilot trên val cho thấy gate Q2 không khả
  thi, PM trình owner mức mới **trước khi** mở test; không hạ gate sau khi đã thấy test.

### Q5 — Latency

| Hạng mục | **Đề xuất** |
| --- | --- |
| Phần cứng chuẩn | Apple M1 Pro, PyTorch MPS; CPU chỉ báo cáo |
| Đo | batch 1, ảnh test thật, 50 lần warm-up + 300 lần đo, gồm tiền xử lý + suy luận + NMS |
| Gate detector | **p95 ≤ 100 ms** (≈ 10 khung hình/giây cho mô phỏng video) |
| Ghi kèm | kích thước ảnh đầu vào, FP32/FP16, phiên bản framework |

### Q6 — Báo cáo bắt buộc mỗi lần chạy

mAP50, mAP50-95, AP-small, precision/recall, AP và recall từng lớp kèm support, confusion matrix,
FP/ảnh, kết quả theo độ phân giải, mẫu lỗi (bỏ sót, sai box, sai lớp), latency; lớp UNKNOWN (31)
báo tỉ lệ bị nhận nhầm thành lớp đã biết; lớp chỉ train báo "chưa kiểm chứng". Hợp đồng tái lập
theo `docs/product_roadmap.md` (seed, commit, lock, hash split/taxonomy).

## 3. Ngoài phạm vi D-05 này

Gate classifier crop (E1–E4) và OOD/UNKNOWN giữ nguyên dạng đề xuất trong template; duyệt khi tới
M2/M3. End-to-end video (M5) duyệt sau khi detector đạt gate.

## 4. Sau khi owner duyệt

Ghi `docs/review/d05_owner_decision_record.md` (append-only) → Gate 0 mở → M1: thêm PyTorch/
Ultralytics vào lock (cần owner duyệt đổi dependency), loader dùng `wp36_r1` check-candidate,
nhãn WP33 + ảnh WP35 cho train, không lật ngang → pilot D1 1 seed trên val.
