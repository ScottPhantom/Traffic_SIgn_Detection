# Bàn giao Codex: chuẩn bị chấm seed 20261019, contract khóa ngưỡng 3 seed, bản nháp contract đánh giá cuối — 2026-11-06

Owner giao ba việc chuẩn bị này cho Codex ngày 06/11, chạy song song trong lúc D1-S2-R1 (seed 20261019)
train trên Colab:

- **a.** Chương trình chấm cho seed 20261019.
- **b.** Contract khóa ngưỡng cho 3 seed.
- **c.** Bản nháp contract đánh giá cuối trên test.

Thông tin chung:
- Người viết bàn giao: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`.
- HEAD lúc viết là `381b42c`.

## 0. Ranh giới (bất biến, áp dụng cho cả ba việc)

- **Cả ba đều là việc chuẩn bị, không chạy gì lên dữ liệu mới:**
  - không suy luận model;
  - không train;
  - không chấm seed 20261019 trước khi có đủ hai thứ: QA kết quả run của nó, và việc **b** đã được commit;
  - không khóa ngưỡng;
  - không đổi D-05 hay app.
- **Không mở, liệt kê, đếm, xuất hay chấm sealed test `afa03d4b…`**, kể cả khi viết contract **c**.
  - Mọi con số về test (ví dụ "32 lớp có box trong test") phải trích từ record đã có, như
    `docs/review/d05_owner_decision_record.md`. Không được đếm lại.
  - Mọi record ghi `sealed_test_accessed=false`.
- **Không sửa file đã QA hoặc đã pin hash.** Chỉ tạo successor mới, append-only.
- **Việc train S2 đang chạy:** không động vào notebook, state Drive hay gói S2 đã commit
  (`fc729d0`, `192939f`).
- **Git:**
  - chỉ `git add` từng đường dẫn cụ thể;
  - không `git add -A`, stash, reset, clean;
  - giữ nguyên các file dirty của Owner;
  - không commit `results/experiments/`;
  - **không push nếu Owner chưa cho phép trong chat.**
- Mỗi QA độc lập do một phiên hoặc agent **khác** với phiên viết, và có đúng một dòng `Verdict:`.
- Phân loại mọi nhận định: verified current behavior / verified artifact / proposal / unknown.

**Thứ tự ưu tiên:**
1. **b trước.** Luật chọn ngưỡng phải được commit **trước khi bất kỳ số nào của seed 20261019 trên
   roster R3 tồn tại**. Nếu làm sau, việc chọn ngưỡng sẽ thành chọn sau khi đã xem số.
2. **a** tiếp theo.
3. **c** cuối.

## Việc b — Contract khóa ngưỡng cho 3 seed (D-05 Q4)

**File:** `docs/review/d1_threshold_lock_r1_contract.md`, trạng thái `FROZEN_BEFORE_SEED_RESULTS`.
Sau đó làm QA độc lập `docs/review/d1_threshold_lock_r1_contract_independent_qa_record.md`.

**Căn cứ phải đọc:**
- `docs/review/d05_owner_decision_record.md`, các mục Q1, Q2 và Q4;
- schema khóa ngưỡng sẵn có: `detector/m1/contract.py:335` (`bind_threshold_lock`) và `detector/m1/cli.py`
  từ dòng 291 (`--threshold-lock`, `--final-eval`);
- `docs/review/d1_nms_sweep_r1_report.md`;
- `docs/review/d1_nms_045_paired_test_r1_report.md`.

**Nội dung phải đóng băng:**
- **Ứng viên:** cấu hình pilot (YOLO11s-54) với 3 seed 20261018 / 20261019 / 20261020.
  - Seed 20261020 **chưa được duyệt train**. Contract chỉ mô tả cách dùng nó khi có, không xin quyền.
- **Lưới:**
  - confidence 0,05–0,95 bước 0,05, **cộng thêm lưới mịn 0,15–0,30 bước 0,01**;
  - NMS theo lớp IoU 0,45–0,80 bước 0,05;
  - NMS gộp khác lớp 0,80 / 0,85 / 0,90 chỉ để chẩn đoán, chỉ được chọn nếu đạt đủ điều kiện "rõ ràng
    tốt hơn" bên dưới.
- **Dữ liệu chọn:** validation R3 (376 ảnh, 624 box, 9 nhóm D-02), chấm bằng bộ chấm chung của pilot.
  - **Phải giải quyết và ghi rõ một điểm mở:** schema `bind_threshold_lock` hiện tại bind các
    `input_val_reports` của `m1.cli` (val export). Nhưng tham chiếu validation hiện hành là roster R3
    qua bộ chấm chung. Contract phải chọn một trong hai:
    1. định nghĩa successor binding cho roster R3;
    2. chứng minh hai đường cho ra cùng điểm chọn.
  - Ghi lý do. QA contract phải xét riêng điểm này.
- **Gộp 3 seed:** mỗi ô (confidence, IoU) lấy **trung bình** recall bỏ qua lớp và FP/ảnh của 3 seed.
  Báo cáo thêm từng seed và độ lệch chuẩn.
- **Luật chọn (D-05 Q4):**
  - trong các ô có recall trung bình ≥ 0,85, chọn ô có FP/ảnh trung bình thấp nhất;
  - nếu bằng nhau: confidence cao hơn, rồi mAP50-95 trung bình cao hơn, rồi IoU gần 0,70 hơn.
  - Ghi thêm: ô đã chọn có đạt recall ≥ 0,85 ở **từng** seed không. Đây là thông tin, không phải điều
    kiện, trừ khi QA contract đề nghị khác.
- **Chỉ đổi NMS khỏi 0,70 khi đạt đủ ba điều kiện:**
  1. CI ghép cặp theo nhóm (1.000 vòng, seed 20261018) của hiệu FP/ảnh nằm hẳn dưới 0, trên dữ liệu gộp;
  2. CI hiệu mAP50-95 không nằm hẳn dưới 0;
  3. cross-validation bỏ một nhóm chọn cùng cấu hình (hoặc mức IoU kề bên) ở ít nhất 7/9 fold.

  Ghi rõ: NMS R1 đã cho thấy gộp khác lớp 0,80 trượt điều kiện 2, còn IoU 0,45 trượt điều kiện 1.
- **Đầu ra khi chạy sau này:** một record khóa đúng schema `LOCKED_ON_VAL`, gồm 3 candidate, conf và
  `nms_iou` giống nhau cho cả 3 seed, `sealed_test_seen=false`. Contract cũng nêu:
  - lệnh tạo record khóa;
  - QA độc lập record khóa;
  - Owner duyệt record khóa.
- **Hiệu chỉnh mốc D-05 (Q4) một lần:** contract chỉ nêu đây là quyết định riêng của Owner, phải có
  trước khi mở test, và không bao giờ hạ mốc sau khi đã thấy test. Contract **không** đề xuất con số.
- **Thời điểm chạy:** chỉ sau khi đủ 3 seed qua QA kết quả. Mỗi lượt suy luận NMS × seed cần record
  duyệt suy luận riêng.

## Việc a — Chương trình chấm cho seed 20261019

**Mẫu:** chương trình chấm A2 đã QA:
- `detector/colab/evaluate_d1_a2_r1_common_r1.py`
- `detector/m1/a2_pilot_paired_ci_r1.py`
- các record `docs/review/d1_a2_r1_evaluator_*` (bao gồm addendum 1 về lệnh `PYTHONPATH=.`)

**File mới:**
- `detector/colab/evaluate_d1_s2_r1_common_r1.py`
- `detector/m1/s2_pilot_paired_ci_r1.py`
- tests tương ứng
- `docs/review/d1_s2_r1_evaluator_implementation_record.md`
- QA nguồn độc lập `docs/review/d1_s2_r1_evaluator_source_independent_qa_record.md`

**Yêu cầu:**
- **Chỉ đổi phía candidate:** archive, manifest và `best.pt` của S2, nhập qua CLI cùng hash. Giữ nguyên
  phía pilot, bundle `8e6ffe77…`, roster R3, bộ chấm và các điểm vận hành D-05.
- **Attestation:** dùng các hàm kiểm của launcher S2 (`detector/colab/run_d1_colab_s2_r1.py`,
  `detector/m1/resumable_train_s2_r1.py`). Phải từ chối nếu gặp bất kỳ trường hợp nào:
  - experiment khác D1-S2-R1;
  - seed khác 20261019;
  - status khác `SUCCEEDED`, hoặc không đủ 100 epoch, hoặc dừng sớm;
  - `git_dirty_files != 0`;
  - train args khác pilot ở bất kỳ đâu ngoài seed và các trường định danh run;
  - authorization SHA khác;
  - `sealed_test_accessed != false`.
- **CI ghép cặp seed 19 − seed 18:** 1.000 vòng, seed 20261018, 9 nhóm, cùng mẫu rút cho hai bên.
  Báo cáo:
  - recall bỏ qua lớp, recall đúng lớp, FP/ảnh ở conf 0,20;
  - mAP50, mAP50-95;
  - recall lớp derived key 7/32/41 (yolo 7/33/42).

  Ghi rõ đây là **đo dao động giữa các seed**, không phải phép thử cải tiến.
- **Bằng chứng tái tạo:** test chứng minh phía pilot tái tạo đúng 547 / 150 / 457, mAP50 0,8521,
  mAP50-95 0,6089.
- Bundle dùng `tmp/yolo11n_n1_extract_r2`, không dùng `_r1`.
- **Chưa chạy trên S2 thật** cho tới khi có QA kết quả run S2 **và** việc b đã được commit.

## Việc c — Bản nháp contract đánh giá cuối (chỉ viết, không chạy)

**File:** `docs/review/d1_final_evaluation_r1_contract_draft.md`, trạng thái `DRAFT_NOT_AUTHORIZED`.
Sau đó làm QA độc lập bản nháp.

**Nội dung:**
- **Điều kiện trước khi mở test**, theo đúng thứ tự:
  1. 3 seed qua QA kết quả;
  2. record khóa ngưỡng (việc b) đã chạy, qua QA và được Owner duyệt;
  3. Owner quyết định có dùng lần hiệu chỉnh mốc duy nhất hay không;
  4. contract này được chốt và qua QA;
  5. Owner duyệt mở test.
- **Lệnh và cơ chế có sẵn:** `m1.cli evaluate --split test --final-eval --reason ... --threshold-lock ...`
  và nhật ký truy cập `contract.log_test_access` (`detector/m1/contract.py:578`).
  - Nếu đánh giá cần dùng roster hoặc bộ chấm khác với đường `m1.cli`, bản nháp phải nêu rõ cần successor
    nào và QA nào. Không tự viết code trong việc này.
- **Mốc D-05 Q2,** trích nguyên văn từ record:
  - mAP50 ≥ 0,60, trung bình trên các lớp có box trong test;
  - mAP50-95 ≥ 0,40;
  - recall bỏ qua lớp ≥ 0,85 ở ngưỡng đã khóa;
  - FP/ảnh ≤ 0,30;
  - lớp quan trọng có ≥ 20 box: recall ≥ 0,70;
  - lớp khác có ≥ 20 box: recall ≥ 0,50 (trượt thì lớp đó bị bỏ khỏi hành vi mô phỏng, không làm trượt
    gate);
  - AP-small và lớp có dưới 20 box chỉ báo cáo;
  - CI 95 % bằng bootstrap theo nhóm D-02;
  - **tính trên trung bình 3 seed, kèm độ lệch chuẩn** (Q1).
- **Latency Q5:** M1 Pro MPS, batch 1, 50 lần khởi động, 300 lần đo, p95 ≤ 100 ms.
- **Quy tắc một lần:** mở đúng một lần. Không đổi model, ngưỡng hay mốc sau khi đã thấy test. Kết quả trượt
  vẫn được báo cáo nguyên trạng.
- **Điều kiện dừng và QA:** QA độc lập kết quả trước khi công bố. Bất kỳ hash nào lệch thì dừng mà không
  chạy lại.

## Gate, commit, báo lại

- `uv run ruff check src tests`, `uv lock --check`.
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q <test mới của việc a>`.
- **Commit riêng từng việc, mỗi việc sau khi QA của nó PASS:**
  - commit b: contract và QA;
  - commit a: code, test, implementation record và QA nguồn;
  - commit c: bản nháp và QA.
- Báo lại SHA các commit và các điểm mở, đặc biệt là điểm binding R3 của việc b. Không push nếu Owner
  chưa cho phép trong chat.

## Điều kiện DỪNG

- Cần suy luận, train hay mở test để làm tiếp.
- Hash của gói A2, S2 hoặc pilot không khớp.
- QA không PASS: sửa rồi QA delta. Sau hai vòng vẫn không PASS thì báo Owner.
- Việc a đã có số của S2 trên R3 trước khi việc b được commit: dừng và báo ngay.
