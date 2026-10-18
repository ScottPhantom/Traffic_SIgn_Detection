# Prompt cho Codex — công việc tiếp theo của CPV301 AutoDrive (từ 2026-10-18)

> Dán nguyên văn vào Codex, **kèm** `docs/codex_handoff_2026-10-18.md`, file báo cáo những gì đã làm.
> Tài liệu này chỉ liệt kê việc cần làm tiếp, thứ tự làm và tiêu chí hoàn thành. Nếu có chỗ mâu
> thuẫn thì tin repo, `PROJECT_MEMORY.md` và các bản ghi quyết định trong `docs/review/`.

## Vai trò và luật bắt buộc

- Bạn là kỹ sư/PM thực thi. **Owner** (chủ dự án) là người duy nhất được quyết định. Những việc
  sau phải **hỏi Owner và chờ trả lời rõ ràng** trước khi làm:
  - tải bất kỳ file nào, kể cả trọng số pretrained;
  - upload dữ liệu ra dịch vụ ngoài, kể cả Google Drive hay Colab;
  - commit hoặc push;
  - đổi ngưỡng D-05;
  - mở test niêm phong.
- Đọc `AGENTS.md` và `PROJECT_MEMORY.md` trước. Dùng Graft trước khi đọc hay sửa code
  (`graft check .`, `graft ask "…" --source .`).
- **Không sửa file đã bị pin hash.** Trong đó có `README.md` (WP27-R1), `pyproject.toml`/`uv.lock`
  ở thư mục gốc (WP6), `src/cpv301_autodrive/dataset_graph.py`, các builder/test/output của
  WP cũ, và `docs/dataset01_card.md`. Muốn đổi thì làm gói `-R` mới, giữ nguyên bản cũ.
- **Test niêm phong `afa03d4b…`**: chỉ mở trong lần đánh giá cuối, qua `--final-eval --reason`;
  lệnh này tự ghi log vào `results/experiments/sealed_test_access_log.jsonl`. Không dùng test để
  chọn model, chọn ngưỡng hay phân tích lỗi.
- Không lật ngang ảnh (biển trái/phải sẽ đổi nghĩa). Nhãn chỉ lấy từ WP33. Ảnh WP35 chỉ dùng
  cho train.
- 13 lớp không có val (9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50) không được dùng để chọn
  model hay chỉnh ngưỡng. 22 lớp không có test luôn ở trạng thái "chưa kiểm chứng".
- Mỗi gói xong phải qua **QA độc lập** ở một session khác, rồi mới cập nhật trạng thái.
- Hành vi xe chỉ là mô phỏng; không có tuyên bố an toàn.
- Mỗi lần xong một việc, chạy kiểm tra:
  `uv run ruff check src tests && uv lock --check`,
  `uv run python scripts/run_parallel_checks.py verifiers` (**phải 51/51**),
  `cd detector && uv run ruff check m1 tests && uv run pytest` (**7 pass**),
  `graft build . && graft check .`.

## Trạng thái xuất phát (đã verify)

- Gate 0 mở (G0.1–G0.9 PASS, D-05 đã duyệt). Chưa có model VN nào được train.
- Dữ liệu YOLO: `scripts/build_m1_yolo_dataset.py export` ghi ra `data/processed/m1_yolo/` gồm
  train 1.912 ảnh thật + 1.800 ảnh WP35 và val 376 ảnh. Test chưa được xuất.
- Gói phân lớp kiểu GTSRB: `data/processed/dataset01_crops/` gồm `train.p` (12.621 crop) và
  `valid.p` (560 crop), builder `scripts/build_dataset01_crops.py`.
- Project detector riêng ở `detector/` (torch 2.14.1, torchvision 0.29.1, ultralytics 8.4.172,
  numpy 2.5.4). CLI: `uv run python -m m1.cli check|train|evaluate|latency`. Đã chạy thử trên MPS.
- Số đo trên M1 Pro (16 GB):
  - Train YOLO11n ở 1280 px, batch 4: khoảng 5,2 ảnh/giây, tức ~21 giờ cho 100 epoch (YOLO11s
    khoảng 45 giờ). Batch 8 ở 1280 px gây swap, không dùng.
  - Suy luận YOLO11n 54 lớp: ~23 ms (~43 FPS); YOLO11s ~39 ms.
  - Số lớp gần như không ảnh hưởng tốc độ (54 lớp ≈ 1 lớp).
  - VGG16 chuẩn ở 224 px tốn khoảng 10 ms cho mỗi biển; CNN E0 ở 32 px khoảng 7 ms cho 3 biển.
- Thời gian trên Colab **chỉ là ước tính, chưa đo**: T4 khoảng 5–12 giờ, L4 khoảng 3–6 giờ,
  A100 khoảng 1,5–2,5 giờ cho 100 epoch.

---

## Việc 0 — Hỏi Owner 4 quyết định (BẮT BUỘC, trước mọi việc khác)

Trình bày ngắn gọn rồi chờ trả lời. Ghi từng câu trả lời thành một bản ghi append-only trong
`docs/review/`, có ngày, nội dung đã duyệt và SHA-256 của input liên quan.

| # | Câu hỏi | Khuyến nghị |
| --- | --- | --- |
| Q1 | Có cho tải trọng số pretrained COCO chính thức của Ultralytics (`yolo11s.pt`) không? | Có. Ghi SHA-256 của file, lưu ngoài git |
| Q2 | Train ở đâu: M1 Pro hay Google Colab? Nếu chọn Colab, có cho upload ảnh **train và val** vào Drive riêng tư không? Test không được upload | Colab L4/A100; điều kiện: Drive riêng tư, chỉ dùng để train, xóa sau khi xong |
| Q3 | Kiến trúc: (a) YOLO 54 lớp như D-05, (b) YOLO 1 lớp + classifier, hay (c) chạy cả hai làm baseline? | (a). Phương án (b) sẽ đổi phạm vi D-05 nên cần một quyết định mới |
| Q4 | Có commit toàn bộ thay đổi hiện tại (khoảng 130 file) trước khi train không? | Có, trên branch hiện tại, để `run_contract.json` ghi được commit sạch |

Hoàn thành khi: có 4 câu trả lời và các bản ghi tương ứng (Q4 thì commit xong, có attribution
nếu Owner yêu cầu).

## Việc 1 — Ghi quyết định dependency và gửi QA gói M1

- Viết `docs/review/m1_dependency_decision_record.md`. Nội dung: Owner đã duyệt PyTorch và
  Ultralytics pin chính xác trong project riêng `detector/`, vì Ultralytics trên macOS xung đột
  numpy với môi trường gốc (E0 pin numpy 2.1.3). Ghi kèm SHA-256 của `detector/pyproject.toml` và
  `detector/uv.lock`.
- Gửi QA độc lập cho:
  - `scripts/build_m1_yolo_dataset.py`;
  - `scripts/build_dataset01_crops.py`;
  - `detector/m1/` (contract, metrics, cli).

  QA cần kiểm: guard split, niêm phong test, `fliplr=0`, tắt telemetry, đúng logic ghép IoU,
  chọn ngưỡng và bootstrap theo nhóm.
- Hoàn thành khi: QA PASS, hoặc sửa xong theo bản R1.

## Việc 2 — Đường train trên Colab (chỉ làm nếu Q2 = Colab)

- Tạo notebook `detector/colab/d1_train.ipynb`, hoặc một script tương đương. Nội dung:
  - cài đúng phiên bản theo `detector/uv.lock` (dùng `uv sync`);
  - kiểm `m1.cli check` trên bản dữ liệu đã upload, cụ thể là hash danh sách stem train/val
    phải khớp `docs/review/generated/m1_yolo_export_manifest.json`;
  - train;
  - đóng gói `weights/`, `results.csv`, `args.yaml`, `run_contract.json` để tải về.
- Viết script đóng gói dữ liệu upload: **chỉ train và val** (copy file thật, không dùng symlink),
  kèm manifest.
- `run_contract.json` phải ghi loại GPU, CUDA và driver. Trên Colab cũng phải tắt telemetry
  Ultralytics.
- Hoàn thành khi: chạy được 1 epoch smoke trên Colab, tải kết quả về, và
  `m1.cli evaluate --split val` chạy được trên máy M1 Pro với trọng số đó.

## Việc 3 — Pilot D1, 1 seed (theo D-05 Q1)

```bash
cd detector && uv run python -m m1.cli train --seed 20261018 --model yolo11s.pt --epochs 100 --imgsz 1280 --batch 4
```

- Dùng `--model yolo11s.yaml` nếu Owner không cho tải pretrained. Trên Colab có thể tăng batch.
- Sau khi train xong, chạy:
  `uv run python -m m1.cli evaluate --weights <run>/weights/best.pt --split val --bootstrap`
  và `uv run python -m m1.cli latency --weights <run>/weights/best.pt`. Latency luôn đo trên M1 Pro.
- Viết báo cáo pilot `docs/review/d1_pilot_report.md`, gồm:
  - mAP50, mAP50-95, AP-small;
  - recall phát hiện (bỏ qua lớp) và FP/ảnh tại ngưỡng conf chọn trên val;
  - recall từng lớp kèm support;
  - kết quả theo độ phân giải. Val chứa toàn bộ ảnh dọc 540×960 và không có ảnh 1920×1080,
    nên phải tách theo độ phân giải;
  - mẫu lỗi (bỏ sót, sai khung, sai lớp);
  - latency p95.
- Hoàn thành khi: có báo cáo và gửi QA.

## Việc 4 — Hiệu chỉnh gate (chỉ khi cần) → Owner duyệt

- Nếu pilot cho thấy gate D-05 không khả thi, đề xuất mức gate mới kèm bằng chứng từ val, rồi
  **chờ Owner duyệt trước khi mở test**. D-05 chỉ cho phép hiệu chỉnh một lần, và không bao giờ
  được hạ gate sau khi đã thấy test.
- Nếu pilot cho thấy lớp hiếm quá yếu, có thể đề xuất phương án (b) YOLO 1 lớp + classifier. Theo
  số đo, nên chọn classifier nhỏ kiểu E0 (khoảng 34 FPS) thay vì VGG16 chuẩn (khoảng 10–19 FPS).
  Phương án này cần Owner duyệt.

## Việc 5 — Ứng viên cuối, 3 seed

- Train 3 seed `20261018`, `20261019`, `20261020` với cùng cấu hình đã chọn trên val.
- Khóa ngưỡng conf và NMS trên val bằng `select_threshold`: recall ≥ 0,85 với FP/ảnh nhỏ nhất.
  Ghi giá trị ngưỡng vào một file trong repo **trước** khi mở test.
- Hoàn thành khi: có 3 run kèm `run_contract.json` và một file ngưỡng đã khóa.

## Việc 6 — Đánh giá cuối trên test niêm phong (một lần)

```bash
uv run python scripts/build_m1_yolo_dataset.py export-test --final-eval --reason "D1 final evaluation, 3 seeds"
cd detector && uv run python -m m1.cli evaluate --weights <seed>/weights/best.pt --split test --final-eval --reason "D1 final" --conf <ngưỡng đã khóa> --bootstrap
```

- Chạy lệnh evaluate cho cả 3 seed. Lấy trung bình và độ lệch chuẩn.
- So với gate D-05:
  - mAP50 ≥ 0,60; mAP50-95 ≥ 0,40;
  - recall phát hiện ≥ 0,85; FP/ảnh ≤ 0,30;
  - 10 lớp quan trọng (0, 2, 7, 32, 13, 22, 45, 39, 40, 41): recall ≥ 0,70 nếu lớp có ≥ 20 box test;
  - các lớp còn lại có ≥ 20 box test: recall ≥ 0,50;
  - p95 ≤ 100 ms.
- Viết `docs/review/d1_final_evaluation_report.md`, ghi rõ lớp nào đạt, lớp nào "chưa đạt" và lớp
  nào "chưa kiểm chứng". Gửi QA, rồi trình Owner chấp nhận M4.

## Việc 7 — Prototype detector trong Streamlit (sau khi M4 được chấp nhận)

- Thêm vào app (đọc skill `developing-with-streamlit`):
  - tải ảnh toàn cảnh lên → chạy detector → vẽ khung và nhãn tiếng Việt;
  - lớp "chưa kiểm chứng" hoặc "chưa đạt" thì hiển thị là chưa kiểm chứng và không kích hoạt hành
    vi mô phỏng (D-04, D-05).
- Vấn đề môi trường: app chạy ở môi trường gốc (TensorFlow, numpy 2.1.3), còn detector ở
  `detector/`. Hãy đề xuất cho Owner chọn một trong ba cách:
  - export ONNX hoặc CoreML để chạy được ở môi trường gốc;
  - một service suy luận riêng chạy trong `detector/.venv`;
  - subprocess.
- Cập nhật `project_status.py` cùng roadmap, rồi kiểm tra bằng trình duyệt (config `cpv301-web`,
  port 8599). Nhớ khởi động lại server sau khi đổi module.

## Việc phụ (không chặn, làm khi rảnh hoặc khi Owner yêu cầu)

1. Sửa 7 test cũ kiểu "chưa có package kế tiếp" (WP26, WP27, WP27-R1, WP28, WP28-R1, WP28-R2,
   WP29). Các test này đang fail vì WP sau đã tồn tại; cập nhật theo cách không làm hỏng hash pin.
   Kiểm tra trước test nào bị pin.
2. Gán nhãn lại 24 ảnh âm bị cách ly, làm thành một gói nhãn dẫn xuất mới. Danh sách và lớp nhìn
   thấy nằm trong `docs/review/generated/wp34_r1_negative_audit.csv`. Chỉ dùng được sau QA và khi
   Owner duyệt.
3. Kế hoạch thu ảnh thật ở nơi khác cho 22 lớp chưa có test, nhất là lớp 38 (P.127 50 km/h) và
   12 lớp hiếm.
4. Track classifier E1–E4 trên gói `dataset01_crops`. Làm sau detector; khi đó cần Owner duyệt
   gate classifier.
5. Cập nhật `docs/codex_handoff_*.md` và `PROJECT_MEMORY.md` sau mỗi mốc. **Không ghi vào README.**

## Định dạng báo cáo cho Owner sau mỗi việc

- Đã làm gì; file nào thay đổi.
- Đã verify gì, kèm số liệu thật (ghi rõ đâu là đo, đâu là ước tính).
- Còn gì chưa xong hoặc chưa kiểm chứng.
- Câu hỏi cần Owner quyết, nếu có.
