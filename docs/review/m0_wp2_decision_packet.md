# M0-WP2 — Decision-ready reviewer packet

Ngày chuẩn bị: 2026-10-10 (Asia/Ho_Chi_Minh)  
Trạng thái: **READY FOR RE-REVIEW / Gate 0 BLOCKED / NO-TRAIN**

Packet này chuẩn bị bằng chứng và phương án cho D-01 đến D-05. Nó không phải phê duyệt
license, taxonomy, grouping, bbox, split hay experiment. Nếu không có quyết định bằng văn bản,
mặc định của mọi mục là **BLOCKED / NO-TRAIN**.

## Nguồn bằng chứng chung

- Audit kỹ thuật: `../dataset01_audit.md`.
- WP1 artifacts: `../../results/data_audit/DATASET01_052bc980a7206f8d/`.
- Bảng taxonomy 52 lớp: `../vietnam_taxonomy_mapping.md`.
- Machine-readable reviewer data: `generated/`.
- Template trạng thái quyết định: `decision_status.json`.
- Generated decision schema: `generated/decision_status.schema.json`.
- Ngưỡng experiment đề xuất: `experiment_acceptance_template.md`.

## D-01 — Provenance và license

### Câu hỏi cần người dùng/owner quyết định

**Ai sở hữu ảnh gốc và văn bản nào xác nhận phiên bản license, quyền cấp phép, attribution và
ShareAlike áp dụng cho đúng dataset/commit này?** Chỉ chọn một phương án sau khi có bằng chứng
truy xuất được; PM không đưa ra kết luận pháp lý.

### VERIFIED evidence

- Source candidate:
  [`thanhhiepvos/vietnam_traffic_sign`](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign),
  commit
  [`d869116a5f89e9ba2aa36b1c0582a39c310e3d0c`](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign/commit/d869116a5f89e9ba2aa36b1c0582a39c310e3d0c).
- Commit upload ghi 6.435 file, object-detection, creator claim “Data Palpating Team”.
- Metadata/tag hiển thị `cc-by-sa-3.0`; card prose trong cùng commit ghi
  `CC-BY-SA-4.0`. Đây là xung đột chưa giải quyết.
- Ba exact hash match:

| File | Local SHA-256 | Remote SHA-256 | Match |
| --- | --- | --- | :---: |
| `archive/classes_en.txt` | `64eb7592cf256765ee691e734499dab7488090e0142bc68672db39ee93e0e9b1` | `64eb7592cf256765ee691e734499dab7488090e0142bc68672db39ee93e0e9b1` | YES |
| `archive/labels/0001.txt` | `12b615e4b6b928137ccb7edf59b05f332f7d9c9ccf53c8fc822d595bb6070a6c` | `12b615e4b6b928137ccb7edf59b05f332f7d9c9ccf53c8fc822d595bb6070a6c` | YES |
| `archive/images/0001.jpg` | `f8b74d8d3d639966c51ce337581153ef1b7485385c099ae2e8d8cff4f8d1aedb` | `f8b74d8d3d639966c51ce337581153ef1b7485385c099ae2e8d8cff4f8d1aedb` | YES |

Archive local có SHA-256
`052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76`, không có
LICENSE/README/YAML nhúng. Owner ảnh gốc, authority của uploader, attribution format, quyền tạo
ảnh augmented và nguồn hai file split đều UNKNOWN.

Evidence có thể giải blocker: LICENSE hoặc statement có ngày từ owner/authorized creator tham
chiếu đúng dataset/commit; chain-of-ownership cho ảnh; license version; attribution text; phạm vi
ShareAlike với ảnh dẫn xuất/model; lineage của augmentation và split.

### Phương án

1. **D01-A — Yêu cầu xác nhận bằng văn bản từ owner/creator.** Giữ dataset audit-only cho tới khi
   nhận đủ evidence. Hệ quả: chậm hơn nhưng có provenance rõ nhất.
2. **D01-B — Người dùng cung cấp source/license chain độc lập và chuyển cho reviewer pháp lý/domain.**
   Hệ quả: có thể giải quyết mà không phụ thuộc uploader, nhưng cần bằng chứng gắn đúng file/hash.
3. **D01-C — Loại dataset khỏi training scope.** Giữ các artifact audit để tham khảo; tìm dataset
   khác có provenance rõ. Hệ quả: không có rủi ro sử dụng dataset này nhưng phải thay nguồn dữ liệu.

**PM recommendation — PROPOSAL:** D01-A trước; nếu không lấy được bằng chứng trong thời hạn do
người dùng đặt, chuyển D01-C. Không suy đoán 3.0 hay 4.0 là phiên bản đúng.

**Default nếu chưa quyết định:** `BLOCKED / NO-TRAIN`.

## D-02 — Group identity và leakage control

### Câu hỏi cần người dùng/domain reviewer quyết định

**Sẽ lấy metadata video/scene/capture-session/physical-sign từ creator, cấp ngân sách review thủ
công, hay loại dataset khỏi experiment cần independent holdout?**

### VERIFIED / PROXY_ONLY evidence

- 3.178 cặp stem số liền kề; 1.031 cặp cắt chéo split hiện tại (`32,44%`).
- Proxy tái lập kết hợp adjacency với cùng kích thước, RGB-thumbnail MAE, dHash và RGB-histogram:
  - 1.691 `strong_candidate` edges, trong đó 539 cắt chéo split;
  - 1.172 `uncertain` edges, trong đó 391 cắt chéo split;
  - 315 `adjacency_only` edges, trong đó 101 cắt chéo split;
  - 589 candidate sequences, 2.280 ảnh, sequence lớn nhất 31 ảnh.
- Thời lượng review ước tính `17,6–46,7 giờ`, dựa trên 1–3 phút/strong sequence,
  20–45 giây/uncertain edge và 15–30 giây/adjacency-only edge. Chưa tính thời gian liên hệ creator
  hoặc review taxonomy.

Artifacts:

- `generated/grouping_proxy_summary.json`;
- `generated/grouping_proxy_edges.csv`;
- `generated/grouping_proxy_clusters.csv`.

Các ID `proxy_sequence_*` chỉ là hàng đợi review. Chúng **không phải** video, scene,
capture-session, physical-sign group hay final `group_id`.

### Phương án

1. **D02-A — Lấy grouping manifest từ creator.** Reviewer đối chiếu một sample với ảnh/proxy.
   Hệ quả: ít chủ quan nhất nếu metadata có lineage và coverage đầy đủ.
2. **D02-B — Duyệt ngân sách review thủ công 17,6–46,7 giờ.** Reviewer xem contact sheet cho 589
   candidate sequences, adjudicate toàn bộ uncertain edges và spot-check boundaries; ghi reviewer,
   date, confidence và evidence. Hệ quả: tốn công và vẫn không thay thế source metadata.
3. **D02-C — Không sử dụng dataset cho matched holdout/training.** Hệ quả: Gate 0 không thể PASS
   với dataset này, nhưng tránh data leakage không kiểm soát.

**PM recommendation — PROPOSAL:** D02-A trước, dùng D02-B làm fallback có kiểm soát. Không tự
copy `proxy_sequence_id` sang `group_id`.

**Default nếu chưa quyết định:** `BLOCKED / NO-SPLIT / NO-TRAIN`.

## D-03 — Taxonomy Việt Nam và GTSRB relation

### Câu hỏi cần người dùng/domain reviewer quyết định

**Ai là reviewer có thẩm quyền và họ có duyệt từng dòng của taxonomy 52 lớp, gồm code/name,
semantic family, Direct/Partial/None với GTSRB, composite/parameterized signs và UNKNOWN policy
hay không?**

### VERIFIED evidence và DRAFT refinement

- Support 52 lớp được đọc từ `per_class_counts.csv`; toàn bộ 52 dòng nằm trong
  `generated/taxonomy_review.csv`, tất cả `review_status=UNAPPROVED`.
- Nguồn quy chuẩn reviewer phải dùng là Thông tư
  [51/2024/TT-BGTVT](https://vanban.chinhphu.vn/?classid=1&docid=211908&orggroupid=4&pageid=27160),
  ban hành QCVN 41:2024/BGTVT, hiệu lực 2025-01-01; file quy chuẩn đính kèm:
  [QCVN 41:2024/BGTVT](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/51-bgtvt-kem.pdf).
- GTSRB là benchmark classification 43 lớp; website benchmark nói rõ detection, tracking và
  temporal integration nằm ngoài task. Mapping Việt Nam↔GTSRB vẫn là cross-jurisdiction proposal:
  [GTSRB official benchmark](https://benchmark.ini.rub.de/gtsrb_about.html).
- Conflict flags nổi bật:
  - ID 3 `R.302a`: English “Right Turn Only” có thể che khuất semantics đi vòng chướng ngại vật;
  - ID 22 `W.221b`: English “Uneven Road” khác “Đường có gồ giảm tốc”;
  - ID 25/28/30 dùng `S.505a*...` như class dù `S` là biển phụ;
  - ID 31 `Camera` không có code QCVN trong dataset;
  - ID 34 ghi `B.8a`, là mục phụ lục; sign code cần reviewer kiểm tra là `P.108a`;
  - ID 47 `P.124b1` chưa xác nhận trong QCVN hiện hành;
  - ID 51 `W.246c` là warning family; GTSRB 38 Keep right chỉ là Partial proposal.

Không có dòng nào được tự merge/relabel từ refinement này.

### Phương án

1. **D03-A — Reviewer duyệt từng dòng theo QCVN và image sample.** Ghi quyết định, bằng chứng,
   ngày, reviewer; phê duyệt riêng GTSRB relation. Hệ quả: tạo taxonomy version có audit trail.
2. **D03-B — Giữ native 52-class taxonomy, bỏ GTSRB mapping khỏi training scope.** Vẫn phải duyệt
   code/name/composite/UNKNOWN. Hệ quả: ít ép semantics Đức↔Việt hơn nhưng không tái sử dụng head 43
   lớp như cùng taxonomy.
3. **D03-C — Giảm/merge taxonomy theo scope sản phẩm.** Chỉ thực hiện sau semantic review và lưu
   mapping many-to-one versioned. Hệ quả: tăng support một số class nhưng mất độ chi tiết và không
   được merge chỉ vì visually similar.

**PM recommendation — PROPOSAL:** D03-A; nếu mục tiêu là classifier Việt Nam độc lập, ưu tiên native
taxonomy theo D03-B và dùng GTSRB mapping chỉ cho analysis, không làm nhãn thật.

**Default nếu chưa quyết định:** `DRAFT / BLOCKED / NO-RELABEL / NO-TRAIN`.

## D-04 — Rare-class handling

### Câu hỏi cần người dùng/domain reviewer quyết định

**Mỗi lớp support thấp sẽ collect-more, merge sau semantic approval, giữ report-only hay loại khỏi
scope?** Quyết định phải theo từng class; không dùng oversampling để che thiếu independent support.

Phạm vi D-04 được khóa bằng rule `box_count < 50`, gồm 20 class ID:
`1, 4, 9, 11, 15, 19, 21, 25, 27, 28, 29, 31, 33, 37, 42, 43, 44, 47, 48, 51`.

### VERIFIED evidence

| Band | Class | Images / boxes | Rủi ro |
| --- | --- | ---: | --- |
| CRITICAL_LOW | 44 `W.233` | 3 / 3 | Không thể ước lượng class-level holdout đáng tin cậy |
| CRITICAL_LOW | 51 `W.246c` | 5 / 5 | Không thể ước lượng class-level holdout đáng tin cậy |
| VERY_LOW | 21 `W.203b` | 11 / 11 | Sau group split có thể không còn support ở val/test |
| VERY_LOW | 47 `P.124b1` | 16 / 16 | Code/taxonomy còn conflict và support thấp |
| VERY_LOW | 33 `W.202b` | 19 / 19 | Sau group split có thể không còn support ở val/test |

Các lớp `LOW` từ 20–49 boxes: 1(22), 4(33), 9(43), 11(26), 15(29), 19(29), 25(25),
27(36), 28(27), 29(45), 31(38), 37(47), 42(21), 43(27), 48(41). Bảng đủ 52 lớp và
split support nằm tại `generated/rare_class_risk.csv`.

### Class-keyed decision record và aggregation rule

- Canonical record: `decision_status.json -> decisions -> D-04 -> class_decisions`.
- Generated blank template: `generated/d04_rare_class_decision_template.json`.
- Generated structural schema: `generated/decision_status.schema.json`.
- Mỗi class record bắt buộc có `selected_option`, `status`, `reviewer`, `decided_at`, `rationale`,
  `evidence_links` và `history`, cùng support fields đã khóa từ audit.
- Mỗi class có thể chọn disposition khác nhau; ví dụ class 44 có thể `collect_more` trong khi class
  51 là `out_of_scope` nếu reviewer cung cấp rationale/evidence riêng.
- Khi `RESOLVED`, `reviewer` và `rationale` phải là chuỗi đã trim và không rỗng; `decided_at` phải
  là RFC 3339/ISO 8601 có timezone rõ ràng; `evidence_links` phải là list có ít nhất một reference
  đã trim và không rỗng.
- Trước mỗi thay đổi, snapshot trạng thái quyết định cũ phải được append vào `history`; không ghi
  đè audit trail. Mỗi history item có đúng `changed_at`, `changed_by`, `previous`; `changed_at` dùng
  RFC 3339 có timezone, `changed_by` là chuỗi đã trim và `previous` có đủ sáu field quyết định
  `status`, `selected_option`, `reviewer`, `decided_at`, `rationale`, `evidence_links`. Ví dụ:

  ```json
  {
    "changed_at": "2026-10-10T15:00:00+07:00",
    "changed_by": "domain-reviewer",
    "previous": {
      "status": "PENDING",
      "selected_option": null,
      "reviewer": null,
      "decided_at": null,
      "rationale": null,
      "evidence_links": []
    }
  }
  ```

  Runtime validator là nguồn thẩm quyền cho tính trimmed và thứ tự timestamp tăng nghiêm ngặt
  trong append-only history; JSON Schema khóa kiểu, trường bắt buộc và cấu trúc từng item.
- D-04 chỉ được chuyển thành `RESOLVED` khi **tất cả 20 class** đều `RESOLVED`, option thuộc bốn
  lựa chọn được phép, có reviewer/rationale hợp lệ, timestamp có timezone, ít nhất một evidence
  link hợp lệ và history transition có cấu trúc. Chỉ một class còn thiếu cũng buộc aggregate giữ
  `PENDING`.

Readback hiện tại: 20/20 record là `PENDING`, mọi `selected_option=null`, D-04 aggregate `PENDING`.

### Phương án áp dụng theo từng lớp

1. **Collect more:** giữ class semantics, yêu cầu thêm independent groups/capture conditions.
   Hệ quả: tốt nhất cho evaluation nhưng kéo dài Gate 0.
2. **Merge sau semantic approval:** chỉ khi QCVN/use-case chứng minh cùng target behavior.
   Hệ quả: tăng support nhưng thay taxonomy, cần version/hash mới.
3. **Report-only:** có thể giữ để train/explore sau khi Gate 0 khác PASS nhưng không phát hành
   class-level acceptance claim. Hệ quả: model có output nhưng class không tham gia go/no-go metric.
4. **Out-of-scope:** loại khỏi approved taxonomy bằng manifest dẫn xuất, không xóa raw.
   Hệ quả: scope hẹp hơn, cần xử lý các ảnh chứa nhiều class để không làm mất nhãn khác.

**PM recommendation — PROPOSAL:** collect-more cho class safety-relevant dưới 20 boxes. Nếu chưa
collect được, đặt 44/51/21/47/33 thành `report-only` hoặc `out-of-scope` theo reviewer; không merge
44 hoặc 51 chỉ vì gần GTSRB.

**Default nếu chưa quyết định:** `BLOCKED / NO-SILENT-MERGE / NO-DROP / NO-TRAIN`.

## G0.4 — Bbox `0248.txt` reviewer packet

Raw dòng 1: `49 0.992188 0.345370 0.053125 0.101852`; ảnh `960×540`.

| Coordinate | Normalized | Pixel |
| --- | ---: | ---: |
| x center | 0,992188 | 952,500 px |
| y center | 0,345370 | 186,500 px |
| width | 0,053125 | 51,000 px |
| height | 0,101852 | 55,000 px |
| x min / x max | — | 927,000 / 978,000 px |
| y min / y max | — | 159,000 / 214,000 px |
| right overflow | — | **18,000 px** |

Reviewer overlay: `assets/bbox_0248_review.png`. Machine coordinates và source hashes:
`generated/bbox_0248_review.json`.

Phương án:

1. **Keep-as-warning:** raw và derived label giữ nguyên; exclude khỏi training cho tới khi consumer
   có policy rõ. Hệ quả: không mất evidence nhưng box vẫn out-of-frame.
2. **Clip-generated:** raw giữ nguyên; tạo derived annotation với `x_max=960`, ghi transformation
   manifest/hash/reviewer. Hệ quả: dùng được cho detector nhưng thay hình học box.
3. **Quarantine:** raw giữ nguyên; ảnh không vào approved split. Hệ quả: mất một sample class 49
   khỏi experiment nhưng tránh policy ngầm.

**PM recommendation — PROPOSAL:** giữ raw, quarantine trong khi chờ reviewer; nếu reviewer xác nhận
vật thể bị cắt tại biên và detector consumer yêu cầu box trong ảnh, tạo **derived clipped label** có
lineage. Không sửa `0248.txt` tại chỗ.

**Default nếu chưa quyết định:** `PARTIAL / QUARANTINE / NO-TRAIN`.

## D-05 — Experiment acceptance và compute budget

### Câu hỏi cần người dùng quyết định

**Sau khi Gate 0 PASS và split được khóa, chọn bundle feasibility, balanced hay robust cho metric,
latency hardware/batch contract và seed budget của classifier, OOD, detector và end-to-end?**

Chi tiết điền được nằm tại `experiment_acceptance_template.md`. Tóm tắt:

1. **D05-A — Feasibility only:** 3 seeds classifier/OOD, 1 detector seed, latency report-only;
   không có promotion claim. Hệ quả: rẻ, chỉ chứng minh pipeline chạy.
2. **D05-B — Balanced research gate:** 5 classifier/OOD seeds, 3 detector seeds, paired matched-split
   metrics, p50/p95 latency trên hardware cố định. Hệ quả: đủ cho chọn hướng nghiên cứu, chưa phải
   safety validation.
3. **D05-C — Robust research gate:** 10 classifier/OOD seeds, 5 detector seeds, CI và failure audit
   rộng hơn. Hệ quả: tốn compute nhất, giảm rủi ro chọn model theo seed.

**PM recommendation — PROPOSAL:** D05-B cho E1 feasibility-to-selection; chỉ dùng D05-C cho run cuối
của candidate đã thắng. Các numeric thresholds trong template là starter proposals và phải được
người dùng duyệt sau pilot, trước khi mở test set.

**Default nếu chưa quyết định:** `BLOCKED / NO-EXPERIMENT-PROMOTION / NO-TRAIN`.

## Chữ ký quyết định

Người quyết định phải cập nhật `decision_status.json` với `selected_option`, `reviewer`,
`decided_at`, `rationale` và `evidence_links`. Riêng D-04 phải cập nhật từng class record, append
trạng thái cũ vào `history` và tuân thủ aggregation rule; không có aggregate shortcut. Gate 0 chỉ
được đánh giá lại sau khi D-01–D-04 và bbox G0.4 có evidence; D-05 chỉ kích hoạt sau split được khóa.
