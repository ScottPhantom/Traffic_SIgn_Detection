# Bàn giao Codex: quét ngưỡng confidence cho các model hiện có, 2026-11-06

Owner giao việc này cho Codex ngày 06/11. Nguyên văn:

> "Threshold Sweeping (chạy từ 0,05 đến 1) để tìm ra ngưỡng tối ưu với từng model hiện đang có, rồi vẽ
> figure giống trang 11 trong Artifact."

- Người viết bàn giao: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`.

## Cập nhật chiều 06/11 (đọc trước; mục này thắng nếu mâu thuẫn với phần dưới)

Owner xác nhận giao việc này sau khi gói NMS R1 (`729547b`), kiểm định NMS 0,45 (`381b42c`) và ba việc
chuẩn bị (`9d3f230`, `29e1562`, `048a30a`) đã commit. HEAD lúc cập nhật là `048a30a`.

1. **Pilot không tính lại.**
   - Lưới confidence 0,05–1,00 của pilot với NMS đang dùng đã có trong
     `docs/review/generated/d1_nms_sweep_r1.json`, cấu hình `classaware_0.70`, mục `cells`. File này đã
     qua QA kết quả.
   - Chỉ đọc lại từ đó, ghi SHA-256 (`6be704d2…0057`), và đối chiếu bước 0 (547 / 150 / 457 ở conf 0,20).
   - Trong bảng và figure, dùng pilot làm đường tham chiếu.
2. **Phạm vi thật của việc này là các model còn lại ở mục 1** (A3, A2, pilot + ghép classifier, các bản
   Cascade S1/N1). Bước 0 của từng model là tái tạo đúng số đã QA ở conf 0,20.
3. **Không liên quan tới việc khóa ngưỡng.**
   - Kết quả là chẩn đoán so sánh giữa các model. Nó **không** phải input cho
     `docs/review/d1_threshold_lock_r1_contract.md` và không thay contract đó.
   - Không đọc, tạo hay chấm dự đoán của seed 20261019 (D1-S2-R1).
4. **Bundle:** dùng `tmp/yolo11n_n1_extract_r2` (manifest `8e6ffe77…`). `_r1` bị bộ kiểm bundle từ chối
   vì có `.venv` thừa. Không dọn `_r1`.
5. **Câu hỏi chính cần trả lời, ghi ở đầu báo cáo:**
   - ở cùng mức báo nhầm/ảnh (0,20 / 0,25 / 0,30), recall bỏ qua lớp và recall đúng lớp của từng model là
     bao nhiêu (nội suy tuyến tính giữa hai điểm lưới kề nhau, ghi rõ là nội suy);
   - có model nào nằm trên đường của pilot ở vùng báo nhầm thấp không.
6. **Figure cho deck:**
   - JSON là output bắt buộc; Claude sẽ dựng slide từ JSON.
   - SVG vẫn làm như mục 3, nhưng chữ trong SVG phải ≥ 22 px trên khung 1100 px, để còn đọc được khi đặt
     lên slide 1920×1080.
7. **QA và commit:** QA độc lập do phiên hoặc agent khác làm, rồi mới commit. **Không push** nếu Owner
   chưa cho phép trong chat.

## 0. Ranh giới (bất biến)

- **Chỉ dùng validation R3**: 376 ảnh, 624 box, 9 nhóm D-02. **Không mở, liệt kê, xuất hay chấm sealed
  test `afa03d4b…`.** Mọi output ghi `sealed_test_accessed=false`.
- **Không train, không suy luận lại nếu không cần**, không tải hay upload gì. Chỉ dùng các file dự đoán đã
  có và đã được pin trong các record QA. Nếu một model không có file dự đoán phù hợp thì DỪNG ở model đó
  và ghi lại, không tự chạy suy luận mới.
- **Đây là chẩn đoán, không phải khóa ngưỡng.** Theo D-05 Q4, ngưỡng chỉ được khóa cho ứng viên cuối,
  sau khi đủ 3 seed, trong một record riêng có Owner duyệt. Không đổi mốc D-05, không đổi ngưỡng đang
  dùng trong app (0,20), không sửa code hay file đã pin hash.
- **Git:** chỉ tạo file mới, chỉ `git add` từng đường dẫn cụ thể. Không `git add -A`, stash, reset,
  clean. Giữ nguyên mọi file dirty của Owner. Không commit gì trong `results/experiments/`. Không push
  nếu Owner chưa cho phép trong chat.
- **Phân loại mọi nhận định:** verified current behavior / verified artifact / proposal / unknown.

## 1. Danh sách model (tìm file dự đoán qua record QA, kiểm SHA-256 trước khi dùng)

| # | Cấu hình | Nơi tìm dự đoán và pin |
| --- | --- | --- |
| 1 | YOLO11s-54 pilot, 100 epoch | CSV dự đoán pilot đã pin, được `detector/colab/evaluate_d1_a3_r2_common_r1.py` và `detector/m1/a3_pilot_paired_ci_r1.py` tham chiếu |
| 2 | YOLO11s-54 A3, 40 epoch | `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/` (CSV `e6a25b01…`) |
| 3 | YOLO11s-54 A2 | `results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1/a2_predictions.csv` (`c45dcf1d…d7f1`) |
| 4 | Pilot + ghép classifier (NO_GO) | `results/experiments/D1_yolo11s_wp33_afa03d4b_…_r2/classifier_fusion_r1/` (predictions `916ad347…`) |
| 5 | Cascade S1 + CompactCNN (B0) | `results/experiments/cascade_b0_seed_20261018_r1/` và `docs/review/cascade_b0_r1_result_independent_qa_record.md` |
| 6 | Cascade S1 + CompactCNN R2 | `docs/review/cascade_classifier_improvement_r2_combined_e2e_result_independent_qa_record.md` |
| 7 | Cascade S1 + VGG16-54 | `results/experiments/vgg16_54_seed_20261018_r2/` và `docs/review/vgg16_54_r4_validation_comparison_report.md` |
| 8 | Cascade N1 (YOLO11n) + CompactCNN, + CompactCNN R2, + VGG16-54 | `results/experiments/yolo11n_n1_seed_20261018_r1_r1/` và `docs/review/yolo11n_n1_r1_validation_independent_qa_record.md` |

Với mỗi model, ghi vào record:
- đường dẫn và SHA-256 của file dự đoán;
- **ngưỡng sàn** khi suy luận, tức điểm nhỏ nhất có trong file. Nếu sàn lớn hơn 0,05 thì các điểm dưới
  sàn không đo được: ghi rõ, không ngoại suy;
- **điểm số dùng làm confidence**, đúng như evaluator đã QA của model đó định nghĩa. Với Cascade, đó là
  điểm của chuỗi detector + classifier mà evaluator gốc dùng cho điểm vận hành conf 0,20.

YOLO11n-54 không có kết quả 100 epoch qua QA, nên bỏ qua.

## 2. Cách quét

- **Lưới:** confidence 0,05; 0,10; …; 1,00 (20 điểm, bước 0,05). Ở 1,00 gần như không còn box: vẫn ghi
  để đủ lưới.
- **Bộ chấm:** dùng đúng bộ chấm chung của pilot (Ultralytics IoU matching / AP cùng các điểm vận hành
  m1 D-05, như trong `evaluate_d1_a3_r2_common_r1.py`), trên roster R3 và bundle `8e6ffe77…`.
  - Dùng `tmp/yolo11n_n1_extract_r2`. Không dùng `_r1`, vì thư mục đó có `.venv` thừa nên bộ kiểm bundle
    từ chối.
  - **Bước 0 bắt buộc:** tại conf 0,20, phải tái tạo đúng số đã QA của từng model. Pilot: recall 0,8766,
    FP 150, đúng lớp 457. A2: 0,7612 / 92 / 406. Lệch thì DỪNG ở model đó.
- **Mỗi điểm lưới, ghi:**
  - recall bỏ qua lớp;
  - recall đúng lớp;
  - precision;
  - FP và FP/ảnh;
  - TP;
  - F1 (bỏ qua lớp);
  - recall các lớp derived key 7/32/41. Tra theo yolo_id 7/33/42, dùng `FOCUS_KEYS` trong
    `detector/m1/yolo54_improvement_r3.py`.
- **Ngưỡng "tối ưu" theo luật D-05 (chính):** trong các điểm có recall bỏ qua lớp ≥ 0,85, chọn điểm có
  FP/ảnh thấp nhất; nếu bằng nhau thì chọn confidence cao hơn. Nếu không điểm nào đạt 0,85 thì ghi
  `NO_POINT_MEETS_RECALL_0_85`, kèm điểm có recall cao nhất.
- **Chỉ mô tả, không dùng để chọn:**
  - điểm có F1 lớn nhất;
  - có điểm nào đạt **cả** recall ≥ 0,85 **và** FP/ảnh ≤ 0,30 không (có / không, và là điểm nào).
- **Khoảng tin cậy:** chỉ tại điểm tối ưu theo luật D-05. Dùng bootstrap theo 9 nhóm D-02, 1.000 vòng,
  seed 20261018, theo đúng cách của `a3_pilot_paired_ci_r1`.

## 3. Figure "giống trang 11 của deck"

Trang 11 của deck ([slide 11](https://claude.ai/artifact/J7MVFbwthTZLgMs1Z13wfR#slide-11)) là biểu đồ
đường SVG, nền sáng, lưới ngang mảnh, hai đường dày và một vạch đứt đánh dấu điểm đặc biệt.

**Mỗi model một file SVG, cùng kiểu và cùng thang trục để so được với nhau:**
- `viewBox="0 0 1100 520"`, vùng vẽ x 40–1080, y 20–500. Lưới ngang `#cbd5e1` dày 1px.
- Trục x là confidence 0,05 → 1,00. Trục y là 0 → 1,2, cố định cho mọi model.
- Đường **recall bỏ qua lớp**: `#2563eb`, dày 5. Đường **FP/ảnh**: `#7c3aed`, dày 5. Nếu FP/ảnh vượt 1,2
  thì cắt ở 1,2 và ghi chú.
- Vạch ngang đứt `#94a3b8` ở recall 0,85 và FP 0,30, có nhãn chữ.
- Vạch dọc đứt `#c2410c` ở ngưỡng tối ưu theo luật D-05, có chấm tròn tại hai giao điểm.
- Không dùng font nhúng hay ảnh ngoài. Mỗi file nặng không quá 50 KB. Có thuộc tính `aria-label` mô tả
  bằng tiếng Việt.

Ngoài ra, vẽ **một file SVG tổng hợp** cùng kích thước: mỗi model là một đường recall so với FP/ảnh khi
quét ngưỡng (đường cong đánh đổi). Hai vạch mốc 0,85 / 0,30 tạo thành "vùng đạt D-05".

## 4. Output

| File | Nội dung |
| --- | --- |
| `docs/review/generated/d1_threshold_sweep_r1.json` | Mọi model × mọi điểm lưới; điểm tối ưu và CI; ngưỡng sàn; SHA của input; `sealed_test_accessed=false`; `thresholds_locked=false` |
| `docs/review/generated/d1_threshold_sweep_r1.csv` | Cùng dữ liệu, dạng bảng phẳng |
| `docs/review/figures/d1_threshold_sweep_r1_<model>.svg` | Mỗi model một figure (mục 3) |
| `docs/review/figures/d1_threshold_sweep_r1_tradeoff.svg` | Figure tổng hợp |
| `detector/m1/threshold_sweep_r1.py` cùng test | Script tái tạo được. Đọc file dự đoán đã pin, không suy luận. |
| `docs/review/d1_threshold_sweep_r1_report.md` | Bảng tóm tắt: model / ngưỡng tối ưu / recall / FP/ảnh / có đạt cả hai mốc không. Ghi rõ đây là chẩn đoán trên val, một seed, không khóa ngưỡng. |
| `docs/review/d1_threshold_sweep_r1_independent_qa_record.md` | QA độc lập, do một phiên hoặc agent khác với phiên viết script. Đúng một dòng `Verdict:`. Phải tự tính lại ít nhất pilot và A2 ở 3 điểm lưới, và kiểm lại figure với JSON. |

## 5. Gate và commit

- `uv run ruff check src tests`, `uv lock --check`.
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q <test mới>`.
- Commit **sau khi QA PASS**, gồm đúng các file ở mục 4.
- Báo lại SHA commit, bảng tóm tắt và đường dẫn các SVG. Claude sẽ đưa figure vào deck.

## 6. Điều kiện DỪNG

- Hash file dự đoán không khớp record QA.
- Bước 0 không tái tạo được số đã QA.
- Thiếu file dự đoán của một model (bỏ qua model đó, làm tiếp các model khác).
- Cần suy luận lại.
- QA độc lập không PASS.
