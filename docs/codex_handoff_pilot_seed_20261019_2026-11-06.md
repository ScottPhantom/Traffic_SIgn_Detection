# Bàn giao Codex: train lặp lại pilot YOLO11s-54 với seed 20261019 trên Colab L4, 2026-11-06

Owner duyệt trong chat ngày 06/11. Nguyên văn:

> "Hãy giao thêm cho Codex công việc train Song Song trên Colab 1 seed pilot trước."

Câu này đáp lại bước "train thêm seed 20261019 và 20261020 cùng cấu hình pilot" của D-05. Owner chọn
làm **một seed trước: 20261019**.

- Người viết: Claude, phiên điều phối.
- Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh `yolo11n-dual-track-r1`.
- Chạy song song với hai việc local: `docs/codex_handoff_threshold_sweep_2026-11-06.md` và
  `docs/codex_handoff_nms_iou_sweep_pilot_2026-11-06.md`. Việc này chạy trên Colab L4, còn hai việc kia
  chạy trên máy, nên không tranh tài nguyên. Ba việc không ghi chung file nào.

## 0. Ranh giới (bất biến)

- **Đúng một thay đổi so với pilot: seed 20261019 thay cho 20261018.**
  - Mọi tham số train khác phải giống hệt `run_contract.json` của pilot (SHA-256 `9f8fc94c…0b88`):
    YOLO11s 54 lớp, pretrained `yolo11s.pt` `85a76fe8…502d5`, 100 epoch, patience 0, imgsz 1280,
    batch 4, workers 4, fraction 1.0, `fliplr=0.0`, deterministic, optimizer `auto`.
  - Dữ liệu train/val và export binding cũng phải giống hệt pilot: **không** dùng danh sách A2.
  - Seed 20261019 nằm trong danh sách seed D-05 đã duyệt (`detector/m1/contract.py:37`).
- **Không mở, xuất hay chấm sealed test `afa03d4b…`.** Gói Colab chỉ có train/val. Mọi record ghi
  `sealed_test_accessed=false`.
- **Không train seed 20261020** và không đổi cấu hình. Việc đó cần Owner duyệt riêng.
- **Không sửa file nguồn đã QA** của pilot, A2 hay A3. Chỉ tạo successor mới, append-only.
- **Git:** chỉ `git add` từng đường dẫn cụ thể. Không `git add -A`, stash, reset, clean. Giữ nguyên
  file dirty của Owner. Không đưa weights hay dữ liệu vào Git.
- **Push:** Colab clone code từ GitHub, nên commit của gói này phải được push thì mới chạy được.
  **Chỉ push khi Owner cho phép trong chat.** Nếu chưa có phép thì DỪNG trước bước push và báo Owner.
- Record append-only. Mỗi QA độc lập do một phiên hoặc agent **khác** với phiên viết hoặc vận hành
  bước được QA, và có đúng một dòng `Verdict:`.

## 1. Cách làm: theo đúng mẫu D1-A2-R1 đã chạy thành công đêm 05/11

Tham khảo, không sửa:
- `docs/review/d1_a2_r1_run_contract.md`
- `detector/m1/resumable_train_a2_r1.py`
- `detector/colab/run_d1_colab_a2_r1.py`
- `detector/colab/d1_train_a2_r1.ipynb`
- các record QA nguồn, QA notebook, QA smoke, QA kết quả của A2

Mẫu A2 đã giải quyết sẵn các bẫy sau. **Gói mới phải giữ nguyên các giải pháp đó:**
- checkout trên Colab phải sạch (`git_dirty_files == 0`), nên record duyệt phải được commit trước;
- tên file record duyệt không chứa chuỗi "test" ở bất kỳ dạng chữ hoa hay thường nào;
- notebook phải clone đúng commit đã pin, không chép thêm file vào sau khi clone;
- smoke 1 epoch, QA smoke, rồi resume trên một runtime L4 khác;
- resume phải dùng đúng đường dẫn checkout `/content/Traffic_Sign_Detector`.

Tên đề xuất cho experiment là `D1-S2-R1` (pilot, seed thứ hai).

| Bước | File hoặc việc |
| --- | --- |
| 1 | Record duyệt `docs/review/d1_s2_r1_owner_authorization_2026-11-06.md`. Trích nguyên văn câu Owner; có một dòng riêng `OWNER_AUTHORIZES_TRAINING: D1-S2-R1`; ghi seed 20261019, cấu hình pilot không đổi, L4, smoke trước, không test. |
| 2 | Contract `docs/review/d1_s2_r1_run_contract.md`: đóng băng mục 0; pin SHA của pilot `run_contract.json`, pretrained weight và bundle Drive mà pilot đã dùng; nêu kiểm tra "chỉ khác seed" (diff train args với pilot chỉ được khác `seed`, cùng các trường định danh run như `name`/`project`). |
| 3 | Code successor append-only: trainer `detector/m1/resumable_train_s2_r1.py`, launcher `detector/colab/run_d1_colab_s2_r1.py`, và test. Dùng lại chuỗi tiền nhiệm bằng import như A2 đã làm; khác A2 ở chỗ không thay `data`, và seed là 20261019. |
| 4 | QA nguồn độc lập. Nếu không PASS thì sửa rồi QA delta. |
| 5 | Commit A: gói nguồn, record duyệt, QA nguồn. |
| 6 | Notebook `detector/colab/d1_train_s2_r1.ipynb` pin commit A, rồi QA notebook độc lập. Commit B: notebook và QA notebook. |
| 7 | Push (chỉ khi Owner đã cho phép). |
| 8 | Colab L4, `MODE="fresh"`, `--stop-after-epoch 1`. QA smoke độc lập từ artifact live trên Drive: `git_dirty_files == 0`; train args giống pilot trừ seed; seed 20261019; log ghi "Using 3712 train, 376 val images"; `sealed_test_accessed=false`. |
| 9 | Chỉ khi QA smoke PASS: mở runtime L4 **mới**, `MODE="resume"`, chạy tới epoch 100. Colab ngắt thì resume lại bằng cùng notebook. Trainer từ chối thì DỪNG, không vá. |
| 10 | `docs/review/d1_s2_r1_execution_record.md` và bàn giao cho Claude, giống `d1_a2_r1_claude_handoff_2026-11-06.md`: hash archive, manifest, `best.pt`, `last.pt`, `results.csv`, hai runtime digest, status. **Không** chấm trên roster R3 và không so với pilot: QA kết quả và chấm chung là việc của Claude. |

## 2. Thời gian dự kiến

| Việc | Ước tính |
| --- | --- |
| Record, contract, code, test, QA nguồn | 2–3 giờ |
| Notebook và QA notebook | khoảng 1 giờ |
| Smoke và QA smoke | khoảng 1 giờ |
| Train tới epoch 100 | khoảng 5–6 giờ L4. Pilot ghi 14.786 s trong `results.csv`; A2 mất 7,6 giờ vì có thêm khoảng 26 % bước train. |

Tổng khoảng **9–11 giờ** tính từ lúc bắt đầu.

## 3. Lưu ý cho Owner (Claude ghi, không thay đổi phạm vi)

Seed 20261019 chỉ dùng được cho đánh giá cuối D-05 nếu cấu hình pilot vẫn là ứng viên cuối. Nếu sau này
đổi cấu hình (ví dụ thêm hard-negative), các seed của pilot không còn tính cho D-05. Khi đó lần train
này vẫn có ích: nó đo **độ dao động giữa các seed** của pilot, cho biết con số FP/ảnh 0,399 có ổn định
không.

## 4. Điều kiện DỪNG

- Diff train args với pilot khác ngoài `seed` và các trường định danh run.
- Hash pretrained weight, bundle hoặc `run_contract.json` của pilot không khớp.
- QA nguồn, QA notebook hoặc QA smoke không PASS.
- GPU không phải NVIDIA L4.
- Trainer hoặc launcher từ chối.
- Owner chưa cho phép push.
