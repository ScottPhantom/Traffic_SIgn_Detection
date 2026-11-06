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

---

## Phụ lục A — bước gắn kết đầu vào (bổ sung 06/11, sau khi bộ khóa R3 được commit `c26e6d4`)

Owner nói trong chat ngày 06/11, nguyên văn: "Bổ sung bàn giao".

Claude đã đọc source của bộ khóa (`detector/m1/d1_threshold_lock_r3_successor.py`, `build_seed_report` và
`_run_binding`). Lệnh `build-report` sẽ **từ chối** nếu thiếu bất kỳ đầu vào nào dưới đây. Hiện chưa seed nào
đủ:
- record cho phép của hai lượt suy luận cũ không ghi `0.001` và hash weight;
- record QA kết quả của hai lượt đó không chứa hash của record cho phép, hash weight hay hash của 11 CSV (các
  hash CSV chỉ nằm trong JSON generated);
- archive kết quả của pilot không có trong checkout;
- weight và run contract của seed 19 chưa được giải nén ra.

Phụ lục này **thay bước 1** của mục 2. Từ bước 2 trở đi giữ nguyên. Ranh giới ở mục 1 giữ nguyên.

### A0. Điều kiện bắt đầu thêm

Owner phải nói rõ trong chat là cho phép sao chép archive pilot từ thư mục Google Drive đồng bộ vào `tmp/`
(bước A1). Không có câu đó thì làm A2–A4 cho seed 19 rồi DỪNG ở A1.

### A1. Archive pilot (chỉ sao chép, không sửa trên Drive)

Nguồn (Drive đồng bộ cục bộ của Owner):
`~/Library/CloudStorage/GoogleDrive-<owner>/Drive của tôi/CPV301/Traffic_Sign_Detector/M1_D1_Colab/runs/pilot_seed_20261018_r2/`
- `D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2_result.tar.gz` (khoảng 144 MB)
- `....tar.gz.manifest.json`

Việc cần làm:
- Sao chép **bản thật**, không dùng symlink (bộ khóa từ chối symlink), vào
  `tmp/d1_two_seed_lock_r1_inputs/pilot/`.
- Chạy `run_d1_colab.verify_result_archive` trên bản sao. Phải PASS.
- `run_attestation_sha256` trong manifest phải bằng
  `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc`.
- Không giải nén, không đọc gì khác trong archive.

Weight và run contract của pilot dùng bản đã giải nén sẵn trong
`results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/`.
Claude đã kiểm prefix hash:
- `weights/best.pt` → `5d5815a9…`
- `run_contract.json` → `9f8fc94c…`

Codex phải kiểm lại bằng full hash so với `RUN_PINS` trong source.

### A2. Weight và run contract của seed 19

- Archive: `tmp/d1_s2_seed_20261019_r1_state/D1_yolo11s_wp33_afa03d4b_20261019_20261106T113001_s2_r1_result.tar.gz`
  cùng file `.manifest.json` đi kèm. Hash của cả hai đã có trong `docs/review/d1_s2_r1_result_independent_qa_record.md`.
- Chỉ giải nén 2 member `<run>/weights/best.pt` và `<run>/run_contract.json` vào
  `tmp/d1_two_seed_lock_r1_inputs/s2/`.
- Full hash phải bằng `RUN_PINS[20261019]`: weight `046cfea2…`, contract `1f1c3f7f…`.
- **Không** dùng `tmp/d1_s2_seed_20261019_r1_state/recovery/snapshots/epoch-0100/`: snapshot đó có hash khác.

### A3. Record cho phép gắn kết (mới, append-only)

Tạo `docs/review/d1_two_seed_lock_r1_inference_binding_authorization_2026-11-06.md`. Record này cho phép
**dùng lại** dự đoán đã có, không cho phép suy luận mới. Nội dung:

1. Trích nguyên văn câu Owner ở đầu bàn giao và câu Owner ở phụ lục này.
2. Hai lượt suy luận gốc, kèm đường dẫn và full SHA-256 của từng file:
   - seed 20261018: `d1_nms_sweep_r1_owner_authorization_2026-11-06.md`, contract
     `d1_nms_sweep_r1_contract.md` (dòng 16 ghi `conf=0.001`), QA kết quả
     `d1_nms_sweep_r1_result_independent_qa_record.md`, JSON `generated/d1_nms_sweep_r1.json`;
   - seed 20261019: `d1_two_seed_provisional_threshold_r1_owner_authorization_2026-11-06.md`, contract/report,
     QA kết quả và JSON `generated/d1_two_seed_provisional_threshold_r1.json`.

   Codex phải tự kiểm và trích dòng ghi `conf=0.001` của lượt seed 19. Nếu không tìm thấy thì DỪNG.
3. Ngưỡng suy luận ghi đúng chuỗi `conf=0.001` (`inference_conf` 0.001), `imgsz=1280`, `max_det=300`.
   Claude đã đo confidence nhỏ nhất trong CSV: pilot 0,0010024; seed 19 0,0010004.
4. Full SHA-256 weight của cả hai seed.
5. Bảng 22 CSV: tên, đường dẫn, full SHA-256. Hash phải bằng hash trong JSON generated đã QA.
6. Phạm vi: dùng 22 CSV cho đúng một lần chạy bộ khóa R3. Không suy luận mới, không train, không mở test,
   không đổi ngưỡng app hay D-05.

Ghi `sealed_test_accessed=false`.

### A4. QA gắn kết độc lập (agent hoặc phiên khác với người viết A3)

Tạo `docs/review/d1_two_seed_lock_r1_inference_binding_independent_qa_record.md`. QA phải tự kiểm:
- tính lại hash của 22 CSV và so với JSON generated đã QA;
- confidence nhỏ nhất ≥ 0,001 trong mọi CSV;
- full hash của 2 weight bằng `RUN_PINS`;
- bằng chứng `conf=0.001` của cả hai lượt gốc;
- archive và manifest của 2 seed qua `verify_result_archive`.

Record QA **phải chứa nguyên văn**, vì bộ khóa kiểm bằng cách tìm chuỗi:
- full SHA-256 của record A3, tính trên bản cuối, nên A3 phải chốt xong trước QA;
- full SHA-256 của 2 weight;
- full SHA-256 của cả 22 CSV.

Record có đúng một dòng `Verdict:` ở dạng `Verdict: PASS …` (bộ khóa chấp nhận `PASS` hoặc `**PASS**`).
Nếu QA không PASS: sửa A3 bằng record mới, không ghi đè, rồi QA lại. Tối đa hai vòng, sau đó DỪNG.

Commit A3 và A4 (chỉ `git add` từng đường dẫn) **trước** khi chạy `build-report`. Không commit `tmp/` hay
`results/`.

### A5. File identity và predictions cho mỗi seed

Đặt trong `tmp/d1_two_seed_lock_r1_inputs/` (không commit). Định dạng lấy từ `build_seed_report`:
- identity: đúng 9 khóa `weight`, `run_contract`, `run_attestation_sha256`, `result_archive`,
  `result_manifest`, `run_result_qa`, `inference_authorization`, `inference_result_qa`, `inference_conf`.
  Mỗi khóa file là `{"path", "sha256"}` với path thật.
  - `run_result_qa`: pilot dùng `docs/review/d1_pilot_run_registry_independent_qa_record.md`; seed 19 dùng
    `docs/review/d1_s2_r1_result_independent_qa_record.md`.
  - `inference_authorization`: A3.
  - `inference_result_qa`: A4.
  - `inference_conf`: số `0.001`.
- predictions: đúng 11 khóa theo `CONFIGS` trong source, mỗi khóa `{"path", "sha256"}`. Pilot lấy từ
  `results/experiments/d1_nms_sweep_r1/`; seed 19 lấy từ `results/experiments/d1_two_seed_provisional_threshold_r1/`.

Sau A5, tiếp tục từ bước 2 của mục 2 bằng các lệnh đã pin trong
`docs/review/d1_threshold_lock_r3_successor_implementation_record.md`. Đường dẫn output:
- report từng seed: `tmp/d1_two_seed_lock_r1_inputs/`;
- record khóa và sidecar: `docs/review/generated/` như bước 3.

### A6. Điều kiện DỪNG thêm

- Archive pilot hoặc seed 19 không qua `verify_result_archive`, hoặc hash lệch `RUN_PINS`.
- Không có bằng chứng `conf=0.001` cho một trong hai lượt gốc.
- Hash CSV lệch so với JSON generated đã QA.
- Bộ khóa vẫn từ chối sau khi có đủ A1–A5: ghi nguyên văn lỗi rồi báo Claude. **Không sửa** source bộ khóa đã QA.
