# M0-WP4 — QCVN 41:2024 taxonomy evidence audit

**Status:** `READY_FOR_RE_REVIEW_EVIDENCE_ONLY_NO_APPROVAL`  
**Decision boundary:** toàn bộ 52 dòng vẫn `UNAPPROVED`; D-03 `PENDING`; Gate 0 `BLOCKED`; `training_authorized=false`. Báo cáo này không relabel dữ liệu và không phê duyệt mapping GTSRB.

## Nguồn chính thức đã khóa

- QCVN 41:2024/BGTVT: 403 trang, SHA-256 `b6b99d0a0aeb13fe79072831857ece15bb254d8fb7817e80e4a2739a0d2145ce`.
- Thông tư 51/2024/TT-BGTVT: 1 trang, SHA-256 `dc822815eb51c6674a40ce91127b636f11a7479c76f24d9a00445dcf248b6689`.
- URL, thời điểm tải và kích thước nằm trong `references/qcvn41_2024/source_provenance.json`.
- Evidence index độc lập `references/qcvn41_2024/qcvn_taxonomy_evidence_index.json` khóa code/name/section/figure/token và fingerprint text + render của từng trang được trích dẫn; class 31 có negative-search scope riêng.
- Đã kiểm tra text layer theo từng khoảng trang được trích dẫn và kiểm tra trực quan các trang 1, 83, 87, 88, 106, 114, 117, 152.

## Kết quả 52 lớp

| Trạng thái | Số dòng |
|---|---:|
| EXACT | 31 |
| PARTIAL | 14 |
| MISMATCH | 6 |
| NOT_FOUND | 1 |
| NON_SIGN_CATEGORY | 0 |

`NOT_FOUND` chỉ có nghĩa chưa tìm được ứng viên trong QCVN 41:2024 ở nguồn đã khóa, không phải kết luận rằng biển/biểu tượng đó không tồn tại trong mọi văn bản khác.

## Các xung đột bắt buộc kiểm tra

| ID | Dataset | Ứng viên QCVN | Kết quả | Lý do ngắn | Nguồn |
|---:|---|---|---|---|---|
| 3 | `R.302a` | `R.302a` | PARTIAL | Mã/hình đúng; nhãn EN 'Right Turn Only' làm mất nghĩa vòng chướng ngại vật. | p.117 |
| 22 | `W.221b` | `W.221b` | PARTIAL | Mã/hình đúng; nhãn EN 'Uneven Road' rộng hơn gồ giảm tốc. | p.106 |
| 25 | `S.505a*Xe máy` | `S.505a` | MISMATCH | S.505a là biển phụ chỉ loại xe chịu hiệu lực của biển chính, không có nghĩa 'Motorcycles Only'. | p.152 |
| 28 | `S.505a*Xe tải và công` | `S.505a` | MISMATCH | S.505a là biển phụ; nhãn 'Trucks and Containers' không phải tên/nghĩa QCVN. | p.152 |
| 30 | `S.505a*Xe tải` | `S.505a` | MISMATCH | S.505a là biển phụ chỉ phạm vi của biển chính, không có nghĩa độc lập 'Trucks Only'. | p.152 |
| 31 | `Camera` | `NOT_FOUND` | NOT_FOUND | Không tìm thấy mã/tên camera giám sát tương ứng trong QCVN; kết luận chỉ giới hạn trong nguồn này. | p.— |
| 34 | `B.8a` | `P.108a` | MISMATCH | B.8a là số mục/hình; mã biển chính thức là P.108a. Nhãn EN 'Containers' cũng sai loại xe. | p.83 |
| 47 | `P.124b1` | `P.124b` | MISMATCH | Không có mã P.124b1 trong QCVN; ứng viên chính thức theo hình/nghĩa là P.124b. | p.87-88 |
| 51 | `W.246c` | `W.246c` | EXACT | Mã và nghĩa trùng QCVN; ánh xạ GTSRB vẫn chỉ là đề xuất khác họ warning/mandatory. | p.114 |

## Tệp reviewer

- `docs/review/generated/wp4_qcvn_taxonomy_worksheet.csv`: worksheet 52 dòng, một dòng mỗi class ID.
- `docs/review/assets/wp4/qcvn_taxonomy_atlas/index.html`: atlas 13 trang, ba crop đại diện/dòng; đủ 156 bbox overlay có lineage tái dựng được về raw label/image.
- Sampling deterministic: `Known audited boundary case 0248 is reserved first for class 49; remaining slots preserve the existing deterministic WP3 source-stem order after removing duplicates.`
- Boundary case bắt buộc `0248` nằm ở class 49 / slot 1. Raw 960x540, label line 1/index 0; bbox pixel `(927.00048, 158.99976, 978.00048, 213.99984)`, vượt mép phải `18.00048 px`. Atlas giữ nguyên bbox bằng virtual padding nền hatch xám và đường biên ảnh cyan; không clamp hay sửa raw.
- `docs/review/wp4_taxonomy_vnext_proposal.md`: đề xuất riêng; không sửa taxonomy hiện hành.
- `docs/review/generated/wp4_qcvn_manifest.json`: hash nguồn, PDF và artifacts.

## Blocker / quyết định còn mở

1. Reviewer chuyên môn phải quyết định từng dòng và D-03; script cố ý không có chức năng approve.
2. ID 31 cần nguồn pháp lý khác nếu muốn giữ claim camera; hiện là `NOT_FOUND` trong QCVN đã kiểm tra.
3. ID 23 và các lớp `S.505a` cần quyết định ontology trước relabel vì đây không phải quan hệ một-mã-một-nhãn đơn giản.
4. GTSRB proposal vẫn là cross-jurisdiction proposal; không được biến thành target training trước Gate 0.
