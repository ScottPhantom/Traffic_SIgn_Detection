# Handoff cho Codex — CPV301 AutoDrive (tình hình đến 2026-10-18)

> Dán nguyên văn tài liệu này vào Codex. Đây là báo cáo của phiên làm việc giữa **Owner** (chủ dự
> án) và **Claude Code** (vai PM/kỹ sư) từ khoảng 2026-10-16 đến 2026-10-18. Mọi số liệu đều đã
> được verify trong repo tại thời điểm viết. Nguồn sự thật vẫn là repo: nếu tài liệu này mâu thuẫn
> với repo, hãy tin repo.

## 0. Việc Codex phải làm trước tiên

1. Đọc `AGENTS.md`, rồi `PROJECT_MEMORY.md`. Phần "Product milestone status", "Current risks" và
   "Immediate PM gate" đã được viết lại ngày 2026-10-18.
2. Dùng Graft trước khi đọc hoặc sửa code: `graft check .`, `graft map .`, `graft ask "…" --source .`.
3. Chạy kiểm tra trước khi sửa:
   - `uv run python scripts/run_parallel_checks.py verifiers` phải ra **50/50 pass**.
   - Trong `detector/`: `uv run pytest` phải ra **7 pass**.
4. **Không commit, push, upload hay publish** khi owner chưa yêu cầu. Hiện có khoảng 128 file
   thay đổi chưa commit, và owner chưa yêu cầu commit.

## 1. Mục tiêu và hướng đi do Owner đặt

- Mục tiêu: **model detector nhận diện biển báo Việt Nam trên ảnh toàn cảnh**, phục vụ **mô phỏng**
  hỗ trợ lái. Không dùng điều khiển xe thật.
- Thứ tự ưu tiên (Owner, 2026-10-17): **detector VN trước, prototype trong app sau**. Quyết định
  này thay cho thứ tự cũ "classifier-first" (đã cập nhật trong "Durable decisions" #1 của memory).
- Quy trình quản trị append-only:
  - Mỗi gói công việc (WP) có builder `scripts/build_*.py` với các lệnh `build`/`verify`.
  - Input được pin bằng SHA-256, và `verify` dựng lại byte-for-byte.
  - Gói nào QA FAIL thì giữ nguyên làm hồ sơ bất biến; bản sửa là `-R1`/`-R2`.
- **QA độc lập** luôn chạy ở một session khác ("Independent QA…", id
  `local_3e90ec3e-27f8-44db-a5ed-65988db27e0d`). Session đó ghi
  `docs/review/<wp>_independent_qa_record.md` và không sửa builder hay input.

## 2. Trạng thái hiện tại (đã verify)

| Hạng mục | Trạng thái |
| --- | --- |
| Gate 0 (G0.1–G0.9) | **9/9 PASS**. D-05 đã duyệt nên **Gate 0 MỞ** cho track detector VN (2026-10-18) |
| Quyết định D-01…D-05 | Owner đã duyệt cả năm (xem §4) |
| Split chính thức | WP36-R1: train 1.912 / val 376 / test 903 ảnh (59,9 / 11,8 / 28,3 %); **test niêm phong `afa03d4b…`** |
| Dataset card | `docs/dataset01_card_r1.md` (WP37-R1, QA PASS, 0 finding) |
| M1 (gói train) | **ĐANG LÀM**: export YOLO + split guard xong; project `detector/` riêng; CLI train/evaluate/latency đã chạy thử trên MPS |
| Model VN | **Chưa train** model thật nào. Mới có một lần chạy thử 1 epoch trong scratchpad, không ghi vào `results/` |
| Đang chờ Owner | Có cho phép tải trọng số pretrained COCO của Ultralytics (ví dụ `yolo11s.pt`) cho pilot D1 hay train từ đầu |

## 3. Việc đã làm, theo thứ tự (Claude làm / Owner quyết)

### 3.1 Hạ tầng và tốc độ
- **Owner yêu cầu** tối ưu bằng CUDA/MPS và chạy song song.
  - Kết luận: GPU không giúp gì cho các WP xử lý dữ liệu, vì ~90 % thời gian là Pillow chạy trên CPU.
- **Claude làm** `scripts/run_parallel_checks.py`:
  - `verifiers` chạy song song mọi verifier (hiện có 50);
  - `tests` chạy WP9/10/11 tuần tự trước, rồi phần còn lại bằng `pytest-xdist --dist loadfile` qua `uv run --with pytest-xdist==3.8.0`. xdist không được thêm vào lock vì `pyproject.toml`/`uv.lock` đang bị WP6 pin.
- `tests/conftest.py` có một autouse fixture chặn các suite WP9/10/11 khi chạy dưới xdist.
- **Owner chọn** "sao chép + kiểm hash". Claude đã chép DATASET01 vào
  `data/raw/DATASET01/staging/052bc980a7206f8d/raw` (git-ignored); nguồn iCloud giữ nguyên.

### 3.2 Streamlit (`src/cpv301_autodrive/web_app.py`)
- Có 3 tab: "Tiến độ dự án", "DATASET01", "Mô phỏng (baseline E0)".
  - Trạng thái lấy từ `src/cpv301_autodrive/project_status.py`. File này phải cập nhật cùng roadmap.
- Tab DATASET01 có bốn phần (module `dataset01_view.py`, assets `dataset01_graph.html` và `dataset01_pipeline.html`):
  - đồ thị theo nhóm D-02;
  - bảng lớp và bảng nhóm (Altair);
  - hoạt hình 8 bước: graph → gán nhãn → nhóm → 4 bucket D-04, trong đó bucket cuối đi qua làm giàu dữ liệu.
- `dataset_graph.py` bị WP31-R1/R2 pin, **không được sửa**.
- Đã kiểm trên trình duyệt (cấu hình `.claude/launch.json` "cpv301-web", port 8599). Server Streamlit giữ module cũ trong bộ nhớ, nên đổi `project_status.py` xong phải **khởi động lại server**.

### 3.3 Gom nhóm D-02 (G0.6)
- WP28-R2 + WP29 được QA PASS. WP30 (cạnh còn lại) **QA FAIL** ở `edge_003047`. **Owner yêu cầu** sửa
  theo tiền lệ WP28-R1 → WP30-R1 chỉ đổi cạnh này thành SAME_CAPTURE / NOT_RELATED / MEDIUM → QA PASS.
- WP31 (đề xuất `group_id` bằng union-find trên cạnh SAME/UNRESOLVED) bị QA chỉ ra lỗi:
  - **R1** sửa lỗi xen kẽ (interleave);
  - **R2** sửa cách gắn đoạn ảnh âm ở cấp scene, nối cả hai cảnh bao quanh.
  - Kèm theo là **WP32**, sinh ứng viên nối nhóm chéo khối bằng thumbnail gần trùng + hình học nhãn.
  - WP31-R2: QA PASS.
- **Owner duyệt D-02 (D02-P1)**: 54 nhóm capture của WP31-R2, stem 0248 bị cách ly. Registry:
  `docs/review/generated/d02_group_id_registry.csv`, kèm lệnh `check-candidate`.

### 3.4 License, taxonomy, nhãn (G0.1, G0.5)
- **Owner D-01**: chấp nhận rủi ro license (metadata CC-BY-SA 3.0 vs mô tả 4.0; chủ sở hữu ảnh
  UNKNOWN) và áp điều khoản chặt nhất. Không phân phối lại ảnh/nhãn gốc. Trọng số model có thể chịu share-alike.
- **Owner D-03**: duyệt taxonomy ở session phụ. **WP33** sinh bộ nhãn dẫn xuất gồm 54 lớp train:
  - lớp 31 → UNKNOWN, chỉ dùng để đánh giá;
  - P.117 tách theo chiều cao 2,0/2,2/2,5 m; W.239b tách 2,5/2,7 m;
  - 4 box không đọc được giá trị bị loại.
  - QA PASS. **Nhãn train chỉ lấy từ `wp33_derived_boxes.csv`**, không dùng class id gốc.

### 3.5 Lớp hiếm và ảnh âm (G0.8)
- **WP34** (hỗ trợ D-04 + audit 25 ảnh âm) bị **QA FAIL**:
  - 5 "ảnh âm" thật ra có biển cls32, và 2793–2797 có cls50;
  - sai trường lớp (1703–1708 phải là `39 40`, 2766 phải là 13);
  - họ biển chiều cao bị tách sai.
- **WP34-R1**:
  - xem lại từng ảnh âm ở 1.600 px và zoom ảnh raw;
  - **chỉ 0544 là nền thật**, 24 ảnh còn lại bị cách ly đến khi gán nhãn lại;
  - gom P.117/W.239b theo họ;
  - cờ "dominated" theo tỉ lệ box (lớp 11, 14, 28, 38).
  - QA PASS. Lỗi P3 về câu chữ đã sửa kèm addendum.
  - Có 2 chỗ R1 khác QA cũ: 2723 bị cách ly vì có biển cls46 ở xa, và 2999 là `6 13 38`. QA đồng ý cả hai.
- **Owner D-04 phần 1**: **không bỏ** 12 lớp hiếm, mà train kèm làm giàu dữ liệu.
  - Trạng thái `EVAL_PENDING_REAL_INDEPENDENT_DATA`; không kích hoạt hành vi xe cho tới khi được đánh giá.
- **WP35** làm giàu dữ liệu:
  - Bản đầu dán biển QCVN lên ảnh. **Owner bác** vì tạo ảnh phi lý.
  - Bản hiện tại chỉ **biến đổi ảnh thật**: xoay ±5°, crop zoom 55–95 % không cắt biển, màu/sáng/tương phản/nhiễu/nhòe/JPEG, **không lật ngang**, seed 20261017. Kết quả 1.800 ảnh (150 ảnh/lớp, git-ignored).
  - QA PASS.
- **Owner D-04 phần 2**: 27 lớp TRAIN_VAL_TEST, 6 TRAIN_AND_TEST_NO_VAL, 9 TRAIN_ONLY_UNVERIFIED.
  - Ảnh âm: chỉ 0544 làm nền; 24 ảnh cách ly.

### 3.6 Split (G0.7)
- Claude viết kế hoạch `docs/review/wp36_g07_split_plan.md`. Đo được 15 nhóm buộc phải vào train, chiếm 49 % số ảnh.
- **Owner chọn phương án A**:
  - các lớp chỉ còn một nhóm tự do (17, 18, 19, 30, 40, 45, 50) đưa nhóm đó vào test;
  - lớp 38 chuyển thành TRAIN_ONLY_UNVERIFIED;
  - tỉ lệ ~70/15/15 ±3.
- **WP36**: QA PASS nhưng có 1 P2, vì builder xếp dải ±3 trên tiêu chí "≥ 2 nhóm test", ngược thứ tự Owner đã duyệt.
  - **Owner chọn áp đúng thứ tự** (`g07_owner_decision_r1_record.md`).
  - Hệ quả Owner chấp nhận: test ~28 %, và lớp 22 mất val để lớp 25 giữ được test.
- **WP36-R1**:
  - xếp lại thứ tự ưu tiên;
  - tính tỉ lệ trên ảnh dùng được (3.191);
  - `check-candidate` từ chối ảnh cách ly, ảnh nền ngoài train và danh sách lệch hash;
  - bước kiểm tra chạy trong thư mục tạm.
  - QA PASS, và QA xác nhận đây là nghiệm tối ưu theo thứ tự của Owner.
- **Owner chấp nhận WP36-R1 làm split chính thức** (`g07_owner_acceptance_record.md`).

### 3.7 Dataset card (G0.9)
- **WP37** (`docs/dataset01_card.md`): QA PASS nhưng có 1 P2. Card gọi 7 ảnh 1843–1851 là "ảnh tối", trong khi đó là ảnh ban ngày chụp ngược tán cây.
- **WP37-R1** (`docs/dataset01_card_r1.md`):
  - nhóm độ sáng được ghi là nội dung cảnh + phơi sáng; card nói rõ **không có ảnh đêm nào được xác minh**;
  - ghi kích thước decode thực tế và độ nét tách theo độ phân giải;
  - box nhỏ ≈ 37 %;
  - ghi công đúng văn bản D-01;
  - QA PASS, 0 finding.
- Phát hiện quan trọng: **val lệch điều kiện chụp**. Toàn bộ 39 ảnh dọc 540×960 nằm ở val, và val không có ảnh 1920×1080.

### 3.8 Ngưỡng nghiệm thu (D-05) → Gate 0 mở
- Claude viết đề xuất `docs/review/d05_proposal.md`. **Owner duyệt toàn bộ Q1–Q6**
  (`docs/review/d05_owner_decision_record.md`):
  - **Seed**: D05-B, pilot 1 seed rồi ứng viên cuối 3 seed (20261018/19/20); gate tính trên trung bình.
  - **Gate trên test niêm phong** (chạy một lần):
    - mAP50 ≥ 0,60; mAP50-95 ≥ 0,40;
    - recall phát hiện (bỏ qua lớp) ≥ 0,85; FP/ảnh ≤ 0,30;
    - recall từng lớp: lớp quan trọng ≥ 0,70, lớp khác ≥ 0,50 (chỉ áp cho lớp có ≥ 20 box test);
    - khoảng tin cậy bằng bootstrap theo nhóm D-02.
  - **10 lớp quan trọng**: 0, 2, 7, 32, 13, 22, 45, 39, 40, 41.
  - **Val** chỉ dùng chỉ số gộp để chọn model và chọn ngưỡng conf/NMS. Được hiệu chỉnh gate một lần trước khi mở test; không hạ gate sau khi đã thấy test.
  - **Latency**: p95 ≤ 100 ms, batch 1, trên M1 Pro MPS.

### 3.9 M1 — gói train detector (đang làm)
- **Owner duyệt** thêm PyTorch + Ultralytics, bản ổn định, pin chính xác.
- **Claude làm** `scripts/build_m1_yolo_dataset.py` (môi trường gốc):
  - manifest commit được `docs/review/generated/m1_yolo_export_manifest.json`;
  - class map `m1_yolo_classes.csv`: 54 lớp WP33 → id YOLO 0–53;
  - guard: kiểm hash danh sách WP36-R1, cột `use` và test seal;
  - `export` ghi train (1.912 + 1.800 ảnh WP35) và val (376) vào `data/processed/m1_yolo/` (git-ignored, ảnh dạng symlink);
  - **test chỉ xuất bằng** `export-test --final-eval --reason …` và được ghi log vào `results/experiments/sealed_test_access_log.jsonl`;
  - verifier `m1-yolo`, 7 test.
- **Xung đột đã kiểm chứng**: trên macOS, Ultralytics 8.4.172 loại trừ numpy ≤ 2.3.4, trong khi môi trường gốc pin
  numpy 2.1.3 cho TensorFlow E0. **Owner chọn tạo project uv riêng `detector/`**:
  - `detector/pyproject.toml` + `detector/uv.lock`: torch 2.14.1, torchvision 0.29.1, ultralytics 8.4.172 (numpy 2.5.4, opencv-python 5.0.0.93); có `.venv` riêng.
  - Môi trường gốc, E0 và WP6 **không đổi**; hash vẫn khớp pin của WP6.
- **Gói `detector/m1/`**:
  - `contract.py`:
    - fail-closed theo hash bản ghi D-05, manifest export và danh sách stem đã xuất;
    - chứa hằng số D-05;
    - ép `fliplr=0`;
    - **tắt telemetry/sync của Ultralytics**.
  - `metrics.py`: ghép IoU, recall có/không phân lớp, FP/ảnh, chọn ngưỡng trên val, bootstrap theo nhóm, latency.
  - `cli.py`, các lệnh `check | train | evaluate | latency`:
    - train ghi `run_contract.json` (commit, hash lock, hash split, phần cứng);
    - evaluate từ chối chạy test nếu thiếu `--final-eval --reason` và `--conf` đã khóa trên val.
- Đã chạy thử trên MPS: 1 epoch, 5 % dữ liệu, 320 px, ghi vào scratchpad. Cả chuỗi chạy được; điểm số = 0 như dự kiến; p95 = 15,6 ms ở 320 px.

## 4. Bảng quyết định của Owner (append-only, ở `docs/review/`)

| Quyết định | Nội dung | Hồ sơ |
| --- | --- | --- |
| D-01 | Chấp nhận rủi ro license, áp CC-BY-SA chặt nhất | `d01_owner_decision_record.md` |
| D-02 | D02-P1: 54 nhóm capture WP31-R2 | `d02_owner_decision_record.md` |
| D-03 | Taxonomy (2 phần + bản sửa) | `d03_owner_decision_part1/part2_record.md` |
| D-04 p1 | 12 lớp hiếm train + làm giàu bằng **biến đổi ảnh thật** (bản sửa 2026-10-17 bác cách dán biển) | `d04_owner_decision_part1_record.md` |
| D-04 p2 | 42 lớp theo WP34-R1; chỉ 0544 làm nền | `d04_owner_decision_part2_record.md` |
| G0.7 | Luật split phương án A; bản R1 áp đúng thứ tự ưu tiên; chấp nhận WP36-R1 | `g07_owner_decision_record.md`, `g07_owner_decision_r1_record.md`, `g07_owner_acceptance_record.md` |
| D-05 | Toàn bộ khuyến nghị Q1–Q6 → Gate 0 mở | `d05_owner_decision_record.md` |
| M1 deps | PyTorch/Ultralytics pin chính xác, trong **project riêng `detector/`** | ghi trong `PROJECT_MEMORY.md` (chưa có record riêng) |

## 5. Các lỗi Claude đã sửa (để Codex không lặp lại)

- **Sai do QA phát hiện**, sửa qua R1/R2:
  - WP30 (`edge_003047`);
  - WP31 (interleave, gắn ảnh âm);
  - WP34 (ảnh âm có biển, sai trường lớp, họ biển chiều cao);
  - WP36 (thứ tự ưu tiên ngược với Owner);
  - WP37 (gọi nhầm ảnh "tối").
- **Báo sai test seal**: trước đó báo `f506…` cho WP36, nhưng đó là hash của một bản build cũ. Giá trị đúng là `01bdb989…` (WP36) và `afa03d4b…` (WP36-R1, bản chính thức).
- **README.md bị WP27-R1 pin hash**. Một lần sửa README làm verifier wp27-r1/r2 fail, đã revert về đúng bytes. **Không sửa README**; trạng thái ghi ở roadmap, memory và app.
- CLI detector:
  - tạo thư mục run trước khi train khiến Ultralytics ghi sang thư mục "-2" → đã sửa (kiểm tra trước, rồi `exist_ok=True`);
  - `model.val` tạo thư mục `runs/` ở gốc repo → đã chỉ định `project` vào thư mục run và xóa `runs/` rỗng.
- Lỗi nhỏ khác:
  - xdist làm crash worker → chuyển sang dùng fixture;
  - `ProcessPoolExecutor` ở WP32 → đổi sang `ThreadPoolExecutor`;
  - sửa panel nguồn của đồ thị (`fmt(undefined)`);
  - Streamlit hiển thị trạng thái cũ cho tới khi khởi động lại server.

## 6. Bẫy và luật quan trọng

- Không sửa file đã bị pin hash, bao gồm:
  - `dataset_graph.py`;
  - các builder và test của WP cũ;
  - `README.md`;
  - `pyproject.toml`/`uv.lock` gốc (WP6 pin);
  - `docs/dataset01_card.md` (WP37).
  Muốn sửa thì làm gói R mới.
- Test niêm phong `afa03d4b…`: chỉ mở trong lần đánh giá cuối có log. Đổi danh sách split phải làm split version mới và có quyết định mới của Owner.
- 13 lớp không có val (9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50) không được dùng để chọn model hay chỉnh ngưỡng.
- 22 lớp không có test (12 lớp làm giàu, 9 lớp chỉ train, lớp 38) luôn ở trạng thái "chưa kiểm chứng".
- Không có ảnh đêm nào được xác minh, nên hiệu năng ban đêm/mưa là UNKNOWN.
- MPS có op không tất định, nên train không lặp lại y hệt từng bit. Báo cáo độ lệch giữa các seed.
- Tải file (ví dụ trọng số pretrained) cần Owner cho phép trước.
- Hành vi xe chỉ là mô phỏng.

## 7. Việc còn lại (theo thứ tự)

1. **Owner quyết**: tải pretrained COCO (khuyến nghị `yolo11s.pt`, ghi SHA-256) hay train từ đầu.
2. Pilot D1, 1 seed: `cd detector && uv run python -m m1.cli train --seed 20261018 --model <…> --epochs 100 --imgsz 1280`,
   rồi `evaluate --split val --bootstrap` và `latency`.
3. Nếu cần hiệu chỉnh gate thì trình Owner **trước** khi mở test. Sau đó chạy 3 seed, rồi `export-test --final-eval` và `evaluate --split test --final-eval --conf <đã khóa trên val>`.
4. Gửi QA độc lập cho gói M1 (export + detector CLI). Thêm record riêng cho quyết định dependency nếu Owner muốn.
5. Việc phụ, không chặn lộ trình:
   - sửa 7 test cũ kiểu "chưa có package kế tiếp" (WP26–WP29) đang fail vì các WP sau đã tồn tại;
   - gán nhãn lại 24 ảnh âm bị cách ly;
   - thu thêm ảnh thật ở nơi khác cho 22 lớp chưa có test;
   - commit, khi Owner yêu cầu.

## 8. Lệnh kiểm tra nhanh

```bash
uv run ruff check src tests && uv lock --check
uv run python scripts/run_parallel_checks.py verifiers          # 50/50
uv run python scripts/run_parallel_checks.py tests              # 7 lỗi cũ đã biết (§7.5)
uv run python scripts/build_m1_yolo_dataset.py verify
cd detector && uv run pytest && uv run python -m m1.cli check
graft build . && graft check .
```
