# Bàn giao Codex: bộ ghi/kiểm khóa ngưỡng R3 cho 3 seed (successor) — 2026-11-06

Owner giao việc này ngày 06/11, sau khi `docs/review/d1_threshold_lock_r1_contract.md` được commit tại
`9d3f230` và qua QA. Contract đó đã kết luận rằng `m1.cli lock-thresholds` và `bind_threshold_lock`
hiện có **không dùng trực tiếp được** cho roster R3. Việc này viết phần successor mà contract yêu cầu.

- Người viết bàn giao: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`,
  HEAD `048a30a` lúc viết.

## Cập nhật tối 06/11: chuyển sang 2 seed (đọc trước; mục này thắng nếu mâu thuẫn với phần dưới)

Owner đã sửa D-05 Q1 thành **2 seed** (20261018, 20261019):
- record quyết định: `docs/review/d05_q1_two_seed_owner_amendment_2026-11-06.md`;
- phụ lục contract khóa ngưỡng: `docs/review/d1_threshold_lock_r1_contract_addendum_1_two_seeds.md`.

Mọi chỗ trong bản giao việc này ghi "3 seed", "ba seed" hoặc "20261020" đổi như sau:
- writer nhận **đúng 2** R3 seed report (20261018 và 20261019), từ chối mọi tập seed khác;
- lấy trung bình **2 seed**; báo cáo từng seed và hiệu giữa hai seed, không báo độ lệch chuẩn của 2 điểm như
  thể là độ bất định;
- bootstrap dùng cùng bộ nhóm rút cho cả 2 seed;
- record khóa có **đúng 2 candidate**, cùng một bộ ngưỡng.

Mọi điều khác giữ nguyên. Phụ lục đang chờ QA độc lập: nếu QA phụ lục chưa PASS, viết code theo phụ lục
nhưng chưa commit, chờ QA.

## 0. Ranh giới (bất biến)

- **Chỉ viết code và test, kiểm bằng dữ liệu tổng hợp hoặc file dự đoán đã có của pilot.**
  - Không suy luận model, không train.
  - Không chạy successor để tạo record khóa thật.
  - Không đọc, tạo hay chấm dự đoán của seed 20261019.
- **Không mở, liệt kê, đếm, xuất hay chấm sealed test `afa03d4b…`.** Không gọi
  `m1.cli evaluate --split test` hay `m1.cli lock-thresholds` để đi vòng. Mọi output ghi
  `sealed_test_accessed=false`.
- **Không sửa file đã pin hoặc đã QA:**
  - `detector/m1/contract.py`
  - `detector/m1/cli.py`
  - `detector/m1/metrics.py`
  - các evaluator
  - các contract

  Chỉ tạo file mới. Nếu thấy cần sửa file cũ thì DỪNG và báo Owner.
- Không động vào lượt train D1-S2-R1 đang chạy.
- **Git:** chỉ `git add` từng đường dẫn cụ thể, không `git add -A`, stash, reset, clean. Giữ nguyên file
  dirty của Owner. Không commit `results/experiments/`. **Không push** nếu Owner chưa cho phép trong chat.
- QA độc lập do phiên hoặc agent **khác** với phiên viết code, và có đúng một dòng `Verdict:`.

## 1. Đặc tả (lấy từ contract khóa ngưỡng, mục "R3 binding decision" và "Frozen grid")

Đọc trọn `docs/review/d1_threshold_lock_r1_contract.md` trước. Successor phải làm đúng và chỉ đúng
những gì contract đó đã khóa. Không được thêm hay bớt luật chọn.

**Module đề xuất** (khớp tên dự kiến trong contract):
- `detector/m1/d1_threshold_lock_r3_successor.py`, gồm hai chức năng `write` và `verify`.
- Tests: `detector/tests/test_d1_threshold_lock_r3_successor.py`.

### 1.1 Báo cáo đầu vào theo từng seed ("R3 seed report")

Định nghĩa một schema có phiên bản (ví dụ `schema_version: 1`). Mỗi seed có một file JSON, gồm:
- danh tính seed: seed, đường dẫn và SHA-256 của weight, SHA-256 của run contract, SHA-256 của run
  attestation, SHA-256 của record QA kết quả run;
- binding R3:
  - SHA-256 của manifest bundle `8e6ffe77…`;
  - danh sách 376 stem cùng hash của nó;
  - 624 box GT kèm nhãn từng khung (hoặc hash của chúng);
  - 9 nhóm;
  - hash của class map;
  - phiên bản và hash của bộ chấm chung (`evaluate_cascade_b0_r1.py`, `m1/metrics.py`, các hàm của
    `nms_sweep_r1`);
- với mỗi cấu hình NMS trong lưới đã khóa, và mỗi mức confidence trong lưới đã khóa:
  - recall bỏ qua lớp, FP/ảnh, TP, FP, số đúng lớp;
  - số đếm theo từng khung, đủ để bootstrap theo nhóm và cross-validation bỏ một nhóm;
- mAP50 và mAP50-95 đúng lớp của mỗi cấu hình NMS, tính trên toàn bộ ứng viên sau NMS, không lọc theo
  confidence;
- SHA-256 của file dự đoán CSV cho từng cấu hình NMS;
- `sealed_test_accessed=false`.

**Lưới đã khóa:**
- confidence: 0,05; 0,10; …; 0,95, **hợp với** 0,15; 0,16; …; 0,30 (bỏ giá trị trùng);
- NMS theo lớp: IoU 0,45–0,80, bước 0,05;
- NMS gộp khác lớp: IoU 0,80 / 0,85 / 0,90, chỉ để chẩn đoán.

Viết một hàm **tạo** R3 seed report từ các file dự đoán CSV của một seed. Có thể dùng lại các hàm của
`nms_sweep_r1` và `a3_pilot_paired_ci_r1` bằng import.

### 1.2 Writer (`write`)

**Đầu vào:** đúng 3 R3 seed report, cho seed 20261018, 20261019 và 20261020.

**Từ chối** nếu gặp bất kỳ trường hợp nào:
- số seed khác 3, hoặc tập seed khác ba seed trên, hoặc weight trùng nhau;
- stem, GT, nhóm, class map, bundle hoặc bộ chấm khác nhau giữa các seed;
- lưới khác lưới đã khóa;
- thiếu SHA của record QA kết quả run;
- `sealed_test_accessed` khác false.

**Chọn ngưỡng theo đúng contract:**
1. Ở mỗi ô, lấy **trung bình 3 seed** của recall bỏ qua lớp và FP/ảnh. Báo cáo thêm từng seed và độ
   lệch chuẩn mẫu.
2. Ô hợp lệ là ô có recall trung bình ≥ 0,85.
3. Trong các ô hợp lệ, chọn ô có FP/ảnh trung bình thấp nhất.
4. Nếu bằng nhau: lấy confidence cao hơn, rồi mAP50-95 trung bình cao hơn, rồi IoU gần 0,70 hơn, rồi
   ưu tiên NMS theo lớp, rồi IoU thấp hơn.
5. Không ô nào hợp lệ thì dừng, không tạo record khóa.
6. Ghi thêm: ô đã chọn có đạt recall ≥ 0,85 ở **từng** seed không. Chỉ báo cáo, không phải điều kiện.

**Đổi NMS khỏi IoU 0,70 theo lớp** chỉ khi đạt đủ cả ba điều kiện:
1. CI ghép cặp của hiệu FP/ảnh nằm hẳn dưới 0;
2. CI hiệu mAP50-95 không nằm hẳn dưới 0;
3. cross-validation bỏ một nhóm chọn cùng cấu hình (hoặc IoU kề bên, **cùng chế độ NMS**) ở ≥ 7/9 fold.

Cách tính:
- bootstrap 1.000 vòng, seed 20261018;
- **cùng một bộ nhóm rút cho cả 3 seed và cả hai cấu hình NMS**;
- tính trung bình 3 seed của mỗi lần rút trước, rồi mới lấy hiệu.

Nếu bất kỳ điều kiện nào trượt: giữ IoU 0,70 theo lớp, kèm mức confidence đã chọn cho 0,70.

**Đầu ra:**
- một record khóa `status: LOCKED_ON_VAL`, `sealed_test_seen: false`, đúng 3 candidate, cùng một bộ
  `(confidence, nms_iou, agnostic_nms)` cho cả 3;
- một **sidecar chứng minh R3** riêng, có hash và được record khóa tham chiếu. Sidecar chứa toàn bộ
  phép chọn, các CI, các fold và mọi hash binding.

**Tương thích với `bind_threshold_lock`:**
- Hàm đó chấp nhận đúng tập key của schema 1. Hai lựa chọn:
  1. record khóa tuân schema 1, còn bằng chứng R3 nằm trong sidecar do reader mới kiểm;
  2. định nghĩa schema có phiên bản mới.
- Ghi rõ đã chọn cách nào và vì sao.
- Contract đã nói: record schema 1 đứng một mình không đủ chứng minh binding R3.

### 1.3 Verifier (`verify`) và reader cho đánh giá cuối

`verify` nhận record khóa và sidecar, rồi:
- tính lại phép chọn từ các R3 seed report;
- kiểm mọi hash;
- từ chối khi có bất kỳ sai lệch nào.

Viết thêm một hàm reader, để contract đánh giá cuối sau này gọi trước khi mở test. Reader trả về bộ ngưỡng
đã khóa **chỉ khi** `verify` qua.

Reader **không** mở test và không gọi lệnh nào chạm tới test.

## 2. Test bắt buộc (dữ liệu tổng hợp, cộng một lần chạy trên dự đoán pilot)

- **Từ chối:**
  - thiếu một seed, thừa seed, seed sai, weight trùng;
  - stem, GT, nhóm, class map, bundle hoặc bộ chấm lệch giữa các seed;
  - lưới sai;
  - thiếu QA kết quả;
  - `sealed_test_accessed=true`;
  - record hoặc sidecar bị sửa một byte;
  - ngưỡng khác nhau giữa các candidate.
- **Phép chọn:**
  - chọn đúng ô theo trung bình 3 seed;
  - đủ các bậc tie-break;
  - dừng khi không ô nào đạt recall 0,85;
  - giữ 0,70 khi một trong ba điều kiện đổi NMS trượt;
  - chỉ đổi khi cả ba đạt.
- **Bootstrap và cross-validation:**
  - cùng bộ nhóm rút cho mọi seed và mọi cấu hình;
  - kết quả lặp lại được với seed 20261018.
- **Kiểm tương đương trên pilot** (không suy luận mới):
  - dựng một R3 seed report cho **pilot** từ 11 CSV của `results/experiments/d1_nms_sweep_r1/`;
  - chứng minh các ô ở lưới 0,05 khớp đúng `docs/review/generated/d1_nms_sweep_r1.json`, ví dụ
    classaware 0,70 ở conf 0,20 phải ra 547 / 150 / 457.

  Pilot chỉ có một seed, nên **không** tạo record khóa thật từ dữ liệu này. Chỉ dùng để kiểm phần tạo
  report và phần chấm.
- **Lưới mịn:** các mức 0,15–0,30 bước 0,01 cần dự đoán ở ngưỡng sàn 0,001. Kiểm rằng CSV của lượt quét
  NMS có ngưỡng sàn đó, rồi tính được các ô mịn cho pilot. Các ô mịn này **chỉ để kiểm code**, không
  được dùng làm bằng chứng chọn ngưỡng.

## 3. Output và gate

| File | Nội dung |
| --- | --- |
| `detector/m1/d1_threshold_lock_r3_successor.py` và test | Mục 1–2 |
| `docs/review/d1_threshold_lock_r3_successor_implementation_record.md` | Thiết kế, lựa chọn schema hoặc sidecar, lệnh chạy chính xác cho sau này (thay cho lệnh "chưa chạy được" trong contract), hash mọi file, kết quả gate |
| `docs/review/d1_threshold_lock_r3_successor_source_independent_qa_record.md` | QA nguồn độc lập. Phải kiểm từng luật chọn so với contract, và tự tính lại ít nhất phần tái tạo pilot. |

Gate:
- `uv run ruff check src tests`;
- `uv lock --check`;
- `cd detector && PYTHONPATH=. uv run --no-sync pytest -q tests/test_d1_threshold_lock_r3_successor.py`.

Rebuild Graft sau khi thêm source (`graft build . && graft check .`).

Commit sau khi QA nguồn PASS, gồm đúng các file ở bảng trên. Báo lại SHA commit và các điểm mở.

## 4. Điều kiện DỪNG

- Cần sửa file cũ đã pin hoặc đã QA.
- Cần suy luận, train hay mở test.
- Đặc tả trong contract mơ hồ tới mức phải tự thêm luật chọn: ghi điểm đó, hỏi Owner, không tự quyết.
- Kiểm tương đương trên pilot không khớp JSON đã QA.
- QA nguồn không PASS sau hai vòng sửa.
