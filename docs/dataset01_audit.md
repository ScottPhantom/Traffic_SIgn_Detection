# DATASET01 — dataset card và audit M0-WP1

Ngày audit: 2026-10-10 (Asia/Ho_Chi_Minh)  
Trạng thái: **technical audit PASS; Gate 0 BLOCKED; NO-TRAIN**

Tài liệu này phân biệt:

- **VERIFIED**: có readback/hash/artifact hiện tại;
- **PROPOSAL**: quy trình chưa thực hiện hoặc chưa được duyệt;
- **UNKNOWN/BLOCKED**: thiếu nguồn, quyền, metadata hoặc quyết định domain.

## 1. Source và staging

Source được giữ read-only:

- Root:
  `/Users/nguyentantai/Library/Mobile Documents/com~apple~CloudDocs/FALL 2026 KỲ 4/CPV301/Data/DATASET01`
- Archive:
  `archive.zip`
- SHA-256:
  `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76`
- Bản giải nén cũ `archive/`: 1.046 ảnh, 3.216 label; không được sửa.

Staging mới:

`DATASET01/staging/052bc980a7206f8d/`

```text
052bc980a7206f8d/
├── raw/archive/                 # exact bytes được extract từ archive.zip
└── generated/normalized/archive/
    ├── classes*.txt             # UTF-8/LF generated copies
    ├── labels/*.txt             # UTF-8/LF generated copies
    └── split_dataset/*.txt      # UTF-8/LF generated copies
```

Extraction được tạo qua thư mục tạm rồi rename sang đường dẫn hash-addressed. Script audit đối
chiếu từng file raw với từng ZIP member bằng SHA-256: 6.437/6.437 member khớp, không thiếu,
không thừa và không có byte mismatch.

## 2. Source preservation proof

Snapshot trước và sau có cùng:

| Check | Giá trị | Trạng thái |
| --- | --- | --- |
| `archive.zip` SHA-256 | `052bc980a7206f8ddd1ec2e59098dbd60a42036d3c7f7384ace4fe6416cbaa76` | VERIFIED unchanged |
| Archive size | 793.394.914 bytes | VERIFIED unchanged |
| Archive mtime ns | `1788918594463195563` | VERIFIED unchanged |
| Source `archive/` tree hash | `05c9955d77862f08f2a43436d9cdea63caa1cb3e56b939000737f93a248c753b` | VERIFIED unchanged |
| Source file count | 4.267 | VERIFIED unchanged |
| Source image/label count | 1.046 / 3.216 | VERIFIED unchanged |

Machine-readable proof:

- `results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_before.json`
- `results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_after.json`
- `results/data_audit/DATASET01_052bc980a7206f8d/source_preservation_proof.json`

## 3. Technical audit result

| Hạng mục | Kết quả | Trạng thái |
| --- | ---: | --- |
| Ảnh JPG | 3.216 | VERIFIED |
| YOLO labels | 3.216 | VERIFIED |
| Stem pairing | 3.216/3.216, không thiếu/thừa | VERIFIED |
| Decode | 3.216/3.216 đọc được | VERIFIED |
| Dimensions | 2.364 ảnh `960x540`; 813 ảnh `1920x1080`; 39 ảnh `540x960` | VERIFIED |
| Class IDs | đủ 0–51 | VERIFIED |
| Bounding boxes | 8.334 | VERIFIED |
| Empty labels | 25 | VERIFIED; candidate negative/non-sign |
| UTF-8 | không có decode error | VERIFIED |
| CRLF labels | 3.069 file | VERIFIED |
| Normalized text copies | 3.221 file, tách khỏi raw | VERIFIED |
| EXIF/GPS | 0/3.216 ảnh có EXIF; 0 có GPS | VERIFIED |

Tất cả dòng YOLO có đúng 5 field, class nằm trong 0–51 và bốn tọa độ/kích thước nằm trong
miền chuẩn hóa. Có một cảnh báo cần reviewer xem:

- `0248.txt`, dòng 1, class 49: `x=0.992188, w=0.053125`; mép bbox vượt biên phải.
- Raw label được giữ nguyên; box vẫn được tính trong 8.334 box và chưa được tự sửa/clamp.

### Box/crop size

| Bucket | Boxes |
| --- | ---: |
| Area ratio < 0,001 | 3.088 |
| 0,001–<0,005 | 3.634 |
| 0,005–<0,02 | 1.337 |
| 0,02–<0,1 | 271 |
| >= 0,1 | 4 |
| Crop min-side <16 px | 886 |
| 16–<32 px | 3.233 |
| 32–<64 px | 2.741 |
| >=64 px | 1.474 |

Phần lớn bbox nhỏ; classifier crop cần ghi rõ resize/interpolation và không được coi ảnh nhỏ là
cùng chất lượng với crop lớn.

## 4. Split audit và leakage proxy

| Check | Kết quả |
| --- | ---: |
| Train | 2.552 |
| Test | 639 |
| Validation | không có |
| Direct filename overlap | 0 |
| Negative trong train/test | 0 / 0 |
| Negative bị loại khỏi split | 25 |
| Numeric consecutive pairs | 3.178 |
| Cross-split consecutive pairs | 1.031 (32,44%) |

“Numeric consecutive pair” là hai stem số `n` và `n+1` cùng tồn tại. Đây chỉ là **leakage
proxy**, không phải bằng chứng rằng hai ảnh thuộc cùng video, scene hoặc biển vật lý. Split hiện
tại không được dùng làm independent holdout.

Danh sách từng cặp nằm trong
`results/data_audit/DATASET01_052bc980a7206f8d/adjacent_pair_leakage.csv`.

## 5. Provenance discovery

### VERIFIED source candidate

Local data khớp trực tiếp với Hugging Face dataset
[`thanhhiepvos/vietnam_traffic_sign`](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign),
commit
[`d869116a5f89e9ba2aa36b1c0582a39c310e3d0c`](https://huggingface.co/datasets/thanhhiepvos/vietnam_traffic_sign/commit/d869116a5f89e9ba2aa36b1c0582a39c310e3d0c):

| File | Local SHA-256 | Remote SHA-256 | Match |
| --- | --- | --- | --- |
| `archive/classes_en.txt` | `64eb7592...e0e9b1` | `64eb7592...e0e9b1` | VERIFIED |
| `archive/labels/0001.txt` | `12b615e4...070a6c` | `12b615e4...070a6c` | VERIFIED |
| `archive/images/0001.jpg` | `f8b74d8d...1aedb` | `f8b74d8d...1aedb` | VERIFIED |

Remote repository mô tả 3.216 ảnh object-detection, 52 class files tương ứng và creator là
“Data Palpating Team”. Hai split text trong ZIP local không xuất hiện trong commit upload 6.435
file, nên nguồn/quy trình tạo split vẫn UNKNOWN.

### License conflict — BLOCKED

- Hugging Face metadata/API và tag ghi `cc-by-sa-3.0`.
- Nội dung mô tả trong commit lại ghi “Creative Commons Attribution-ShareAlike 4.0
  International”.
- ZIP local không chứa LICENSE/README/YAML.

Vì phiên bản license mâu thuẫn, G0.1 chưa PASS. Cần chủ dataset hoặc người dùng xác nhận phiên
bản license áp dụng, attribution, ShareAlike obligations và quyền dùng các ảnh gốc/ảnh tăng cường.

### Attempted provenance paths

- Exact archive SHA-256 search: không tìm thấy public match.
- Exact EN/VI class-string search: dẫn tới Hugging Face/Roboflow derivatives.
- So sánh remote/local hash cho class list, một label và một image: match.
- ZIP comment: rỗng; ZIP timestamps chủ yếu 2025-04-09.
- EXIF/GPS trên toàn bộ ảnh: không có.
- Linked augmentation repository:
  [`nguyenmai333/Image-Augmentation`](https://github.com/nguyenmai333/Image-Augmentation);
  repository mô tả blur/noise/brightness/contrast nhưng không chứng minh scene/group lineage.

Evidence machine-readable:
`results/data_audit/DATASET01_052bc980a7206f8d/provenance_evidence.json`.

## 6. Group ID procedure — PROPOSAL, chưa tạo final split

Thứ tự bằng chứng đề xuất:

1. thu source video/session/route/time/physical-sign metadata từ creator;
2. nếu không có, lập candidate clusters bằng numeric adjacency, near-duplicate/perceptual
   similarity và chuỗi hình có camera viewpoint liên tục;
3. domain reviewer xem từng cluster và gán `group_id` ổn định theo
   `scene_<id>/physical_sign_<id>/capture_session_<id>`;
4. lưu mapping `stem -> group_id -> evidence -> reviewer -> confidence`;
5. chỉ sau adjudication mới tạo split stratified-group train/validation/test;
6. kiểm tra group overlap bằng 0, test được khóa trước tuning và rare-class support đủ để report.

Không dùng `stem // N` hay numeric adjacency như group truth. WP1 chỉ tạo leakage report; không
tạo final split.

## 7. Reproducible artifacts

Audit runner:

`scripts/audit_dataset01.py`

Fail-closed regression coverage:

- raw staging khác ZIP member/hash -> audit FAIL, CLI exit 1;
- ảnh không decode được -> audit FAIL, CLI exit 1;
- YOLO class/coordinate/size/non-finite/field-count sai -> audit FAIL, CLI exit 1;
- bbox vượt biên -> warning nhưng box không bị drop hoặc clamp ngầm;
- source mutation -> preservation proof false, compare CLI exit 1;
- normalization rerun idempotent; generated file khác nội dung bị từ chối overwrite;
- artifact bị sửa sau manifest -> verifier báo hash mismatch và exit 1.

Readback sau QA repair: audit-specific suite `14 passed`; full repository `24 passed`.

Verifier:

```bash
uv run python scripts/audit_dataset01.py verify-manifest \
  --manifest results/data_audit/DATASET01_052bc980a7206f8d/wp1_artifact_manifest.json
```

Outputs:

- `audit_summary.json`
- `file_manifest.csv`
- `image_inventory.csv`
- `per_class_counts.csv`
- `box_size_buckets.csv`
- `adjacent_pair_leakage.csv`
- `transformation_manifest.csv`
- `output_manifest.json`
- `wp1_artifact_manifest.json` (hash/size cho toàn bộ 13 WP1 result artifacts)
- source preservation snapshots/proof
- provenance evidence

Tất cả nằm dưới:
`results/data_audit/DATASET01_052bc980a7206f8d/`.

## 8. Gate 0 status sau WP1

| Gate | Trạng thái | Lý do |
| --- | --- | --- |
| G0.1 provenance/license | **BLOCKED** | Source candidate có hash match; license 3.0/4.0 mâu thuẫn |
| G0.2 immutable staging | **PASS** | Hash-addressed raw staging; source before/after unchanged |
| G0.3 complete extraction/pair/decode | **PASS** | 3.216/3.216, pairing 1:1, decode 100% |
| G0.4 text/YOLO/negatives | **PARTIAL** | normalized copies và validation pass; 1 bbox boundary warning cần review |
| G0.5 taxonomy | **DRAFT/BLOCKED** | mapping draft chưa được domain reviewer duyệt |
| G0.6 group identity | **BLOCKED** | không có video/scene/physical-sign ground truth |
| G0.7 group-aware split | **BLOCKED** | chưa tạo split; split hiện tại không hợp lệ làm holdout |
| G0.8 rare-class decision | **BLOCKED** | class 44 có 3 box, class 51 có 5 box; cần quyết định scope/collect/merge |
| G0.9 dataset card | **PARTIAL** | card/audit đã có; license, group và capture-condition metadata còn thiếu |

Gate 0 tổng thể: **BLOCKED / NO-TRAIN**.
