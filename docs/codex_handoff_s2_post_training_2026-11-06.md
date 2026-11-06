# Bàn giao Codex: sau khi train xong seed 20261019 (D1-S2-R1) — QA kết quả run, chấm, QA kết quả chấm

Owner giao cho Codex ngày 06/11: "Để Codex làm" phần chấm seed 19 so với seed 18.

- Người viết bàn giao: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`.
- **Chỉ bắt đầu khi lượt resume trên Colab đã kết thúc**: status `SUCCEEDED`, 100 epoch, có result
  archive và manifest trên Drive.

## 0. Ranh giới (bất biến)

- **Chỉ validation R3.** Không mở, liệt kê, xuất hay chấm sealed test `afa03d4b…`. Mọi output ghi
  `sealed_test_accessed=false`.
- **Không train lại**, không sửa gói S2 đã commit (`fc729d0`, `192939f`), không sửa evaluator S2 đã qua
  QA (`29e1562`).
- **Không khóa ngưỡng.** Kết quả của bước này chỉ là input cho contract khóa ngưỡng
  `docs/review/d1_threshold_lock_r1_contract.md`, không thay contract đó.
- **Độc lập:** phiên Codex đã vận hành lượt train S2 **không được** tự làm QA kết quả run hay QA kết quả
  chấm. Hai bước QA đó phải do một phiên hoặc agent Codex **khác** làm. Đây là cùng quy tắc đã áp dụng
  cho A2.
- **Git:** chỉ `git add` từng đường dẫn cụ thể, không `git add -A`, stash, reset, clean. Giữ nguyên file
  dirty của Owner. Không commit `results/experiments/` hay weights. **Không push** nếu Owner chưa cho phép
  trong chat.
- Mỗi record QA có đúng một dòng `Verdict:`.

## 1. Bàn giao thực thi (phiên vận hành)

- Viết `docs/review/d1_s2_r1_execution_record.md` theo mẫu `docs/review/d1_a2_r1_execution_record.md`
  và `docs/review/d1_a2_r1_claude_handoff_2026-11-06.md`. Gồm:
  - commit nguồn và notebook;
  - giờ bắt đầu và kết thúc;
  - hai runtime digest (fresh và resume, phải khác nhau);
  - status cuối, `completed_epoch`;
  - SHA-256 và kích thước của archive, manifest, `best.pt`, `last.pt`, `results.csv`;
  - đường dẫn thư mục state trên Drive.
- Chép nguyên byte thư mục state đã đồng bộ (archive, manifest, `colab_execution.json`,
  `execution_attempts.jsonl`, SQLite, text log, `recovery/latest.json`, `recovery/training_outcome.json`,
  `recovery/snapshots/epoch-0100/`) vào một thư mục local bị Git bỏ qua. Ghi SHA-256 trước và sau khi chép.

## 2. QA kết quả run độc lập (phiên khác)

Mẫu: `docs/review/d1_a2_r1_result_independent_qa_record.md`.

Ghi `docs/review/d1_s2_r1_result_independent_qa_record.md`. Phải kiểm:
- **Hash và nội dung archive:** hash, kích thước, manifest khớp archive, giải nén từng thành viên và kiểm
  hash từng file.
- **Trạng thái run:** `SUCCEEDED`, đủ 100 epoch, không dừng sớm.
- **Runtime:** đúng một lần chạy fresh dừng ở epoch 1 cộng một lần resume, hai runtime digest khác nhau,
  cả hai đều là NVIDIA L4.
- **Checkpoint:** `epoch-0100` và binding của nó giống binding lúc smoke.
- **Môi trường và cấu hình:**
  - `git_dirty_files == 0`;
  - train args khác pilot **chỉ ở seed** (20261019) và các trường định danh run;
  - authorization SHA khớp record duyệt S2.
- **Log:**
  - SQLite `integrity_check` đạt, khớp từng dòng với text log;
  - log có "Using 3712 train, 376 val images";
  - không có traceback và không có đường dẫn nào tới test.
- **Test niêm phong:** `sealed_test_accessed=false` ở mọi chỗ.
- **Attestation:** chạy hàm attestation offline của evaluator S2. Chỉ gọi hàm kiểm, không suy luận.

Chỉ khi verdict PASS mới sang bước 3.

## 3. Chấm seed 19 so với seed 18 (phiên vận hành hoặc phiên khác)

- Dùng `detector/colab/evaluate_d1_s2_r1_common_r1.py` và `detector/m1/s2_pilot_paired_ci_r1.py`, đúng
  lệnh trong `docs/review/d1_s2_r1_evaluator_implementation_record.md`. Lưu ý:
  - `PYTHONPATH=.`;
  - bundle `tmp/yolo11n_n1_extract_r2`, không dùng `_r1`;
  - state là bản chép local ở bước 1;
  - các hash lấy từ record QA kết quả run.
- Chạy cả bước `write` và bước `verify` của CI ghép cặp.
- Output vào `results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/`, không commit, cùng file
  JSON CI trong `docs/review/generated/`.

## 4. QA kết quả chấm độc lập (phiên khác với phiên chạy bước 3)

Mẫu: `docs/review/d1_a2_r1_common_validation_result_independent_qa_record.md`.

Ghi `docs/review/d1_s2_r1_common_validation_result_independent_qa_record.md`. Phải:
- tự tính lại từ CSV dự đoán: recall bỏ qua lớp, recall đúng lớp, FP/ảnh ở conf 0,20, recall lớp
  derived key 7/32/41 (yolo 7/33/42);
- tự tính lại CI ghép cặp của FP/ảnh và recall;
- xác nhận phía pilot vẫn là 547 / 150 / 457, mAP 0,8521 / 0,6089;
- kiểm cách diễn đạt: đây là **đo dao động giữa các seed**, không phải phép thử cải tiến; chỉ là
  validation; chưa khóa ngưỡng.

## 5. Báo cáo và bàn giao

- Viết `docs/review/d1_s2_r1_common_validation_report_r1.md`, gồm:
  - bảng seed 18 / seed 19 / hiệu / CI;
  - câu trả lời trực tiếp cho câu hỏi "báo nhầm 0,399 của pilot có ổn định giữa hai seed không";
  - các giới hạn.
- Commit theo nhóm, mỗi nhóm sau khi QA tương ứng PASS:
  - record thực thi;
  - QA kết quả run;
  - kết quả chấm cùng QA và báo cáo.
- Báo lại cho Owner và Claude: các SHA commit, bảng tóm tắt, đường dẫn kết quả. Claude sẽ cập nhật
  deck và báo cáo 07/11.

## 6. Điều kiện DỪNG

- Run không phải `SUCCEEDED` hoặc chưa đủ 100 epoch.
- Có quá hai runtime, hoặc dùng packager sửa chữa. Evaluator S2 kế thừa quy tắc của A2 nên sẽ từ chối
  trường hợp này. Không nới lỏng evaluator.
- Hash lệch ở bất kỳ bước nào.
- Một bước QA không PASS.
- Cần mở test, train lại hay sửa code đã QA.
