# Bàn giao Codex: chọn ngưỡng **tạm thời** trên 2 seed (20261018 + 20261019) — 2026-11-06

Owner nói trong chat ngày 06/11, nguyên văn:

> "lấy trung bình trên 19 trước vì không đủ thời gian chạy 3 seed."

Trước đó Owner đã quyết **giữ D-05 với 3 seed**. Câu trên vì vậy được hiểu như sau:
- tính ngưỡng **tạm thời** từ trung bình của seed 20261018 và 20261019, để có số dùng trước cho báo cáo và
  trình bày;
- **không** thay việc khóa ngưỡng 3 seed;
- **không** dùng để mở test.

Thông tin chung:
- Người viết bàn giao: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`.

## Cập nhật tối 06/11 (đọc trước)

Sau đó Owner đã sửa D-05 Q1 thành **2 seed**
(`docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`). Vì vậy:
- Phép chọn 2 seed **ràng buộc** (binding) sẽ do **bộ khóa ngưỡng R3**
  (`docs/codex_handoff_r3_threshold_lock_successor_2026-11-06.md`) tính ra.
- Việc ở bản giao việc này vẫn làm được như một chẩn đoán sớm, và phần suy luận seed 19 với 11 cấu hình NMS
  dùng chung được cho bộ khóa sau. Nhưng output **vẫn giữ nhãn** `PROVISIONAL_TWO_SEED_NOT_A_LOCK`, không
  được đổi tên thành record khóa.
- Luật chọn phải khớp đúng phụ lục `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md`.

## 0. Ranh giới (bất biến)

- **Chỉ bắt đầu sau khi** gói sau-train của seed 19 (`docs/codex_handoff_s2_post_training_2026-11-06.md`)
  đã có **QA kết quả run PASS**.
- **Chỉ validation R3:** 376 ảnh, 624 box, 9 nhóm D-02, bundle `tmp/yolo11n_n1_extract_r2`. Không mở, liệt
  kê, xuất hay chấm sealed test `afa03d4b…`. Mọi output ghi `sealed_test_accessed=false`.
- **Không phải record khóa.**
  - Không tạo record `LOCKED_ON_VAL`.
  - Không gọi `m1.cli lock-thresholds`.
  - Không sửa `docs/review/d1_threshold_lock_r1_contract.md`.
  - Mọi output ghi `status: PROVISIONAL_TWO_SEED_NOT_A_LOCK` và `thresholds_locked=false`.
- **Luật chọn giữ nguyên tuyệt đối** như contract khóa ngưỡng `9d3f230`, chỉ khác số seed là 2 thay vì 3.
  Không thêm, bớt hay đổi luật sau khi thấy số. Lần khóa 3 seed sau này sẽ dùng đúng luật đó, kể cả khi
  kết quả tạm thời "đẹp" hay "xấu".
- **Không đổi app, không đổi D-05.** Không train.
- **Git:** chỉ `git add` từng đường dẫn cụ thể, không `git add -A`, stash, reset, clean. Giữ nguyên file
  dirty của Owner. Không commit `results/experiments/`. **Không push** nếu Owner chưa cho phép trong chat.
- QA độc lập do phiên hoặc agent **khác** với phiên viết hoặc chạy, và có đúng một dòng `Verdict:`.

## 1. Record duyệt suy luận

Tạo `docs/review/d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md`:
- trích nguyên văn câu Owner ở trên;
- phạm vi: chạy suy luận **một lần** với weight `best.pt` của seed 20261019 (lấy hash từ record QA kết quả
  run) trên val R3, với 11 cấu hình NMS như lượt quét NMS R1;
- không train, không mở test, không khóa.

Seed 20261018 (pilot) **không chạy lại**: dùng 11 CSV đã pin trong `results/experiments/d1_nms_sweep_r1/`.

## 2. Cách làm

1. **Suy luận seed 19.** Dùng lại hàm `infer` của `detector/m1/nms_sweep_r1.py` bằng import, nhưng với weight
   S2:
   - `conf=0.001`, `imgsz=1280`, `max_det` mặc định;
   - 11 cấu hình: NMS theo lớp IoU 0,45–0,80, NMS gộp khác lớp 0,80 / 0,85 / 0,90.

   **Kiểm tương đương:** cấu hình 0,70 theo lớp phải khớp đúng số đếm và mAP mà QA kết quả chấm seed 19 đã
   ghi ở conf 0,20. Lệch thì DỪNG.
2. **Lưới confidence** đúng như contract khóa ngưỡng: 0,05; 0,10; …; 0,95 **hợp với** 0,15; 0,16; …; 0,30.
3. **Gộp 2 seed:** mỗi ô (confidence, chế độ NMS, IoU) lấy trung bình cộng của 2 seed, cho recall bỏ qua lớp
   và FP/ảnh. Báo cáo thêm từng seed. **Không** báo độ lệch chuẩn như thể có ý nghĩa: với 2 điểm, chỉ ghi
   hiệu giữa hai seed.
4. **Luật chọn** (chép từ contract khóa ngưỡng):
   - ô hợp lệ là ô có recall trung bình ≥ 0,85;
   - chọn ô có FP/ảnh trung bình thấp nhất;
   - nếu bằng nhau: confidence cao hơn, rồi mAP50-95 trung bình cao hơn, rồi IoU gần 0,70 hơn, rồi NMS theo
     lớp, rồi IoU thấp hơn.
   - Chỉ đổi NMS khỏi 0,70 theo lớp khi đạt đủ ba điều kiện:
     1. CI ghép cặp FP/ảnh nằm hẳn dưới 0;
     2. CI mAP50-95 không nằm hẳn dưới 0;
     3. cross-validation bỏ một nhóm chọn cùng cấu hình (hoặc IoU kề bên, cùng chế độ) ở ≥ 7/9 fold.
   - Bootstrap 1.000 vòng, seed 20261018, **cùng bộ nhóm rút cho cả 2 seed và cả hai cấu hình**; tính
     trung bình 2 seed của mỗi lần rút trước rồi mới lấy hiệu.
   - Ghi thêm: ô đã chọn có đạt recall ≥ 0,85 ở từng seed không.
5. **Câu hỏi phải trả lời rõ ở đầu báo cáo:**
   - bộ ngưỡng tạm thời là gì;
   - recall và FP/ảnh trung bình tại đó;
   - có ô nào đạt cùng lúc recall ≥ 0,85 **và** FP/ảnh ≤ 0,30 không;
   - kết quả có khác chẩn đoán 1 seed (confidence 0,20, NMS 0,70) không.

## 3. Output

| File | Nội dung |
| --- | --- |
| `detector/m1/two_seed_provisional_threshold_r1.py` và test | Mục 2. Dùng lại module cũ bằng import, không sửa file đã pin. |
| `docs/review/generated/d1_two_seed_provisional_threshold_r1.json` | Mọi ô × 2 seed; trung bình; điểm chọn; CI; các fold; kết quả kiểm tương đương; hash mọi input và CSV; `status: PROVISIONAL_TWO_SEED_NOT_A_LOCK`; `thresholds_locked=false`; `sealed_test_accessed=false` |
| `docs/review/d1_two_seed_provisional_threshold_r1_report.md` | Kết quả, theo khung ở mục 2.5. Ghi rõ: tạm thời, 2/3 seed, không phải khóa, không dùng để mở test. |
| `docs/review/d1_two_seed_provisional_threshold_r1_source_independent_qa_record.md` | QA nguồn, trước khi chạy |
| `docs/review/d1_two_seed_provisional_threshold_r1_result_independent_qa_record.md` | QA kết quả. Phải tự tính lại ít nhất ô được chọn, ô 0,20 / 0,70 và CI FP/ảnh. |

CSV dự đoán của seed 19 lưu ở `results/experiments/d1_two_seed_provisional_threshold_r1/` (không commit).

Gate:
- `uv run ruff check src tests`;
- `uv lock --check`;
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q <test mới>`;
- `graft build . && graft check .`.

Commit sau khi QA kết quả PASS. Báo lại SHA commit và bảng tóm tắt; Claude sẽ cập nhật deck và báo cáo.

## 4. Điều kiện DỪNG

- Seed 19 chưa có QA kết quả run PASS.
- Hash weight, bundle hoặc CSV của pilot không khớp.
- Kiểm tương đương ở cấu hình 0,70 không khớp.
- Cần sửa luật chọn, sửa file đã pin, train hay mở test.
- QA nguồn hoặc QA kết quả không PASS.
