# Taxonomy vNext proposal — M0-WP4

**PROPOSAL ONLY — DO NOT APPLY.** D-03 remains `PENDING`; every row remains `UNAPPROVED`. This file is intentionally separate from the canonical taxonomy and contains no relabel operation.

## Candidate changes requiring domain review

| ID | Current code | Candidate code | Evidence status | Proposed review question |
|---:|---|---|---|---|
| 3 | `R.302a` | `R.302a` | PARTIAL | Mã/hình đúng; nhãn EN 'Right Turn Only' làm mất nghĩa vòng chướng ngại vật. |
| 14 | `P.106a*Xe tải` | `P.106a` | PARTIAL | Ứng viên chính thức là P.106a; hậu tố '*Xe tải' không phải cú pháp mã QCVN. |
| 16 | `P.117*` | `P.117` | PARTIAL | Biển có trị số; dấu '*' trong mã dataset không phải cú pháp QCVN. |
| 17 | `P.124a*` | `P.124a` | PARTIAL | Ứng viên P.124a đúng; dấu '*' trong mã dataset không phải cú pháp QCVN. |
| 18 | `P.107` | `P.107` | PARTIAL | Nhãn VI gần đúng; 'Passenger Cars' không tương đương 'ô tô khách'. |
| 22 | `W.221b` | `W.221b` | PARTIAL | Mã/hình đúng; nhãn EN 'Uneven Road' rộng hơn gồ giảm tốc. |
| 23 | `P.111` | `P.111a-d` | MISMATCH | QCVN không có một biển P.111 chung cho cả xe hai và ba bánh; phải chọn biến thể a-d. |
| 24 | `P.129` | `P.129` | PARTIAL | Mã/VI đúng; 'Customs Checkpoint' hẹp hơn nghĩa kiểm tra chung của QCVN. |
| 25 | `S.505a*Xe máy` | `S.505a` | MISMATCH | S.505a là biển phụ chỉ loại xe chịu hiệu lực của biển chính, không có nghĩa 'Motorcycles Only'. |
| 26 | `W.246a` | `W.246a` | PARTIAL | Mã đúng; nhãn dataset có lỗi chính tả và lược bỏ hướng vòng tránh. |
| 28 | `S.505a*Xe tải và công` | `S.505a` | MISMATCH | S.505a là biển phụ; nhãn 'Trucks and Containers' không phải tên/nghĩa QCVN. |
| 29 | `P.104` | `P.104` | PARTIAL | Mã đúng; nhãn dataset mở rộng thành 'mô tô và xe máy' so với tên QCVN. |
| 30 | `S.505a*Xe tải` | `S.505a` | MISMATCH | S.505a là biển phụ chỉ phạm vi của biển chính, không có nghĩa độc lập 'Trucks Only'. |
| 31 | `Camera` | `NOT_FOUND` | NOT_FOUND | Không tìm thấy mã/tên camera giám sát tương ứng trong QCVN; kết luận chỉ giới hạn trong nguồn này. |
| 34 | `B.8a` | `P.108a` | MISMATCH | B.8a là số mục/hình; mã biển chính thức là P.108a. Nhãn EN 'Containers' cũng sai loại xe. |
| 38 | `P.127*50` | `P.127` | PARTIAL | Trị số 50 hợp lệ trên biển P.127; '*50' không phải cú pháp mã QCVN. |
| 39 | `P.127*60` | `P.127` | PARTIAL | Trị số 60 hợp lệ trên biển P.127; '*60' không phải cú pháp mã QCVN. |
| 40 | `P.127*80` | `P.127` | PARTIAL | Trị số 80 hợp lệ trên biển P.127; '*80' không phải cú pháp mã QCVN. |
| 41 | `P.127*40` | `P.127` | PARTIAL | Trị số 40 hợp lệ trên biển P.127; '*40' không phải cú pháp mã QCVN. |
| 43 | `W.239b*` | `W.239b` | PARTIAL | Ứng viên đúng; dấu '*' biểu thị tham số nhưng không phải cú pháp mã QCVN. |
| 47 | `P.124b1` | `P.124b` | MISMATCH | Không có mã P.124b1 trong QCVN; ứng viên chính thức theo hình/nghĩa là P.124b. |

## Suggested reviewer actions

- Confirm official code/name against the cited page and figure.
- Inspect all three representative crops plus the full class corpus before accepting any semantic change.
- Decide whether parameterized values belong in one class, subclasses, or structured attributes.
- For S.505a, decide how the main sign and supplementary plate must be represented together.
- Record any approval only through the future D-03 workflow; do not edit this evidence file into an approval.
