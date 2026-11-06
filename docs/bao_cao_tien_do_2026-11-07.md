# CPV301 AutoDrive — Báo cáo tiến độ: xử lý ảnh, hiệu suất model và các hướng cải tiến

Ngày lập: 2026-11-05 · Mốc nộp: thứ Bảy 2026-11-07 · Kế thừa: `docs/bao_cao_tien_do_2026-10-24.md`
Trạng thái: `DRAFT_FOR_OWNER_REVIEW`. Mục 7 (A2) đã có kết quả qua QA, cập nhật 06/11.

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
| Khi nào mở test? | Sau khi chốt model, train đủ 3 seed và khóa ngưỡng trên val. Sớm nhất là tuần sau. |

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

## 7. A2 — lặp ảnh train của lớp 7/32/41 (đang chạy)

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

## 8. Ứng dụng Streamlit (mô phỏng)

- **Demo ảnh tĩnh D1 + CenterCam.** YOLO11s-54 vẽ khung và mã biển. CenterCam ước lượng hướng
  đường để xác định biển bên phải hay bên trái làn. Đã qua QA tích hợp độc lập.
- **Demo S1.** Detector một lớp chỉ vẽ khung, không gán loại biển.
- **Dynamic threshold.** So sánh song song các chính sách ngưỡng. Chính sách đang dùng vẫn là ngưỡng
  cố định 0,20.
- **Prototype video Review 2.**
  - Có clip 206 khung ghép từ ảnh camera trước, upload MP4 ngắn, track ID heuristic, và giải thích
    hành vi mô phỏng (`vehicle_action=none`).
  - Trạng thái **DEMO_ONLY**: 0/6 gói video đạt gate, chưa có GT video.

## 9. Giới hạn

- Một seed, chỉ trên validation, và val chỉ có 9 nhóm chuyến chụp.
- Có 13 lớp không có box nào trong val, nên không có số đo cho các lớp này (D-05 Q4).
- Với classifier, chỉ 19 lớp có đủ crop val để đo.
- Chưa có ảnh đêm hoặc mưa đã xác minh.
- Chưa có kết quả trên test niêm phong.
- Hành vi xe chỉ là mô phỏng.

## 10. Bước tiếp theo

1. **Chốt ứng viên cuối.** A2 không đạt, nên ứng viên hiện tại là pilot. Pilot vẫn chưa đạt FP/ảnh
   trên val, nên chủ dự án cần quyết định trước khi train thêm seed 20261019 và 20261020.
2. **Hướng tiếp theo cho báo nhầm và lớp quan trọng:** hard-negative sau khi rà nhãn train, hoặc một
   biến thể A2 cân bằng số bước. Mỗi hướng cần contract riêng và được duyệt.
3. **Khóa ngưỡng confidence/NMS trên val:** chọn mức có recall ≥ 0,85 với ít FP nhất. Nếu cần,
   hiệu chỉnh mốc D-05 **một lần**, có chủ dự án duyệt, trước khi mở test.
4. **Đánh giá một lần trên test niêm phong.**
5. **Song song:** kiểm độ đầy đủ nhãn train (contract đã QA, còn phụ lục 2), rồi đào hard-negative
   để giảm báo nhầm. Việc này cần khoảng 35–98 giờ công người rà nhãn và cần chủ dự án duyệt.

## 11. Nguồn số liệu

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
| Dữ liệu | `docs/dataset01_card_r1.md`, `docs/review/wp35_rare_class_enrichment_report.md`, báo cáo 24/10 mục 3 |
