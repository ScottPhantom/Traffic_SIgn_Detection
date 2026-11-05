# SAHI R1 — kiểm chứng độc lập artifact validation, 2026-11-04

Verdict: **PASS giới hạn**

Phạm vi PASS: tính toàn vẹn đầu vào/CSV, phép gộp NMS, các điểm vận hành và diễn giải NO-GO của thực nghiệm validation. Đây không phải chấp thuận bật SAHI trong app, D-05, huấn luyện hay thử nghiệm thực địa. Bài đo latency được kiểm code và artifact, không chạy lại suy luận MPS; AP-small CI do lệnh `verify` của gói tái tính, còn QA tự tính lại điểm AP và CI ghép cặp của recall/FP từ CSV. `sealed_test_accessed=false`; QA chỉ đọc validation R3 và artifact đã có.

## Nguồn và ranh giới

Checkout chính `yolo11n-dual-track-r1`, HEAD `02ed548` sau `fc61d62`, ahead 2; rất nhiều thay đổi chưa commit từ trước, không sửa hay stage. Bản giao QA riêng đọc được. Phần 1 của report trùng byte với pre-registration snapshot (snapshot mtime 19:19:23 +07; result JSON mtime 19:36:36; report mtime 19:45:50). Mtime và snapshot là bằng chứng phù hợp thứ tự, không phải đồng hồ bất biến độc lập. §2.6 được ghi rõ `POST HOC`.

| Mã | Kiểm chứng độc lập | Kết quả |
| --- | --- | --- |
| C1 | `cmp -s` full-frame CSV với D1-VRE-R2; đọc lại GT R3 và chấm bằng `m1.metrics` | Trùng byte; 376 ảnh, 624 GT, tại 0,20: TP 547, FP 150, đúng lớp 457, AP-small 0,2891060189. PASS. |
| C2 | QA parse hai CSV dự đoán riêng, không đọc số từ summary JSON để tính; cùng `m1.metrics` làm scorer đã pin | SAHI 640+full: AP-small 0,3022506819 (chênh +0,0131447); tại 0,20 TP 577, đúng lớp 503, FP 328 = 0,87234/ảnh. Ngưỡng nhỏ nhất trên lưới 0,001 có FP ≤150 là 0,505: TP 496, đúng lớp 414, FP 149 = 0,39628/ảnh. Ceiling baseline/SAHI 612/620. Lớp 7/32/41/46 tại 0,20: baseline 66/18/12/55, SAHI 75/26/12/69; ở 0,505 SAHI 48/17/10/47. PASS. |
| C3 | QA tự gộp CSV full-frame và 16.127 dòng tile bằng NMS theo lớp, IoU 0,70, top 300; kiểm bbox so với mép tile | 376/376 frame khớp tập box CSV gộp; 0 box vượt ô quá 1 px. Ô 640 trên 960×540 đúng `[0,0,640,540]` và `[320,0,960,540]`; overlap 0,1/0,2/0,3 cho cùng bố cục theo công thức; ô 480 có 6, ô 800 có 2. PASS. |
| C4 | QA lấy mẫu ghép cặp 1.000 vòng, seed 20261018, **9 nhóm D-02 nguyên vẹn**, trên số đếm từng frame | CI Δ đúng lớp @0,20 = +0,04444…+0,11502; FP/ảnh = +0,35322…+0,64883. Ở ngân sách FP: CI Δ đúng lớp = −0,11208…−0,01937 (hoàn toàn âm). Trùng report. AP-small CI −0,00472…+0,03427 do verify của gói tái tính; QA không viết scorer AP khác. PASS giới hạn. |
| C5 | Đọc source `latency()` và JSON MPS | Cùng 960×540, `imgsz=1280`, conf 0,20, batch ảnh 1, 50 warm-up/300 lượt đo mỗi nhánh, đồng bộ MPS; p95 full 54,422 ms, SAHI 174,106 ms, vượt 100 ms. Hai nhánh đo nối tiếp bằng model mới nên chưa loại hoàn toàn ảnh hưởng thứ tự/nhiệt. Không chạy lại vì không cần để quyết định: tiêu chí độ chính xác đã trượt độc lập. PASS giới hạn. |
| C6 | So §1 của snapshot/report và mtime; áp quy tắc §1.6 | AP-small tăng +0,013 < +0,03; CI AP chứa 0; CI đúng lớp ở cùng ngân sách FP hoàn toàn âm; latency p95 >100 ms. `NO-GO SAHI thuần` đúng quy tắc. PASS. |
| C7 | QA tính lại FP không khớp GT trên hai CSV và phân loại lồng/trùng bằng diện tích giao ≥50% | Baseline: 80 lồng/trùng, 1 gần GT, 69 nền = 150. SAHI: 228, 3, 97 = 328; chênh lồng/trùng +148 của +178 FP. Report ghi rõ đây là hậu kiểm; 612→620 candidate GT là +8. PASS cho mô tả, không suy ra rule sửa FP. |
| C8 | `graft check .`; Ruff/lock root và detector; verify model-free; pytest scoped | Graft `OK`, Ruff `All checks passed`, hai `uv lock --check` thành công. Pytest scoped SAHI/VRE/M1 exit 0; `uv run python -m m1.sahi_eval_r1 verify` trả `verified=true`, `errors=[]`, exit 0. |

**Giới hạn:** Chỉ một checkpoint, một seed và validation đã được xem nhiều lần. Ngưỡng 0,505 được chọn trong chính validation nên chỉ là chẩn đoán, không phải policy đã khóa. Không đo lại latency và không độc lập triển khai AP scorer mới. Không có sealed test, train, app change hoặc thay D-05. Kết luận được kiểm là SAHI thuần **NO-GO cho bước kế tiếp theo quy tắc đã khóa**, không phải đánh giá an toàn của model.

## Hash đầu vào

| File/nguồn | SHA-256 |
| --- | --- |
| QA brief ngoài repo | `816dfbe8dbfe4ca81a095ee30e95eeb434b98c9f8529f5c2fa8f6ff0a2721746` |
| Pre-registration snapshot ngoài repo | `57791b9c870ca9611f49145563fc0293eeb6e7b27647a2b37ddc3eb77567b8f4` |
| `docs/review/sahi_r1_validation_report.md` | `38adbfaf1df8744ccac97da72667ca6ae8be71224268c16b53216cda72258cab` |
| `docs/review/generated/sahi_r1_validation_summary.json` | `96c48f2e841c62b576aeade69316ab00712ac0c4755df811a81a81eeb68ab038` |
| `detector/m1/sahi_eval_r1.py` | `2ca327ed2901b03b1c302457c881eac0bdf0018c601ac413f70bee489163ebeb` |
| `detector/tests/test_sahi_eval_r1.py` | `f77f42faba84cfa71f46650a1824ddc3e189b2545763da84f6e24036775fbca4` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/m1/val_reeval_r2.py` | `2a0823faa15f7cb9cecb64a1f21e48e8b5b84f7e7f949683683a6992ee13ccc9` |
| Pilot `weights/best.pt` (hash only; no inference in QA) | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| D1-VRE-R2 and SAHI full-frame CSV (identical) | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| SAHI raw tile CSV | `78caf77e174125713daec3554836b2867e937565357508065875affee93b6aa4` |
| SAHI merged CSV | `8b964cc68930ae9ae6ab89c605db2ee7de06e2c2d27e4979057669ba4f29b423` |
| SAHI eval JSON | `bfb62e7b48454e6ae4294d0a33dc5708ab6b4ac109dfe7fd4bca3bc868325243` |
| SAHI latency JSON | `a8b06702cfe50f4956c9b1f118b5b58b5494aa52e218013ba76cc07a43d811b8` |

## Lệnh và readback

`graft check .` → OK; `uv run ruff check src tests && uv lock --check` → PASS; `(cd detector && uv lock --check)` → PASS; `cmp -s ...` → exit 0; `(cd detector && uv run pytest -q tests/test_sahi_eval_r1.py tests/test_val_reeval_r2.py tests/test_m1.py)` → exit 0; `(cd detector && uv run python -m m1.sahi_eval_r1 verify)` → `verified=true`, `errors=[]`, exit 0. Các script kiểm độc lập tạm nằm trong `/tmp/sahi_independent_*_20261104.py`; không ghi vào repo. File record mới này chưa commit/push. Không thể tự nhúng SHA-256 của chính record vào record mà không đổi hash; SHA cuối cùng được báo riêng khi bàn giao.
