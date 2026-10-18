# Vietnam traffic-sign taxonomy mapping — DRAFT

Ngày tạo draft: 2026-10-10  
Trạng thái: **DRAFT / UNAPPROVED / Gate G0.5 BLOCKED**

Nguồn tên/code/support:
`results/data_audit/DATASET01_052bc980a7206f8d/per_class_counts.csv`.

Nguồn quy chuẩn để reviewer đối chiếu là
[Thông tư 51/2024/TT-BGTVT](https://vanban.chinhphu.vn/?classid=1&docid=211908&orggroupid=4&pageid=27160)
và [QCVN 41:2024/BGTVT đính kèm](https://datafiles.chinhphu.vn/cpp/files/vbpq/2024/11/51-bgtvt-kem.pdf),
có hiệu lực từ 2025-01-01. Nguồn này là review target; việc dẫn nguồn không tự phê duyệt bất kỳ
dòng nào.

Đây là worksheet cho domain reviewer, không phải taxonomy đã duyệt. Mapping GTSRB chỉ thể hiện
đề xuất semantic gần nhất; hình dạng, luật áp dụng và điều kiện phương tiện tại Việt Nam có thể
khác. Không dùng bảng này để relabel/train cho tới khi reviewer ký duyệt từng dòng.

## Quy ước

- **Direct?**: có vẻ cùng ý nghĩa chính, vẫn phải review hình/luật.
- **Partial?**: chỉ giao nhau một phần; có thể cần split/merge hoặc giữ lớp riêng.
- **None**: không có lớp GTSRB tương đương đủ gần.
- Criticality **H/M/L** là đề xuất ưu tiên error analysis, không phải safety certification.
- Support ghi theo `images / boxes`; đây không phải bảo đảm đủ train/holdout.

## Mapping worksheet

| ID | Code | VI / EN | Family | Proposed GTSRB mapping | Relation | Crit. | Support | Review |
| ---: | --- | --- | --- | --- | --- | :---: | ---: | --- |
| 0 | W.224 | Đường người đi bộ cắt ngang / Pedestrian Crossing | warning-person | 27 Pedestrians | Direct? | H | 312 / 312 | UNAPPROVED |
| 1 | W.205c | Đường giao nhau (ngã ba bên phải) / Equal-level Intersection | warning-intersection | 11 Right-of-way at next intersection | Partial? | H | 22 / 22 | UNAPPROVED |
| 2 | P.102 | Cấm đi ngược chiều / No Entry | prohibition-entry | 17 No entry | Direct? | H | 467 / 470 | UNAPPROVED |
| 3 | R.302a | Phải đi vòng sang bên phải / Right Turn Only | mandatory-direction | 38 Keep right | Partial?; EN label needs review | H | 454 / 454 | UNAPPROVED |
| 4 | W.205a | Giao nhau với đường đồng cấp / Intersection | warning-intersection | 11 Right-of-way at next intersection | Partial? | H | 33 / 33 | UNAPPROVED |
| 5 | W.207 | Giao nhau với đường không ưu tiên / Intersection with a non-priority road | warning-intersection | 11 Right-of-way at next intersection | Partial? | H | 256 / 256 | UNAPPROVED |
| 6 | W.201a | Chỗ ngoặt nguy hiểm vòng bên trái / Danger zone on the left | warning-curve | 19 Dangerous curve to the left | Direct? | H | 163 / 182 | UNAPPROVED |
| 7 | P.123a | Cấm rẽ trái / No Left Turn | prohibition-direction | — | None | H | 247 / 247 | UNAPPROVED |
| 8 | I.434a | Bến xe buýt / Bus Stop | information-transit | — | None | M | 213 / 213 | UNAPPROVED |
| 9 | R.303 | Nơi giao nhau chạy theo vòng xuyến / Roundabout | mandatory-direction | 40 Roundabout mandatory | Direct? | H | 43 / 43 | UNAPPROVED |
| 10 | P.130 | Cấm dừng và đỗ xe / No Stopping and No Parking | prohibition-parking | — | None | M | 1030 / 1071 | UNAPPROVED |
| 11 | I.409 | Chỗ quay xe / U-Turn Allowed | information-direction | — | None | M | 26 / 26 | UNAPPROVED |
| 12 | R.415a | Biển gộp làn đường theo phương tiện / Lane Allocation | mandatory-lane | — | None; likely multi-sign semantics | H | 279 / 280 | UNAPPROVED |
| 13 | W.245a | Đi chậm / Slow Down | warning-speed | 18 General caution | Partial? | H | 371 / 372 | UNAPPROVED |
| 14 | P.106a*Xe tải | Cấm xe tải / No Trucks Allowed | prohibition-vehicle | 16 Vehicles over 3.5t prohibited | Partial?; weight scope differs | H | 47 / 85 | UNAPPROVED |
| 15 | W.203c | Đường bị thu hẹp về phía phải / Narrow Road on the Right | warning-road | 24 Road narrows on the right | Direct? | H | 29 / 29 | UNAPPROVED |
| 16 | P.117* | Giới hạn chiều cao / Height Limit | prohibition-clearance | — | None; numeric/parameterized class | H | 73 / 73 | UNAPPROVED |
| 17 | P.124a* | Cấm quay đầu / No U-Turn | prohibition-direction | — | None | H | 105 / 105 | UNAPPROVED |
| 18 | P.107 | Cấm ô tô khách và ô tô tải / No Passenger Cars and Trucks | prohibition-vehicle | 15 No vehicles | Partial?; vehicle scope differs | H | 154 / 214 | UNAPPROVED |
| 19 | P.124d | Cấm rẽ phải và quay đầu / No U-Turn and No Right Turn | prohibition-composite | — | None; composite class | H | 29 / 29 | UNAPPROVED |
| 20 | P.103a | Cấm ô tô / No Cars Allowed | prohibition-vehicle | 15 No vehicles | Partial? | H | 52 / 52 | UNAPPROVED |
| 21 | W.203b | Đường bị thu hẹp về phía trái / Narrow Road on the Left | warning-road | — | None | H | 11 / 11 | UNAPPROVED |
| 22 | W.221b | Gồ giảm tốc phía trước / Uneven Road | warning-road | 22 Bumpy road | Partial?; bump vs uneven wording | H | 92 / 131 | UNAPPROVED |
| 23 | P.111 | Cấm xe hai và ba bánh / No Two or Three-wheeled Vehicles | prohibition-vehicle | — | None | H | 465 / 465 | UNAPPROVED |
| 24 | P.129 | Kiểm tra / Customs Checkpoint | prohibition-control | — | None | M | 56 / 56 | UNAPPROVED |
| 25 | S.505a*Xe máy | Chỉ dành cho xe máy / Motorcycles Only | mandatory-vehicle | — | None | H | 25 / 25 | UNAPPROVED |
| 26 | W.246a | Chướng ngoại vật phía trước / Obstacle on the Road | warning-obstacle | 18 General caution | Partial? | H | 80 / 80 | UNAPPROVED |
| 27 | W.225 | Trẻ em / Children Present | warning-person | 28 Children crossing | Direct? | H | 36 / 36 | UNAPPROVED |
| 28 | S.505a*Xe tải và công | Xe tải và xe công / Trucks and Containers | mandatory-vehicle | — | None; VI/EN wording needs review | H | 27 / 27 | UNAPPROVED |
| 29 | P.104 | Cấm mô tô và xe máy / No Motorcycles Allowed | prohibition-vehicle | — | None | H | 45 / 45 | UNAPPROVED |
| 30 | S.505a*Xe tải | Chỉ dành cho xe tải / Trucks Only | mandatory-vehicle | — | None | H | 138 / 138 | UNAPPROVED |
| 31 | Camera | Đường có camera giám sát / Road with Surveillance Camera | information-camera | — | None; code/source needs review | M | 38 / 38 | UNAPPROVED |
| 32 | P.123b | Cấm rẽ phải / No Right Turn | prohibition-direction | — | None | H | 186 / 186 | UNAPPROVED |
| 33 | W.202b | Nhiều chỗ ngoặt, chỗ đầu sang phải / Double curve first to right | warning-curve | 21 Double curve | Partial?; first-turn direction differs | H | 19 / 19 | UNAPPROVED |
| 34 | B.8a | Cấm xe sơ-mi rơ-moóc / No Containers Allowed | prohibition-vehicle | — | None; EN wording needs review | H | 82 / 82 | UNAPPROVED |
| 35 | P.137 | Cấm rẽ trái và phải / No Left or Right Turn | prohibition-composite | — | None; composite class | H | 87 / 87 | UNAPPROVED |
| 36 | P.139 | Cấm đi thẳng và rẽ phải / No Straight and Right Turn | prohibition-composite | — | None; composite class | H | 75 / 75 | UNAPPROVED |
| 37 | W.205b | Đường giao nhau (ngã ba bên trái) / Intersection with T-Junction | warning-intersection | 11 Right-of-way at next intersection | Partial? | H | 47 / 47 | UNAPPROVED |
| 38 | P.127*50 | Giới hạn tốc độ 50 / Speed limit 50 | prohibition-speed | 2 Speed limit 50 | Direct? | H | 114 / 189 | UNAPPROVED |
| 39 | P.127*60 | Giới hạn tốc độ 60 / Speed limit 60 | prohibition-speed | 3 Speed limit 60 | Direct? | H | 342 / 459 | UNAPPROVED |
| 40 | P.127*80 | Giới hạn tốc độ 80 / Speed limit 80 | prohibition-speed | 5 Speed limit 80 | Direct? | H | 210 / 210 | UNAPPROVED |
| 41 | P.127*40 | Giới hạn tốc độ 40 / Speed limit 40 | prohibition-speed | — | None; GTSRB lacks 40 class | H | 274 / 275 | UNAPPROVED |
| 42 | R.301e | Các xe chỉ được rẽ trái / Left Turn | mandatory-direction | 34 Turn left ahead | Direct? | H | 21 / 21 | UNAPPROVED |
| 43 | W.239b* | Chiều cao tĩnh không thực tế / Low Clearance | warning-clearance | — | None; parameter semantics need review | H | 27 / 27 | UNAPPROVED |
| 44 | W.233 | Nguy hiểm khác / Other Danger | warning-general | 18 General caution | Direct?/Partial? | H | 3 / 3 | UNAPPROVED |
| 45 | I.407a | Đường một chiều / One-way street | information-direction | — | None; not equal to Ahead only | H | 190 / 195 | UNAPPROVED |
| 46 | P.131a | Cấm đỗ xe / No Parking | prohibition-parking | — | None | M | 423 / 435 | UNAPPROVED |
| 47 | P.124b1 | Cấm ô tô quay đầu / No U-Turn for Cars | prohibition-vehicle-direction | — | None | H | 16 / 16 | UNAPPROVED |
| 48 | W.210 | Giao nhau với đường sắt có rào chắn / Level Crossing with Barriers | warning-rail | — | None | H | 41 / 41 | UNAPPROVED |
| 49 | P.124c | Cấm rẽ trái và quay đầu / No U-Turn and No Left Turn | prohibition-composite | — | None; composite class | H | 120 / 221 | UNAPPROVED |
| 50 | W.201b | Chỗ ngoặt nguy hiểm vòng bên phải / Danger zone on the right | warning-curve | 20 Dangerous curve to the right | Direct? | H | 105 / 121 | UNAPPROVED |
| 51 | W.246c | Chướng ngại vật – vòng tránh phải / Obstacle ahead – pass right | warning-obstacle | 38 Keep right | Partial?; QCVN W-family là warning, GTSRB 38 là mandatory | H | 5 / 5 | UNAPPROVED |

## WP2 refinement và conflict register

Machine-readable worksheet `review/generated/taxonomy_review.csv` giữ đủ 52 dòng, đọc support
trực tiếp từ audit và thêm conflict flags. Tất cả dòng vẫn là `UNAPPROVED`. Các conflict cần xem
trước gồm:

- ID 3: English “Right Turn Only” cần phân biệt với ý nghĩa đi vòng chướng ngại vật của `R.302a`;
- ID 22: English “Uneven Road” không đồng nhất với “Đường có gồ giảm tốc” của `W.221b`;
- ID 25/28/30: code `S.505a*...` mô tả biển phụ/composite dataset class;
- ID 31: code `Camera` chưa gắn với một code QCVN đã xác nhận;
- ID 34: dataset dùng `B.8a`, trong khi reviewer phải kiểm tra sign code `P.108a`;
- ID 47: `P.124b1` chưa được xác nhận trong QCVN hiện hành;
- ID 51: semantic family được sửa trong worksheet từ mandatory sang warning, nhưng mapping GTSRB
  38 vẫn chỉ là Partial proposal.

GTSRB relation là cross-jurisdiction proposal. Website benchmark chính thức xác định GTSRB là
classification 43 lớp và không bao gồm detection/tracking/temporal integration:
[German Traffic Sign Recognition Benchmark](https://benchmark.ini.rub.de/gtsrb_about.html).

## Reviewer decisions required

1. Xác nhận tên/code chuẩn cho từng class, đặc biệt ID 3, 12, 28, 31, 34 và các dấu `*`.
2. Duyệt mapping Direct/Partial/None; không tự merge vì tên gần nhau.
3. Quyết định composite signs là class riêng hay multi-label attributes.
4. Quyết định speed/height có phải parameterized taxonomy hay class rời.
5. Quyết định rare classes:
   - ID 44: 3 images/3 boxes;
   - ID 51: 5 images/5 boxes;
   - ID 21: 11 images/11 boxes;
   - ID 47: 16 images/16 boxes.
6. Chỉ định lớp nào critical cho go/no-go và support tối thiểu cho validation/test.
7. Duyệt chính sách UNKNOWN/non-sign và vai trò 25 empty-label images.

Không tạo final split hoặc train từ bảng này trước khi trạng thái từng dòng được reviewer chuyển
từ `UNAPPROVED` sang quyết định có tên/ngày/bằng chứng.
