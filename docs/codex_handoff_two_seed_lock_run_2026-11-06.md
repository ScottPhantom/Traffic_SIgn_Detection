# Bàn giao Codex: chạy khóa ngưỡng 2 seed bằng bộ khóa R3 — 2026-11-06

Owner nói trong chat ngày 06/11, nguyên văn: "Bắt đầu bàn giao công việc". Câu này đáp lại danh sách bước,
trong đó có bước "Chạy bộ khóa trên 2 seed. Kết quả phải tái tạo được ngưỡng tạm thời conf 0,19 / NMS 0,70.
Sau đó QA và anh duyệt."

- Người viết: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`, HEAD
  `6ba906d` lúc viết.

## 0. Điều kiện bắt đầu

**Chỉ bắt đầu khi đã có đủ ba thứ:**
1. Bộ khóa R3 (`docs/codex_handoff_r3_threshold_lock_successor_2026-11-06.md`) đã được viết, có **QA nguồn
   PASS** và đã commit.
2. Phụ lục 2 seed của contract khóa ngưỡng đã commit: `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md`
   (commit `c1f3e1d`).
3. Hai seed đều đã có QA run PASS:
   - pilot: `docs/review/d1_pilot_run_registry_independent_qa_record.md`;
   - seed 19: `docs/review/d1_s2_r1_result_independent_qa_record.md`.

## 1. Ranh giới (bất biến)

- **Chỉ validation R3.** Không mở, liệt kê, đếm, xuất hay chấm sealed test `afa03d4b…`. Không gọi
  `m1.cli evaluate --split test` hay `m1.cli lock-thresholds`. Mọi output ghi `sealed_test_accessed=false`.
- **Không train, không suy luận mới.** Dùng lại dự đoán đã có:
  - seed 20261018: 11 CSV trong `results/experiments/d1_nms_sweep_r1/`;
  - seed 20261019: 11 CSV của lượt ngưỡng tạm thời trong
    `results/experiments/d1_two_seed_provisional_threshold_r1/`.

  Hash phải khớp với các JSON đã QA. Nếu thiếu CSV nào thì DỪNG, không suy luận bù.
- **Không sửa** contract, phụ lục, bộ khóa đã QA hay file đã pin.
- **Record khóa chưa có hiệu lực khi chưa được duyệt.** Codex tạo record, nhưng record chỉ có hiệu lực khi đã
  qua QA độc lập **và** Owner duyệt bằng một record riêng. Codex không tự tạo record duyệt đó.
- **Git:** chỉ `git add` từng đường dẫn cụ thể. Không `git add -A`, stash, reset, clean. Giữ nguyên file dirty
  của Owner. Không commit `results/experiments/`. **Không push** nếu Owner chưa cho phép trong chat.
- QA độc lập do phiên hoặc agent **khác** với phiên chạy, và có đúng một dòng `Verdict:`.

## 2. Các bước

1. **Record duyệt dùng lại dự đoán.** Tạo `docs/review/d1_two_seed_lock_r1_owner_authorization_2026-11-06.md`:
   - trích nguyên văn câu Owner ở trên;
   - phạm vi: dùng lại 22 CSV dự đoán validation đã có (11 cho mỗi seed) để chạy bộ khóa R3 một lần;
   - không suy luận mới, không train, không mở test.

   Ghi kèm hash của từng CSV.
2. **Tạo 2 R3 seed report** bằng hàm tạo report của bộ khóa, mỗi seed một report.
3. **Chạy writer**, đúng lệnh đã pin trong implementation record của bộ khóa. Kết quả gồm record khóa
   `docs/review/generated/d1_threshold_lock_r1.json` và sidecar chứng minh R3
   `docs/review/generated/d1_threshold_lock_r1_r3_proof.json`.
4. **Chạy verifier** trên record và sidecar. Phải PASS.
5. **Kiểm tái tạo.** Kết quả chọn phải trùng với lượt tạm thời
   (`docs/review/generated/d1_two_seed_provisional_threshold_r1.json`, SHA-256 `d6ce4556…b627e33`):
   - confidence 0,19;
   - NMS 0,70 theo lớp;
   - recall trung bình 0,85497;
   - FP/ảnh trung bình 0,38032;
   - NMS gộp lớp 0,80 bị loại theo điều kiện mAP.

   Nếu khác ở bất kỳ điểm nào: DỪNG, ghi lại khác ở đâu và vì sao. Không chọn lại bằng tay.
6. **QA kết quả độc lập.** Ghi `docs/review/d1_threshold_lock_r1_result_independent_qa_record.md`. QA phải tự
   tính lại ô được chọn, hai ô đối chứng (0,20 / 0,70 và 0,19 / gộp lớp 0,80), CI của điều kiện đổi NMS và
   cross-validation. QA cũng phải xác nhận record có đúng 2 candidate cùng một bộ ngưỡng, và
   `sealed_test_seen=false`.
7. **Báo cáo** `docs/review/d1_threshold_lock_r1_report.md`, gồm:
   - bộ ngưỡng khóa và các số tại đó;
   - từng seed;
   - hiệu giữa hai seed;
   - giới hạn (2 seed; CI theo nhóm ảnh, không theo seed);
   - trạng thái `AWAITING_OWNER_APPROVAL`.
8. **Commit** sau khi QA kết quả PASS, gồm: record duyệt dùng lại, record khóa, sidecar, QA, báo cáo. Báo lại SHA
   commit cho Owner và Claude.

## 3. Điều kiện DỪNG

- Bộ khóa R3 chưa có QA nguồn PASS.
- CSV thiếu hoặc lệch hash.
- Verifier không PASS.
- Kết quả không tái tạo được lượt tạm thời.
- Cần suy luận mới, train, mở test, hay sửa file đã QA.
- QA kết quả không PASS.
