# DATASET01 — dataset card (M0-WP37, G0.9)

Trạng thái: `WP37_AWAITING_QA_REVIEW` · Boundary: `DATASET_CARD_DOCUMENTATION_ONLY_NO_LABEL_CHANGE_NO_TRAINING`

Card này thay phần "dataset card" của `docs/dataset01_audit.md` (WP1, giữ nguyên làm hồ sơ audit
kỹ thuật). Mỗi con số được sinh lại bởi `scripts/build_wp37_dataset_card.py verify`. Nhãn phân loại
thông tin: **VERIFIED** (đo/đối chiếu được), **OWNER DECISION** (đã duyệt), **UNKNOWN** (không có
nguồn).

## 1. Mục đích và giới hạn sử dụng

- Dùng cho: huấn luyện và đánh giá detector/classifier biển báo Việt Nam trong **mô phỏng** hỗ trợ
  lái của dự án CPV301 (nghiên cứu, học tập).
- Không dùng cho: điều khiển xe thật, tuyên bố an toàn, phát hành công khai ảnh/nhãn gốc.
- Hành vi tự động trong mô phỏng chỉ được dùng cho lớp có test niêm phong; lớp chỉ train hiển thị
  "chưa kiểm chứng" (D-04).

## 2. Nguồn, license, ghi công — OWNER DECISION (D-01)

- Ghi công bắt buộc: DATASET01 = huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign@d869116 (creator: Data Palpating Team), CC-BY-SA, archive SHA-256 052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76.
- License: metadata ghi CC-BY-SA 3.0, mô tả ghi 4.0; chủ sở hữu ảnh gốc UNKNOWN. Owner chấp nhận
  rủi ro (2026-10-17) và áp điều khoản chặt hơn: share-alike CC-BY-SA 4.0 cho mọi bản phái sinh
  được phân phối, không phân phối lại ảnh/nhãn gốc, coi trọng số model có thể chịu share-alike,
  mở lại D-01 nếu có phản hồi/khiếu nại (`docs/review/d01_owner_decision_record.md`).
- Dataset gốc có liên kết tới một repo augmentation (blur/noise/brightness/contrast); không có
  bằng chứng ảnh nào là bản tăng cường của ảnh khác ngoài các cặp gần trùng đã gộp nhóm (WP32).

## 3. Thành phần — VERIFIED

- 3216 ảnh và nhãn YOLO; stem 0248 cách ly (G0.4) → 3215 ảnh có
  nhóm D-02; 24 ảnh âm có biển chưa gán nhãn bị cách ly → **3191 ảnh dùng được**.
- Nhãn huấn luyện chỉ lấy từ bộ dẫn xuất WP33 (`wp33_derived_boxes.csv`), không dùng class id gốc:
  8290 box train-eligible trong 54 lớp; không train: EXCLUDED (raw class 18 is a mislabelled height-limit sign; value unreadable): 1; EXCLUDED (sign cut off at image edge): 1; EXCLUDED (very blurry): 2; QUARANTINED (G0.4 quarantined stem): 2; UNKNOWN_EVAL_ONLY (class 31 routed to UNKNOWN): 38.
- Ảnh tăng cường WP35: 1800 ảnh biến đổi từ frame thật, **chỉ dùng cho train**, không phải
  instance mới (cùng biển vật lý với ảnh nguồn).

## 4. Điều kiện chụp — VERIFIED proxy / UNKNOWN metadata

- EXIF: 0 ảnh; GPS: 0 ảnh. Địa điểm, ngày giờ, thời tiết, thiết
  bị: **UNKNOWN**. Ảnh là camera hành trình/cầm tay trên đường đô thị có xe máy dày đặc (quan sát
  của reviewer khi duyệt nhóm, không phải metadata).
- Độ sáng = trung bình luminance trên ảnh decode nháp 480×270 xám; bucket
  DARK < 60 ≤ DIM < 100 ≤ BRIGHT. Độ nét = trung bình FIND_EDGES (proxy, không phải đo blur chuẩn).
  Quartile ghi dạng Q1 / median / Q3.

| Split | Ảnh | 1920x1080 | 540x960 | 960x540 | DARK | DIM | BRIGHT | Luma Q1/med/Q3 | Edge Q1/med/Q3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| train | 1912 | 671 | 0 | 1241 | 0 | 366 | 1546 | 103.6 / 118.1 / 131.6 | 19.7 / 23.2 / 27.6 |
| val | 376 | 0 | 39 | 337 | 7 | 132 | 237 | 94.8 / 106.3 / 124.7 | 20.4 / 29.4 / 33.5 |
| test | 903 | 134 | 0 | 769 | 0 | 35 | 868 | 120.3 / 130.0 / 143.1 | 22.3 / 24.0 / 29.5 |

- Ảnh DARK dùng được: 7 (1843, 1844, 1845, 1848, 1849, 1850, 1851). Không có
  tập ban đêm riêng: hiệu năng ban đêm/mưa lớn là **UNKNOWN**.
- **Lệch điều kiện chụp giữa các split** (hệ quả của chia theo nhóm): 1920x1080 chỉ có ở train, test; 540x960 chỉ có ở val; DARK chỉ có ở val.
  Val tối hơn train/test (median luma 106.3 so với train
  118.1, test 130.0). Khi so sánh val với test phải báo cáo
  theo độ phân giải; kết quả trên ảnh dọc và ảnh tối chỉ có ở val, không có test niêm phong.
- Chi tiết từng ảnh: `docs/review/generated/wp37_capture_conditions.csv`.

## 5. Nhóm D-02 và nguồn gốc nhóm — OWNER DECISION (D-02)

Chuỗi: cạnh ứng viên WP5 → review cạnh WP7–WP30-R1 (AI review hai lượt, QA độc lập) → nối khối
WP32 → đề xuất nhóm WP31-R2 → owner duyệt D02-P1 (54 nhóm capture, 2026-10-17). Giới hạn: không có
metadata của tác giả; nhóm là suy luận thị giác, chưa chứng minh không rò rỉ.

| Nhóm | Ảnh | Stem | Split | Độ phân giải | Luma median | Lớp | Box train-eligible | WP35 |
| --- | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |
| D02-C0001 | 71 | 0001–0071 | val | 960x540:71 | 106.2 | 1 | 69 | 0 |
| D02-C0002 | 120 | 0072–0413 | train | 960x540:120 | 109.3 | 1 | 219 | 0 |
| D02-C0003 | 9 | 0104–0112 | test | 960x540:9 | 124.5 | 2 | 18 | 0 |
| D02-C0004 | 12 | 0123–0134 | train | 960x540:12 | 138.2 | 1 | 12 | 0 |
| D02-C0005 | 41 | 0145–0185 | test | 960x540:41 | 113.8 | 6 | 140 | 0 |
| D02-C0006 | 15 | 0196–0210 | test | 960x540:15 | 133.9 | 2 | 16 | 0 |
| D02-C0007 | 21 | 0221–0241 | train | 960x540:21 | 136.6 | 1 | 21 | 0 |
| D02-C0008 | 17 | 0252–0268 | train | 960x540:17 | 136.9 | 2 | 28 | 0 |
| D02-C0009 | 68 | 0279–0346 | val | 960x540:68 | 139.7 | 4 | 155 | 0 |
| D02-C0010 | 21 | 0357–0377 | train | 960x540:21 | 126.7 | 2 | 25 | 150 |
| D02-C0011 | 17 | 0388–0404 | val | 960x540:17 | 115.8 | 1 | 17 | 0 |
| D02-C0012 | 21 | 0414–0434 | test | 960x540:21 | 113.7 | 2 | 41 | 0 |
| D02-C0013 | 29 | 0435–0463 | train | 960x540:29 | 124.0 | 2 | 58 | 150 |
| D02-C0014 | 87 | 0464–0550 | train | 960x540:87 | 120.1 | 8 | 222 | 300 |
| D02-C0015 | 44 | 0551–0594 | train | 960x540:44 | 125.9 | 5 | 273 | 150 |
| D02-C0016 | 10 | 0595–0604 | train | 960x540:10 | 137.7 | 2 | 19 | 150 |
| D02-C0017 | 40 | 0605–0644 | test | 960x540:40 | 126.7 | 4 | 103 | 0 |
| D02-C0018 | 25 | 0645–0669 | test | 960x540:25 | 125.2 | 2 | 47 | 0 |
| D02-C0019 | 45 | 0670–0719 | train | 960x540:45 | 115.3 | 7 | 104 | 150 |
| D02-C0020 | 35 | 0707–0845 | val | 960x540:35 | 91.3 | 2 | 64 | 0 |
| D02-C0021 | 11 | 0730–0740 | train | 960x540:11 | 119.0 | 2 | 22 | 150 |
| D02-C0022 | 68 | 0751–0818 | train | 960x540:68 | 131.6 | 11 | 511 | 300 |
| D02-C0023 | 17 | 0819–0835 | train | 960x540:17 | 118.7 | 2 | 32 | 0 |
| D02-C0024 | 16 | 0846–0861 | test | 960x540:16 | 102.2 | 3 | 36 | 0 |
| D02-C0025 | 66 | 0862–1318 | train | 960x540:66 | 97.3 | 1 | 66 | 0 |
| D02-C0026 | 38 | 0872–0909 | train | 960x540:38 | 81.0 | 2 | 51 | 0 |
| D02-C0027 | 190 | 0920–1109 | train | 960x540:190 | 112.1 | 10 | 689 | 0 |
| D02-C0028 | 2 | 1120–1121 | test | 960x540:2 | 95.0 | 1 | 1 | 0 |
| D02-C0029 | 3 | 1122–1124 | train | 960x540:3 | 134.6 | 1 | 3 | 0 |
| D02-C0030 | 63 | 1145–1207 | test | 960x540:63 | 115.0 | 8 | 223 | 0 |
| D02-C0031 | 38 | 1208–1245 | val | 960x540:38 | 100.2 | 6 | 91 | 0 |
| D02-C0032 | 41 | 1256–1296 | test | 960x540:41 | 141.7 | 6 | 97 | 0 |
| D02-C0033 | 16 | 1297–1312 | train | 960x540:16 | 120.0 | 1 | 14 | 0 |
| D02-C0034 | 39 | 1319–1357 | val | 540x960:39 | 123.8 | 2 | 29 | 0 |
| D02-C0035 | 44 | 1358–1479 | test | 960x540:44 | 109.6 | 3 | 132 | 0 |
| D02-C0036 | 65 | 1362–1426 | train | 960x540:65 | 124.2 | 7 | 140 | 0 |
| D02-C0037 | 13 | 1437–1449 | train | 960x540:13 | 124.3 | 2 | 25 | 0 |
| D02-C0038 | 226 | 1480–1985 | train | 960x540:226 | 130.6 | 11 | 453 | 0 |
| D02-C0039 | 18 | 1519–1536 | train | 960x540:18 | 147.7 | 3 | 50 | 0 |
| D02-C0040 | 75 | 1547–1621 | train | 960x540:75 | 113.8 | 4 | 203 | 0 |
| D02-C0041 | 49 | 1632–1680 | test | 960x540:49 | 120.4 | 2 | 57 | 0 |
| D02-C0042 | 13 | 1716–1728 | val | 960x540:13 | 125.3 | 2 | 25 | 0 |
| D02-C0043 | 28 | 1739–1766 | train | 960x540:28 | 105.2 | 2 | 34 | 0 |
| D02-C0044 | 83 | 1777–1859 | val | 960x540:83 | 92.1 | 5 | 96 | 0 |
| D02-C0045 | 14 | 1938–1951 | val | 960x540:14 | 127.0 | 1 | 14 | 0 |
| D02-C0046 | 72 | 1986–2057 | test | 960x540:72 | 125.6 | 5 | 92 | 0 |
| D02-C0047 | 10 | 2058–2067 | train | 960x540:10 | 138.9 | 2 | 20 | 0 |
| D02-C0048 | 411 | 2068–2478 | test | 1920x1080:75 960x540:336 | 141.6 | 14 | 1090 | 0 |
| D02-C0049 | 115 | 2479–2593 | train | 1920x1080:115 | 127.2 | 9 | 366 | 150 |
| D02-C0050 | 23 | 2594–2616 | test | 1920x1080:23 | 97.1 | 5 | 102 | 0 |
| D02-C0051 | 513 | 2617–3129 | train | 1920x1080:513 | 101.8 | 21 | 1668 | 0 |
| D02-C0052 | 36 | 3130–3165 | test | 1920x1080:36 | 122.5 | 2 | 120 | 0 |
| D02-C0053 | 25 | 3166–3190 | train | 1920x1080:25 | 182.1 | 3 | 35 | 150 |
| D02-C0054 | 26 | 3191–3216 | train | 1920x1080:26 | 112.3 | 2 | 52 | 0 |

## 6. Split — OWNER DECISION (G0.7, WP36-R1)

- Ảnh dùng được: train 1912 / val 376 /
  test 903; không nhóm nào nằm ở hai split.
- Hash danh sách (sha256 của stem đã sort nối bằng `\n`): train `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`,
  val `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`, **test niêm phong** `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`.
- Test chỉ dùng trong lần đánh giá cuối có log; loader kiểm hash + cột `use` (`g07_owner_acceptance_record.md`).
- Lớp không có test niêm phong (22): 1, 15, 16:2.0, 16:2.2, 16:2.5, 21, 24, 27, 29, 33, 35, 36, 37, 38, 42, 43:2.5, 43:2.7, 44, 47, 48, 49, 51.
- Lớp có test nhưng không được dùng để chọn model/chỉnh ngưỡng (không có val): 9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50.

## 7. Lớp (D-03 taxonomy, D-04 quyết định, phân bố box theo split)

| Key | Mã QCVN | Tên | Vai trò | Box train-eligible | D-04 | Box train/val/test | Test niêm phong | Dùng tuning | WP35 |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | ---: |
| 0 | W.224 | Đường người đi bộ cắt ngang | CLASS | 312 | TRAIN_VAL_TEST | 204/13/95 | có | có | 0 |
| 1 | W.205c | Đường giao nhau (nhánh phải) | CLASS | 22 | TRAIN_WITH_ENRICHMENT | 22/0/0 | không | không | 150 |
| 2 | P.102 | Cấm đi ngược chiều | CLASS | 470 | TRAIN_VAL_TEST | 371/5/94 | có | có | 0 |
| 3 | R.302a | Phải đi vòng sang bên phải | CLASS | 454 | TRAIN_VAL_TEST | 370/5/79 | có | có | 0 |
| 4 | W.205a | Đường giao nhau | CLASS | 33 | TRAIN_VAL_TEST | 12/12/9 | có | có | 0 |
| 5 | W.207 | Giao nhau với đường không ưu tiên | CLASS | 256 | TRAIN_VAL_TEST | 128/14/114 | có | có | 0 |
| 6 | W.201a | Chỗ ngoặt nguy hiểm vòng bên trái | CLASS | 182 | TRAIN_VAL_TEST | 145/22/15 | có | có | 0 |
| 7 | P.123a | Cấm rẽ trái | CLASS | 247 | TRAIN_VAL_TEST | 83/111/53 | có | có | 0 |
| 8 | I.434a | Bến xe buýt | CLASS | 213 | TRAIN_VAL_TEST | 150/51/12 | có | có | 0 |
| 9 | R.303 | Nơi giao nhau chạy theo vòng xuyến | CLASS | 43 | TRAIN_AND_TEST_NO_VAL | 14/0/29 | có | không | 0 |
| 10 | P.130 | Cấm dừng xe và đỗ xe | CLASS | 1071 | TRAIN_VAL_TEST | 637/21/413 | có | có | 0 |
| 11 | I.409 | Chỗ quay xe | CLASS | 26 | TRAIN_AND_TEST_NO_VAL | 21/0/5 | có | không | 0 |
| 12 | R.415a | Biển gộp làn đường theo phương tiện | CLASS | 280 | TRAIN_VAL_TEST | 150/57/73 | có | có | 0 |
| 13 | W.245a | Đi chậm | CLASS | 372 | TRAIN_VAL_TEST | 224/17/131 | có | có | 0 |
| 14 | P.106a | Cấm xe ô tô tải | CLASS | 85 | TRAIN_VAL_TEST | 9/3/73 | có | có | 0 |
| 15 | W.203c | Đường bị thu hẹp về phía phải | CLASS | 29 | TRAIN_WITH_ENRICHMENT | 29/0/0 | không | không | 150 |
| 16:2.0 | P.117*2.0 | Hạn chế chiều cao 2,0 m | CLASS | 43 | TRAIN_ONLY_UNVERIFIED | 43/0/0 | không | không | 0 |
| 16:2.2 | P.117*2.2 | Hạn chế chiều cao 2,2 m | CLASS | 18 | TRAIN_WITH_ENRICHMENT | 18/0/0 | không | không | 150 |
| 16:2.5 | P.117*2.5 | Hạn chế chiều cao 2,5 m | CLASS | 9 | TRAIN_WITH_ENRICHMENT | 9/0/0 | không | không | 150 |
| 16:UNREADABLE | P.117 | Hạn chế chiều cao (không rõ giá trị) | EXCLUDED | 0 | — | — | không | không | 0 |
| 17 | P.124a | Cấm quay đầu xe | CLASS | 105 | TRAIN_VAL_TEST | 95/0/10 | có | không | 0 |
| 18 | P.107 | Cấm xe ô tô khách và xe ô tô tải | CLASS | 213 | TRAIN_VAL_TEST | 151/0/62 | có | không | 0 |
| 19 | P.124d | Cấm rẽ phải và quay đầu xe | CLASS | 29 | TRAIN_VAL_TEST | 16/0/13 | có | không | 0 |
| 20 | P.103a | Cấm xe ô tô | CLASS | 52 | TRAIN_AND_TEST_NO_VAL | 30/0/22 | có | không | 0 |
| 21 | W.203b | Đường bị thu hẹp về phía trái | CLASS | 11 | TRAIN_WITH_ENRICHMENT | 11/0/0 | không | không | 150 |
| 22 | W.221b | Đường có gồ giảm tốc | CLASS | 131 | TRAIN_VAL_TEST | 100/0/31 | có | không | 0 |
| 23 | P.111a+P.111b | Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép) | CLASS | 465 | TRAIN_VAL_TEST | 264/16/185 | có | có | 0 |
| 24 | P.129 | Kiểm tra | CLASS | 56 | TRAIN_ONLY_UNVERIFIED | 56/0/0 | không | không | 0 |
| 25 | S.505a | Biển phụ loại xe: xe máy | CLASS | 25 | TRAIN_AND_TEST_NO_VAL | 7/0/18 | có | không | 0 |
| 26 | W.246a | Chú ý chướng ngại vật - Vòng tránh ra hai bên | CLASS | 80 | TRAIN_VAL_TEST | 47/14/19 | có | có | 0 |
| 27 | W.225 | Trẻ em | CLASS | 36 | TRAIN_ONLY_UNVERIFIED | 36/0/0 | không | không | 0 |
| 28 | S.505a | Biển phụ loại xe: xe tải và xe công | CLASS | 27 | TRAIN_AND_TEST_NO_VAL | 26/0/1 | có | không | 0 |
| 29 | P.104 | Cấm xe máy | CLASS | 45 | TRAIN_ONLY_UNVERIFIED | 45/0/0 | không | không | 0 |
| 30 | S.505a | Biển phụ loại xe: xe tải | CLASS | 138 | TRAIN_VAL_TEST | 93/0/45 | có | không | 0 |
| 32 | P.123b | Cấm rẽ phải | CLASS | 186 | TRAIN_VAL_TEST | 86/29/71 | có | có | 0 |
| 33 | W.202b | Nhiều chỗ ngoặt nguy hiểm liên tiếp, đầu tiên sang phải | CLASS | 19 | TRAIN_WITH_ENRICHMENT | 19/0/0 | không | không | 150 |
| 34 | P.108a | Cấm xe sơ-mi rơ-moóc | CLASS | 82 | TRAIN_VAL_TEST | 23/37/22 | có | có | 0 |
| 35 | P.137 | Cấm rẽ trái, rẽ phải | CLASS | 87 | TRAIN_ONLY_UNVERIFIED | 87/0/0 | không | không | 0 |
| 36 | P.139 | Cấm đi thẳng, rẽ phải | CLASS | 75 | TRAIN_ONLY_UNVERIFIED | 75/0/0 | không | không | 0 |
| 37 | W.205b | Đường giao nhau (nhánh trái) | CLASS | 47 | TRAIN_ONLY_UNVERIFIED | 47/0/0 | không | không | 0 |
| 38 | P.127 | Tốc độ tối đa cho phép (50 km/h) | CLASS | 189 | TRAIN_ONLY_UNVERIFIED | 189/0/0 | không | không | 0 |
| 39 | P.127 | Tốc độ tối đa cho phép (60 km/h) | CLASS | 459 | TRAIN_VAL_TEST | 245/8/206 | có | có | 0 |
| 40 | P.127 | Tốc độ tối đa cho phép (80 km/h) | CLASS | 210 | TRAIN_VAL_TEST | 67/0/143 | có | không | 0 |
| 41 | P.127 | Tốc độ tối đa cho phép (40 km/h) | CLASS | 275 | TRAIN_VAL_TEST | 171/21/83 | có | có | 0 |
| 42 | R.301e | Hướng đi phải theo - rẽ trái | CLASS | 21 | TRAIN_WITH_ENRICHMENT | 21/0/0 | không | không | 150 |
| 43:2.5 | W.239b*2.5 | Chiều cao tĩnh không thực tế 2,5 m | CLASS | 22 | TRAIN_WITH_ENRICHMENT | 22/0/0 | không | không | 150 |
| 43:2.7 | W.239b*2.7 | Chiều cao tĩnh không thực tế 2,7 m | CLASS | 5 | TRAIN_WITH_ENRICHMENT | 5/0/0 | không | không | 150 |
| 44 | W.233 | Nguy hiểm khác | CLASS | 3 | TRAIN_WITH_ENRICHMENT | 3/0/0 | không | không | 150 |
| 45 | I.407a | Đường một chiều | CLASS | 195 | TRAIN_VAL_TEST | 125/0/70 | có | không | 0 |
| 46 | P.131a | Cấm đỗ xe | CLASS | 435 | TRAIN_VAL_TEST | 220/104/111 | có | có | 0 |
| 47 | P.124b | Cấm ô tô quay đầu xe | CLASS | 16 | TRAIN_WITH_ENRICHMENT | 16/0/0 | không | không | 150 |
| 48 | W.210 | Giao nhau với đường sắt có rào chắn | CLASS | 41 | TRAIN_ONLY_UNVERIFIED | 41/0/0 | không | không | 0 |
| 49 | P.124c | Cấm rẽ trái và quay đầu xe | CLASS | 219 | TRAIN_ONLY_UNVERIFIED | 219/0/0 | không | không | 0 |
| 50 | W.201b | Chỗ ngoặt nguy hiểm vòng bên phải | CLASS | 121 | TRAIN_VAL_TEST | 113/0/8 | có | không | 0 |
| 51 | W.246c | Chú ý chướng ngại vật - Vòng tránh sang bên phải | CLASS | 5 | TRAIN_WITH_ENRICHMENT | 5/0/0 | không | không | 150 |
| UNKNOWN | UNKNOWN | Ngoài taxonomy | UNKNOWN_EVAL_ONLY | 0 | — | — | không | không | 0 |

## 8. Rủi ro và giới hạn đã biết

- License/ownership chưa được tác giả xác nhận (D-01 rủi ro đã chấp nhận).
- Nhóm D-02 do AI suy luận; cùng một biển vật lý có thể xuất hiện ở hai nhóm → điểm test có thể lạc quan.
- Một địa bàn/khoảng thời gian không rõ; không có dữ liệu độc lập từ nơi khác → chưa có claim triển khai.
- Box nhỏ chiếm đa số (WP1: 3.088 box có diện tích < 0,1 % ảnh).
- Val nhỏ (376 ảnh) và lệch điều kiện chụp so với train/test (mục 4); chỉ dùng metric gộp để chọn model.
- Ảnh tăng cường WP35 không thêm instance mới; box sau xoay lỏng ~8 % (WP35 QA).

## 9. Kiểm chứng

```bash
uv run python scripts/build_wp37_dataset_card.py verify --repo-root . --raw-root data/raw/DATASET01/staging/052bc980a7206f8d/raw
uv run python scripts/build_wp36_r1_group_split.py verify --repo-root .
```

## 10. G0.9 checklist

| Hạng mục | Nguồn | Trạng thái |
| --- | --- | --- |
| Nguồn, hash, staging | WP1 audit | VERIFIED |
| License + ghi công | D-01 | OWNER DECISION |
| Điều kiện chụp | WP37 capture proxy | VERIFIED proxy; metadata UNKNOWN |
| Taxonomy + nhãn dẫn xuất | D-03, WP33 | OWNER DECISION + QA PASS |
| Group lineage | D-02, WP31-R2, WP37 lineage | OWNER DECISION + QA PASS |
| Lớp hiếm / trạng thái đánh giá | D-04 part 1+2 | OWNER DECISION |
| Split + niêm phong test | G0.7, WP36-R1 | OWNER DECISION + QA PASS |
