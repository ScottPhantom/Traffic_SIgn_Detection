# Temporal DT R1 — công tắc thử nghiệm trong "Ứng dụng Model cho Cam Hành trình"

File **append-only**. Ngày 2026-11-04 (Asia/Ho_Chi_Minh). Owner duyệt qua phiên điều phối.
Nhãn: `VERIFIED` (đã chạy/đọc lại trong checkout này), `PROPOSAL`, `UNKNOWN`.
Trạng thái: **QA độc lập UI + source PENDING**; tác giả không tự ghi PASS. Không commit/push.

## §1 Phạm vi và quyết định thiết kế

- Công tắc `st.toggle` "Ngưỡng động theo thời gian (thử nghiệm)", **mặc định tắt**, hai key
  riêng: `review2_temporal_dt_r1_precomputed` (preview dựng sẵn R14/R1) và
  `review2_temporal_dt_r1_upload` (luồng tải clip). Ở luồng tải, công tắc bị vô hiệu với
  Cascade B0 (chỉ hỗ trợ YOLO11s-54).
- Bật thì **chỉ hiển thị** khung so sánh trước/sau: số box, số track, số lần đổi nhãn (ngưỡng
  cố định 0,20 so với Temporal DT R1 0,35 / 0,15 / N = 5 / max_miss = 2), dòng lý do, và bảng
  giữ/bỏ cho từng candidate (`giữ/bỏ`, `fixed_0.20`, `lý_do_temporal`, track, trạng thái, nhãn
  track, điểm track). Ghi chú bắt buộc nằm ngay trong khung, đúng văn bản Owner yêu cầu.
- Video chú giải, CSV dự đoán/track/sự kiện, sự kiện và manifest vẫn là ngưỡng 0,20. Temporal DT
  không vẽ lên video và không đổi export.
- **An toàn hành vi:** khi bật, mô phỏng hành vi có điều kiện bị tắt hẳn
  (`behavior_enabled=False`) với thông điệp riêng "Mô phỏng hành vi tạm tắt vì công tắc Temporal
  DT (thử nghiệm) đang bật; không phát lệnh điều khiển xe." Lý do: đây là cách đơn giản nhất bảo
  đảm Temporal DT không tạo thêm hành động xe. Cổng R13 và `vehicle_action="none"` giữ nguyên.
  Trong lúc dựng, browser lộ lỗi: bản đầu hiện thông điệp của Cascade B0 khi tắt hành vi cho D1.
  Đã sửa bằng tham số `disabled_reason` (mặc định giữ đúng văn bản Cascade cũ).
- **Candidate 0,001:**
  - Preview dựng sẵn: dùng CSV Mini conf 0,001 đã pin
    (`67b714a7…`, manifest `8145ef27…`), lấy mỗi 2 frame, nên khác nhịp của video R14/R1; UI ghi
    rõ. Thiếu file thì UI báo chỉ hỗ trợ luồng tải.
  - Luồng tải: khi bật, `process_uploaded_video(..., temporal_candidates=True)` gọi D1 một lần ở
    conf 0,001 và lấy các box ≥ 0,20 cho pipeline cố định. Manifest có thêm khối
    `temporal_dt_r1_display` (`EXPERIMENTAL_DISPLAY_ONLY_NOT_D05`, `behavior_simulation_disabled`).
    Kết quả cũ tạo khi tắt không có pool, nên UI nhắc bấm tạo lại.
- Không đổi: ngưỡng mặc định 0,20, D-05, raw prediction, manifest đã pin, chế độ D1/S1 ảnh tĩnh,
  `temporal_threshold.py` (vẫn `a519066a…`), `app_pages/07_demo.py` và `views.py` (không sửa).

## §2 File

| File | Thay đổi | SHA-256 |
| --- | --- | --- |
| `src/cpv301_autodrive/review2_temporal_dt_r1.py` | mới | `936b2cdd1310c069b047a000034cae1191e3b955a58e8f6bcb4e08c4377f9591` |
| `src/cpv301_autodrive/review2_front_demo_r1.py` | hook công tắc + so sánh + chặn hành vi | `af5a843b2d6ffa5c34e2a99209d391ac5abe129d6303b64a66fc721288d32f1e` |
| `src/cpv301_autodrive/review2_upload_video_r1.py` | kwarg `temporal_candidates`, công tắc, so sánh | `b8d368d7f70ef1d73db7a28a999e19320212b59ba959f9e92e434aa4d59eff1a` |
| `src/cpv301_autodrive/review2_video_seek_r1.py` | tham số `disabled_reason` (mặc định = văn bản Cascade cũ) | `c0bfda8141869e863e40ce497c0072954ba2faa0560c0643e28a6b2fc03a3b4b` |
| `tests/test_review2_temporal_dt_r1.py` | mới, 11 test | `e16dde962dcadb9f280f8250f68cf900af61862d2c56e2d7ae46168dc4bc3d79` |
| `.claude/launch.json` | thêm cấu hình `cpv301-web-temporal-dt` port 8641 | `19a66a83857fb81b31317808c8994a5f28d3ba789e5d33509bd0a33982470e94` |

## §3 Kiểm tra (VERIFIED)

- **Tắt = như trước, so với source trước khi sửa.** Vì các file `review2_*` chưa được track
  trong git, script `revert.py` dựng lại bản trước khi sửa của ba file đã đổi trong một bản sao
  scratch bằng cách đảo đúng từng chỉnh sửa. `offcheck.py` chạy cùng phép đo trên bản gốc và bản
  mới:
  - (a) `process_uploaded_video` với D1 thật trên clip Mini `1fab7593…`: video, CSV dự đoán,
    CSV track, CSV sự kiện và manifest **byte-identical**. CSV dự đoán = `343e00c3…`, đúng bản
    upload đã pin trước đây.
  - (b) AppTest preview dựng sẵn: cây phần tử giống hệt (35 phần tử, không tính toggle), không
    exception.
  - Script và hai JSON kết quả nằm ở `tmp/temporal_dt_r1_ui_evidence/` (ignored), hash ở §4.
- **Bật không đổi export:** D1 thật trên Mini với `temporal_candidates=True`: video/CSV/manifest
  (trừ khối mới) trùng hoàn toàn với khi tắt. Pool 246 candidate, so sánh 54 → 55 box, 10 → 10
  track, 11 → 4 lần đổi nhãn. Lý do: `below_keep_floor` 185, `kept_confirmed_track` 55,
  `tentative_evidence_below_enter` 6.
- **Test** (`tests/test_review2_temporal_dt_r1.py`, 11 test):
  - tắt gọi D1 ở 0,20, không có pool, không có khối manifest; bật gọi ở 0,001, export trùng
    hoàn toàn;
  - Cascade bị từ chối;
  - `compare` loại báo nhầm 1 frame và giữ biển nhiều frame;
  - CSV Mini pin hash nạp được (103 frame, 246 candidate, 54 box ≥ 0,20);
  - AppTest tắt: không có khung so sánh, 2 video;
  - AppTest bật: có ghi chú, 2 cặp metric, ghi chú tắt hành vi;
  - `session_state` cũ `"on"`, `1`, `None`, `["x"]` không làm app crash, công tắc về tắt;
  - thông điệp tắt hành vi là của Temporal DT, không phải Cascade.
- **Gate:** `uv run ruff check src tests scripts` PASS. 103 test liên quan PASS (13 file
  review2/temporal/web_app/DT product/S1). `uv lock --check` PASS, `git diff --check` PASS,
  `graft build . && graft check .` in sync. Blast radius `process_uploaded_video`: chỉ
  `render_upload_demo` và test.
- **Browser thật** (in-app browser, server riêng `127.0.0.1:8641`; không chạm 8599/8611/8612/8631;
  restart sau khi sửa module):
  1. Preview dựng sẵn, công tắc tắt: không có khung so sánh.
  2. Tắt, chọn sự kiện P.130 9,1 s / track 5: hiện mô phỏng có điều kiện như cũ.
  3. Bật: khung so sánh 54/55 box, 10/10 track, 11/4 đổi nhãn, ghi chú Owner, bảng giữ/bỏ.
  4. Bật, cùng sự kiện: ô hành vi hiện thông điệp tắt của Temporal DT.
  5. Luồng tải: nạp đúng clip Mini mà trang đang phục vụ (SHA-256 kiểm trong trình duyệt
     `1fab7593…`, 23.713.392 byte) vào uploader bằng DataTransfer, vì in-app browser không có công
     cụ chọn file. Chạy với công tắc tắt: không có so sánh. Bật lên: UI nhắc tạo lại. Tạo lại: khung
     so sánh "Clip vừa tải … 103 frame, 246 candidate", lý do 185/55/6.
  - Server không log lỗi. Console chỉ có lỗi kết nối/404 media do restart server.

## §4 Bằng chứng (ignored, `tmp/temporal_dt_r1_ui_evidence/`)

| File | SHA-256 |
| --- | --- |
| `01_precomputed_off.jpg` | `e8d3fdff36a569fdc3ca3cb373a76eea72816b811f42cb8f1b1128f9a3930e39` |
| `02_precomputed_off_event_behavior.jpg` | `dd4c397140d8f678e89135a56bb22f6154f6379cd371a135f84aae7cb68552cb` |
| `03_precomputed_on_comparison.jpg` | `50ed76973ce3df702320758d446a11d739d9427e05b828b773c785743f4ca713` |
| `04_precomputed_on_behavior_disabled.jpg` | `d5064aff00acf30a348b5cf5e8033ecedc1fd746310131b67ee1e93df5a6935d` |
| `05_upload_off_processed.jpg` | `9800ccdbdca7a1bc89ff2b8b939bc13af58ca760c56e5e93e2a6511e77b83870` |
| `06_upload_on_comparison.jpg` | `e6e47078413c47d650e9ef9bf8d4d1c7c11703d73e545cbc2789b2454e74a227` |
| `revert.py` / `offcheck.py` | `41c9f80c…f2` / `66e2bd04…54c` |
| `off_orig2.json` / `off_new2.json` | `a6abc55d…7005` / `c32a72b3…2ff2d` |

Ảnh 03 chụp sau khi sửa bố cục metric. Ảnh 01/02 chụp trước khi sửa `disabled_reason` và bố
cục, nhưng ở trạng thái tắt hai thay đổi đó không hiển thị.

## §5 Giới hạn và việc còn lại

- VERIFIED: mọi so sánh trong khung là đếm box/track trên clip, **không phải độ chính xác**;
  clip Mini không có GT đầy đủ.
- UNKNOWN: hành vi với clip khác Mini qua trình duyệt; phép tắt = như trước chỉ đo trên clip
  Mini và trên preview dựng sẵn.
- `PROJECT_MEMORY.md` và `docs/product_roadmap.md` chưa cập nhật (chờ QA).
- PROPOSAL: sau QA PASS mới cân nhắc vẽ box giữ/bỏ lên video; hiện chỉ có bảng.
