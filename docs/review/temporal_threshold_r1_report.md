# Temporal Dynamic Threshold R1 — D1 YOLO11s-54, offline

File này **append-only**: các mục mới thêm ở cuối, không sửa mục cũ. Mỗi khẳng định được gắn
`VERIFIED` (đã chạy/đọc lại trong checkout này), `PROPOSAL` (đề xuất, chưa làm) hoặc `UNKNOWN`.
Gói này không bật gì trong app, không train, không mở sealed test, không đổi D-05.

## §1 Pre-registration — khóa trước khi tính bất kỳ kết quả temporal nào

Ghi lúc 2026-11-04T13:37+07:00, trước khi module tồn tại và trước khi chạy đánh giá temporal.
Trước thời điểm này chỉ có các phép kiểm dữ liệu: tái tạo baseline 0,20 và kiểm giả định chuỗi
(§2). Không có số đo temporal nào được nhìn thấy khi khóa các mục dưới đây.

### Tham số chính (không đổi sau khi xem kết quả)

| Tham số | Giá trị |
| --- | --- |
| `enter` (ngưỡng xác nhận) | 0,35 |
| `keep` (ngưỡng giữ, đồng thời sàn liên kết) | 0,15 |
| `window` N | 5 frame của chuỗi |
| `max_miss` | 2 (frame thiếu thứ 2 liên tiếp thì CLOSED) |
| Liên kết | `review2_temporal_r1.track_prediction_rows`, cấu hình R12: `iou_min=0.30`, `predict_motion=True`, `max_missing_samples = max_miss − 1 = 1` |
| Baseline | ngưỡng cố định 0,20 từng frame (`metrics.match`, IoU 0,5) |

### Định nghĩa thuật toán

- Candidate có điểm thô `s < keep` bị loại trước liên kết, lý do `below_keep_floor`. Chúng không
  bao giờ được xuất. Box có cạnh ≤ 0 bị loại (`invalid_box`), giống adapter D1 hiện tại.
- Liên kết chỉ được gọi qua hàm R1 có sẵn (import, không sửa). Lớp dùng làm `code` là `yolo_id`.
  Mỗi chuỗi được liên kết độc lập.
- Bằng chứng mỗi frame: `e = logit(s) − logit(keep)`. Frame không có candidate liên kết đóng góp 0.
- Điểm track tại frame t: `S_t = sigmoid(logit(keep) + Σ e)` trên các frame quan sát trong N = 5
  frame gần nhất của chuỗi (t−4…t). Với một frame duy nhất, `S = s`, nên candidate chỉ xuất hiện
  một frame với `s < enter` không bao giờ được xác nhận hay xuất.
- `TENTATIVE → CONFIRMED` khi `S_t ≥ enter`. Không xuất ngược các frame tentative trước đó
  (online, nhân quả).
- Track CONFIRMED xuất box của frame t khi có candidate liên kết với `s ≥ keep` và `S_t ≥ keep`.
- Frame không có candidate liên kết là một lần miss; miss thứ `max_miss` liên tiếp → `CLOSED`
  (track tentative cũng bị đóng như vậy). Nếu liên kết tái dùng ID sau khi đã đóng, module mở một
  track temporal mới.
- Box trùng trong cùng frame mà liên kết gộp vào một track (`same_frame_duplicate`) không được xuất.
- Nhãn track: `argmax` tổng điểm `s` theo lớp, cộng dồn nhân quả từ đầu track đến frame t; hòa thì
  lấy lớp có `yolo_id` nhỏ hơn. Số lần đổi nhãn = số lần nhãn xuất thay đổi giữa hai frame xuất
  liên tiếp của cùng track.
- Box xuất mang nhãn track (không phải nhãn thô của frame) và điểm `S_t`; prediction thô không đổi.

### Chuỗi đánh giá A

- Chuỗi = các stem val liên tiếp trong cùng nhóm D-02; khoảng trống stem > 1 cắt chuỗi.
  Đây là quy tắc chính, khóa trước. Một biến thể chỉ để báo cáo cắt thêm ở các cạnh liền kề không
  nằm trong cùng chuỗi `CONTINUOUS_CANDIDATE` của WP16–WP21.

### Số đo và cách so sánh

- `metrics.operating_point(frames, 0)` trên box xuất (điểm `S_t`) cho recall phát hiện, FP/ảnh,
  precision; `metrics.match(class_aware=True)` cho recall đúng lớp. Cùng hàm cho baseline 0,20.
- Cùng ngân sách FP/ảnh: ngưỡng cố định cao nhất trên lưới 0,20…0,95 bước 0,01 có FP/ảnh không
  vượt FP/ảnh của temporal; so recall và recall đúng lớp.
- Theo lớp 7/32/41/46/10/12: GT support, hit đúng lớp baseline/temporal.
- GT bị mất do hysteresis: GT có match đúng lớp ở baseline nhưng không ở temporal (và ngược lại).
- Đổi nhãn theo GT track: GT track suy ra bằng chính hàm liên kết R1 trên box GT (cùng R12
  settings, theo lớp GT); đếm số lần lớp của prediction match (IoU ≥ 0,5, agnostic) đổi giữa hai
  frame có match liên tiếp của cùng GT track, cho baseline và temporal.
- CI bootstrap theo cặp: 1000 vòng, seed 20261018, lấy mẫu lại nhóm D-02; báo CI của hiệu
  temporal − baseline cho recall, recall đúng lớp, FP/ảnh.
- Lưới độ nhạy chỉ để báo cáo (không chọn tham số): `enter ∈ {0,25; 0,30; 0,35; 0,40; 0,50}`,
  `keep ∈ {0,10; 0,15; 0,20}`, `N ∈ {3; 5; 7}`, `max_miss ∈ {1; 2; 3}`, liên kết IoU
  `{0,30; 0,50}`; mỗi lần đổi một trục quanh điểm chính.

### Đánh giá B (chẩn đoán, DEMO_ONLY)

- Clip PHENIKAA Mini front `1fab7593…`, lấy mỗi 2 frame (103 frame) như chẩn đoán R2. Prediction
  đã lưu chỉ có ở conf 0,20, nên chạy lại D1 (`detector_d1_r3.D1Detector`, cùng checkpoint
  `5d5815a9…`) ở conf 0,001 chỉ trên clip này; ghi lệnh và hash; không train.
- Chấm theo đúng quy tắc scorer R2 (`scripts/score_review2_frame_diagnostic_r2.py`): chỉ 74 frame
  và hai mã W.205c/P.130 trong nhãn `b90710ee…`. Báo frame-level và event-level, số lần nhãn nhảy
  (đặc biệt P.130/P.131a). Clip không dùng để chọn tham số.

## §1a Erratum pre-registration — ghi 2026-11-04T13:5x+07:00, vẫn trước mọi kết quả temporal

§1 viết "ngưỡng cố định **cao nhất** … có FP/ảnh không vượt temporal" với lưới 0,20…0,95. Đó là
lỗi diễn đạt: ngưỡng cao nhất luôn thỏa ngân sách và cho recall thấp nhất, nên không phải phép
so công bằng. Quy tắc dùng thật: ngưỡng cố định **thấp nhất** trên lưới **0,05…0,95** bước 0,01
có FP/ảnh ≤ FP/ảnh của temporal (thấp nhất = recall cao nhất trong ngân sách). Ngoài ra báo
thêm chiều ngược: FP/ảnh của ngưỡng cố định có recall phát hiện ≥ recall temporal. Không đổi
tham số temporal nào.

## §2 Kiểm giả định chuỗi (VERIFIED, chạy trước khi viết module)

Nguồn: `sequence_audit` trong `docs/review/generated/temporal_threshold_r1_val.json`.

- 376 frame, 9 nhóm D-02; stem tăng nghiêm ngặt theo thứ tự loader; mỗi nhóm là một khối liền
  trong thứ tự val.
- 363 cặp liền kề cùng nhóm có bước stem = 1. Có 4 khoảng trống trong nhóm: C0001 `0059→0062`
  (0060/0061 quarantined) và C0020 `0711→0720`, `0729→0741`, `0750→0836` (xen kẽ với nhóm train
  C0019/C0021/C0022). Quy tắc chính cắt tại các khoảng trống này → 13 chuỗi.
- Chỉ 200/363 cặp nằm trong cùng một chuỗi `CONTINUOUS_CANDIDATE` đã rà ở WP16–WP21; 163 cặp
  còn lại có proxy `uncertain` (137) hoặc `adjacency_only` (26). Các rà soát WP16–21 là provisional
  PM review, không phải sequence truth.
- Chuyển động giữa hai frame lớn: trong 607 lần chuyển của GT, chỉ 197 (32%) có box cùng lớp ở
  frame sau với IoU ≥ 0,5; 336 (55%) với IoU ≥ 0,3; trung vị IoU 0,37; 28 lần không còn box cùng
  lớp.

**Kết luận:** giả định "stem liên tiếp trong nhóm là chuỗi thời gian" **đúng một phần**: thứ tự
và tính liền kề có thật trong phần lớn nhóm, nhưng đây là chuỗi **tần suất khung thấp**, không
phải video liên tục; một phần cặp chưa được xác nhận là cùng một lần quay. Hệ quả dự kiến: liên
kết bị phân mảnh, track ngắn, nên các tham số N và `max_miss` ít tác dụng (xem §3.6).

## §3 Kết quả đánh giá A — val DATASET01, 1 seed (VERIFIED artifact, chờ QA độc lập)

Output canonical `docs/review/generated/temporal_threshold_r1_val.json`, SHA-256
`05527c98e3a6ea47e337639d57e370620973ca2843bbd525b5be00e846b037f3`. Đây là val 1 seed, chuỗi suy
ra từ stem, val đã bị nhìn ở R1–R6; **không phải nghiệm thu D-05**, không phải holdout độc lập.

### 3.1 Bước 0 — baseline 0,20 tái tạo đúng

TP 547, FP 150, recall 0,8766, FP/ảnh 0,3989, đúng lớp 457/624 (script dừng nếu lệch).

### 3.2 Điểm chính (0,35 / 0,15 / N = 5 / max_miss = 2)

| | Fixed 0,20 | Temporal R1 | Δ |
| --- | ---: | ---: | ---: |
| GT định vị được (/624) | 547 | 519 | −28 |
| Recall phát hiện | 0,8766 | 0,8317 | −0,0449 |
| GT đúng lớp | 457 | 442 | −15 |
| Recall đúng lớp | 0,7324 | 0,7083 | −0,0240 |
| FP | 150 | 125 | −25 |
| FP/ảnh | 0,3989 | 0,3324 | −0,0665 |
| Precision | 0,7848 | 0,8059 | +0,0211 |

CI 95% bootstrap theo cặp (1000 vòng, seed 20261018, đơn vị nhóm D-02, chỉ 9 nhóm) cho hiệu
temporal − baseline: recall phát hiện [−0,101; +0,002]; recall đúng lớp [−0,061; +0,012];
FP/ảnh [−0,137; −0,020]. Chỉ khoảng FP/ảnh loại trừ 0; với 9 nhóm, CI này thô.

### 3.3 Cùng ngân sách FP/ảnh (quy tắc §1a)

- Ngưỡng cố định thấp nhất có FP/ảnh ≤ 0,3324 là **0,29**: FP 122, định vị 507, đúng lớp 425.
  Temporal ở FP 125: **+12 định vị, +17 đúng lớp**, đổi lại +3 FP.
- Ngưỡng cố định đạt recall phát hiện ≥ 0,8317 là **0,26**: FP 130, đúng lớp 433. Temporal:
  **−5 FP, +9 đúng lớp** ở cùng recall phát hiện.

Tức là trên val này, temporal nằm hơi phía trên đường cong ngưỡng cố định ở vùng FP ≈ 0,33/ảnh;
lợi thế nhỏ (≈ 1–3% GT) và chưa có CI riêng cho phép so cùng ngân sách.

### 3.4 Theo lớp (yolo_id), GT đúng lớp

| Lớp | Support | Fixed 0,20 | Temporal |
| --- | ---: | ---: | ---: |
| 7 P.123a | 111 | 66 | 63 |
| 10 P.130 | 48 | 48 | 48 |
| 12 R.415a | 65 | 60 | 58 |
| 32, 41, 46 | 0 | — | — |

Lớp 32/41/46 không có GT trong val R3, nên không có kết luận nào cho chúng.

### 3.5 GT bị mất / cứu được so với baseline, và đổi nhãn

- Mất do temporal: 38 GT định vị, 33 GT đúng lớp (nhiều nhất lớp 48: 11, lớp 7: 8, lớp 40: 4,
  lớp 12: 3). Nguyên nhân chính là frame đầu track còn TENTATIVE (100 candidate bị giữ ở trạng thái
  tentative) và phân mảnh track.
- Cứu được: 10 GT định vị (nhờ sàn giữ 0,15 < 0,20) và 18 GT đúng lớp (nhờ nhãn đa số).
- Đổi nhãn dọc GT track (GT track suy bằng chính linker R1): baseline 34 lần trên 77 track có
  ≥ 2 frame match (23 track có đổi, 0,44/track); temporal **12 lần trên 73 track (10 track,
  0,16/track)**.
- Thống kê chạy: 340 track, 266 được xác nhận, 644 box xuất (baseline 697), 1237 candidate dưới
  sàn, 18 box không hợp lệ; tổng thời gian hậu xử lý cục bộ ~14 ms cho 376 frame (không gồm
  inference).

### 3.6 Lưới độ nhạy — chỉ báo cáo, không dùng để chọn

| Biến thể | Định vị | Đúng lớp | FP |
| --- | ---: | ---: | ---: |
| enter 0,25 | 542 | 459 | 148 |
| enter 0,30 | 528 | 449 | 136 |
| **chính 0,35** | **519** | **442** | **125** |
| enter 0,40 | 505 | 432 | 117 |
| enter 0,50 | 492 | 421 | 96 |
| keep 0,10 | 524 | 452 | 140 |
| keep 0,20 | 506 | 428 | 120 |
| N = 3 hoặc 7 | 519 | 442 | 125 |
| max_miss 1 / 3 | 519 | 442 / 443 | 125 |
| link IoU 0,50 | 498 | 420 | 113 |
| Cắt chuỗi theo WP16–21 (176 chuỗi) | 502 | 424 | 119 |

N và `max_miss` gần như không ảnh hưởng, đúng như dự đoán ở §2 (track ngắn). Không có biến thể
nào vừa giữ recall baseline vừa giảm FP rõ rệt: `enter` chủ yếu dịch dọc đường đánh đổi.

## §4 Kết quả đánh giá B — Mini front clip, DEMO_ONLY (VERIFIED artifact, chờ QA độc lập)

Output `docs/review/generated/temporal_threshold_r1_mini.json`, SHA-256
`1c619fd59e6c8d18a2f3becf39e5f105908ec0eb1a6af15a7c0f2715c4d8eae3`. Không dùng để chọn tham số.

- Inference lại (chỉ clip `1fab7593…`, conf 0,001, mỗi 2 frame, MPS, `detector_d1_r3`):
  lệnh `uv run python scripts/evaluate_temporal_threshold_r1.py mini-infer`; 206 frame giải mã,
  103 frame lấy mẫu, 246 candidate. CSV SHA-256
  `67b714a7763a46afb5fa21467dcd8d6f930809b09527d5b66877104cbb9327c0`, manifest SHA-256
  `8145ef272917893d65b50ab9a1bec6ca7c0f14d0a59cab82d05265c8f0d80b8a` (thư mục ignored
  `data/processed/temporal_threshold_r1_mini/`). Lọc lại ≥ 0,20 cho đúng 54 dòng, 0 lệch
  (frame, mã) so với prediction upload đã pin `343e00c3…`.
- Baseline 0,20 tái tạo đúng số R2: P.130 TP/FP/FN 12/0/5, W.205c 0/0/16, 26 dự đoán mã khác
  chồng box đích, 11 ở vùng ignore.

| 74 frame, 2 mã | Fixed 0,20 | Temporal R1 |
| --- | ---: | ---: |
| P.130 TP/FP/FN (/17) | 12/0/5 | 15/1/2 |
| W.205c TP/FP/FN (/16) | 0/0/16 | 0/0/16 |
| P.131a chồng box đích | 7 | 3 |
| Mã khác chồng box đích (tổng) | 26 | 23 |
| Nhãn nhảy dọc event P.130 (P.130↔P.131a) | 6 | 4 |
| Event có ≥ 1 frame đúng mã | P.130 1/1, W.205c 0/1 | P.130 1/1, W.205c 0/1 |

FP P.130 duy nhất của temporal là loại "trùng / sai lớp trên box đích". W.205c vẫn sai hoàn toàn:
baseline gán 11 W.224 + 5 W.207; temporal **ổn định hóa thành 16/16 W.224** — tức temporal làm
nhãn sai nhất quán hơn chứ không sửa được. Chỉ có 2 event GT trong một cảnh; đây là chẩn đoán,
không phải số đo video.

## §5 Diễn giải và giới hạn

- VERIFIED: ở điểm chính, temporal giảm FP 150 → 125 và đổi nhãn dọc GT track 34 → 12, nhưng
  mất 28 GT định vị và 15 GT đúng lớp so với 0,20. Ở cùng ngân sách FP, nó tốt hơn ngưỡng cố
  định một chút (+9 đến +17 GT đúng lớp).
- VERIFIED: chuỗi val là chuỗi thưa, chỉ đúng một phần là video; mọi kết luận về "video" từ val
  là gián tiếp.
- UNKNOWN: hiệu quả trên video liên tục 10 fps có GT đầy đủ; hành vi với lớp 32/41/46; độ ổn
  định qua seed khác; tác động đến D-05 (chưa đánh giá, không đổi).
- PROPOSAL: nếu QA độc lập PASS, có thể thêm một công tắc **experimental, tắt mặc định** trong
  app Review 2 (chỉ hiển thị), ghi rõ không phải nghiệm thu. Không đề xuất thay thế 0,20 làm
  mặc định trên cơ sở val này.
- Gói này không bật gì trong app, không train, không đổi D-05; `sealed_test_accessed=false` trong
  cả hai JSON.

## §6 File và hash tại thời điểm bàn giao

| File | SHA-256 |
| --- | --- |
| `src/cpv301_autodrive/temporal_threshold.py` | `a519066abc6106ae0e729d09d846847997a1d9b584efc769c88d4b03308e9fdc` |
| `scripts/evaluate_temporal_threshold_r1.py` | `b6f17073c7a27cb38154affc516971241f43245fafd39b57499d43b70dd9881d` |
| `tests/test_temporal_threshold_r1.py` | `655254766cd4c6bb69a8f6470531817c26061fc4f48d1581d9d8611b0394b2c9` |
| `docs/review/generated/temporal_threshold_r1_val.json` | `05527c98e3a6ea47e337639d57e370620973ca2843bbd525b5be00e846b037f3` |
| `docs/review/generated/temporal_threshold_r1_mini.json` | `1c619fd59e6c8d18a2f3becf39e5f105908ec0eb1a6af15a7c0f2715c4d8eae3` |

Input chính: prediction val `87884c53…c893`, roster nhãn R3 `dc72ebd9…`, split
`8e197d9c…`, checkpoint `5d5815a9…`, class map `7cda296a…`, nhãn Mini R2 `b90710ee…`, clip
`1fab7593…` (đầy đủ trong `inputs_sha256` và `source_sha256` của từng JSON).

Kiểm tra đã chạy: `uv run ruff check src tests scripts` PASS; `uv run pytest -q
tests/test_temporal_threshold_r1.py tests/test_review2_temporal_overlay_r2.py` 17 passed;
`uv lock --check` PASS; `graft build . && graft check .` in sync. Ghi chú quy trình: sau khi
`ruff format` đổi định dạng hai file mới, hai JSON (chưa QA, do phiên này tạo) được tạo lại; nội
dung trùng hoàn toàn với lần chạy trước ngoài hash source và thời gian hậu xử lý.

Trạng thái: **QA độc lập PENDING** — phiên này không tự ghi PASS.

## §7 Independent QA và đính chính thời gian §1a — 2026-11-04

- QA độc lập: `docs/review/temporal_threshold_r1_independent_qa_record.md` (SHA-256
  `f6eddb296e166d09efedfcde94437a1288106e67478437c9fe33b5cdc040fbc9`) ghi **PASS cho chẩn đoán
  offline, chỉ trên val, tái lập được**; C1–C8 PASS, C6 kèm giới hạn. PASS này không phải nghiệm
  thu D-05 và không cho phép bật trong app.
- Đính chính (lỗi C6 của QA): nhãn thời gian "13:5x" ở tiêu đề §1a là placeholder do tác giả gõ,
  không phải thời điểm đo được. Thứ tự thực tế, theo nhật ký phiên tác giả: §1a được append sau
  khi viết module và test, và trước lần dry-run đầu tiên của đánh giá A (lần đầu sinh ra số
  temporal). Phút chính xác không được ghi lại, và không có timestamp mật mã. §1a giữ nguyên, không
  sửa tại chỗ.
