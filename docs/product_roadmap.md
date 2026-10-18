# CPV301 AutoDrive — Product roadmap

Ngày kiểm tra gần nhất: 2026-10-16 (Asia/Ho_Chi_Minh).

Mục tiêu dài hạn là một pipeline nghiên cứu có thể tái lập cho biển báo Việt Nam và một
webapp mô phỏng phản ứng của xe. Mọi đầu ra hành vi hiện tại chỉ là mô phỏng; dự án chưa có
bằng chứng đủ để triển khai ngoài đường hoặc điều khiển xe thật.

## Quy ước trạng thái bằng chứng

- **VERIFIED**: đã đọc lại từ checkout/artifact hiện tại bằng lệnh cụ thể.
- **PROPOSAL**: thiết kế hoặc công việc chưa triển khai/chưa được kiểm chứng.
- **UNKNOWN/BLOCKED**: thiếu bằng chứng hoặc quyết định bắt buộc; không được tự suy diễn.

## Ranh giới hệ thống và hai track đánh giá

```text
Camera/frame
    -> detector tìm bounding box                 [track detection]
    -> crop ROI theo bounding box
    -> classifier gán taxonomy cho ROI           [track classification]
    -> temporal voting/tracking                   [future]
    -> behavior planner + vehicle simulation      [simulation only]
    -> Streamlit dashboard
```

**VERIFIED:** runtime hiện tại chỉ có classifier ảnh crop RGB `32x32`, 43 lớp GTSRB, cùng
shell UI/behavior mô phỏng. Detector toàn cảnh, tracking, temporal voting, lane/PID và CARLA
chưa được nối vào runtime.

**Quyết định bắt buộc:** không đưa nguyên frame `960x540` vào classifier `32x32`; detector
phải được đánh giá riêng trước khi nối `detector -> crop -> classifier`.

## Snapshot audit hiện tại

### E0 — baseline GTSRB hiện hữu

| Hạng mục | Bằng chứng | Trạng thái |
| --- | --- | --- |
| Model | `models/VGG16_model.h5`; SHA-256 `745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565` | VERIFIED |
| Kiến trúc | CNN tuần tự nhỏ lấy cảm hứng từ VGG; không phải `keras.applications.VGG16` | VERIFIED |
| Contract | RGB `32x32x3`, chia pixel cho 255, Softmax 43 lớp GTSRB | VERIFIED |
| GTSRB holdout | 12.630 crop; accuracy `0.8682`, macro-F1 `0.7921`, balanced accuracy `0.7949` | VERIFIED |
| Lỗi confidence cao | 324/1.665 lỗi có confidence `>=0.90` | VERIFIED |
| Training defect | `horizontal_flip=True` làm sai ngữ nghĩa trái/phải | VERIFIED |
| Phạm vi | Chỉ là closed-set GTSRB crop; không chứng minh hiệu năng Việt Nam/OOD/detection | VERIFIED |

E0 được đóng băng làm control; manifest kiểm soát nằm tại
`results/experiments/E0_GTSRB_baseline/manifest.json`. Không ghi đè model hoặc các artifact
evaluation hiện có. Mọi run mới phải có experiment ID và đường dẫn mới.

### Candidate DATASET01 ngoài checkout

Nguồn đang được audit read-only:
`/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/FALL 2026 KỲ 4/CPV301/Data/DATASET01/archive.zip`.

| Hạng mục | Readback 2026-10-10 | Trạng thái |
| --- | --- | --- |
| Archive | SHA-256 `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76`; `unzip -tq` không lỗi | VERIFIED |
| Nội dung ZIP | 3.216 JPG + 3.216 label YOLO | VERIFIED |
| Bản giải nén source hiện có | 1.046 ảnh + 3.216 label; được giữ nguyên | VERIFIED |
| Immutable staging | `staging/052bc980a7206f8d/raw`; 6.437 ZIP members khớp byte/hash | VERIFIED |
| Taxonomy | 52 class ID quan sát được; 8.334 bounding box | VERIFIED |
| Negative/non-sign | 25 label rỗng; không nằm trong split hiện tại | VERIFIED |
| Imbalance | lớp 44 có 3 box; lớp 10 có 1.071 box | VERIFIED |
| Split hiện tại | 2.552 train + 639 test; không có validation | VERIFIED |
| Leakage proxy | 1.031/3.178 cặp filename số liên tiếp bị chia chéo train/test (`32,44%`) | VERIFIED RISK |
| Text format | class/label text dùng CRLF | VERIFIED |
| Provenance/license | Exact files khớp HF `thanhhiepvos/vietnam_traffic_sign@d869116`; license metadata 3.0 mâu thuẫn card prose 4.0 | PARTIAL/BLOCKED |
| Group identity | Chưa có mapping video/scene/biển vật lý | UNKNOWN/BLOCKED |
| GTSRB↔Việt Nam | Chưa có taxonomy mapping đã duyệt | UNKNOWN/BLOCKED |

Các filename liên tiếp chỉ là proxy cho tương quan frame/scene; chúng không thay thế group ID
thật. Split hiện tại không được dùng làm independent holdout cho tới khi Gate 0 hoàn tất.

## Gate 0 — Data contract (**MỞ** ngày 2026-10-18: 9/9 PASS + D-05 đã duyệt; mở cho track detector VN)

Không được train E1–E4 hoặc detector trước khi toàn bộ tiêu chí sau đạt **PASS**.

| ID | Deliverable/acceptance criteria | Trạng thái |
| --- | --- | --- |
| G0.1 | Source candidate được exact-hash. License 3.0/4.0 vẫn mâu thuẫn và chủ sở hữu ảnh chưa rõ; owner chấp nhận rủi ro ngày 2026-10-17 với điều kiện CC-BY-SA chặt nhất (ghi công, share-alike 4.0, không phát tán ảnh gốc ra ngoài dự án) — `docs/review/d01_owner_decision_record.md` | PASS — D-01 OWNER RISK ACCEPTED |
| G0.2 | Hash-addressed raw staging hoàn chỉnh; source snapshot trước/sau không đổi | PASS |
| G0.3 | 3.216 ảnh + 3.216 label, pairing 1:1, decode 100%, raw bytes khớp ZIP | PASS |
| G0.4 | Owner đã chọn quarantine toàn bộ stem 0248; WP10 overlay/registry fail-closed đã QA PASS với 0 blocker, raw giữ nguyên | PASS — QA-M0-WP10 |
| G0.5 | Owner đã quyết định đủ 52 lớp (D-03 part 1 + part 2 + bản sửa đổi, 2026-10-17); bộ nhãn dẫn xuất WP33 (54 lớp train, lớp 31 → UNKNOWN chỉ để đánh giá, 4 box không đọc được bị loại) đã independent QA PASS (`docs/review/wp33_independent_qa_record.md`). Raw label giữ nguyên | PASS — D-03 OWNER APPROVED / WP33 QA PASS |
| G0.6 | Mỗi ảnh có `group_id`: owner đã duyệt D02-P1 ngày 2026-10-17 — 54 nhóm capture của WP31-R2 (QA PASS), registry `docs/review/generated/d02_group_id_registry.csv`, record `docs/review/d02_owner_decision_record.md`; stem `0248` vẫn cách ly. Giới hạn đã chấp nhận: nhóm dựa trên review AI tạm thời, chưa chứng minh hết rò rỉ | PASS — D-02 OWNER APPROVED |
| G0.7 | Sinh train/val/test group-aware; không có group overlap; test được khóa trước tuning; mọi split có manifest và SHA-256. Owner duyệt luật phương án A (2026-10-18). WP36 QA PASS (1 P2: thứ tự ưu tiên). Owner chọn đúng thứ tự đã duyệt → WP36-R1: train/val/test 59,9 / 11,8 / 28,3 % ảnh dùng được, 17 lớp có ≥ 2 nhóm test, test niêm phong `afa03d4b…`; lớp 22 không có val (lớp 25 giữ test) Owner chấp nhận WP36-R1 làm split chính thức (2026-10-18, `docs/review/g07_owner_acceptance_record.md`) | PASS — WP36-R1 OWNER ACCEPTED, TEST SEALED |
| G0.8 | D-04 dựa trên nhãn WP33 và nhóm D-02 (WP34: 27 lớp ≥ 3 nhóm, 6 lớp 2 nhóm, 9 lớp 1 nhóm ≥ 30 ảnh, 12 lớp 1 nhóm < 30 ảnh). Owner đã duyệt D-04 part 1 (2026-10-17): 12 lớp hiếm được train kèm làm giàu bằng biến đổi ảnh thật (WP35, QA PASS), trạng thái `EVAL_PENDING_REAL_INDEPENDENT_DATA`, không kích hoạt hành vi xe. WP34 QA FAIL → WP34-R1 QA PASS (2026-10-18): chỉ ảnh 0544 là nền thật, 24 ảnh âm khác có biển chưa gán nhãn và bị cách ly; họ P.117/W.239b gộp theo họ. Owner duyệt D-04 part 2 (2026-10-18, `docs/review/d04_owner_decision_part2_record.md`): 27 TRAIN_VAL_TEST, 6 TRAIN_AND_TEST_NO_VAL, 9 TRAIN_ONLY_UNVERIFIED; lớp 11/14/28/38 bị một nhóm chi phối | PASS — D-04 PART 1 + PART 2 APPROVED |
| G0.9 | WP37 dataset card: license + ghi công (D-01), lineage 54 nhóm (D-02), bảng lớp (D-03/D-04) theo split, hash split WP36-R1, điều kiện chụp đo được (độ phân giải, độ sáng, độ nét; EXIF/GPS = 0 nên địa điểm/thời gian UNKNOWN). Phát hiện: val lệch điều kiện chụp (toàn bộ ảnh dọc và ảnh tối nằm ở val) WP37 QA PASS với 1 P2 (gọi nhầm 7 ảnh ban ngày ngược tán cây là ảnh tối) → WP37-R1 `docs/dataset01_card_r1.md` sửa P2 + 4 P3 WP37-R1 QA PASS (0 finding, 2026-10-18) | PASS — WP37-R1 QA PASS |

### Exit criteria Gate 0

- G0.1–G0.9 đều PASS và có đường dẫn artifact.
- Train/validation/test không chia chéo cùng `group_id`; direct filename overlap bằng 0.
- Test manifest được niêm phong trước khi chọn model/ngưỡng.
- Số mẫu/support trên từng split được report theo class; lớp không đủ support được xử lý bằng
  quyết định taxonomy/data, không bằng tuyên bố metric thiếu bằng chứng.
- Người dùng duyệt taxonomy và phạm vi license. Nếu chưa có hai phê duyệt này, trạng thái vẫn
  là **NO-TRAIN**.

## Reproducibility contract

Mỗi experiment sau Gate 0 phải:

1. chạy từ module/script có cấu hình, không chỉ từ notebook;
2. ghi seed Python/NumPy/TensorFlow hoặc PyTorch, deterministic flags và số run;
3. ghi Git commit, `uv.lock`, Python/framework/hardware và lệnh chạy;
4. ghi archive/dataset/split/taxonomy hash và preprocessing contract;
5. dùng artifact name mới theo `experiment_id`; không ghi đè E0 hoặc run cũ;
6. lưu config, logs, checkpoint, metrics machine-readable, confusion matrix và failure samples;
7. có experiment table so sánh cùng split/protocol; test set chỉ được mở ở run đánh giá cuối;
8. chạy lại được từ môi trường sạch trong sai số đã công bố.

Tên đề xuất:
`<experiment_id>_<model>_<taxonomy_version>_<split_hash>_<seed>_<timestamp>`.

## Experiment matrix sau Gate 0

| ID | Câu hỏi | Can thiệp | Control/so sánh | Điều kiện giữ |
| --- | --- | --- | --- | --- |
| E0 | Baseline hiện có làm gì trên GTSRB crop? | Không train lại; artifact tải về | Chính nó | Frozen reference; không dùng để tuyên bố VN |
| E1 | Pipeline sửa lỗi có tái lập và cải thiện baseline matched-split không? | Cùng kiến trúc VGG-inspired; bỏ semantic flip; sửa generator/steps; config hóa train | Baseline matched taxonomy/split | Chỉ gọi cải thiện khi independent holdout và per-class report xác nhận |
| E2 | Canonical VGG16 ImageNet transfer có tốt hơn E1 không? | `keras.applications.VGG16`, head mới, freeze/unfreeze theo config | E1 trên cùng crop, taxonomy, split và seed protocol | Macro-F1/critical-class recall tốt hơn mà calibration/latency không vượt giới hạn đã duyệt |
| E3 | Xử lý imbalance có tạo lợi ích thật không? | Class-balanced loss hoặc sampling; từng can thiệp là một ablation | E1/E2 winner không rebalancing | Chỉ giữ nếu ablation tăng macro-F1/per-class recall trên holdout, không chỉ train metric |
| E4 | Abstention/OOD nào đáng tin hơn raw Softmax? | Baseline MSP + temperature scaling; sau đó OpenMax/energy/OOD khác nếu có benchmark | Uncalibrated matched model | Báo đầy đủ coverage/rejection/false acceptance; không gọi UNKNOWN nếu chưa có benchmark |
| D1 | Detector có tìm đúng biển trong frame toàn cảnh không? | Detector trên bbox dataset đã qua Gate 0 | Detector baseline đã cấu hình | Đánh giá độc lập mAP50-95/AP-small/per-class AP; chưa nối classifier nếu detector chưa đạt gate |

E1/E2 trên taxonomy Việt Nam phải dùng crop tạo từ bounding box, không resize nguyên frame xuống
`32x32`. E0 GTSRB và experiment taxonomy Việt Nam khác scope nên không được so sánh trực tiếp như
cùng một leaderboard.

## Metrics bắt buộc

| Track | Metric/report bắt buộc |
| --- | --- |
| Classifier | accuracy; macro/weighted F1; balanced accuracy; precision/recall/F1/support từng lớp; confusion matrix; NLL; ECE; Brier score; latency kèm hardware/batch size |
| Selective/OOD | coverage; accepted-set accuracy; known rejection; unknown false acceptance; đường cong threshold và benchmark composition |
| Detector | mAP50-95; AP50; AP-small; precision/recall; per-class AP; latency; failure samples |
| End-to-end | detection+classification exact-label rate; miss/wrong-box/wrong-class taxonomy; breakdown ngày/đêm/mưa/blur/occlusion và latency toàn pipeline |

Không được gọi một experiment là “tốt hơn” nếu chưa có independent holdout cùng protocol. Khi
sample nhỏ hoặc class hiếm, báo confidence interval/repeated seeds và support thay vì chỉ báo một
điểm số.

## Work breakdown theo milestone

| Milestone | Phạm vi/deliverable | Gate hoàn thành | Trạng thái |
| --- | --- | --- | --- |
| M0 — Data governance | WP1–WP37-R1 (chi tiết từng WP trong `PROJECT_MEMORY.md`). Đã duyệt D-01…D-04; split WP36-R1 được owner chấp nhận (test niêm phong `afa03d4b…`); dataset card WP37-R1. D-05 đã duyệt (`docs/review/d05_owner_decision_record.md`) | Gate 0 PASS | **GATE 0 MỞ (2026-10-18): G0.1–G0.9 PASS + D-05 ĐÃ DUYỆT** |
| M1 — Training package | dataset loader crop, config/seed/logging, corrected augmentation, reproducible train/eval CLI. Track detector: loader YOLO kiểm hash split WP36-R1, nhãn WP33, ảnh WP35 chỉ train, không lật ngang | Clean rerun tạo cùng artifact class/metric tolerance; không còn input-exhaust warning | **ĐANG LÀM** — export YOLO + split guard (`scripts/build_m1_yolo_dataset.py`), project uv riêng `detector/` (torch 2.14.1, ultralytics 8.4.172), CLI train/evaluate/latency đã chạy thử trên MPS; dependency layout đã được owner duyệt, independent M1 QA còn pending, Q1 pretrained còn mơ hồ nên chưa được tải |
| M2 — Classifier study | E1, E2, E3 theo experiment matrix | Independent classifier holdout + toàn bộ metrics/artifacts | PROPOSAL |
| M3 — Calibration/OOD | E4 MSP/temperature baseline và ablation OOD | Selective/OOD report; threshold được chọn trên validation, không trên test | PROPOSAL |
| M4 — Full-scene detector | D1 bbox training/evaluation, detector -> crop contract | Detector metrics pass ngưỡng được duyệt; error analysis hoàn chỉnh | PROPOSAL — **ƯU TIÊN KẾ TIẾP** (owner 2026-10-17: detector VN trước, prototype sau) |
| M5 — End-to-end/video | detector + classifier + tracking/temporal voting | Exact-label/failure taxonomy theo điều kiện; latency report | PROPOSAL |
| M6 — Product integration | Streamlit evidence UI, simulation-only behavior, packaging/hardening. Đã có: tab "DATASET01" (2026-10-17) gồm hoạt hình 8 bước xử lý dữ liệu, đồ thị theo nhóm D-02, bảng lớp và bảng nhóm; trước đó là tab "Đồ thị DATASET01" hiển thị read-only cạnh proxy WP5 và kết quả review WP5–WP29 ở mức PROVISIONAL, không tạo group truth | Browser E2E, performance gate, user guide; không có safety claim | PROPOSAL (evidence graph tab đã có) |

MVP hiện hữu (UV environment, Streamlit shell, crop classifier, behavior mô phỏng và GTSRB
evaluation) vẫn được giữ; nó không làm Gate 0 tự động PASS.

### Owner follow-up — 2026-10-18

- Q1 trả lời literal `Có/Không`, nên chưa có quyền tải pretrained weights.
- Owner chọn Colab và cho phép upload riêng tư chỉ train/val; test không upload. Colab phải lưu
  log/run artifacts có thể audit theo notebook VGG16 mà owner chỉ định.
- Owner chọn chạy cả hai baseline: YOLO 54 lớp và detector một lớp + classifier. Baseline 54 lớp
  giữ gate D-05 hiện tại; baseline thứ hai cần addendum metric/gate trước khi dùng sealed test.
- Owner cho phép commit và push source checkpoint lên branch hiện tại. Vì remote là public,
  DATASET01-derived review renders và raw/processed/model files không được đưa vào checkpoint.
- Canonical records: `docs/review/m1_pretrained_weights_owner_response_record.md`,
  `m1_colab_training_owner_decision_record.md`, `d1_dual_baseline_owner_decision_record.md`,
  `m1_dependency_decision_record.md`, `git_checkpoint_owner_decision_record.md`.

## Blocker và quyết định cần người dùng duyệt

Reviewer packet cho năm quyết định nằm tại `docs/review/m0_wp2_decision_packet.md`; machine status
template giữ toàn bộ quyết định ở `PENDING`. Packet không mở Gate 0 và không cho phép training.

1. **D-01 — Provenance/license: ĐÃ DUYỆT 2026-10-17 (owner chấp nhận rủi ro, `docs/review/d01_owner_decision_record.md`).** Lịch sử: xác nhận chủ sở hữu và license áp dụng cho
   [Hugging Face source candidate](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign);
   metadata ghi CC-BY-SA 3.0 nhưng card prose ghi 4.0.
2. **D-02 — Group identity: ĐÃ DUYỆT 2026-10-17 (D02-P1, 54 nhóm capture WP31-R2).** Lịch sử: cung cấp video/scene/physical-sign metadata hoặc duyệt ngân sách gán
   `group_id` thủ công. WP7 Batch A hiện là 100 double-reviewed provisional pairs đã QA PASS;
   WP12-R1 thêm 250 pairs tiếp theo và đã QA PASS ở mức double-reviewed provisional evidence.
   WP13 thêm 250 pairs tiếp theo và đã QA PASS ở mức double-reviewed provisional evidence. WP14
   thêm 250 pairs tiếp theo và cũng đã QA PASS ở cùng evidence boundary. WP15 thêm exact 176
   cross-split pairs cuối cùng và đã QA PASS với 0 blocker. Năm overlay phủ đủ 1.026 cross-split
   pairs mà không sửa canonical WP5; zero cross-split rows còn lại ngoài overlays, nhưng filename
   proximity và provisional outcomes vẫn không phải ground truth. WP16-R1 Sequence Batch A đã
   QA PASS với 0 blocker sau khi harden exact manifest schema. WP17 Sequence Batch B cũng đã QA
   PASS với 0 blocker. WP18 Sequence Batch C, WP19 Sequence Batch D và WP20 Sequence Batch E cũng
   đã QA PASS ở cùng provisional evidence boundary. WP21 exact residual `eligible[500:]` gồm 88
   sequence `proxy_sequence_0502`…`proxy_sequence_0589`/363 unique frames cũng đã QA PASS với 0
   findings; sáu overlay phủ đủ 588 quarantine-eligible sequence. Chỉ whole quarantined
   `proxy_sequence_0050` còn ngoài sequence overlays và vẫn nguyên vẹn. WP22 đã QA PASS với 0
   findings cho first 250 review-eligible rows của exact 2.146 remaining-edge residual, loại đúng
   hai cạnh quarantine `edge_000242`/`edge_000243`. Initial WP23 review exact next 250 rows sau khi
   loại WP22 prefix đã QA FAIL vì một High finding tại `edge_000664`. WP23-R1 sửa đúng một
   decision/rationale và đã independently QA PASS với 0 findings; package lịch sử vẫn giữ status
   `WP23_R1_AWAITING_QA_REVIEW`. WP24 exact next 250 eligible rows sau WP22/WP23-R1 đã
   independent QA PASS với 0 findings; hash-pinned package vẫn giữ status lịch sử
   `WP24_AWAITING_QA_REVIEW`. Initial WP25 đã independent QA FAIL với đúng một P1 tại
   `edge_001358`; WP25-R1 sửa append-only đúng decision/rationale này và đã independent QA PASS
   với 0 findings. WP26 Batch E là exact next 250 eligible rows và đã independent QA PASS với
   0 findings. Initial WP27 Batch F đã independent QA FAIL với đúng một P2 vì stale layout-status
   `176` dù `pair_count=250`; WP27-R1 sửa append-only đúng một field nhưng QA FAIL với một P2
   verifier type-confusion; WP27-R2 verifier hardening đã independent QA PASS. WP28 Batch G
   QA FAIL hai lần (WP28, WP28-R1); WP28-R2 và WP29 Batch H đã independent QA PASS ngày
   2026-10-17 (`docs/review/wp28_r2_wp29_independent_qa_record.md`). WP30 final Batch I review
   toàn bộ 144 cạnh eligible cuối cùng (`edge_002973`…`edge_003176`); initial WP30 QA FAIL với
   một P1 tại `edge_003047`, WP30-R1 sửa append-only đúng cạnh này và đã independent QA PASS;
   sau WP30 không còn cạnh eligible nào, chỉ còn 2 cạnh cách ly chạm stem `0248`.
   M0-WP31 (`docs/review/wp31_group_id_proposal_report.md`) đề xuất hai cấp `group_id` cho owner
   chọn: capture (85 nhóm, lớn nhất 16,0%) hoặc scene (99 nhóm, lớn nhất 7,4%); 37 cặp liền kề quanh
   25 ảnh âm chưa từng được review và nên được xem trước khi chốt D-02. WP31 đã independent QA FAIL (2 P1): tên file của các chuyến đi xen kẽ nhau nên cùng một biển nằm ở nhiều nhóm; cần bước nối nhóm chéo khối (cross-block) được review trước khi phương án D-02 nào được coi là an toàn. WP32 (review 71 cặp ứng viên chéo khối) đã QA PASS; WP31-R1 QA PASS ở cấp capture (54 nhóm) — cấp scene còn một P2 (6 ảnh âm gán nhầm cảnh); WP31-R2 sửa P2 (nối cả hai cảnh quanh mỗi đoạn ảnh âm, 61 nhóm scene) và đã QA PASS: cấp capture (54 nhóm) sẵn sàng để owner duyệt D-02; cấp scene cần bổ sung giải thích một chỗ tách cảnh trong báo cáo.
   Toàn bộ
   589 canonical sequence rows và
   3.172 canonical WP5 edge rows vẫn `PENDING`; coverage/overlay evidence không phải
   owner-approved group truth.
3. **D-03 — Taxonomy: ĐÃ QUYẾT ĐỊNH ĐỦ 52 LỚP (2026-10-17, part 1 + part 2 `docs/review/d03_owner_decision_part2_record.md`); G0.5 chờ QA bộ nhãn dẫn xuất WP33 (lớp 23 giữ 1 lớp biển ghép P.111a+P.111b sau khi review 465 box; biển chiều cao tách theo giá trị; 4 box không đọc được bị loại khỏi train).** Lịch sử: dùng package M0-WP8-R1 đã QA PASS ở mức proposal/evidence để chỉ định người duyệt và
   approve/reject từng dòng taxonomy Việt Nam; GTSRB chỉ là analysis-only. Đồng thời duyệt chính
   sách composite/parameterized/supplementary và UNKNOWN. WP8 chưa giải quyết D-03.
4. **D-04 — Rare classes:** WP11 đã QA PASS ở mức package-only; tiếp theo duyệt riêng từng lớp
   trong 20 lớp có `box_count < 50`. Các khuyến nghị `COLLECT_MORE`/
   `OWNER_REVIEW_REQUIRED` chưa phải phê duyệt.
   Không tự merge taxonomy hoặc train để che thiếu dữ liệu.
5. **D-05 — Acceptance thresholds/compute:** sau khi có val/test hợp lệ, duyệt ngưỡng metric,
   latency và ngân sách số seed trước khi chạy E1–E4/D1.
   **ĐÃ DUYỆT 2026-10-18** toàn bộ khuyến nghị của `docs/review/d05_proposal.md`
   (`docs/review/d05_owner_decision_record.md`). Gate 0 mở cho track detector VN.

## M0-WP1 evidence

- Dataset card: `docs/dataset01_card_r1.md` (WP37-R1; bản WP37 giữ làm hồ sơ); audit kỹ thuật WP1: `docs/dataset01_audit.md`.
- Taxonomy draft: `docs/vietnam_taxonomy_mapping.md`.
- Audit runner: `scripts/audit_dataset01.py`.
- Fail-closed audit regression suite covers ZIP/raw mismatch, corrupt images, invalid YOLO,
  boundary warnings, source mutation, normalization overwrite protection and manifest tampering.
- Machine-readable outputs:
  `results/data_audit/DATASET01_052bc980a7206f8d/`.
- Source preservation proof có `unchanged=true`; technical audit có `PASS`; Gate 0 vẫn
  `BLOCKED`.

## M0-WP2 evidence — QA PASS / DECISION-READY, chưa phê duyệt

- Decision packet: `docs/review/m0_wp2_decision_packet.md`.
- `QA-M0-WP2-R2` đã review HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` trên worktree
  chưa commit và kết luận `0 blockers`. PASS này chỉ phê duyệt chất lượng của WP2 decision packet;
  Gate 0 vẫn `BLOCKED`, `training_authorized=false`, không cho phép training/final split hay thay
  đổi model.
- Machine status template lịch sử `docs/review/decision_status.json` vẫn hash-pin với D-01…D-05 và
  G0.4 bbox 0248 ở `PENDING`; G0.4 hiện được supersede theo kiểu append-only bởi WP10 owner overlay,
  không sửa in-place artifact lịch sử này.
- Grouping proxy dùng numeric adjacency + conservative visual cues: 1.691 strong edges,
  1.172 uncertain edges, 315 adjacency-only edges; 589 candidate sequences/2.280 ảnh. Các ID là
  `PROXY_ONLY`, không phải ground-truth groups và không được dùng tự động để split.
- Taxonomy reviewer CSV giữ đủ 52 dòng `UNAPPROVED`, support khớp audit và có conflict flags dựa
  trên QCVN 41:2024/BGTVT review target.
- Rare-class risk table giữ đủ 52 lớp; ID 44 có 3 boxes, ID 51 có 5 boxes; không merge/drop ngầm.
- D-04 có 20 class-keyed records cho rule `box_count < 50`; mỗi record có option/status/reviewer/
  timestamp/rationale/evidence/history riêng. Runtime validator và generated schema fail-closed
  với reviewer/rationale rỗng hoặc chưa trim, timestamp thiếu timezone, evidence sai kiểu/rỗng và
  history item thiếu cấu trúc; runtime còn khóa thứ tự timestamp append-only. Aggregate không thể
  `RESOLVED` khi còn một class unresolved. Generated template/schema nằm trong
  `docs/review/generated/`; hiện 20/20 là `PENDING` và không có option được chọn.
- Taxonomy và rare-class builders fail-closed nếu class IDs không phải tập duy nhất chính xác
  `0..51` hoặc support source không đủ.
- Bbox 0248 overlay xác nhận `x_max=978,00048 px` trên ảnh rộng 960 px, overflow phải
  `18,00048 px`; raw image/label hash không đổi.
- Experiment acceptance template đưa ba bundle PROPOSAL; không bundle nào là safety claim.
- Builder và machine-readable evidence: `scripts/build_wp2_review_packet.py` và
  `docs/review/generated/`.

## M0-WP3 evidence — QA PASS package, chưa phê duyệt decision

- `QA-M0-WP3-R1` đã review HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` trên worktree
  chưa commit và kết luận `0 blockers`. PASS này chỉ xác nhận chất lượng package bằng chứng/
  reviewer của WP3; không phê duyệt dataset, license, taxonomy, group ID, split, model hoặc
  experiment. Trong snapshot WP3 đã pin, D-01…D-05/G0.4 vẫn `PENDING`; WP10 hiện supersede G0.4
  bằng append-only overlay. Gate 0 vẫn `BLOCKED`, `training_authorized=false`.

- Báo cáo chính: `docs/review/wp3_provenance_and_fallback_report.md`; máy đọc được tại
  `docs/review/generated/wp3_provenance_escalation.json` và
  `docs/review/generated/wp3_fallback_dataset_candidates.csv`.
- Lịch sử nguồn giữ URL/revision/timestamp/hash của Hugging Face, Kaggle và repository
  augmentation. Bằng chứng xác nhận có mâu thuẫn CC-BY-SA 3.0/4.0; quan hệ Kaggle upstream chỉ là
  `CANDIDATE`; quyền cấp phép, sở hữu ảnh và group lineage vẫn `UNKNOWN`.
- Fallback Roboflow/VIA/Dataset Ninja chỉ là `CANDIDATE`; không download, chọn, merge hoặc duyệt
  dataset nào. DATASET01 hiện tại vẫn là control vì có hash và audit lineage cục bộ mạnh hơn.
- `docs/review/dataset_owner_outreach_draft.md` là `DRAFT — NOT SENT`; WP3 không liên hệ, đăng
  issue, upload, login hoặc gửi biểu mẫu nào.
- Generator `scripts/build_wp3_reviewer_assets.py` tạo 589 grouping rows/24 contact sheets với
  trạng thái `PROXY_ONLY_NOT_GROUP_TRUTH`, và atlas 52 lớp/13 trang bbox overlay với toàn bộ dòng
  `UNAPPROVED`. Không tạo final `group_id`, split hoặc taxonomy approval.
- `wp3_source_lineage.csv` giữ đường dẫn/hash cho 2.325 source files được dùng; toàn bộ hash đã
  được so lại với raw. `wp3_render_layout_audit.json` chứng minh text đầy đủ và pixel bounds hợp lệ
  trên cả 589 grouping rows/24 pages và 52 taxonomy rows/13 pages; không còn cắt dHash/cosine hoặc
  conflict flags. Cả 37 JPEG đều decode; grouping 001/017/024, taxonomy 008/013 và crowded page
  011 đã visual-readback.
- Manifest schema v2 dùng logical root ID + relative path, không nhúng output path tuyệt đối. Test
  build ở hai temp roots yêu cầu manifest bytes/hash giống hệt nhau. Verifier fail-closed kiểm tra
  47 artifacts, 9 source inputs và 5 controls, gồm decision status, source-preservation/tree hash,
  WP1/WP2 manifests và provenance snapshot; test âm bao phủ tamper/missing/wrong-type/traversal.
- Manifest 47 artifact/21.576.108 bytes xác minh zero mismatch và hai build thật lặp lại cùng
  SHA-256 `8b2e9ef3b2418623eb92673f3c58591e29f5ed7479bca2b03582c12ef0191dcd`.
- SHA của WP1 manifest, WP2 manifest và `decision_status.json` không đổi. Snapshot lịch sử giữ
  D-01…D-05/G0.4 `PENDING`; WP10 hiện supersede G0.4 append-only. Gate 0 vẫn `BLOCKED`,
  `training_authorized=false`. QA độc lập đã xác nhận package WP3
  PASS tại `QA-M0-WP3-R1`; PASS này không tự phê duyệt bất kỳ decision nào.

## M0-WP4 QCVN taxonomy evidence — QA PASS package, taxonomy chưa phê duyệt

- `QA-M0-WP4-R2` review HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` trên worktree chưa
  commit và kết luận PASS với `0 blockers`. PASS này chỉ đóng chất lượng evidence package WP4;
  toàn bộ taxonomy rows vẫn `UNAPPROVED`, D-03 `PENDING`, Gate 0 `BLOCKED` và
  `training_authorized=false`.

- QA trước đó trả về FAIL vì atlas thiếu target bbox overlay và verifier có thể chấp nhận worksheet
  sai ngữ nghĩa nếu artifact hash được cập nhật. Hai blocker đã được sửa và được R2 xác nhận.
- Re-review tiếp theo phát hiện coverage gap riêng: atlas chưa chứa đúng boundary case `0248` cho
  class 49. Repair hiện reserve `0248` ở slot 1; stem vượt biên khác như `0809` không được phép thay
  thế tiêu chí này.

- Nguồn pháp lý được khóa tại `references/qcvn41_2024/`: Thông tư 51/2024/TT-BGTVT (1 trang,
  SHA-256 `dc822815...`) và QCVN 41:2024/BGTVT đính kèm (403 trang, SHA-256 `b6b99d0a...`), cùng
  URL, retrieval timestamp, kích thước và page count trong `source_provenance.json`.
- `scripts/build_wp4_qcvn_taxonomy_audit.py` tạo và verify worksheet 52 dòng, một dòng cho mỗi
  class ID `0..51`; kết quả bằng chứng là 31 `EXACT`, 14 `PARTIAL`, 6 `MISMATCH`, 1 `NOT_FOUND`.
  Toàn bộ 52 dòng giữ `UNAPPROVED`; D-03 vẫn `PENDING`.
- `references/qcvn41_2024/qcvn_taxonomy_evidence_index.json` là control 52 dòng riêng, được khóa
  bằng SHA-256 `62233e56a47c9c7116805d2b9d38846f2a20696b952507752810a83192abd7aa` trong code và
  provenance. Nó bind code/name/page/section/figure/token, 39 fingerprint text + render của trang
  PDF, và negative-search scope class 31 (trang 80–154; query `camera`, `giám sát`, `surveillance`).
- Các conflict bắt buộc 3/22/25/28/30/31/34/47/51 có test cố định. Kết luận chính: S.505a là biển
  phụ `Loại xe`; `B.8a` phải được phân biệt với mã P.108a; `P.124b1` không được xác nhận và ứng
  viên theo QCVN là P.124b; class 31 không có ứng viên được khẳng định trong nguồn QCVN này; class
  51 đúng mã/nghĩa QCVN nhưng mapping GTSRB vẫn chỉ là proposal khác họ warning/mandatory.
- Reviewer report: `docs/review/m0_wp4_qcvn_taxonomy_report.md`; worksheet và manifest nằm trong
  `docs/review/generated/`; atlas 13 trang nằm tại
  `docs/review/assets/wp4/qcvn_taxonomy_atlas/index.html`. Atlas giữ ba crop đại diện mỗi lớp,
  class/code/stem tag và target bbox overlay trong đủ 156 ô. Lineage 156 dòng bind raw hash,
  label line/index, normalized/source/context/render/atlas geometry; 152 stem là duy nhất vì bốn
  stem được dùng ở nhiều class-slot. Sampling reserve `0248` trước cho class 49; hai slot còn lại
  giữ thứ tự deterministic WP3. `0248` là slot 1, raw 960x540, label line 1/index 0, bbox pixel
  `(927,00048; 158,99976; 978,00048; 213,99984)`, vượt phải `18,00048 px`. Phần vượt frame được
  hiển thị bằng nền hatch xám và đường biên ảnh cyan, không clamp và không sửa raw.
- `docs/review/wp4_taxonomy_vnext_proposal.md` tách riêng mọi candidate change và được ghi rõ
  `PROPOSAL ONLY — DO NOT APPLY`; WP4 không sửa taxonomy hiện hành, label, split hay raw data.
- Manifest schema v2 có 20 artifacts, 13 source/control hashes, `source_hashes_unchanged=true`,
  SHA-256 `c60c09018900071cc66d8bc01db32300f4efc6a4316bda9f506819026400db1c`. Bộ 26 test WP4 bao
  phủ deterministic rebuild, raw-preservation/geometry/pixel overlay, wrong page/code/name/section/
  figure với artifact hash mới, token/page-fingerprint/negative-scope với index hash mới, missing/
  tampered index, path traversal, exact stem `0248` và từ chối stem vượt biên thay thế.
- Đây là evidence package chờ re-review, không phải taxonomy approval. Gate 0 vẫn `BLOCKED`,
  `training_authorized=false`; không training, final split, relabel, upload, deploy hoặc publish.

## M0-WP5 provisional grouping adjudication — QA PASS PARTIAL, review chưa hoàn tất

- `QA-M0-WP5-R1` review HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` cùng current
  uncommitted tree và kết luận PASS với `0 blockers`. PASS chỉ đóng chất lượng package WP5, không
  xác nhận complete grouping truth: 3.172 edges vẫn `PENDING` (gồm 1.026 cross-split), toàn bộ
  589 sequences vẫn `PENDING`, provisional components không phải final group truth, D-02 vẫn
  `PENDING`, Gate 0 vẫn `BLOCKED`, `training_authorized=false`; không split mutation hoặc training.

- QA vòng đầu trả về FAIL với đúng một blocker: verifier chỉ kiểm các record còn có mặt nên vẫn
  chấp nhận roster 137→136 artifacts, 11→10 sources và count giả. Repair schema v2 hiện suy ra
  roster độc lập từ contract và bắt đúng 11 source/control records cùng 137 artifacts không tính
  chính manifest (`EXCLUDES_MANIFEST_FILE`). Source allowlist khóa WP2/WP3/WP4 manifests, grouping
  inputs, inventory, source-preservation, decision status và visual annotations.

- Generator `scripts/build_wp5_provisional_grouping_review.py` tạo queue quyết định fail-closed
  cho đủ 3.178 adjacency edges, xếp toàn bộ 1.031 cross-split edges trước, và liên kết đủ 589
  proxy sequences với 24 contact sheets WP3 đã QA PASS. Pair atlas gồm 128 trang có ảnh nguồn,
  class, split relation, proxy metrics, review status và provisional outcome.
- Chỉ sáu cặp đã được quan sát trực tiếp và ghi reviewer/timestamp/confidence/rationale/evidence:
  bốn `SAME_CAPTURE_CANDIDATE`, hai `NOT_RELATED`; năm trong sáu cặp là cross-split. Còn 3.172
  edges (gồm 1.026 cross-split) và toàn bộ 589 sequences ở trạng thái `PENDING`. Không suy kết
  luận từ proxy metrics cho các hàng chưa review.
- Capture hypothesis và physical-sign hypothesis được giữ riêng. Chỉ cạnh `REVIEWED` có
  confidence `HIGH` mới tạo component: bốn capture components/tám ảnh và hai physical-sign
  components/bốn ảnh, tất cả gắn `PROVISIONAL_COMPONENT_NOT_GROUP_TRUTH`; hiện không có conflict
  nội bộ trong sáu cạnh đã review. Không có final grouping field hoặc split assignment.
- Machine schema bắt hàng `PENDING` để trống toàn bộ decision fields. Manifest schema v2 kiểm
  exact ID/path roster, record type/hash/size, declared counts/bytes, 128-page layout, decision
  boundary và 3.216 cặp image/label. Bộ 26 test WP5 bao phủ exact coverage, component,
  no-final-fields, deterministic generation/layout và các negative case: xóa/trùng/thêm record,
  valid-but-unexpected file, count `999`, total bytes giả, thiếu page 001/064/128, path escape,
  directory-for-file và wrong type. Hai clean builds cho cùng SHA-256 manifest
  `f8d620a3cbb3b500153f6685b94a9936a8f83eb6f5399ce0a2e8be77982d4b80`, zero artifact mismatch.
- Khuyến nghị D-02: ưu tiên **D02-A** lấy creator/session metadata. **D02-B** chỉ là fallback khi
  duyệt hết 3.178 edges/589 sequences, giải quyết đủ 1.031 cross-split pairs và có reviewer thứ
  hai cho positive/conflict cases. D-02 vẫn `PENDING`; Gate 0 vẫn `BLOCKED` và
  `training_authorized=false`.
- Báo cáo: `docs/review/wp5_provisional_grouping_report.md`; machine artifacts và manifest tại
  `docs/review/generated/`; atlas tại `docs/review/assets/wp5/pairs/index.html`.

## M0-WP6 frozen-E0 compute/readiness preflight — QA PASS, local read-only package only

- `QA-M0-WP6-R2` reviewed HEAD `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current
  uncommitted tree and reported PASS with `0 blockers`; 29 targeted and 158 full tests passed,
  together with Ruff, lock, diff and Graft gates. PASS applies only to this local read-only
  frozen-E0 preflight package.
- WP6 chỉ kiểm kê và đo diagnostic read-only trên E0/GTSRB đã đóng băng. Nó không chạy E1–E4,
  không duyệt D-05, không fit calibration, không chọn UNKNOWN/OOD threshold, không đánh giá miền
  Việt Nam và không cấp quyền training.
- Runtime quan sát được: macOS arm64, Apple M1 Pro, 10 CPU cores, 16 GB RAM và GPU Metal 16 cores
  ở mức hardware. TensorFlow 2.20.0/Keras 3.15.1 chỉ nhìn thấy `/device:CPU:0`; backend benchmark
  thực tế là `TENSORFLOW_CPU_ONLY`, không phải Metal GPU.
- Contract latency batch 1 dùng seed `20261010`, 20 warm-up và 300 lượt đo thành ba repeat 100.
  Vùng timing gồm `preprocess_image` và `keras model.predict`; loại trừ đọc pickle, load model,
  tạo PIL object, chọn sample và serialize report. Kết quả host-specific: p50 `21,7390 ms`, p95
  `25,0992 ms`, mean `22,4386 ms`, population std `5,3250 ms`, max `106,9830 ms`; không dùng các
  số này làm gate.
- Model E0 giữ SHA-256 `745cf3f6...`, input `32x32x3`, output 43 lớp và 2.188.107 parameters.
  Ba pickle GTSRB được hash-pin và kiểm schema: train 34.799, valid 4.410, test 12.630 samples;
  tất cả có class IDs `0..42`. `valid.p` chỉ phù hợp cho thiết kế diagnostic sau này vì cùng nguồn
  GTSRB và đã được dùng trong model development; nó không phải independent Vietnamese holdout.
- Manifest schema v2 khóa đúng 20 source/control records và 3 artifacts, không tính chính manifest.
  Verifier trả `valid=true`; manifest SHA-256
  `656afe56bf342a0d4d0110dcd6b1d601f9f35633d03c65c98d54d3d454760bb0`; fingerprint non-timing
  `40ca8550b29d228885e05d7f31c1e34febb08c0117715f9848fa973b42509ed3`. Clean-build attestation
  SHA-256 `5102dc7493cd32f0f958430b3d0dd25b0e288ba10052b81ee17236b4acfb3c56` được pin trực tiếp trong
  source verifier; digest 300 quan sát là
  `c01ce409b094fa46b76117ea2833c95241e737b219967561618eb450bf3b3887`. Verifier kiểm source anchor
  trước khi tin attestation, rồi load lại model hash-pin và re-observe TensorFlow devices/runtime.
  Bộ 29 test WP6 tính lại thống kê và từ chối missing/duplicate/extra roster, count/bytes giả,
  path escape, wrong type, source/artifact hash tamper, cùng năm coherent re-hash forgery của QA:
  canonical-VGG16 giả, Vietnamese-holdout giả, D-05/GPU/Vietnam claim giả, GPU inventory giả và
  toàn bộ latency 999 ms. Regression 999 ms thực hiện cả việc tạo lại attestation từ evidence giả,
  regenerate report/fingerprint và refresh toàn bộ manifest hashes/sizes nhưng vẫn bị source-anchor
  mismatch. Deletion, substitution, old attestation và unpinned candidate cũng bị từ chối.
- Workflow trust mới tách measurement khỏi acceptance: `build` chỉ ghi unpinned candidate dưới
  `tmp/wp6_candidate` và báo `official_package_modified=false`; nó không sửa official artifacts
  hoặc anchor. Chỉ sau code review và manual source update của `TRUSTED_ATTESTATION_SHA256`, lệnh
  `promote-pinned` mới được phép tạo package chính thức. Verifier không tự học hay tự cập nhật anchor.
- Báo cáo: `docs/review/wp6_e0_compute_readiness_report.md`; evidence/manifest machine-readable:
  `docs/review/generated/wp6_e0_compute_readiness.json` và
  `docs/review/generated/wp6_e0_compute_manifest.json`; attestation riêng:
  `docs/review/generated/wp6_e0_compute_attestation.json`.
- Official-artifact symlink escape hiện fail closed bằng `ValueError` thay vì structured
  `valid=false`; đây là technical debt không blocking và không tạo acceptance bypass.
- Frozen WP6 control snapshot giữ D-01…D-05 và G0.4 `PENDING`; WP10 hiện supersede G0.4
  append-only. Gate 0 vẫn `BLOCKED`, `training_authorized=false`; acceptance
  template vẫn `UNAPPROVED / INACTIVE`. QA PASS không tạo calibration/OOD/Vietnam/detector/training
  claim mới.

## M0-WP7 cross-split visual adjudication pilot Batch A — QA PASS, provisional evidence only

- Milestone `QA-M0-WP7` independently reviewed HEAD
  `dee2b82682d650052a9b5fc7b92fc0b3d00b54d1` plus the current uncommitted tree and reported
  PASS with `0 blockers`: 100/100 blind capture-outcome agreement and 20/20 atlas pages reviewed.
  QA PASS closes only this double-reviewed provisional Batch-A evidence.

- WP7 là package riêng và không sửa bất kỳ output QA-approved nào của WP5. Selection được derive
  độc lập từ exact WP5 priority/order: 100 unique rows đầu tiên có `cross_split=True` và
  `review_status=PENDING`, từ `edge_000006` đến `edge_000307`; toàn bộ sáu edge đã review trong
  WP5 bị loại.
- PM/Codex provisional visual reviewer đã quan sát trực tiếp cả hai source image cho đủ 100 cặp.
  Dedicated atlas có 20 JPEG pages × 5 cặp với ảnh toàn cảnh lớn, bbox overlay, stem/path/split,
  quyết định, confidence và rationale. Vòng readback sau build đã kiểm tra đủ 20/20 trang.
- Kết quả provisional: 98 `SAME_CAPTURE_CANDIDATE`, 2 `NOT_RELATED`; confidence 99 `HIGH`,
  1 `MEDIUM`. Independent QA đồng thuận đủ 100 capture outcomes và xác nhận 97
  `SAME_PHYSICAL_SIGN_CANDIDATE` cùng 3 physical-sign `NOT_RELATED`; `edge_000153` đúng là
  same-capture nhưng physical-sign `NOT_RELATED` ở `MEDIUM`. Capture hypothesis và physical-sign
  hypothesis được ghi riêng. Mọi record nêu rõ không có creator/session/physical-sign identity
  metadata và bind hai raw image hashes với đúng WP7 atlas page/slot.
- Canonical WP5 vẫn giữ nguyên 3.172 edges `PENDING`, trong đó 1.026 là canonical cross-split
  pending. Pilot overlay đã double-review 100 Batch-A pairs nhưng không đổi trạng thái WP5; còn
  3.072 edges ngoài Batch A, gồm 926 cross-split edges ngoài Batch A, và toàn bộ 589 sequences
  vẫn `PENDING`. D02-A creator/session metadata vẫn là hướng ưu tiên; ngân sách D02-B chưa được
  phê duyệt.
- Builder/verifier: `scripts/build_wp7_cross_split_review_batch.py`. Report:
  `docs/review/wp7_cross_split_review_batch_a_report.md`. Decisions/notes, exact selection, layout
  audit và manifest nằm tại `docs/review/` và `docs/review/generated/`; atlas tại
  `docs/review/assets/wp7/batch_a/index.html`.
- Manifest SHA-256
  `73ed4095a1f59b72f010fd87b63c4a7f0b16bcf8e0c667ec77576ec827e5d7f2` khóa exact 9-source và
  25 non-manifest artifact roster; verifier trả `valid=true`. Bộ 20 test WP7 từ chối roster/order/
  status/hash/path/symlink/count/bytes và coherently re-hashed selection/annotation/layout/note
  tampering. Full repository gate: Ruff PASS, 178/178 tests PASS và `uv lock --check` PASS với
  168 packages; Graft in sync ở 30 files/464 nodes/1.299 edges.
- Artifact package giữ nguyên status lúc build là
  `WP7_AWAITING_QA_BATCH_A_PM_PROVISIONAL_REVIEW`; closure `QA-M0-WP7` được ghi ở roadmap/memory
  mà không sửa artifact hay hash. Đây không phải D-02 approval, final/transitive group truth,
  `group_id`, relabel, final split hay training authorization. D-02 vẫn `PENDING`, Gate 0 vẫn
  `BLOCKED`, `training_authorized=false`.

## M0-WP8-R1 provisional 52-class taxonomy recommendation — QA PASS, proposal package only

- `scripts/build_wp8_taxonomy_recommendation.py` chuyển evidence WP4 đã pin thành đúng 52 dòng
  reviewer; mọi dòng giữ `UNAPPROVED`. Bốn quyết định độc lập gồm native taxonomy, GTSRB
  analysis-only, loại biển và UNKNOWN/rejection routing. Package không sửa WP4, taxonomy hiện
  hành, raw labels hoặc split.
- Native recommendation có 23 `KEEP_CURRENT`, 19 `CORRECT_CODE_OR_NAME_PROPOSAL`, 9
  `SEMANTIC_REVIEW_REQUIRED`, 1 `OUT_OF_SCOPE_PROPOSAL`. GTSRB disposition có 11
  `DIRECT_ANALYSIS_ONLY`, 13 `PARTIAL_ANALYSIS_ONLY`, 27 `NONE`, 1 `REVIEW_REQUIRED`.
- R1 sửa đúng bốn semantic defect từ QA: class 14 dùng `ATOMIC_SIGN` vì P.106a là biển cấm xe tải
  cố định còn tham số khối lượng thuộc P.106b; classes 6/42/50 chuyển sang
  `CORRECT_CODE_OR_NAME_PROPOSAL` để sửa nhãn Anh thành `Dangerous Curve to the Left`,
  `Mandatory Left Turn`, và `Dangerous Curve to the Right`. GTSRB/UNKNOWN counts không đổi.
- Conflict register khóa độc lập các lớp `3/22/23/25/28/30/31/34/47/51`: P.111 cần chọn biến thể
  a-d; S.505a là biển phụ `Loại xe`; B.8a là mục/hình còn P.108a mới là mã biển; P.124b1 không
  được QCVN hỗ trợ và P.124b chỉ là ứng viên; class 31 không được gán mã QCVN; W.246c đúng native
  code nhưng chỉ partial với GTSRB 38 do khác warning/mandatory family.
- Matrix machine-readable tại `docs/review/generated/wp8_taxonomy_recommendation.csv` và `.json`
  bind QCVN page/section/figure hoặc negative-search scope, support/risk/rare flag, cùng 156
  representative stems, image/label SHA-256 và bbox references. Rarity (`image_count < 100`) chỉ
  là data-risk flag, không phải lý do merge semantics.
- Dedicated atlas tại `docs/review/assets/wp8/taxonomy_decision_atlas/index.html` gồm 13 PNG pages;
  mỗi trang giữ nguyên WP4 visual evidence đã pin ở bên trái và thêm decision panel ở bên phải.
  PM đã visual-readback đủ 13/13 trang; layout audit xác nhận đủ 52 panel, text/bounds hoàn chỉnh.
- Contract độc lập tại `references/qcvn41_2024/wp8_recommendation_contract.json`. Manifest SHA-256
  `9d8fc460b8162874b4082940b0e7f3ceb174c068a92378974ebd93b55da20348` khóa exact 21 sources và
  19 non-manifest artifacts; verifier trả `valid=true`. Bộ 32 test WP8 từ chối roster/count/path/
  symlink và coherently re-hashed matrix/report/layout/atlas/contract/critical-row/R1 rollback
  tampering. Full gate đạt 210 test cases, Ruff, `uv lock --check` (168 packages) và
  `git diff --check`; Graft đồng bộ ở 32 Python files/525 nodes/1.468 edges.
- Independent QA kết luận **PASS với 0 blocker**: QCVN được kiểm tra lại; 48 non-R1 rows không
  semantic drift; clean-room rebuild tạo byte-identical đủ 19 non-manifest artifacts; 32/32 test
  WP8 và 210/210 full-suite test pass; source/artifact hashes khớp manifest. Nonblocking debt còn
  lại là Starlette `TestClient` deprecation và optional Graft deep layer chưa build.
- QA PASS chỉ xác nhận chất lượng proposal/evidence package. Cả 52 rows vẫn `UNAPPROVED`, D-03 vẫn
  `PENDING`, Gate 0 vẫn `BLOCKED`, `training_authorized=false`; không relabel, split hoặc training.
  Domain reviewer/owner vẫn phải approve hoặc reject từng proposal theo governance.

## M0-WP9-R1 bbox 0248 adjudication — QA PASS, decision-support package only

- Raw fact đã pin: ảnh `0248.jpg` SHA-256
  `07eab2035dc10b7b08be71d76c3c32ffdb960722839414f1e474da20c3ad0cbd`, nhãn raw SHA-256
  `f4ec410f7bff3ee03f6110308e8e95f57c92bcc7ebf45ff3affcfd885b419c77`, ảnh `960x540`, dòng 1 /
  index 0 class 49 có YOLO `(0.992188, 0.345370, 0.053125, 0.101852)` và pixel bbox
  `(927.00048, 158.99976, 978.00048, 213.99984)`, tràn phải `18.00048 px`.
- Full-frame và boundary zoom cho thấy vật thể biển báo thật sự bị cắt bởi mép phải ảnh; đánh giá
  `IMAGE_EDGE_TRUNCATED_OBJECT_WITH_RAW_BOX_EXTENDING_BEYOND_RIGHT_BOUNDARY`, confidence `HIGH`.
  Ảnh 0247/0249 chỉ là adjacency context proxy, không phải group ground truth.
- PM đề xuất `QUARANTINE_FROM_TRAINING_PENDING_OWNER_DECISION`: giữ raw immutable cho provenance;
  bản clip riêng chỉ là `REVIEW_ONLY_NOT_APPROVED_TRAINING_LABEL`. Derived line 1 clip đúng
  `x_max=960`, thành `49 0.982812750 0.345370000 0.034374500 0.101852000`; dòng 2 giữ nguyên.
- Package gồm contract `references/dataset01/wp9_bbox_0248_adjudication_contract.json`, report,
  machine-readable adjudication, derived candidate, layout audit và review sheet. Manifest SHA-256
  `cea9423616de0bf4649d71e40f395b4cdc18ff3ea2f80e9829ea4063f009656f` khóa exact 17 sources và
  5 non-manifest artifacts; verifier trả `valid=true`. Bộ 30 test WP9 có clean-room rebuild
  byte-identical và từ chối raw/semantic/roster/count/path/symlink tampering. Full repository gate
  đạt 240/240 tests, Ruff, `uv lock --check` (168 packages) và `git diff --check`; Graft đồng bộ ở
  34 Python files/575 nodes/1.596 edges. Optional Graft deep layer vẫn chưa build và không chặn gate.
- M0-WP9-R1 independent QA kết luận **PASS với 0 blocker** sau khi closure routing stale được sửa;
  PASS chỉ xác nhận decision-support package, không tự ghi owner decision và không sửa WP9 artifact.
  Owner decision sau đó được ghi append-only trong WP10. Gate 0 vẫn `BLOCKED`,
  `relabel_authorized=false`, `split_authorized=false`, `training_authorized=false`; raw data không
  bị ghi đè.

## M0-WP10 G0.4 owner-approved quarantine — QA PASS, G0.4 closed

- Owner phê duyệt `APPROVED_QUARANTINE` ngày `2026-10-11` theo timezone `Asia/Saigon`. Quyết định
  áp dụng cho toàn bộ image/stem `0248`, gồm cả hai label rows. Chỉ sample 0248 bị quarantine;
  class 49 và taxonomy của lớp không bị loại.
- Historical `docs/review/decision_status.json` không bị sửa. Append-only overlay tại
  `docs/review/generated/wp10_g04_owner_decision_overlay.json` bind decision lineage với raw
  image/label hashes, WP8 manifest và WP9 manifest. Derived clip tiếp tục là
  `REVIEW_EVIDENCE_ONLY_NOT_TRAINING_LABEL`.
- Registry `docs/review/generated/wp10_quarantine_registry.json` yêu cầu fail closed nếu overlay/
  registry thiếu hoặc invalid, và reject mọi candidate stem list/split manifest chứa `0248`.
  Candidate không chứa 0248 chỉ pass quarantine-specific check; không được hiểu là split/training
  authorization.
- Contract: `references/dataset01/wp10_g04_owner_quarantine_contract.json`; builder/verifier/CLI:
  `scripts/build_wp10_g04_quarantine.py`; report: `docs/review/wp10_g04_quarantine_report.md`.
  Manifest SHA-256 `9c9581e2026f036a79fc1c58bce5f1b87e4c4f0786ee50a49f890e94d0e529e5`
  khóa exact 10 sources và 3 non-manifest artifacts; verifier trả `valid=true`. Bộ 48 test WP10 có
  clean-room byte-identical rebuild, candidate accept/reject fixtures và tamper/path/symlink tests.
  Full repository gate đạt 288/288 tests, Ruff, `uv lock --check` (168 packages) và
  `git diff --check`; Graft đồng bộ ở 36 Python files/627 nodes/1.720 edges. Optional deep layer
  chưa build và không chặn gate.
- Independent milestone `QA-M0-WP10` kết luận **PASS với 0 blocker**. Closure này chỉ được ghi ở
  roadmap/memory; package WP10 hash-pinned giữ nguyên các status string lịch sử `AWAITING_QA`.
  G0.4 hiện formally closed/non-blocking. D-01…D-05 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`,
  `split_authorized=false`, `training_authorized=false`; không final split, training hoặc raw relabel.

## M0-WP11 D-04 rare-class decision support — QA PASS package only, owner decision pending

- Package dùng đúng policy hiện hành `box_count < 50`: 20 class IDs
  `1, 4, 9, 11, 15, 19, 21, 25, 27, 28, 29, 31, 33, 37, 42, 43, 44, 47, 48, 51`. Policy này tách
  biệt với WP8 analytic flag `image_count < 100` gồm 29 lớp.
- Matrix 52 lớp và subset 20 lớp ghi raw image/box counts, raw train/test counts mô tả,
  post-quarantine eligible counts, representative stems, G0.4 effect, WP8 taxonomy status,
  group uncertainty, recommendation/confidence và owner state. Raw split không phải independent
  evidence; effective independent support là `UNKNOWN_PENDING_D02`; proxy không phải group truth.
- Recommendation deterministic: 5 lớp `COLLECT_MORE` (`21, 33, 44, 47, 51`), 15 lớp
  `OWNER_REVIEW_REQUIRED`, và 32 lớp ngoài scope `KEEP_NATIVE_PENDING_D03`. Không auto merge;
  D-03 và toàn bộ owner state vẫn `PENDING`/`UNAPPROVED`.
- Class 44 (`W.233`) pin/render đủ 3/3 instance trên stems `0670`–`0672`; class 51 (`W.246c`)
  pin/render đủ 5/5 instance trên stems `0530`–`0534`. Lineage giữ exact image/label SHA-256,
  label line, normalized bbox và pixel bbox; atlas gồm đúng 2 trang/8 hàng đã được visual-readback.
- WP10 registry được áp dụng fail-closed: cả stem `0248` bị loại, class 49 còn 119 eligible images/
  219 eligible boxes từ 120/221 raw, taxonomy class 49 vẫn hiện diện và WP9 derived clip không phải
  training sample. WP10 artifacts không bị sửa.
- Contract: `references/dataset01/wp11_d04_rare_class_contract.json`; builder/verifier:
  `scripts/build_wp11_d04_rare_class_review.py`; report:
  `docs/review/wp11_d04_rare_class_report.md`. Manifest SHA-256
  `61b5bfbb92ac872ae4d5bfc6d508426f59b4065d4cd2f43f3f979e664095b465` khóa đúng 28 sources và
  9 non-manifest artifacts; verifier trả `valid=true`. Bộ 48 targeted tests pass và bao phủ
  deterministic/clean-room rebuild, exact source/artifact rosters, count/hash/bbox drift, thiếu
  class/visual, class49 eligibility, semantic merge/governance promotion, recommendation rollback,
  path traversal và symlink escape. Full repository gate đạt 336/336 tests, Ruff,
  `uv lock --check` (168 packages) và `git diff --check`; Graft đồng bộ ở 38 Python files,
  688 nodes và 1.875 edges. Optional deep layer chưa build và không chặn gate.
- Independent milestone `QA-M0-WP11` kết luận **PASS với 0 blocker**. Closure chỉ ghi ở
  roadmap/memory; package hash-pinned giữ nguyên status lịch sử
  `M0_WP11_AWAITING_QA_D04_DECISION_SUPPORT_ONLY`. PASS này chỉ xác nhận package, không phê duyệt
  khuyến nghị hay owner decision. D-04 vẫn `PENDING_OWNER_DECISION`, Gate 0 vẫn `BLOCKED`,
  `split_authorized=false`, `training_authorized=false`; không relabel, final split, training,
  upload, deploy hoặc publish.

## M0-WP12-R1 D02-B cross-split manual review Batch B — QA PASS, provisional evidence only

- Selection giữ đúng 250 canonical WP5 rows kế tiếp có `cross_split=True` và
  `review_status=PENDING`, loại exact 100-edge WP7 Batch-A roster và giữ WP5 order. Roster chạy từ
  `edge_000315` đến `edge_001033`, gồm 500 endpoint rows/1.553 boxes; stem quarantine `0248`
  không xuất hiện. Canonical WP5/WP7/WP10/WP11 artifacts không bị sửa.
- PM đã trực tiếp review 250/250 cặp. Capture outcomes là 240
  `SAME_CAPTURE_CANDIDATE`, 8 `NOT_RELATED`, 2 `UNRESOLVED` tại `edge_000535` và
  `edge_000539`; physical-sign outcomes là 235 `SAME_PHYSICAL_SIGN_CANDIDATE`, 14
  `NOT_RELATED`, 1 `UNRESOLVED` tại `edge_000539`; confidence là 243 `HIGH`, 7 `MEDIUM`.
  Capture và physical-sign hypotheses độc lập; adjacency/proxy không phải creator/session/group
  identity.
- Independent QA xác nhận 0 blind capture-decision disagreements và 50/50 trang atlas đạt visual
  review, nhưng trả FAIL do ba blocker verifier: atlas chưa bind bằng tái sinh byte, layout chưa
  bind deep-exact, và review-notes chưa có trusted source anchor. Không có quyết định thị giác nào
  bị đổi trong R1.
- R1 khóa exact atlas roster `index.html` + `page_001.jpg`…`page_050.jpg`, reject extra/missing/
  wrong-type/symlink; verifier tái sinh index, 50 JPEG và layout audit trong isolated temp rồi
  byte/deep-compare. Review-notes SHA-256
  `27adbf366cfbfd2c03c1025e82bd6cef26e1b353e1e50340ddc6d7a5f9ed75b4` được pin trong source
  contract cùng exact counts và unresolved IDs. Regression coherent rollback của `edge_000539`
  bị từ chối dù mọi downstream artifact/manifest được dựng lại.
- Pre-repair manifest `0b5c90de79326bc7cccb18830078c5aef5ec46bd8559ca1f909e3a5878456347`
  đã bị supersede. R1 manifest SHA-256
  `8e576954bc3de456704aecdb67e8625d8621ca017fb08e3b866635db6afcc0f0` khóa đúng 12 sources và
  56 non-manifest artifacts; 55 WP12-R1 targeted tests và 391/391 tests toàn repo pass, cùng Ruff,
  `uv lock --check` (168 packages), `git diff --check` và Graft 40 files/755 nodes/2.082 edges.
  Coverage gồm clean-room byte rebuild và tamper matrix mở rộng. PM post-repair đã đọc lại đủ
  50/50 atlas pages: đủ rows, bbox overlays, decision text và không thấy clipping. Independent
  `QA-M0-WP12-R1` sau đó trả PASS với 0 blocker, từ chối đủ 18/18 attack classes và xác nhận
  clean-room byte-identical. Hash-pinned package vẫn giữ historical status
  `WP12_R1_AWAITING_QA_BATCH_B_PM_PROVISIONAL_REVIEW`; closure chỉ nằm trong routing docs.
- Hai overlay WP7+WP12 phủ 350 pairs nhưng canonical WP5 vẫn có 3.172 `PENDING`. Ngoài hai overlay
  còn 2.822 pending edges, trong đó 676 cross-split; 589 sequences vẫn `PENDING`. D02-A metadata
  vẫn ưu tiên, D02-B budget chưa duyệt, D-02 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`, không final/
  transitive `group_id`, split hay training.

## M0-WP13 D02-B cross-split manual review Batch C — QA PASS, provisional evidence only

- Selection giữ đúng 250 canonical WP5 rows kế tiếp có `cross_split=True` và
  `review_status=PENDING`, loại exact WP7 Batch-A và WP12 Batch-B rosters, đồng thời giữ WP5 order
  356…605. Roster chạy từ `edge_001041` đến `edge_001882`, gồm 500 endpoint rows/1.079 boxes;
  stem quarantine `0248` không xuất hiện.
- PM đã trực tiếp đọc 250/250 cặp và đọc lại đủ 50/50 atlas pages sau annotation. Capture outcome:
  241 `SAME_CAPTURE_CANDIDATE`, 9 `NOT_RELATED`; physical-sign outcome:
  240 `SAME_PHYSICAL_SIGN_CANDIDATE`, 10 `NOT_RELATED`; toàn bộ confidence `HIGH`.
  `edge_001802` giữ đúng phân biệt capture continuity với physical-sign identity.
- Package mới không sửa WP5/WP7/WP12. Trusted notes hash
  `e3c6414feee901b39e44fb406ac25571e429c2c72b803b6909c7641a32dfff69`; manifest SHA-256
  `5db80e215f318a6b782d813b4560c20e35e4f3e51ef0423d7298f4818ea3db65` khóa 16 sources và
  56 non-manifest artifacts. Verifier dựng atlas/index/layout trong isolation rồi byte/deep-compare,
  từ chối roster/path/type/symlink/semantic/geometry/pixel/index tamper và coherent notes rollback.
- 60/60 targeted WP13 tests và 450/450 full-suite tests pass, gồm exact exclusion của WP7/WP12,
  đủ 18/18 attack classes kế thừa từ WP12, clean-room byte determinism và negative attack coverage.
  Ruff, `uv lock --check` (168 packages), `git diff --check` đều pass; Graft đồng bộ ở 42 Python
  files/799 nodes/2.188 edges. Independent `QA-M0-WP13` sau đó trả PASS với 0 blocker, tự đọc lại
  50/50 pages và 250/250 panels, từ chối 18/18 CLI attacks kể cả coherent/count-preserving
  semantic rollback, và dựng lại byte-identical 56/56 artifacts. Package hash-pinned vẫn giữ
  historical status `WP13_AWAITING_QA_BATCH_C_PM_PROVISIONAL_REVIEW`; closure chỉ nằm trong routing docs.
- Ba overlay WP7+WP12+WP13 phủ 600 pairs nhưng canonical WP5 vẫn có 3.172 `PENDING`. Ngoài ba overlay
  còn 2.572 pending edges, trong đó 426 cross-split; 589 sequences vẫn `PENDING`. D02-A metadata
  vẫn ưu tiên, D02-B budget chưa duyệt, D-02 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`, không final/
  transitive `group_id`, split hay training authorization.

## M0-WP14 D02-B cross-split manual review Batch D — QA PASS, provisional evidence only

- Selection giữ đúng 250 canonical WP5 rows kế tiếp có `cross_split=True` và
  `review_status=PENDING`, loại exact WP7/WP12/WP13 rosters và giữ WP5 order 606…855. Roster
  `edge_001894`…`edge_002664` gồm 500 endpoints/1.413 boxes/365 unique stems; stem quarantine
  `0248` không xuất hiện.
- PM đã trực tiếp đọc 250/250 cặp và đọc lại đủ 50/50 atlas pages sau annotation. Capture outcome:
  246 `SAME_CAPTURE_CANDIDATE`, 4 `NOT_RELATED` (`edge_001968`, `edge_002032`, `edge_002453`,
  `edge_002568`). Physical-sign outcome: 238 `SAME_PHYSICAL_SIGN_CANDIDATE`, 12 `NOT_RELATED`
  (bốn edge trên cộng `edge_002107`, `edge_002108`, `edge_002161`, `edge_002162`, `edge_002172`,
  `edge_002173`, `edge_002262`, `edge_002263`). Toàn bộ confidence `HIGH`; capture và physical
  identity vẫn là hai giả thuyết riêng.
- Trusted notes hash `ac63ad6fafc767a81263ad181fa3a96a19d8c493e648d145abedc641bc09b84e`;
  manifest SHA-256 `ea4667c2ea18bc6fff23ce23beffe5b27372e494160fa9d6ffbc86c3cb3f2dc5` khóa 20 sources và
  56 non-manifest artifacts. Verifier fail-closed trên exact rosters, path/type/symlink,
  deterministic isolated index/JPEG/layout regeneration, pixel/index/layout/coverage/bbox/context/
  geometry, trusted-note rollback và exact exceptional edge IDs.
- 65/65 targeted WP14 tests pass, gồm đủ 18 attack classes, clean-room 56/56 byte determinism,
  coherent rollback và count-preserving swap rejection. Full repository gate pass 516/516 tests,
  Ruff, `uv lock --check` (168 packages) và `git diff --check`; Graft đồng bộ ở 44 Python files,
  845 nodes/2.298 edges. Independent `QA-M0-WP14` sau đó PASS với `0 blockers`: 18/18 CLI attacks
  bị từ chối, coherent rebuild và count-preserving exact-ID swap đều thất bại, 56/56 artifacts
  clean-room byte-identical, và reviewer độc lập đã đọc 50/50 atlas pages cùng 250/250 panels.
  Package hash-pinned giữ nguyên historical status `WP14_AWAITING_QA_BATCH_D_PM_PROVISIONAL_REVIEW`;
  closure chỉ được ghi ở routing docs. D-02 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`, không tạo final/
  transitive `group_id`, split hoặc training authorization.
- Bốn overlay WP7+WP12+WP13+WP14 phủ 850 pairs nhưng canonical WP5 vẫn có 3.172 `PENDING`. Ngoài
  bốn overlay còn 2.322 pending edges, trong đó 176 cross-split; 589 sequences vẫn `PENDING`.
  D02-A metadata vẫn ưu tiên và D02-B budget chưa được duyệt.

## M0-WP15 D02-B cross-split manual review Batch E — QA PASS, provisional evidence only

- Selection giữ đúng toàn bộ 176 canonical WP5 rows cross-split còn lại sau exact
  WP7/WP12/WP13/WP14 prefix, theo WP5 order 856…1.031. Roster `edge_002665`…`edge_003178`
  gồm 352 endpoints/992 boxes; stem quarantine `0248` không xuất hiện.
- PM đã trực tiếp đọc 176/176 cặp và đọc lại đủ 36/36 atlas pages sau annotation. Pagination được
  khóa ở 35 pages × 5 rows + page 36 × 1 row. Capture outcome: 176
  `SAME_CAPTURE_CANDIDATE`. Physical-sign outcome: 173 `SAME_PHYSICAL_SIGN_CANDIDATE` và 3
  `NOT_RELATED` (`edge_002798`, `edge_002847`, `edge_002901`). Toàn bộ confidence `HIGH`;
  đây vẫn chỉ là hai giả thuyết provisional riêng biệt.
- Trusted notes SHA-256 `740fe42e79ec6e2a8c921ac254c31172188c5860898b81f205a494843f6e0bd7`;
  manifest SHA-256 `032aee9da985c5dcb772ddd1c73fa9e4e6794e1beb5107fdb49b0168948a241d`
  khóa 24 sources và 42 non-manifest artifacts. Verifier fail-closed trên exact roster/page
  cardinality, path/type/symlink, isolated regeneration, byte/layout/coverage/bbox/context,
  trusted-note rollback và exact exceptional edge IDs.
- 69/69 targeted WP15 tests pass, gồm 18 attack classes, coherent rollback,
  count-preserving exception swap rejection và clean-room byte determinism. Full repository gate
  pass 585/585 tests, Ruff, `uv lock --check` (168 packages) và `git diff --check`; Graft đồng bộ
  ở 46 Python files, 892 nodes/2.415 edges. Mọi CLI verifier WP5, WP7…WP14 và WP15 đều trả
  `valid=true`. Independent `QA-M0-WP15` đã PASS với 0 blocker và 0 functional/package finding:
  QA tự hash 704 raw bindings, đọc đủ 36/36 pages và 176/176 panels, từ chối 18/18 attacks và dựng
  lại byte-identical 42/42 artifacts. Package hash-pinned vẫn giữ historical status
  `WP15_AWAITING_QA_BATCH_E_PM_PROVISIONAL_REVIEW`; closure chỉ được ghi trong routing docs.
- Năm overlay phủ 1.026 pairs nhưng canonical WP5 vẫn có 3.172 `PENDING`. Ngoài năm overlay còn
  2.146 pending edges và không còn cross-split edge; 589 sequences vẫn `PENDING`. D-02 vẫn
  `PENDING`, Gate 0 vẫn `BLOCKED`; không có final/transitive `group_id`, split hoặc training
  authorization.

## M0-WP16-R1 D02-C sequence review Batch A — QA PASS, provisional evidence only

- Selection là exact first 100 quarantine-eligible canonical `PENDING` sequences theo thứ tự
  WP5: `proxy_sequence_0001`…`proxy_sequence_0101`, bỏ nguyên hàng
  `proxy_sequence_0050` vì chứa stem quarantine `0248`; không cắt chuỗi hoặc đánh dấu hàng đó đã
  review. Exclusion registry giữ hàng 50 ở `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`. Overlay phủ 100 sequences/339 unique member frames; 489
  sequences còn ngoài overlay và cả 589 canonical rows vẫn `PENDING`.
- PM đã trực tiếp đọc 100/100 prepared atlas pages và toàn bộ 339/339 member frames trước khi pin
  quyết định; post-build đã đọc lại pages 1/50/100. Deterministic verifier tái dựng và deep/byte-
  compare toàn bộ index + 100 JPEG pages cùng layout. Capture outcome là 100
  `CONTINUOUS_CANDIDATE`; physical-sign outcome là 40
  `SAME_PHYSICAL_SIGN_CANDIDATE` và 60 `MULTIPLE_SIGNS`; toàn bộ confidence `HIGH`. Đây là
  provisional visual evidence, không phải creator/session metadata hay physical-sign ground truth.
- Trusted notes SHA-256 `d673ac00d0345fcf1fc0b46c2e9e3396ba97d3bd17259ce7a4d370756ed38e9d`;
  manifest R1 SHA-256 `f3e3fb7a13631ef60b9046f745c07cb39ff3df501c18d5e15e79ee2e505964bc`
  khóa exact 19 sources và 107 non-manifest artifacts (`19.105.566` bytes). QA nội dung ban đầu
  xác nhận package PASS với 0 blocker, clean-room/rollback/swap đều PASS, nhưng phát hiện một
  finding P3 thực: manifest staged vẫn được chấp nhận khi có unknown top-level key. R1 khóa exact
  31 top-level fields và từ chối unknown key thường, unknown key mang ý nghĩa governance, hoặc
  missing key. Audit xác nhận source/artifact record đã được inherited verifier khóa exact nested
  keys; không thay đổi schema lồng nhau hay các verifier lịch sử. So với package trước R1, 106/107
  artifacts byte-identical; chỉ report tự sinh đổi để mô tả contract R1, và chỉ source builder đổi.
  Verifier fail-closed
  trên source/artifact roster, quarantine exclusion, path/type/symlink, raw image/label lineage,
  isolated atlas regeneration, byte/layout/coverage/bbox/context và forbidden final group/split
  fields.
- 32/32 targeted WP16 tests pass, gồm exact 21 attack classes, coherent rollback rejection,
  count-preserving decision-ID swap rejection và clean-room 107/107 artifact byte determinism.
  Full repository gate pass 617/617 tests, Ruff, `uv lock --check` (168 packages) và
  `git diff --check`. Mọi CLI verifier WP5, WP7, WP10…WP16 đều trả `valid=true`; Graft đồng bộ ở
  48 Python files, 943 nodes và 2.564 edges. README và manifests WP5/WP7/WP10…WP15 giữ nguyên
  hash đã pin.
- Status package là `WP16_AWAITING_QA_SEQUENCE_BATCH_A_PM_PROVISIONAL_REVIEW`. D-02 vẫn
  `PENDING`, Gate 0 vẫn `BLOCKED`, `training_authorized=false`; chưa tạo final/transitive
  `group_id`, split hoặc training authorization. Independent `QA-M0-WP16-R1` đã PASS với 0
  blocker và không có P0/P1/P2/P3 mới: 32/32 targeted tests, 617/617 full-suite tests, 21 attack
  classes và clean-room 107/107 đều PASS. Closure chỉ ghi trong routing docs; package hash-pinned
  giữ historical status `AWAITING_QA`. PASS này chỉ xác nhận provisional evidence package.

## M0-WP17 D02-C sequence review Batch B — QA PASS, provisional evidence only

- Deterministic selection là exact next 100 quarantine-eligible canonical `PENDING` sequences sau
  WP16: `proxy_sequence_0102`…`proxy_sequence_0201`, không gap và không overlap. Builder xác minh
  WP16 selection là exact first-100 eligible prefix trước khi chọn Batch B. Hàng quarantine
  `proxy_sequence_0050` vẫn nguyên vẹn ở `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; stem `0248` không xuất hiện trong WP17.
- Overlay WP17 phủ 100 sequences/344 unique member frames/1.312 bbox occurrences. PM đã trực tiếp
  đọc 100/100 prepared atlas pages và 344/344 member frames, sau build đọc lại pages 1/50/100.
  Outcome provisional là 100 `CONTINUOUS_CANDIDATE`; physical-sign outcome là 91
  `MULTIPLE_SIGNS` và 9 `SAME_PHYSICAL_SIGN_CANDIDATE`; toàn bộ confidence `HIGH`. Đây không phải
  creator/session metadata hoặc physical-sign ground truth.
- Trusted notes SHA-256 `cdefee98149db85d4600cf7f69ee004d6f769ecc23bc6c57dce898732c2e4248`;
  manifest SHA-256 `374ada61066f70f8ff3ba282dba41229ad2c161303146edd83aba583591b144b`.
  Exact contract gồm 21 sources, 107 non-manifest artifacts, `18.636.827` artifact bytes và 31
  exact top-level manifest fields; nested source/artifact records cũng exact-key checked.
- Verifier fail-closed cho missing/unknown fields, nested record schema, roster/order, path
  traversal/symlink, hash/count, selection/exclusion/lineage/decision-ID semantics, same-count
  decision swap, coherent rollback, governance tamper, layout và atlas bytes. 28/28 targeted tests
  PASS với đúng 21 attack classes và clean-room 107/107 byte determinism. Full repository gate
  PASS 645/645 tests, Ruff, `uv lock --check` (168 packages) và `git diff --check`; mọi CLI
  verifier WP5/WP7/WP10–WP17 đều PASS. Graft đồng bộ ở 50 Python files/970 nodes/2.631 edges.
- Independent QA PASS routing-only với 0 blocker, không có severity finding mới, từ chối đủ 21/21
  attack classes, tái dựng clean-room 107/107 artifact byte-identical và xác nhận full suite
  645/645. Package/report hash-pinned vẫn giữ historical status
  `WP17_AWAITING_QA_SEQUENCE_BATCH_B_PM_PROVISIONAL_REVIEW`; không sửa để hồi tố verdict.
- WP16+WP17 overlays phủ 200/589 canonical sequences; 389 còn ngoài cả hai và toàn bộ 589 rows
  vẫn `PENDING`. QA PASS chỉ đóng package provisional WP17, không duyệt D-02, final/transitive
  `group_id`, split hoặc training authorization.

## M0-WP18 D02-C sequence review Batch C — QA PASS, provisional evidence only

- Deterministic derivation trước khi encode ID đã chứng minh union WP16+WP17 là exact first-200
  quarantine-eligible canonical prefix, rồi chọn exact next 100 sequence liên tục
  `proxy_sequence_0202`…`proxy_sequence_0301`, không gap/overlap. Whole-sequence quarantine
  `proxy_sequence_0050` vẫn `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; stem `0248` không xuất hiện trong WP18.
- Overlay phủ 100 sequences/400 unique member frames/944 bbox occurrences. PM đã trực tiếp đọc
  100/100 prepared atlas pages và 400/400 member frames, sau build đọc lại pages 1/50/100.
  Outcome provisional là 100 `CONTINUOUS_CANDIDATE`; physical-sign outcome là 70
  `MULTIPLE_SIGNS` và 30 `SAME_PHYSICAL_SIGN_CANDIDATE`; toàn bộ confidence `HIGH`. Đây không
  phải creator/session metadata hoặc physical-sign ground truth.
- Trusted notes SHA-256 `69eb2da7c8dadcb5d27aadc46fa90e7941a1798ac4dca790110e4f8484d0d915`;
  manifest SHA-256 `35bf843db7eb626404c81477efb509b2e4881a2cc7ea81fcee3187fcfab93649`;
  builder SHA-256 `e9a232bf2945c04abccc92665b0726d450e7091b2057c5fd5c71e43b22ea5146`;
  generated report SHA-256 `e6bd7fc4ff775bfa68f4576f59128332de851883c022398e4675c4adaf31ddc4`.
  Exact contract gồm 23 sources, 107 non-manifest artifacts, `20.715.246` artifact bytes và 31
  exact top-level manifest fields; nested source/artifact records exact-key checked.
- Verifier fail-closed cho semantic/prefix/schema/roster/order/path/symlink/hash/decision/swap/
  rollback/governance/layout/pixel attacks. Targeted suite PASS 29/29 với đúng 22 attack classes,
  gồm WP17-prefix tamper, và clean-room 107/107 byte determinism. Full repository gate PASS
  674/674 tests; Ruff, `uv lock --check` (168 packages), `git diff --check` và mọi CLI verifier
  WP5/WP7/WP10–WP18 đều PASS. Graft đồng bộ ở 52 Python files/997 nodes/2.698 edges.
- WP16+WP17+WP18 overlays phủ 300/589 canonical sequences; 289 còn ngoài cả ba, gồm 288 sequence
  quarantine-eligible và whole quarantined `proxy_sequence_0050`. Toàn bộ 589 canonical rows vẫn
  `PENDING`. Status là `WP18_AWAITING_QA_SEQUENCE_BATCH_C_PM_PROVISIONAL_REVIEW`; D-02 và Gate 0
  vẫn blocked, `training_authorized=false`, không final/transitive `group_id` hay split.
- Independent QA PASS routing-only với 0 blocker và không có severity finding; tái xác nhận exact
  selection/counts, từ chối đủ 22/22 attack classes, clean-room 107/107 byte-identical và full
  suite 674/674. Package/report hash-pinned giữ nguyên historical status; không sửa để hồi tố
  verdict.

## M0-WP19 D02-C sequence review Batch D — QA PASS, provisional evidence only

- Deterministic derivation chứng minh WP16+WP17+WP18 là exact first-300 quarantine-eligible
  canonical prefix, rồi chọn exact next 100 sequence liên tục `proxy_sequence_0302`…
  `proxy_sequence_0401`, không gap/overlap. Whole-sequence quarantine `proxy_sequence_0050` vẫn
  `PENDING`, `overlay_reviewed=False`, reason `CONTAINS_QUARANTINED_STEM_0248`; stem `0248` không
  xuất hiện trong WP19.
- Overlay phủ 100 sequences/422 unique member frames/824 bbox occurrences. PM đã trực tiếp đọc
  100/100 prepared atlas pages và 422/422 member frames, sau build đọc lại pages 1/50/100.
  Outcome provisional là 100 `CONTINUOUS_CANDIDATE`; physical-sign outcome là 61
  `MULTIPLE_SIGNS` và 39 `SAME_PHYSICAL_SIGN_CANDIDATE`; toàn bộ confidence `HIGH`. Đây không
  phải creator/session metadata hoặc physical-sign ground truth.
- Trusted notes SHA-256 `627e0598d077ccb568c252b7980833cd317803398385fce61e467c3e2de483b1`;
  manifest SHA-256 `6796c3a16b2af347f0a74a06cde4477b214d97233d0d38848d9077933c7f712f`;
  selection SHA-256 `a63c8125fd570d19af5719bf11800d6b9ea70e3a03596cf195c63753e0c0296f`;
  builder SHA-256 `4a434d670c7da9e76cf3d0972f2ae3a8e36ba5fd86596741596cff175401508f`;
  generated report SHA-256 `9442725d3b25492ae2f2f21768e91ea29d652e6970b7a38dddb62de5e806dfd9`.
  Exact contract gồm 25 sources, 107 non-manifest artifacts, `20.702.974` artifact bytes và 31
  exact top-level manifest fields; nested source/artifact records exact-key checked.
- Verifier fail-closed cho semantic/prefix/schema/roster/order/path/symlink/hash/decision/swap/
  rollback/governance/layout/pixel attacks. Targeted suite PASS 29/29 với đúng 22 attack classes,
  gồm WP18-prefix tamper, và clean-room 107/107 byte determinism. Mọi CLI verifier
  WP5/WP7/WP10–WP19 đều PASS; full repository gate PASS 703/703 tests; Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Graft đồng bộ ở 54 Python files,
  1.024 nodes và 2.765 edges.
- WP16+WP17+WP18+WP19 overlays phủ 400/589 canonical sequences; 189 còn ngoài cả bốn, gồm 188
  sequence quarantine-eligible và whole quarantined `proxy_sequence_0050`. Toàn bộ 589 canonical
  rows vẫn `PENDING`. Status là `WP19_AWAITING_QA_SEQUENCE_BATCH_D_PM_PROVISIONAL_REVIEW`; D-02
  và Gate 0 vẫn blocked, `training_authorized=false`, không final/transitive `group_id` hay split.
- Independent QA PASS routing-only với 0 findings; targeted suite 29/29 và full suite 703/703.
  Package/report hash-pinned giữ nguyên historical status; không sửa để hồi tố verdict. PASS này
  chỉ đóng package provisional WP19, không duyệt D-02, group truth, split hoặc training.

## M0-WP20 D02-C sequence review Batch E — QA PASS, provisional evidence only

- Deterministic derivation chứng minh WP16…WP19 là exact first-400 quarantine-eligible canonical
  prefix, rồi chọn exact next 100 sequence liên tục `proxy_sequence_0402`…
  `proxy_sequence_0501`, không gap/overlap. Whole-sequence quarantine `proxy_sequence_0050` vẫn
  `PENDING`, `overlay_reviewed=False`, reason `CONTAINS_QUARANTINED_STEM_0248`; stem `0248` không
  xuất hiện trong WP20.
- Overlay phủ 100 sequences/406 unique member frames/1.287 bbox occurrences. PM đã trực tiếp đọc
  100/100 prepared atlas pages và 406/406 member frames, sau build đọc lại pages 1/50/100.
  Outcome provisional là 100 `CONTINUOUS_CANDIDATE`; physical-sign outcome là 81
  `MULTIPLE_SIGNS` và 19 `SAME_PHYSICAL_SIGN_CANDIDATE`; toàn bộ confidence `HIGH`. Đây không
  phải creator/session metadata hoặc physical-sign ground truth.
- Trusted notes SHA-256 `04a70bfa693c105da29ac263ab8f24a1e030b489b8379078c79e0dd3f21e6f8b`;
  manifest SHA-256 `4523c698ff948ee2adaf879195662caec25ac80280cceb0aaaf91ae72fe89a6c`;
  selection SHA-256 `b99abd53de497e74e42a75396be9f565c391977c4f35f633975cba3081c3bfc3`;
  builder SHA-256 `699d76a3378f89af5b23bb328fc2d381c15c1544cbfc4c1d6cf6c87b1514af7f`;
  generated report SHA-256 `a3d23524323554181822d7448966c5b34a86672cfc3d23c7fa5eb7e834ecf4ba`.
  Exact contract gồm 27 sources, 107 non-manifest artifacts và `20.410.750` artifact bytes.
- Verifier fail-closed cho semantic/prefix/schema/roster/order/path/symlink/hash/decision/swap/
  rollback/governance/layout/pixel attacks. Targeted suite PASS 29/29 với đúng 22 attack classes,
  gồm WP19-prefix tamper, và clean-room 107/107 byte determinism. Mọi CLI verifier
  WP5/WP7/WP10–WP20 đều PASS; full repository gate PASS 732/732 tests; Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Graft đồng bộ ở 56 Python files,
  1.051 nodes và 2.832 edges.
- WP16…WP20 overlays phủ 500/589 canonical sequences; 89 còn ngoài cả năm, gồm 88 sequence
  quarantine-eligible và whole quarantined `proxy_sequence_0050`. Toàn bộ 589 canonical rows vẫn
  `PENDING`. Status là `WP20_AWAITING_QA_SEQUENCE_BATCH_E_PM_PROVISIONAL_REVIEW`; D-02 và Gate 0
  vẫn blocked, `training_authorized=false`, không final/transitive `group_id` hay split.
- Independent QA PASS routing-only với 0 findings và full suite 732/732. Package/report
  hash-pinned giữ nguyên historical status; không sửa để hồi tố verdict. PASS này chỉ đóng
  provisional package WP20, không duyệt D-02, group truth, split hoặc training.

## M0-WP21 D02-C final eligible sequence review batch — QA PASS, provisional evidence only

- Deterministic derivation chứng minh WP16…WP20 là exact first-500 quarantine-eligible canonical
  prefix, rồi chọn toàn bộ residual `eligible[500:]`: 88 sequence liên tục
  `proxy_sequence_0502`…`proxy_sequence_0589`, không gap/overlap. Whole-sequence quarantine
  `proxy_sequence_0050` vẫn `PENDING`, `overlay_reviewed=False`, reason
  `CONTAINS_QUARANTINED_STEM_0248`; stem `0248` không xuất hiện trong WP21.
- Overlay phủ 88 sequences/363 unique member frames/1.068 bbox occurrences. PM đã trực tiếp đọc
  88/88 prepared atlas pages và 363/363 member frames, sau build đọc lại pages 1/44/88. Outcome
  provisional là 88 `CONTINUOUS_CANDIDATE`; physical-sign outcome là 60 `MULTIPLE_SIGNS` và 28
  `SAME_PHYSICAL_SIGN_CANDIDATE`; toàn bộ confidence `HIGH`. Đây không phải creator/session
  metadata hoặc physical-sign ground truth.
- Trusted notes SHA-256 `8acdfdb0041214f933eb4933cbddfd97bc90868361c4b9351975b6dacbb3e8c1`;
  manifest SHA-256 `7ed7e1355ae1dfc88ec81b7f580aad3bf0874b59832708652ad1ba02265d4e4c`;
  selection SHA-256 `40c7c7d9c94767b2b6d82bd9d2d134aa74af0afd7f62ce5ed470e55ab9efbc68`;
  builder SHA-256 `7a3184f94c2b5f77b075069bec50a8354898f08bd6dad6eb3d4424a1ab8b7761`;
  generated report SHA-256 `44c7526b48997669ee3553d967d237cbc5f41ef7291373aed8c014b68545b17b`.
  Exact contract gồm 29 sources, 95 non-manifest artifacts và `17.536.294` artifact bytes.
- Verifier fail-closed cho semantic/prefix/schema/roster/order/path/symlink/hash/decision/swap/
  rollback/governance/layout/pixel attacks. Targeted suite PASS 29/29 với đúng 22 attack classes,
  gồm WP20-prefix tamper, và clean-room 95/95 byte determinism. Mọi CLI verifier
  WP5/WP7/WP10–WP21 đều PASS; full repository gate PASS 761/761 tests; Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Graft đồng bộ ở 58 Python files,
  1.078 nodes và 2.899 edges.
- WP16…WP21 overlays phủ đủ 588/588 quarantine-eligible canonical sequences. Chỉ whole
  quarantined `proxy_sequence_0050` còn ngoài overlay; toàn bộ 589 canonical rows vẫn `PENDING`.
  Status là `WP21_AWAITING_QA_FINAL_ELIGIBLE_SEQUENCE_BATCH_PM_PROVISIONAL_REVIEW`; D-02 và Gate
  0 vẫn blocked, `split_authorized=false`, `training_authorized=false`, không final/transitive
  `group_id`.
- Independent QA kết luận **PASS với 0 findings**: exact 588/588 eligible coverage, 761/761 full
  tests, mọi verifier/pin/preservation check và clean-room 95/95 đều PASS. Closure là routing-only;
  package/report hash-pinned vẫn giữ historical `AWAITING_QA` status và không được sửa hồi tố.

## M0-WP22 D02-D remaining-edge manual reconciliation Batch A — independent QA PASS

- Read-only derivation chứng minh canonical residual có đúng 2.146 unique non-cross-split PENDING
  edges sau khi loại sáu WP5-reviewed rows và exact 1.026 QA-passed cross-split overlay rows.
  `edge_000242`/`edge_000243` chạm stem `0248` vẫn residual/PENDING nhưng bị loại nguyên vẹn; queue
  review-eligible còn 2.144 rows. Selection là exact first 250 rows theo WP5 order,
  `edge_000002`…`edge_000378`, 500 endpoints/903 bbox, không stem `0248` và không cross-split.
- PM trực tiếp đọc 50/50 atlas pages và 250/250 pair panels. Provisional outcomes gồm 240
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE` và 10 `NOT_RELATED`, tất cả confidence
  `HIGH`. WP16–WP21 evidence được pin chỉ làm context/risk; sequence context không sinh edge
  decision hoặc group truth.
- Trusted notes SHA-256 `c49c00bc85bbc0bc1cfc4683d9dbbd6403705a42600a1251e46e7ade949c6a27`;
  selection SHA-256 `af70edc35a2a925f4e23bd8ce2e481c7fdf6e18f1c904c963561c412ac74d6aa`;
  manifest SHA-256 `7086371d65d1389c26541a3621745e0eadb9df7bfe62ca3dab34ffbb45e3b487`.
  Exact contract gồm 52 sources, 56 non-manifest artifacts và 54.312.346 artifact bytes.
- Official verifier `valid=true`; targeted suite PASS 45/45 với 18 attack classes và clean-room
  56/56 byte determinism. Full repository gate PASS 806/806; Ruff, `uv lock --check` và
  `git diff --check` PASS; mọi historical verifier WP5/WP7/WP10–WP22 đều `valid=true`. Graft
  check-clean tại 60 Python files, 1.121 nodes và 2.998 edges; optional deep layer chưa build.
- Canonical WP5 vẫn 3.172 PENDING edges; 1.896 PENDING edges còn ngoài WP7/WP12–WP15/WP22
  overlays, gồm hai cạnh quarantine, và zero cross-split. Cả 589 canonical sequences vẫn PENDING.
  Status dừng ở `WP22_AWAITING_QA_REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 vẫn
  blocked, split/training không được phép, không final/transitive `group_id`.
- Independent QA kết luận **PASS với 0 findings** sau khi xác nhận exact selection/decision/hash,
  preservation, mọi verifier, full gate 806/806 và clean-room 56/56. Closure là routing-only;
  package/report hash-pinned vẫn giữ historical `AWAITING_QA` status và không được sửa hồi tố.

## M0-WP23 D02-D remaining-edge manual reconciliation Batch B — independent QA FAIL

- Derivation sau exact WP22-prefix removal chứng minh residual có đúng 1.896 unique non-cross-split
  PENDING edges. `edge_000242`/`edge_000243` chạm stem `0248` vẫn residual/PENDING nhưng bị loại
  nguyên vẹn; queue review-eligible còn 1.894 rows. Selection là exact next 250 rows theo WP5 order,
  `edge_000379`…`edge_000760`, order 1.285…1.534, 500 endpoints/1.556 bbox, không stem `0248` và
  không cross-split.
- PM trực tiếp đọc 50/50 atlas pages và 250/250 pair panels. Provisional outcomes gồm 233
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE` và 17 `NOT_RELATED`, tất cả confidence
  `HIGH`. WP16–WP21 evidence được pin chỉ làm context/risk; sequence context không sinh edge
  decision hoặc group truth.
- Trusted notes SHA-256 `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8`;
  selection SHA-256 `e6913b2eeba22c990cef393490f8d8cb2caaa6745b2045e6edf64c3a6f9973a6`;
  annotations SHA-256 `2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be`;
  manifest SHA-256 `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd`.
  Exact contract gồm 56 sources, 56 non-manifest artifacts và 54.019.044 artifact bytes.
- Official verifier `valid=true`; targeted suite PASS 45/45 với đúng 18 attack classes và
  clean-room 56/56 byte determinism. Full repository gate PASS 851/851; Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Mọi historical verifier
  WP5/WP7/WP10–WP23 đều `valid=true`. Graft check-clean tại 62 Python files, 1.164 nodes và 3.097
  edges; optional deep layer chưa build.
- Canonical WP5 vẫn 3.172 PENDING edges; 1.646 PENDING edges còn ngoài
  WP7/WP12–WP15/WP22/WP23 overlays, gồm hai cạnh quarantine, và zero cross-split. Cả 589 canonical
  sequences vẫn PENDING. Status dừng ở
  `WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW`; D-02/Gate 0 vẫn blocked,
  split/training không được phép, không final/transitive `group_id`. Đây là historical package đã
  QA FAIL; correction chỉ được phát hành append-only qua WP23-R1.
- Independent QA kết luận **FAIL** với đúng một High finding và zero Critical/Medium/Low finding:
  `edge_000664` (WP5 order 1476, page 039 slot 2, raw 0671→0672) bị gán sai `NOT_RELATED` dù raw
  cho thấy cùng camera tiến nhẹ trong cùng cảnh và cùng năm class `7 10 17 19 44`.
  `strong_candidate`, MAE `6.303241`, dHash `6`, histogram `0.99600903` đều hỗ trợ correction.
  Technical/integrity gates vẫn PASS. Initial package được giữ nguyên byte-for-byte làm audit trail.

## M0-WP23-R1 D02-D Batch B one-edge correction — independent QA PASS

- Append-only correction overlay chỉ đổi decision/rationale của `edge_000664` thành
  `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence `HIGH`; 249 decision khác
  giữ nguyên. Tally mới là 234 same, 16 `NOT_RELATED`, 250 `HIGH`. Cả 16 `NOT_RELATED` còn lại đều
  có rationale rõ discontinuous scene hoặc non-matching physical signs.
- Exact selection vẫn là 250 edge `edge_000379`…`edge_000760`, 500 endpoints/1.556 bbox, zero
  cross-split, không stem `0248`; lineage và raw hash không thay đổi. R1 atlas 50 trang được tái
  sinh. Read-back trực quan pages 39/1/25/50 xác nhận R1 status/boundary, bbox và correction.
- Official verifier `valid=true`: 62 sources, 56 artifacts, 54.306.219 artifact bytes. Mọi 16
  historical/current verifier WP5/WP7/WP10–WP23 đều `valid=true`. Targeted R1 suite PASS 28/28
  với đúng 18 attack classes, semantic regression và clean-room 56/56; full repository gate PASS
  879/879. Ruff, `uv lock --check` (168 packages) và `git diff --check` PASS. Graft check-clean tại
  64 Python files, 1.198 nodes và 3.174 edges; optional deep layer chưa build.
- Initial→R1 manifest SHA-256:
  `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd` →
  `8b1ca3c9953209d5fc86a8b2265228e27adb63cb430d5c5f5f1375d8d6f86783`. Bảng 57 dòng hash
  manifest + toàn bộ 56 artifact nằm tại
  `docs/review/generated/wp23_r1_artifact_hash_delta.csv`.
- Independent delegated QA kết luận **PASS với 0 findings**. Closure chỉ được ghi ở routing docs;
  package hash-pinned giữ nguyên status lịch sử `WP23_R1_AWAITING_QA_REVIEW` và không sửa hồi tố.
  QA PASS này không phê duyệt D-02, group truth, split hoặc training.

## M0-WP24 D02-D remaining-edge manual reconciliation Batch C — independent QA PASS

- Read-only derivation loại exact QA-passed WP22/WP23-R1 prefixes khỏi canonical non-cross-split
  PENDING queue, chứng minh residual trước package là 1.646 rows. Hai cạnh quarantine
  `edge_000242`/`edge_000243` vẫn residual/PENDING nhưng bị loại nguyên vẹn. Selection là exact
  next 250 eligible rows theo WP5 order: `edge_000763`…`edge_001154`, order 1.535…1.784.
- Coverage gồm 500 endpoints, 323 unique stems, 1.581 endpoint bbox và 1.044 unique-stem bbox;
  endpoint split train/test là 470/30, proxy tiers là 132 strong/96 uncertain/22 adjacency-only,
  và có 55 nonempty sequence IDs. Selection có zero cross-split row và không stem `0248`.
- PM trực tiếp đọc 50/50 atlas pages và 250/250 pair panels. Provisional outcomes gồm 243
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE` và 7 `NOT_RELATED`, tất cả `HIGH`.
  Sequence evidence được pin làm context-only và không sinh edge decision hoặc group truth.
- Trusted notes SHA-256 `086f1c58acbe1434b5bf295576d24e4279fccb59e01f56ba5f3aafaec4508ab1`;
  selection SHA-256 `19194c430c03fcaa507646ca0065776e1279471e1b2ed240f05506f74f3b5c9d`;
  annotations SHA-256 `82d480a5f0aee86d92236c73a7651b0ed4068385c69a5bdb571ddc071dd10f6f`;
  manifest SHA-256 `e5f49a4c5840a6e682f2a7d0cc418183ec6f52d7b745b9f397b570d6770ceaea`.
  Exact contract gồm 67 sources, 56 non-manifest artifacts và 50.037.488 artifact bytes.
- Official verifier `valid=true`; targeted WP24 suite PASS 46/46. Combined
  WP22/WP23/WP23-R1/WP24 suites PASS 164/164; full repository gate PASS 925/925. Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Historical/current verifier
  WP22/WP23/WP23-R1/WP24 đều `valid=true` với đúng 52/56, 56/56, 62/56 và 67/56
  source/artifact contracts. Graft check-clean tại 66 Python files, 1.238 nodes và 3.265 edges;
  optional deep layer chưa build.
- Status dừng ở `WP24_AWAITING_QA_REVIEW`. Canonical WP5 vẫn 3.172 PENDING edges; 1.396 residual
  PENDING edges còn ngoài edge overlays, gồm hai cạnh quarantine, và zero cross-split. Cả 589
  canonical sequences vẫn `PENDING`. D-02 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`,
  `split_authorized=false`, `training_authorized=false`; không có final/transitive group truth.
- Independent delegated QA kết luận **PASS với 0 findings**. Closure chỉ được ghi ở routing docs;
  package hash-pinned giữ nguyên status lịch sử `WP24_AWAITING_QA_REVIEW` và không sửa hồi tố.
  QA PASS này không phê duyệt D-02, group truth, split hoặc training.

## M0-WP25 D02-D remaining-edge manual reconciliation Batch D — independent QA FAIL

- Read-only derivation loại exact QA-passed WP22/WP23-R1/WP24 prefixes khỏi canonical
  non-cross-split PENDING queue, chứng minh residual trước package là 1.396 rows. Hai cạnh
  quarantine `edge_000242`/`edge_000243` vẫn residual/PENDING nhưng bị loại nguyên vẹn. Selection
  là exact next 250 eligible rows theo WP5 order: `edge_001155`…`edge_001502`, order 1.785…2.034.
- Coverage gồm 500 endpoints, 307 unique stems, 1.090 endpoint bbox và 671 unique-stem bbox;
  endpoint split train/test là 468/32, proxy tiers là 142 strong/79 uncertain/29 adjacency-only,
  và có 58 nonempty sequence IDs. Selection có zero cross-split row, không stem `0248` và không
  `proxy_sequence_0050`; whole quarantined sequence vẫn nguyên vẹn ngoài selection.
- PM trực tiếp đọc 50/50 atlas pages và 250/250 pair panels. Provisional outcomes gồm 240
  `SAME_CAPTURE_CANDIDATE`/`SAME_PHYSICAL_SIGN_CANDIDATE` và 10 `NOT_RELATED`, tất cả `HIGH`.
  Sequence evidence được pin làm context-only và không sinh edge decision hoặc group truth.
- Trusted notes SHA-256 `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8`;
  selection SHA-256 `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`;
  annotations SHA-256 `990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5`;
  manifest SHA-256 `1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9`.
  Exact contract gồm 72 sources, 56 non-manifest artifacts và 51.739.615 artifact bytes.
- Official verifier `valid=true`; targeted WP25 suite PASS 46/46. Verifier fail-closed khóa 18
  attack classes, một semantic same-count decision-ID swap và clean-room rebuild 56/56
  byte-identical. Combined WP22/WP23/WP23-R1/WP24/WP25 suites PASS 210/210; full repository gate
  PASS 971/971. Cả 18 historical/current verifier WP5/WP7/WP10–WP25 đều `valid=true`. Ruff,
  `uv lock --check` (168 packages) và `git diff --check` PASS. Graft check-clean tại 68 Python
  files, 1.278 nodes và 3.356 edges; optional deep layer chưa build. README/model hashes và raw
  source-preservation proof vẫn khớp.
- Status dừng ở `WP25_AWAITING_QA_REVIEW`. Canonical WP5 vẫn 3.172 PENDING edges; 1.146 residual
  PENDING edges còn ngoài edge overlays, gồm hai cạnh quarantine, và zero cross-split. Cả 589
  canonical sequences vẫn `PENDING`. D-02 vẫn `PENDING`, Gate 0 vẫn `BLOCKED`,
  `split_authorized=false`, `training_authorized=false`; không có final/transitive group truth.
- Independent QA kết luận **FAIL** với đúng một `P1` và zero `P0`/`P2`/`P3`: `edge_001358`
  (batch position 144, WP5 order 1928, page 029 slot 4, stems 1365→1366) bị gán sai
  `NOT_RELATED`. Raw frames và labels cho thấy cùng road scene/cùng class-5 physical sign sau một
  dịch chuyển camera nhỏ; bbox class 5 đổi từ
  `(0.388021, 0.303704)/(0.036458, 0.055556)` sang
  `(0.406250, 0.313889)/(0.037500, 0.046296)`. `same_dimensions=true`, proxy `uncertain`, MAE
  `12.005787`, dHash `18`, histogram cosine `0.99375935` hỗ trợ correction. Technical/integrity
  checks vẫn PASS; toàn bộ initial WP25 package được giữ immutable làm QA-fail audit trail.

## M0-WP25-R1 D02-D Batch D one-edge correction — independent QA PASS

- Append-only overlay chỉ đổi decision/rationale của `edge_001358` thành
  `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence `HIGH`; 249 decision còn
  lại giữ nguyên. Effective tallies là 241 same, 9 `NOT_RELATED`, 250 `HIGH`; cả 9
  `NOT_RELATED` còn lại giữ rationale rõ discontinuous scene và non-matching physical signs.
- Selection vẫn byte-identical với initial WP25: 250 edges `edge_001155`…`edge_001502`, 500
  lineage endpoints, 1.090 bbox occurrences, zero cross-split, không stem `0248`, không
  `proxy_sequence_0050`. Whole quarantined sequence và hai cạnh `edge_000242`/`edge_000243` vẫn
  nguyên vẹn ngoài selection. R1 atlas 50 trang được tái sinh; visual readback page 029 slot 4 xác
  nhận đúng raw pair, bbox và corrected decision, không text overflow.
- Official verifier `valid=true`: 78 sources, 56 non-manifest artifacts, 52.026.143 artifact
  bytes. Manifest SHA-256
  `96a19417256c312c1ec005f13c5abccf85a1718d12ab0c729cb234baebfe9fe8`; selection
  `8cb67fb593d610978dcec472f0dbd0dc53b5ae1d416468b908f92ba94320e10f`; annotations
  `90e6016abcbba10df96c32625e84df3284a9c8a55daccae25771fe2159db8807`; one-row correction
  overlay `a1385c5a295b927887ffe73c29987d1c3487812d7d25b1a3aa9688c25f39ecd9`; QA record
  `e1e641ee6b36abd257d284d3231c6672934b6ed906964536352b5a8de706439d`.
- Targeted WP25-R1 suite PASS 29/29 với đúng 18 fail-closed attack classes, regression guard,
  exact raw-label anchors, correction-source pin và clean-room 56/56 byte determinism. Combined
  WP22/WP23/WP23-R1/WP24/WP25/WP25-R1 compatibility PASS 239/239; full repository gate PASS
  1.000/1.000. Cả 19 current/historical CLI verifier trong supported chain đều `valid=true`.
  Ruff, `uv lock --check` (168 packages) và `git diff --check` PASS. Graft rebuilt/check-clean tại
  70 Python files, 1.313 nodes và 3.435 edges; optional deep layer chưa build.
- Independent QA kết luận **PASS với 0 findings** sau direct raw frame/label readback, exact oracle
  checks, 18/18 fail-closed attack classes, clean-room 56/56, targeted 29/29, compatibility
  239/239, full suite 1.000/1.000 và tất cả 19 supported CLI verifiers. Closure routing-only;
  hash-pinned package giữ historical status `WP25_R1_AWAITING_QA_REVIEW`, initial WP25 giữ nguyên
  làm QA-fail audit trail. PASS không phê duyệt D-02, group truth, split hoặc training.

## M0-WP26 D02-D remaining-edge manual reconciliation Batch E — independent QA PASS

- Read-only derivation pin exact QA-passed chain WP22→WP23-R1→WP24→WP25-R1 và canonical
  1.026-row cross-split overlay, rồi chọn exact `eligible[1000:1250]`: 250 rows
  `edge_001505`…`edge_001850`, WP5 order 2.035…2.284, stems 1512→1513…1867→1868. Pre-batch
  residual là 1.146 rows gồm hai quarantine edges / 1.144 eligible; post-batch còn 896 rows gồm
  quarantine / 894 eligible.
- Coverage gồm 500 endpoints, 305 unique stems, 997 endpoint bbox occurrences và 600 unique-stem
  bbox occurrences. Endpoint split train/test là 472/28; proxy tiers 160 strong/68 uncertain/22
  adjacency-only; 55 nonempty sequence IDs. Selection có zero cross-split row, không stem `0248`
  và không `proxy_sequence_0050`; hai cạnh quarantine `edge_000242`/`edge_000243` vẫn nguyên vẹn
  ngoài selection.
- PM trực tiếp đọc 50/50 prepared atlas pages và 250/250 pair panels, rồi đọc lại mọi annotated
  exceptional page. Capture outcomes là 240 `SAME_CAPTURE_CANDIDATE` và 10 `NOT_RELATED`;
  physical-sign outcomes là 239 `SAME_PHYSICAL_SIGN_CANDIDATE` và 11 `NOT_RELATED`, tất cả
  `HIGH`. `edge_001644` là exact intentional capture-same/physical-not case; sequence context
  không sinh decision hoặc group truth.
- Official verifier `valid=true`: 83 sources, 56 non-manifest artifacts, 48.503.108 artifact bytes.
  Manifest SHA-256 `4e0ddff49a83baac0c41e6be28f376d09f2d887fd0742ac2efd439e46fdf62e7`;
  selection `70f9a1a77172eac59761d642cce2689c9bb5a5ba07dc87cea426f0814be51582`;
  annotations `be125fcc5b97ad9c0439b09543d00b62edcc1611c0bc750ae6bf7252b6d4ee70`;
  trusted notes `47178a56aa80d5da39e146e1319dea6015e4361161b1a1fe45b91e973dcdf64d`.
  Exact verifier contract khóa roster/schema/source/path/symlink/layout/pixels/semantic IDs,
  predecessor hashes, same-count ID swap, coherent rollback, clean-room rebuild và no-WP27.
- Final PM validation PASS 47/47 targeted WP26 tests, 286/286 compatibility tests cho
  WP22/WP23/WP23-R1/WP24/WP25/WP25-R1/WP26 và 1.047/1.047 full-suite tests trong durable
  `screen` với exit code 0. Cả 24 CLI package verifiers, Ruff, `uv lock --check` (168 packages)
  và `git diff --check` đều PASS. Graft rebuilt/check-clean tại 72 Python files, 1.354 nodes và
  3.528 edges; optional deep layer chưa build.
- Independent QA sau đó kết luận **PASS với 0 findings**. Closure chỉ cập nhật routing; test,
  builder, manifest và toàn bộ WP26 package giữ nguyên hash/bytes và historical status
  `WP26_AWAITING_QA_REVIEW`. PASS không duyệt D-02, group truth, split hoặc training.

## M0-WP27 D02-D remaining-edge manual reconciliation Batch F — awaiting independent QA

- Read-only derivation pin exact QA-passed chain WP22→WP23-R1→WP24→WP25-R1→WP26 và canonical
  1.026-row cross-split overlay, rồi chọn exact `eligible[1250:1500]`: 250 rows
  `edge_001851`…`edge_002213`, WP5 order 2.285…2.534, stems 1868→1869…2238→2239. Pre-batch
  residual là 896 rows gồm hai quarantine edges / 894 eligible; post-batch còn 646 rows gồm
  quarantine / 644 eligible.
- Coverage gồm 500 endpoints, 306 unique stems, 1.069 endpoint bbox occurrences và 650
  unique-stem bbox occurrences. Endpoint split train/test là 476/24; proxy tiers 127 strong/84
  uncertain/39 adjacency-only; 56 nonempty sequence IDs. Selection có zero cross-split row,
  không stem `0248` và không `proxy_sequence_0050`; hai quarantine edge `edge_000242`/
  `edge_000243` vẫn nguyên vẹn ngoài selection.
- PM trực tiếp đọc 50/50 prepared atlas pages và 250/250 pair panels, rồi đọc lại toàn bộ 12
  annotated exceptional pages. Capture outcomes là 247 `SAME_CAPTURE_CANDIDATE` và 3
  `NOT_RELATED`; physical-sign outcomes là 229 `SAME_PHYSICAL_SIGN_CANDIDATE` và 21
  `NOT_RELATED`, tất cả `HIGH`. Sequence context chỉ hỗ trợ review, không sinh decision hay group
  truth.
- Official verifier `valid=true`: 88 sources, 56 non-manifest artifacts, 49.363.156 artifact
  bytes. Manifest SHA-256 `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`;
  selection `3f8915b661bc53df3e2a736bb0dce0481ce95c4ed2c2cdce7e144dfe8b8aadbf`;
  annotations `ce35afc20a4b8ee2f1fefb86210ea61838123dd4a7b9e58969a33e57bb4d4de9`;
  trusted notes `2635a14140fb4d7dd82c2a0118707db1553babfafb322285ac36722d5f6a7ff8`.
  Contract fail-closed khóa exact roster/schema/source/path/symlink/layout/pixels/semantic IDs,
  predecessor hashes/preservation, same-count ID swap, coherent rollback/rehash/substitution,
  stale sources, clean-room determinism và no-WP28.
- Targeted WP27 tests PASS 47/47. Applicable compatibility WP22…WP27 PASS 332/332 sau khi
  deselect duy nhất immutable historical assertion
  `tests/test_wp26_remaining_edge_review_batch.py::test_no_wp27_artifacts_or_authorization_are_created`;
  assertion này kiểm tra WP27 chưa tồn tại tại thời điểm đóng WP26, nên không thể đồng thời đúng
  sau khi WP27 được người dùng cho phép mà vẫn giữ exact WP26 test SHA-256
  `99d60ffa317f2f3a566a8f3768fb907b8728240051c3c77f8754c492d12c5d1d`. Cả 26 executable
  verifier entrypoints — 24 package `verify` commands cộng WP3 `verify-manifest` và WP4 `verify`
  — cùng full final-state applicable suite 1.093/1.093 trong durable `screen` với explicit exit
  code 0, Ruff, `uv lock --check` (168 packages) và `git diff --check` PASS. Graft
  rebuilt/check-clean tại 74 Python files, 1.395 nodes và 3.621 edges; optional deep layer chưa
  build.
- Status dừng ở `WP27_AWAITING_QA_REVIEW`. Canonical WP5 vẫn 3.172 PENDING; 646 residual PENDING
  edges còn ngoài overlays, cả 589 sequence rows vẫn `PENDING`. D-02/Gate 0 vẫn blocked,
  `split_authorized=false`, `training_authorized=false`; không final/transitive group truth và
  không khởi động WP28.

## M0-WP27-R1 layout-status correction — independent QA FAIL (P2, superseded by WP27-R2)

- Independent QA đánh initial WP27 **FAIL** với đúng một P2 và zero P0/P1/P3: layout audit có
  `pair_count=250`, `page_count=50` nhưng status kế thừa stale
  `PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`. Historical WP27 verifier cũng
  explicit accept/require literal stale `176`; semantic decisions/raw/coverage còn lại PASS.
- Initial WP27 package được giữ byte-identical làm audit record: manifest
  `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`, layout
  `5b0c938465b5af1c44cf276f0633692a2769b8db49eaac9cd9dbc221dc19c506`, builder
  `831ad27ab3fba6fc2f78b121db752654306586a8bbfffc315f5a6c6869b2ab73` và test
  `fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce`.
- WP27-R1 là correction package append-only. Effective layout status là exact
  `PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`; corrected layout SHA-256
  `d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3`. Semantic-delta artifact
  chứng minh only `/status` changed; SHA-256
  `a3bb4ced80bae9b3c4124af7e53e16fe1673ca3f1794fdd249f9218accc8fe6e`.
- Effective roster giữ 55/56 artifacts ở exact initial path/hash và chỉ thay `layout_audit` bằng
  corrected evidence; roster SHA-256
  `c4b25036ea12820f7d0a9434d93bcea1b2e0461f7dc83878964a69255c8bc741`. Vì vậy selection,
  lineage, annotations, index và 50 JPEG pixels không đổi.
- Official R1 verifier `valid=true`: 151 exact sources, 4 correction artifacts, 56 effective
  artifacts và exactly 1 changed artifact. R1 manifest SHA-256
  `6992625b062649ba979a39eb7e4ef8fd00eadad666558fb40886d520390d96fc`; targeted tests PASS
  47/47, gồm inherited-176, 249/251, missing/type, rollback/substitution, path/symlink, ID-swap,
  coherent rehash/manifest refresh và clean-room 4/4 byte determinism. Applicable compatibility
  WP22…WP27-R1 PASS 379/379 sau khi deselect duy nhất immutable WP26 no-WP27 assertion. Cả 27
  executable verifier entrypoints (26 historical/current + WP27-R1), Ruff, `uv lock --check`
  (168 packages) và `git diff --check` PASS. Graft rebuilt/check-clean tại 76 Python files, 1.438
  nodes và 3.744 edges; blast radius của R1 builder/verify chỉ gồm CLI `main` và test module.
- Status dừng ở `WP27_R1_AWAITING_INDEPENDENT_QA`. Canonical WP5 vẫn 3.172 PENDING; 646 residual
  PENDING gồm hai quarantine edges / 644 eligible; cả 589 sequence rows vẫn PENDING. D-02/Gate 0
  vẫn blocked, split/training false, không final/transitive group truth và không WP28.

## M0-WP27-R2 type-strict verifier hardening — independent QA PASS

- Independent QA đánh WP27-R1 **FAIL** với đúng một P2 và zero P0/P1/P3 (đã tái hiện độc lập):
  R1 `semantic_diff` so sánh leaf bằng `==` và `verify()` không pin corrected-layout bytes, nên
  layout type-confused (`pair_count=250.0`, `page=true`, `slot=true`, `batch_position=true`,
  float bounds) cộng coherent refresh của R1 delta/roster/report/manifest trả `valid=true`. Bytes
  R1 đã ship vẫn đúng. WP27-R1 giữ byte-identical làm immutable QA-FAIL record.
- WP27-R2 chỉ thêm file, đổi 0 predecessor byte: QA record
  `docs/review/wp27_r2_qa_correction_record.md`, builder/verifier
  `scripts/build_wp27_r2_verifier_hardening.py`, 34 targeted tests, type-strict audit
  (`d04e74dd7d9d412b7d2108d044e7c4aac3e438f3ffaddd2a58f572217c6924f0`), report và manifest
  `01e2993888761793943bdfe0ea3c0d96d58c00b1965fc8cabcc402b7fa77b426`. R2 pin mọi R1 file bằng
  hằng số, yêu cầu layout bytes đúng canonical serialization của `corrected_layout(initial)`,
  type-strict diff đúng `/status`, exact `int` cho 3.704 count/position/bounds fields, và R1 +
  initial WP27 verifier vẫn `valid=true`. Effective layout giữ nguyên `d7af4b26…`.
- PM evidence: R2 verify `valid=true` (11 sources/2 artifacts); targeted 34/34; full suite
  1.174/1.174 exit 0 (chỉ deselect immutable WP26 no-WP27 assertion), trong đó compatibility
  WP22…WP27-R2 413/413; 28/28 verifier entrypoints PASS đúng CLI contract (WP4 `status=PASS`);
  Ruff, `uv lock --check` (168), `git diff --check` PASS; Graft rebuilt/check-clean 78 files,
  1.477 nodes.
- Independent QA agent (context sạch, attack harness riêng, clean-room rebuild 2 lần
  byte-identical, raw-free recomputation của audit) trả **PASS, 0 P0/P1/P2**, 2 P3 non-blocking:
  P3-1 R2 manifest chấp nhận duplicate JSON keys/non-canonical formatting (kế thừa R1/initial;
  values Python thấy vẫn đúng); P3-2 `rejected_type_confusion_probes` là danh sách khai báo,
  được chứng minh bởi tests chứ không chạy lúc build. Không sửa ngược R2 đã hash-pin; WP28 áp
  dụng bài học canonical/type-strict manifest.
- Quan sát ngoài phạm vi: tests WP9/WP10/WP11 gọi `build(REPO_ROOT, …)` và ghi đè artifacts
  trong repo khi chạy full suite; sau đó cả ba verifier vẫn `valid=true` (bytes tái tạo đúng hash).
  Nên chuyển các test đó sang tmp copy trong một package tương lai.
- PASS này chỉ phê duyệt WP27-R2 correction ở provisional-evidence boundary. Không phê duyệt
  D-02, group truth, split, Gate 0 hay training. WP28 được phép bắt đầu.

## Technical backlog — nonblocking

- **P3 — Parameterize inherited atlas diagnostic:** verifier kế thừa trong
  `scripts/build_wp12_cross_split_review_batch.py` vẫn ghi “WP12 / exact 51-file contract” khi
  WP15 thực thi exact 37-file roster. Đây chỉ là wording chẩn đoán, không phải functional/package
  finding. Không sửa in-place các builder đã hash-pin trong WP15; parameterize tên work package và
  expected roster size ở phiên bản verifier tương lai.

## Definition of done cho vòng Phase 0 đầu tiên

- Audit read-only và risk register được ghi lại bằng evidence hiện tại.
- E0 có manifest/hash và chính sách không overwrite.
- Gate 0, experiment matrix, metric contract và milestone breakdown được duyệt về cấu trúc.
- Chưa có training mới, detector mới hoặc tuyên bố cải thiện nào.
- D02-C Sequence Batches A–E và WP21 final eligible batch đã QA PASS ở provisional evidence
  boundary; chỉ whole quarantined sequence còn ngoài sáu overlays. Eligible coverage hoàn tất vẫn
  không tạo owner-approved group truth. WP22 remaining-edge Batch A và corrected WP23-R1 Batch B
  đã QA PASS ở provisional boundary; initial WP23 vẫn là immutable QA-FAIL record. WP24 Batch C
  đã independent QA PASS với 0 findings ở provisional boundary. Initial WP25 Batch D đã QA FAIL
  với đúng một P1; WP25-R1 sửa append-only đúng `edge_001358` và đã independent QA PASS với 0
  findings. WP26 Batch E đã independent QA PASS với 0 findings. Initial WP27 Batch F đã QA FAIL
  với đúng một P2 layout-status finding; WP27-R1 QA FAIL với một P2 verifier finding; WP27-R2
  đã independent QA PASS. Có 646 other pending edges vẫn ngoài overlays; WP28 được phép bắt đầu. Người
  dùng/domain reviewer vẫn phải quyết
  định D-01–D-05; chưa tạo final split hoặc train. G0.4 đã đóng qua
  `QA-M0-WP10`, nhưng các blocker Gate 0 khác vẫn mở.
