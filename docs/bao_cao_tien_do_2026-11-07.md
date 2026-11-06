# CPV301 AutoDrive — Báo cáo tiến độ: xử lý ảnh, hiệu suất model và các hướng cải tiến

Ngày lập: 2026-11-05 · Mốc nộp: thứ Bảy 2026-11-07 · Kế thừa: `docs/bao_cao_tien_do_2026-10-24.md`
Trạng thái: `DRAFT_FOR_OWNER_REVIEW`.
- Mục 7 (A2) đã có kết quả qua QA, cập nhật 06/11.
- Mục 8 (ngưỡng NMS × confidence) và mục 11 (bước tiếp theo) cập nhật chiều 06/11.

**Phạm vi bằng chứng:**
- Chỉ dùng dữ liệu validation của DATASET01 và GTSRB test.
- **Test niêm phong `afa03d4b…` chưa được mở** (`sealed_test_accessed=false`).
- Mọi số là kết quả **một seed trên validation**. Không số nào là kết quả nghiệm thu D-05: D-05 chỉ
  được kết luận một lần trên test niêm phong, lấy trung bình 3 seed.
- Hành vi xe trong ứng dụng chỉ là **mô phỏng**. Không có tuyên bố an toàn hay kiểm chứng thực địa.

## 1. Tóm tắt

| Câu hỏi | Trả lời ngắn |
| --- | --- |
| Model tốt nhất hiện tại? | **YOLO11s-54 pilot** (100 epoch, seed 20261018). Trên val R3: mAP50 **0,852**, mAP50-95 **0,609**, recall phát hiện **0,877**, đúng lớp **457/624**, latency p95 **47,3 ms** (M1 Pro). |
| Đạt D-05 trên val chưa? | **Chưa.** Báo nhầm 0,399 FP/ảnh (mốc ≤ 0,30). Recall ba lớp quan trọng 7/32/41 là 0,595 / 0,621 / 0,462 (mốc ≥ 0,70). |
| Từ 24/10 đã làm gì? | Đánh giá lại trên nhãn val R3. So sánh 7 cấu hình model trên cùng bộ chấm. Thử 5 hướng cải tiến: A3, SAHI, temporal, dynamic threshold, ghép classifier. **Không hướng nào vượt pilot** khi xét đủ các tiêu chí khóa trước. |
| A2 (lặp ảnh lớp 7/32/41) thì sao? | Train xong ngày 06/11 và đã qua QA. Báo nhầm giảm (0,245 FP/ảnh) và ba lớp quan trọng tăng, nhưng recall tổng tụt còn 0,761 (mốc 0,85). **Không đạt tiêu chí**, nên giữ pilot. |
| Ngưỡng tốt nhất của pilot? | Trên một pilot: confidence 0,20, NMS IoU 0,70 theo lớp. **Trên trung bình 2 seed (tạm thời): confidence 0,19, NMS 0,70 theo lớp**, cho recall 0,855 và báo nhầm 0,380. Không cấu hình nào vừa đạt recall ≥ 0,85, vừa có báo nhầm ≤ 0,30, mà không làm sai nhãn. **Chưa khóa** (mục 8.2). |
| Seed thứ hai (20261019) cho kết quả thế nào? | Cùng cấu hình pilot, chỉ đổi seed, đã qua QA. mAP50 đúng lớp **0,731** (pilot 0,852); recall đúng lớp 0,607 (pilot 0,732); báo nhầm 0,338 (pilot 0,399, nhưng CI [−0,365; +0,145] chứa 0). Kết quả **dao động lớn giữa các lần train**. Trung bình tạm thời 2 seed ở conf 0,20: recall phát hiện 0,845, báo nhầm 0,368. |
| Khi nào mở test? | Sau khi đủ 3 seed qua QA, khóa ngưỡng trên dữ liệu gộp 3 seed và chốt contract đánh giá cuối. Seed 20261019 đang train ngày 06/11; seed 20261020 chưa được duyệt. Sớm nhất là tuần sau. |

## 2. Thay đổi so với báo cáo 24/10

1. **Nhãn val R3 thành chuẩn đánh giá chung.**
   - Bộ nhãn dẫn xuất D1-VRL-R3 được chủ dự án chấp nhận ngày 23/10.
   - So với nhãn gốc: thêm 64 box, có 40 vùng bỏ qua cho biển quá nhỏ.
   - Tổng cộng 376 ảnh, 624 box.
   - Lượt đánh giá lại D1-VRE-R2 đã qua QA kết quả độc lập. Từ đây mọi model được chấm trên cùng
     376 ảnh / 624 box này.
2. **So sánh thêm các kiến trúc giảng viên yêu cầu** (YOLO11n, Cascade): mục 5.
3. **Năm hướng cải tiến đã thử và đều bị loại**: mục 6. Mỗi hướng có contract khóa trước và QA độc
   lập.
4. **Ứng dụng.** Có demo ảnh tĩnh D1 + CenterCam, demo S1, so sánh dynamic threshold, và prototype
   video Review 2 (chỉ demo): mục 8.

## 3. Dữ liệu và quy trình xử lý ảnh

**Nguồn:**
- DATASET01: `huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116` (CC-BY-SA).
- 3.216 ảnh đường phố, nhãn YOLO, 52 lớp gốc.
- Ảnh không có EXIF/GPS. Địa điểm, thời tiết và thiết bị chụp là UNKNOWN.

| # | Bước | Làm gì | Kết quả |
| --- | --- | --- | --- |
| 1 | Kiểm kê | Băm SHA-256 archive và từng file, audit nhãn | Nguồn bất biến |
| 2 | Cách ly ảnh lỗi | Cách ly 1 stem lỗi bbox và 24 ảnh âm có biển chưa gán nhãn | 3.191 ảnh dùng được |
| 3 | Chuẩn hóa nhãn theo QCVN 41:2024 | Ánh xạ sang mã QCVN; tách biển ghép và biển giá trị (ví dụ P.127 40/60 km/h) | 54 lớp, 8.290 box train được |
| 4 | Gom nhóm chuyến chụp (D-02) | Ghép ảnh gần trùng thành nhóm, review hai lượt rồi QA độc lập | 54 nhóm |
| 5 | Chia theo nhóm (WP36-R1) | Mỗi nhóm nằm trọn trong một split | train 1.912 / val 376 / test 903; test niêm phong |
| 6 | Làm giàu lớp hiếm (WP35) | Biến đổi ảnh thật của 12 lớp hiếm: xoay ±5°, crop, độ sáng, haze, blur, nhiễu, JPEG. **Không lật ngang**, không dán biển tổng hợp | 1.800 ảnh, chỉ dùng cho train |
| 7 | Sửa hướng ảnh (WP38-R1) | 39 ảnh val bị lưu xoay 90°, xuất lại bản PNG không mất dữ liệu | Val đã sửa |
| 8 | Sửa nhãn val (D1-VRL-R3) | Rà biển thật chưa gán nhãn, vẽ thêm box, đánh dấu vùng bỏ qua cho biển ≤ 17,5 px | 624 box val |
| 9 | Xuất gói huấn luyện | Kiểm hash split; ảnh vào model 1280 px (letterbox); gói Colab chỉ có train/val | 3.712 ảnh train, 376 ảnh val, không có ảnh test |

- **Vì sao không lật ngang:** nhiều biển Việt Nam mang nghĩa trái/phải. Ví dụ P.123a là cấm rẽ
  trái, P.123b là cấm rẽ phải. Lật ngang sẽ biến nhãn thành sai nghĩa, nên mọi lần train đều đặt
  `fliplr = 0`.
- **Vì sao chia theo nhóm:** các khung liền nhau của một chuyến đi gần như trùng nhau. Chia ngẫu
  nhiên sẽ làm rò rỉ ảnh và thổi phồng điểm số.
- **Đặc điểm cần lưu ý:**
  - khoảng 37 % box chiếm dưới 0,1 % diện tích ảnh;
  - val tối hơn train (luma trung vị 106 so với 118);
  - chưa có ảnh nào được xác minh là đêm hay mưa;
  - val chỉ có **9 nhóm chuyến chụp**, nên khoảng tin cậy rộng.

## 4. Model D1 — YOLO11s-54 pilot (model chính)

**Cấu hình:**
- Khởi tạo từ YOLO11s pretrained COCO, 54 lớp.
- Ảnh 1280 px, batch 4, 100 epoch, seed 20261018, `fliplr = 0`.
- Train trên Colab NVIDIA L4, khoảng 4,1 giờ, có checkpoint/resume qua Drive.

**Kết quả trên val R3** (376 ảnh, 624 box), confidence 0,20:

| Chỉ số | Bộ chấm chung | Bộ chấm D1-VRE-R2 | Mốc D-05 tham chiếu |
| --- | ---: | ---: | --- |
| mAP50 (đúng lớp) | 0,8521 | 0,8839 | ≥ 0,60, đạt |
| mAP50-95 (đúng lớp) | 0,6089 | 0,6261 | ≥ 0,40, đạt |
| Recall phát hiện (bỏ qua lớp) | 0,8766 | 0,8766 | ≥ 0,85, đạt |
| Báo nhầm / ảnh | 0,3989 | 0,3989 | ≤ 0,30, **chưa đạt** |
| Recall đúng lớp | 0,7324 (457/624) | — | — |
| AP biển nhỏ | 0,2891 | — | — |
| Latency p95, M1 Pro MPS, batch 1 | 47,30 ms | 47,30 ms | ≤ 100 ms, đạt |

Hai cột dùng hai bộ chấm khác nhau nên phải đọc riêng, không trộn. Mục 5 dùng bộ chấm chung để so
các model với nhau.

**Lớp quan trọng có ít nhất 20 box val** (D1-VRE-R2):

| Lớp | Mã QCVN | Recall | Mốc |
| --- | --- | ---: | --- |
| 7 | P.123a, cấm rẽ trái | 0,595 | ≥ 0,70, **chưa đạt** |
| 32 | P.123b, cấm rẽ phải | 0,621 | ≥ 0,70, **chưa đạt** |
| 41 | P.127, tốc độ tối đa 40 km/h | 0,462 | ≥ 0,70, **chưa đạt** |

## 5. So sánh kiến trúc trên cùng bộ chấm (val R3, 376 ảnh / 624 box)

| Cấu hình | mAP50 đúng lớp | mAP50-95 đúng lớp | Recall phát hiện | FP/ảnh @0,20 | Latency p95 (M1 Pro) |
| --- | ---: | ---: | ---: | ---: | ---: |
| **YOLO11s-54 pilot, 100 epoch** | **0,8521** | **0,6089** | 0,8766 | 0,3989 | 47,3 ms |
| YOLO11s-54 A3, 40 epoch, cos_lr | 0,8015 | 0,5633 | 0,7837 | 0,2287 | — |
| Cascade S1: YOLO11s-1 + CompactCNN | 0,4120 | 0,3050 | 0,9054 | 0,2154 | 51,1 ms |
| Cascade S1 + CompactCNN R2 (cân bằng nhóm, jitter crop) | 0,4783 | 0,3310 | — | — | 48,9 ms |
| Cascade S1 + VGG16-54 (train từ đầu) | 0,3323 | 0,2367 | 0,9006 | 0,2261 | — |
| Cascade N1: YOLO11n-1 + CompactCNN | 0,4000 | 0,2954 | — | — | — |
| Cascade N1 + CompactCNN R2 | 0,4500 | 0,3130 | — | — | 31,2 ms |
| Cascade N1 + VGG16-54 | 0,3334 | 0,2412 | — | — | — |

"—" là chưa đo theo cùng giao thức, không phải bằng 0.

**Đọc bảng:**
- **Phát hiện (biển ở đâu) không phải nút thắt.**
  - Detector một lớp S1 đạt mAP50 / mAP50-95 định vị 0,921 / 0,602.
  - N1 đạt 0,912 / 0,592.
  - Đây là thang đo định vị, không đặt chung thang với các số đúng lớp ở bảng trên.
- **Phân lớp mới là nút thắt.** Trên crop của box thật, CompactCNN chỉ đúng top-1 0,598, còn
  VGG16-54 đúng 0,527. Vì vậy Cascade kém YOLO11s-54 trực tiếp về đúng lớp, dù báo nhầm ít hơn.
- **YOLO11n-54** dừng sớm ở epoch 46 và wrapper báo FAILED. Chưa có kết quả đủ 100 epoch qua QA,
  nên không đưa vào bảng.
- **E0** (CNN nhỏ, GTSRB 43 lớp, ảnh crop của Đức) giữ làm mốc tham chiếu: accuracy 0,8682 trên
  GTSRB test. E0 không áp dụng được cho biển Việt Nam toàn cảnh.

## 6. Các hướng cải tiến đã thử (đều có contract khóa trước và QA độc lập)

| Hướng | Ý tưởng | Kết quả chính trên val R3 | Kết luận |
| --- | --- | --- | --- |
| **A3** | Lịch học cosine, 40 epoch | mAP50-95 0,563 so với 0,609 của pilot. Ở điểm vận hành recall ≥ 0,85, A3 báo nhầm nhiều hơn (0,545 so với 0,399). CI ghép cặp theo nhóm: chỉ hiệu mAP50-95 loại trừ 0 (Δ −0,046, CI [−0,102; −0,016]). | Không thay pilot |
| **SAHI** | Suy luận chia ô để bắt biển nhỏ | Đúng lớp 457 → 503 nhưng FP 150 → 328. Ở cùng ngân sách FP, đúng lớp chỉ còn 414. p95 54 → 174 ms. | NO-GO |
| **Temporal** | Bỏ phiếu theo thời gian, ngưỡng động | Đúng lớp 457 → 442, FP 150 → 125. | Chưa có lợi, chờ GT video |
| **Dynamic threshold R1–R6** | Ngưỡng theo lớp, xử lý box chồng lớp | Gộp box tham lam: FP 150 → 99 nhưng đúng lớp 457 → 433. Luật ưu tiên cặp lớp: FP 150 → 123 mà không mất đúng lớp, nhưng nhóm bị ảnh hưởng không có GT của lớp liên quan, và luật được chọn ngay trên val. | Không bật trong app |
| **Ghép YOLO54 + classifier** | Classifier đổi nhãn ở 6 cặp lớp dễ nhầm khi tự tin ≥ 0,80 | Đúng lớp 457 → 456. mAP50 0,852 → 0,834. CI của hiệu chứa 0. p95 58,1 ms. | NO-GO |

**Bài học chung:**
- Đa số "cải tiến" chỉ đổi qua lại giữa báo nhầm và recall.
- Val chỉ có 9 nhóm, nên phải dùng CI ghép cặp theo nhóm và khóa tiêu chí trước khi xem kết quả. Nếu
  không, rất dễ chọn nhầm một cấu hình "thắng" do ngẫu nhiên.
- Một phần báo nhầm là biển thật chưa được gán nhãn. Vì vậy kiểm độ đầy đủ nhãn train là điều kiện
  trước khi đào hard-negative.

## 7. A2 — lặp ảnh train của lớp 7/32/41 (đã xong)

**Thiết kế (khóa trước, đã qua hai QA nguồn độc lập):**
- Mọi ảnh train có nhãn lớp 7, 32 hoặc 41 được liệt kê hai lần.
- 975 ảnh được lặp (339 ảnh thật, 636 ảnh làm giàu), danh sách train tăng từ 3.712 lên 4.687 dòng.
- Đây là thay đổi duy nhất so với pilot. Không thêm pixel mới, không đụng val/test.

**Tiêu chí thắng (chép từ contract R3, không đổi):** so với pilot ở confidence 0,20 trên cùng bộ
chấm, với CI ghép cặp theo 9 nhóm. Xét recall lớp 7/32/41, FP/ảnh và recall tổng.

**Thực thi:**
- Train trên hai runtime L4 khác nhau: smoke 1 epoch, rồi resume tới epoch 100, kết thúc 06:38 ngày
  06/11. Tổng khoảng 7,6 giờ L4.
- QA kết quả độc lập: PASS. Archive, checkpoint, log và attestation đều khớp; thư mục code sạch.
- Epoch tốt nhất trên val khi train: 36.

**Kết quả trên val R3** (confidence 0,20, chấm cùng bộ chấm với pilot, CI ghép cặp theo 9 nhóm;
QA so sánh độc lập: PASS):

| Chỉ số | Pilot | A2 | CI 95 % của hiệu |
| --- | ---: | ---: | --- |
| Recall phát hiện tổng | 0,877 | **0,761** | [−0,241; +0,000] |
| Báo nhầm / ảnh | 0,399 | **0,245** | [−0,388; 0,000] |
| mAP50 đúng lớp | 0,852 | 0,764 | [−0,145; −0,009] |
| mAP50-95 đúng lớp | 0,609 | 0,555 | [−0,092; −0,012] |
| Recall lớp 7 / 32 / 41 | 0,595 / 0,621 / 0,462 | 0,676 / 1,000 / 0,615 | lớp 32 chỉ có 1 nhóm, CI không có thông tin |

**Đánh giá theo tiêu chí khóa trước:**
- Ba lớp quan trọng đều tăng ≥ 0,05: đạt.
- Báo nhầm không tăng quá 0,03: đạt (giảm 0,154).
- Recall tổng ≥ 0,85: **không đạt** (0,761).
- Ngay cả ở ngưỡng A2 tự chọn trên val (0,05), recall vẫn chỉ 0,848 và báo nhầm tăng lên 0,566.

**Kết luận: A2 không đạt tiêu chí. Giữ pilot làm model tham chiếu.**

Lặp ảnh ba lớp đã kéo model về phía các lớp đó: báo nhầm ít hơn, nhận đúng ba lớp nhiều hơn, nhưng
bỏ sót nhiều biển khác hơn. mAP (không phụ thuộc ngưỡng) giảm có ý nghĩa. Lưu ý:
- A2 train nhiều bước hơn pilot khoảng 26 %, nên đây không phải phép thử nhân quả thuần của việc lặp
  ảnh.
- Hồ sơ chi tiết: `docs/review/d1_a2_r1_common_validation_report_r1.md`.

## 8. Ngưỡng NMS IoU × confidence trên pilot (chẩn đoán, chưa khóa)

**Cách làm:**
- Chạy lại pilot trên 376 ảnh val R3 với 11 cấu hình NMS:
  - NMS theo lớp, IoU 0,45 → 0,80;
  - NMS gộp khác lớp, IoU 0,80 / 0,85 / 0,90.
- Mỗi cấu hình quét 20 mức confidence 0,05 → 1,00, tổng 220 ô.
- Cấu hình đang dùng (IoU 0,70) tái tạo đúng số cũ: 547 box đúng vị trí, 150 báo nhầm, 457 đúng lớp.
- QA nguồn và QA kết quả độc lập đều PASS. QA đã tính lại đủ 220 ô.

| Cấu hình (conf 0,20) | Báo nhầm/ảnh | Đúng lớp | mAP50-95 | Kết luận |
| --- | ---: | ---: | ---: | --- |
| **Theo lớp, IoU 0,70 (đang dùng)** | 0,399 | 457 | 0,609 | **Giữ** |
| Theo lớp, IoU 0,45 | 0,359 | 457 | 0,610 | Kiểm định ghép cặp riêng: **chưa đủ bằng chứng** |
| Theo lớp, IoU 0,80 | 0,428 | 457 | 0,608 | Tệ hơn |
| Gộp khác lớp, IoU 0,80 | **0,290** | 433 | 0,539 | Loại: mất 24 box đúng lớp, mAP giảm có ý nghĩa |

**Ba điều rút ra:**
- **Recall chỉ phụ thuộc confidence, không phụ thuộc NMS IoU** (trong vùng đã thử).
  - Ở conf 0,20 recall là 0,877; ở 0,25 đã xuống 0,838, dưới mốc 0,85.
  - Vì vậy, với mọi mức IoU, luật D-05 đều chọn confidence 0,20.
- **NMS chỉ bớt được box trùng, không bớt được báo nhầm trên nền.** Mức tốt nhất theo lớp (IoU 0,45)
  vẫn còn 0,359 báo nhầm/ảnh. Kiểm định ghép cặp khóa trước cho thấy:
  - 15 box bớt đi nằm hết ở 2 trong 9 nhóm chuyến chụp;
  - CI là [−0,104; 0,000], chạm 0, nên chưa đủ bằng chứng;
  - không mất box đúng lớp nào, và cả 9 lần cross-validation đều chọn 0,45: tín hiệu nhất quán nhưng
    quá hẹp.
- **Rủi ro biển đứng chồng nhau chưa kiểm được.** Val không có cặp biển thật nào chồng lên nhau, nên
  không đo được cái hại khi hạ IoU.

**Lưới đã quét có hai giới hạn được ghi lại:**
- Lưới IoU dừng ở 0,45. Mức tốt nhất nằm ngay biên dưới của lưới.
- Lưới confidence có bước 0,05, nên chưa đo chi tiết giữa 0,20 và 0,25.

Contract khóa ngưỡng 3 seed (mục 11) đã thêm lưới confidence mịn 0,15–0,30 bước 0,01, và được khóa
trước khi có số của seed mới.

### 8.1 So sánh các model ở cùng mức báo nhầm (quét confidence, QA PASS)

**Cách làm:**
- Quét 10 cấu hình × 20 mức confidence (0,05 → 1,00), chỉ đọc file dự đoán đã có, không chạy lại model.
- Hai cột đầu của bảng là recall ở mức báo nhầm 0,30/ảnh, **nội suy tuyến tính** giữa hai mức confidence
  kề nhau, không phải một lượt chạy mới.

| Cấu hình | Tìm thấy biển | Đúng tên biển | Có mức conf đạt recall ≥ 0,85 và FP ≤ 0,30? | mAP50 (mốc 0,60) |
| --- | ---: | ---: | --- | ---: |
| YOLO11s-54 pilot | 0,794 | 0,664 | Không | **0,852** |
| YOLO11s-54 A2 | 0,791 | 0,671 | Không | 0,764 |
| YOLO11s-54 A3 | 0,808 | 0,616 | Không | 0,802 |
| Các Cascade (S1/N1 × CompactCNN, R2, VGG16) | 0,869–0,917 | 0,519–0,569 | Có | 0,332–0,478 |

**Đọc bảng:**
- Ở cùng mức báo nhầm, Cascade **tìm thấy** biển nhiều hơn pilot, nhưng **gọi đúng tên** ít hơn.
- Cascade đạt được cặp mốc recall và báo nhầm trên val, nhưng mAP50 nằm dưới mốc 0,60.
- Chưa cấu hình nào đạt đồng thời cả ba mốc. Pilot vẫn tốt nhất cho nhiệm vụ nhận đúng loại biển.
- Nguồn: `docs/review/d1_threshold_sweep_r1_report.md` (commit `03303b6`).

### 8.2 Ngưỡng tạm thời trên 2 seed (chưa khóa, QA PASS)

**Cách làm:** áp đúng luật đã khóa trong contract khóa ngưỡng (`9d3f230`) lên trung bình của seed 20261018
và 20261019. Lưới gồm confidence 0,05–0,95, cộng thêm lưới mịn 0,15–0,30 bước 0,01, nhân với 11 cấu hình
NMS. Commit `f914d31`; QA nguồn và QA kết quả đều PASS. QA đã tính lại 341 ô, 9 fold và các CI.

| Cấu hình | Recall TB (seed 18 / 19) | FP/ảnh TB | Đúng tên TB | Kết luận |
| --- | --- | ---: | ---: | --- |
| Conf 0,20 · NMS 0,70 theo lớp | 0,845 (0,877 / 0,813) | 0,368 | 0,670 | Không hợp lệ: recall < 0,85 |
| **Conf 0,19 · NMS 0,70 theo lớp** | **0,855** (0,889 / 0,821) | **0,380** | 0,676 | **Chọn tạm thời** |
| Conf 0,19 · NMS 0,80 gộp lớp | 0,855 (0,889 / 0,821) | 0,247 | 0,645 | Loại: CI hiệu mAP50-95 [−0,131; −0,034] nằm hẳn dưới 0 |

**Đọc bảng:**
- Muốn giữ recall trung bình ≥ 0,85 thì phải hạ confidence xuống 0,19. Khi đó báo nhầm tăng lên 0,380, vẫn
  trên mốc 0,30.
- Riêng seed 19, recall ở ngưỡng này chỉ 0,821.
- Cấu hình gộp khác lớp đạt cả hai mốc trên val, nhưng làm giảm mAP50-95 có ý nghĩa thống kê, nên bị luật
  khóa trước loại. Không được gọi đây là cải tiến đã được chấp nhận.
- Đây **chưa phải ngưỡng khóa**:
  - chủ dự án đã sửa D-05 Q1 thành 2 seed (record đang QA lại);
  - ngưỡng chính thức phải do bộ khóa R3 tính lại bằng cùng luật, qua QA và được chủ dự án duyệt trước khi
    mở test.

## 9. Ứng dụng Streamlit (mô phỏng)

- **Demo ảnh tĩnh D1 + CenterCam.** YOLO11s-54 vẽ khung và mã biển. CenterCam ước lượng hướng
  đường để xác định biển bên phải hay bên trái làn. Đã qua QA tích hợp độc lập.
- **Demo S1.** Detector một lớp chỉ vẽ khung, không gán loại biển.
- **Dynamic threshold.** So sánh song song các chính sách ngưỡng. Chính sách đang dùng vẫn là ngưỡng
  cố định 0,20.
- **Prototype video Review 2.**
  - Có clip 206 khung ghép từ ảnh camera trước, upload MP4 ngắn, track ID heuristic, và giải thích
    hành vi mô phỏng (`vehicle_action=none`).
  - Trạng thái **DEMO_ONLY**: 0/6 gói video đạt gate, chưa có GT video.

## 10. Giới hạn

- Một seed, chỉ trên validation, và val chỉ có 9 nhóm chuyến chụp.
- Có 13 lớp không có box nào trong val, nên không có số đo cho các lớp này (D-05 Q4).
- Với classifier, chỉ 19 lớp có đủ crop val để đo.
- Chưa có ảnh đêm hoặc mưa đã xác minh.
- Chưa có kết quả trên test niêm phong.
- Hành vi xe chỉ là mô phỏng.

## 11. Bước tiếp theo

| # | Việc | Trạng thái 06/11 chiều |
| --- | --- | --- |
| 1 | **Seed 20261019** (pilot, chỉ đổi seed) | **Xong.** Train hết 100 epoch lúc 16:51 ngày 06/11. QA kết quả run và QA kết quả chấm đều PASS. mAP50 0,731 so với 0,852 của pilot. Báo cáo chi tiết: `docs/review/d1_s2_r1_common_validation_report_r1.md`. Tiếp theo là tính ngưỡng **tạm thời** trên 2 seed (không phải khóa). |
| 2 | **Seed 20261020** | **Bỏ.** Tối 06/11 chủ dự án sửa D-05 Q1: đánh giá cuối dùng trung bình 2 seed (20261018, 20261019) vì không đủ thời gian (`docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`). Quyết định ghi sau khi đã biết kết quả seed 19 trên val, trước khi mở test. Các mốc D-05 giữ nguyên. |
| 3 | **Khóa ngưỡng trên dữ liệu gộp 2 seed** (phụ lục 1 của contract khóa ngưỡng) | Contract đã khóa trước khi có số seed mới, và đã qua QA. Còn phải viết và QA một bộ ghi/kiểm khóa ngưỡng mới cho nhãn R3, vì code cũ không gắn được với roster R3. |
| 4 | **Hiệu chỉnh mốc D-05 một lần** (nếu cần) | Quyết định riêng của chủ dự án, chỉ được làm trước khi mở test, không bao giờ hạ mốc sau khi đã thấy test |
| 5 | **Đánh giá một lần trên test niêm phong** | Đã có bản nháp contract qua QA, trạng thái chưa được duyệt |
| 6 | **Giảm báo nhầm từ dữ liệu train** | Contract rà nhãn train cùng hai phụ lục đều đã qua QA. Chờ duyệt khoảng 57 giờ công (37–100 giờ) và hai quyết định D-A1, D-A2. Sau đó mới đào hard-negative. |

Pilot vẫn chưa đạt mốc báo nhầm trên val, và các hướng hậu xử lý (ngưỡng, NMS) không đưa được về dưới
0,30 mà không làm sai nhãn. Vì vậy việc 6 là đường cải thiện còn lại có triển vọng nhất trước khi mở test.

## 12. Nguồn số liệu

| Nội dung | File |
| --- | --- |
| Pilot trên val R3 (D1-VRE-R2) | `docs/product_roadmap.md` mục M4; record QA kết quả D1-VRE-R2 |
| So sánh chung pilot với A3 | `docs/review/d1_a3_r2_common_validation_report_r1.md` (result JSON `98b8947e…`) |
| CI ghép cặp A3 − pilot | `docs/review/d1_a3_pilot_paired_ci_r1_report.md`, QA `d1_a3_pilot_paired_ci_r1_independent_qa_record.md` |
| Cascade S1 | `docs/review/cascade_b0_r1_validation_comparison_report.md`, `cascade_b0_r1_result_independent_qa_record.md` |
| VGG16-54 | `docs/review/vgg16_54_r4_validation_comparison_report.md` |
| YOLO11n N1 | `docs/review/yolo11n_n1_r1_validation_comparison_report.md`, `yolo11n_n1_r1_validation_independent_qa_record.md` |
| CompactCNN R2 | `docs/review/cascade_classifier_improvement_r2_report.md` và ba record QA kết quả, e2e, latency |
| SAHI | `docs/review/sahi_r1_validation_report.md`, `sahi_r1_independent_qa_record.md` |
| Temporal | `docs/review/temporal_threshold_r1_report.md`, `temporal_threshold_r1_loss_diagnostic_report.md` |
| Dynamic threshold | `docs/review/dynamic_threshold_full_val_overlap_r5_report.md`, `dynamic_threshold_conflict_r6_offline_report.md` |
| Ghép classifier | `docs/review/d1_yolo54_classifier_fusion_r1_result_independent_qa_record.md` (NO_GO) |
| A2 | `docs/review/d1_a2_r1_run_contract.md`, `d1_a2_r1_common_validation_report_r1.md`, `d1_a2_r1_result_independent_qa_record.md`, `d1_a2_r1_common_validation_result_independent_qa_record.md` |
| Quét NMS × confidence | `docs/review/d1_nms_sweep_r1_report.md`, `generated/d1_nms_sweep_r1.json`, hai record QA nguồn và kết quả |
| Quét confidence 10 cấu hình | `docs/review/d1_threshold_sweep_r1_report.md`, `generated/d1_threshold_sweep_r1.json`, `d1_threshold_sweep_r1_independent_qa_record.md` |
| Ngưỡng tạm thời 2 seed | `docs/review/d1_two_seed_provisional_threshold_r1_report.md`, `generated/d1_two_seed_provisional_threshold_r1.json`, hai record QA nguồn và kết quả |
| Kiểm định NMS 0,45 | `docs/review/d1_nms_045_paired_test_r1_report.md`, `d1_nms_045_paired_test_r1_independent_qa_record.md` |
| Khóa ngưỡng 3 seed (contract) | `docs/review/d1_threshold_lock_r1_contract.md` cùng record QA |
| Đánh giá cuối (bản nháp) | `docs/review/d1_final_evaluation_r1_contract_draft.md` cùng record QA |
| Seed 20261019 | `docs/review/d1_s2_r1_run_contract.md`, `d1_s2_r1_execution_record.md`, `d1_s2_r1_result_independent_qa_record.md`, `d1_s2_r1_common_validation_report_r1.md`, `d1_s2_r1_common_validation_result_independent_qa_record.md` |
| Dữ liệu | `docs/dataset01_card_r1.md`, `docs/review/wp35_rare_class_enrichment_report.md`, báo cáo 24/10 mục 3 |
