# M0-WP33 — D-03 derived label set

Status: `WP33_DERIVED_LABELS_AWAITING_QA`

Applies the owner's D-03 decisions to all 8334 raw boxes. Raw labels are read only and
hash-checked; nothing in the staging copy or the iCloud original is modified.

## Changes against the raw labels

- Class 23 → one class `P.111a+P.111b` "Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép)".
  The owner first chose to split it into P.111a–d; review of all 465 boxes showed the same combined
  design (moped and motorised three-wheeler in one circle), so the owner revised the decision.
- Class 16 (P.117) and class 43 (W.239b) → one class per height value
  (`docs/review/wp33_height_value_decisions.csv`). Unreadable values are excluded from training.
- Stem 0776 line 7 → removed from class 18 (it is a height-limit sign); value unreadable, excluded.
- Class 31 → UNKNOWN, evaluation only.
- Stem 0248 → all boxes quarantined (G0.4).

## Derived taxonomy (54 trainable keys before D-04)

| Key | Code | Name | Train boxes | Excluded |
| --- | --- | --- | --- | --- |
| `0` | W.224 | Đường người đi bộ cắt ngang | 312 | 0 |
| `1` | W.205c | Đường giao nhau (nhánh phải) | 22 | 0 |
| `2` | P.102 | Cấm đi ngược chiều | 470 | 0 |
| `3` | R.302a | Phải đi vòng sang bên phải | 454 | 0 |
| `4` | W.205a | Đường giao nhau | 33 | 0 |
| `5` | W.207 | Giao nhau với đường không ưu tiên | 256 | 0 |
| `6` | W.201a | Chỗ ngoặt nguy hiểm vòng bên trái | 182 | 0 |
| `7` | P.123a | Cấm rẽ trái | 247 | 0 |
| `8` | I.434a | Bến xe buýt | 213 | 0 |
| `9` | R.303 | Nơi giao nhau chạy theo vòng xuyến | 43 | 0 |
| `10` | P.130 | Cấm dừng xe và đỗ xe | 1071 | 0 |
| `11` | I.409 | Chỗ quay xe | 26 | 0 |
| `12` | R.415a | Biển gộp làn đường theo phương tiện | 280 | 0 |
| `13` | W.245a | Đi chậm | 372 | 0 |
| `14` | P.106a | Cấm xe ô tô tải | 85 | 0 |
| `15` | W.203c | Đường bị thu hẹp về phía phải | 29 | 0 |
| `16:2.0` | P.117*2.0 | Hạn chế chiều cao 2,0 m | 43 | 0 |
| `16:2.2` | P.117*2.2 | Hạn chế chiều cao 2,2 m | 18 | 0 |
| `16:2.5` | P.117*2.5 | Hạn chế chiều cao 2,5 m | 9 | 0 |
| `16:UNREADABLE` | P.117 | Hạn chế chiều cao (không rõ giá trị) | 0 | 4 |
| `17` | P.124a | Cấm quay đầu xe | 105 | 0 |
| `18` | P.107 | Cấm xe ô tô khách và xe ô tô tải | 213 | 0 |
| `19` | P.124d | Cấm rẽ phải và quay đầu xe | 29 | 0 |
| `20` | P.103a | Cấm xe ô tô | 52 | 0 |
| `21` | W.203b | Đường bị thu hẹp về phía trái | 11 | 0 |
| `22` | W.221b | Đường có gồ giảm tốc | 131 | 0 |
| `23` | P.111a+P.111b | Cấm xe gắn máy và xe ba bánh có động cơ (biển ghép) | 465 | 0 |
| `24` | P.129 | Kiểm tra | 56 | 0 |
| `25` | S.505a | Biển phụ loại xe: xe máy | 25 | 0 |
| `26` | W.246a | Chú ý chướng ngại vật - Vòng tránh ra hai bên | 80 | 0 |
| `27` | W.225 | Trẻ em | 36 | 0 |
| `28` | S.505a | Biển phụ loại xe: xe tải và xe công | 27 | 0 |
| `29` | P.104 | Cấm xe máy | 45 | 0 |
| `30` | S.505a | Biển phụ loại xe: xe tải | 138 | 0 |
| `32` | P.123b | Cấm rẽ phải | 186 | 0 |
| `33` | W.202b | Nhiều chỗ ngoặt nguy hiểm liên tiếp, đầu tiên sang phải | 19 | 0 |
| `34` | P.108a | Cấm xe sơ-mi rơ-moóc | 82 | 0 |
| `35` | P.137 | Cấm rẽ trái, rẽ phải | 87 | 0 |
| `36` | P.139 | Cấm đi thẳng, rẽ phải | 75 | 0 |
| `37` | W.205b | Đường giao nhau (nhánh trái) | 47 | 0 |
| `38` | P.127 | Tốc độ tối đa cho phép (50 km/h) | 189 | 0 |
| `39` | P.127 | Tốc độ tối đa cho phép (60 km/h) | 459 | 0 |
| `40` | P.127 | Tốc độ tối đa cho phép (80 km/h) | 210 | 0 |
| `41` | P.127 | Tốc độ tối đa cho phép (40 km/h) | 275 | 0 |
| `42` | R.301e | Hướng đi phải theo - rẽ trái | 21 | 0 |
| `43:2.5` | W.239b*2.5 | Chiều cao tĩnh không thực tế 2,5 m | 22 | 0 |
| `43:2.7` | W.239b*2.7 | Chiều cao tĩnh không thực tế 2,7 m | 5 | 0 |
| `44` | W.233 | Nguy hiểm khác | 3 | 0 |
| `45` | I.407a | Đường một chiều | 195 | 0 |
| `46` | P.131a | Cấm đỗ xe | 435 | 0 |
| `47` | P.124b | Cấm ô tô quay đầu xe | 16 | 0 |
| `48` | W.210 | Giao nhau với đường sắt có rào chắn | 41 | 0 |
| `49` | P.124c | Cấm rẽ trái và quay đầu xe | 219 | 2 |
| `50` | W.201b | Chỗ ngoặt nguy hiểm vòng bên phải | 121 | 0 |
| `51` | W.246c | Chú ý chướng ngại vật - Vòng tránh sang bên phải | 5 | 0 |
| `UNKNOWN` | UNKNOWN | Ngoài taxonomy | 0 | 38 |

## Governance

This package does not assign training class indices, generate a split, or authorize training.
D-04 (rare classes) and D-05 remain pending; Gate 0 remains BLOCKED.
