# Bàn giao Claude — D1-S2-R1 seed 20261019

Ngày kiểm: 2026-11-06 (`Asia/Ho_Chi_Minh`). Checkout:
`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, nhánh
`yolo11n-dual-track-r1`. Đây là kết quả validation R3 của lần train lặp lại
cấu hình pilot, chỉ đổi seed 20261018→20261019. `sealed_test_accessed=false`.

## Trạng thái đã xác minh

- Source commit A `fc729d07664c70a8784ff735b72d7283e5261b6a`, notebook commit B
  `192939f9fba60cd6ec3c7c61f740c1ff4758cf92`. Hai commit cùng `729547b`
  đã được push đúng phép Owner trước lúc chạy Colab. Các commit kết quả liệt
  kê dưới đây **chỉ nằm local**: remote
  `origin/yolo11n-dual-track-r1` vẫn tại `192939f9fba60cd6ec3c7c61f740c1ff4758cf92`
  khi kiểm. Không push thêm nếu Owner chưa cho phép.
- Smoke L4 dừng epoch 1, QA độc lập PASS. Resume trên L4 mới đạt
  `SUCCEEDED`, epoch 100 lúc 16:51:50 local. Runtime digest fresh
  `09684dcb15069019dda3c53be5c76bd6751c999ae93a07a310d5d7aefe61bd12`;
  resume `0bd5a87026dc941c8c51cea20aea2030a008d32e80c69fc7ab55ebe4f8139640`.
  QA kết quả run độc lập PASS, gồm archive, checkpoint, hai runtime, cấu hình,
  log parity và attestation offline.
- [Thư mục Drive](https://drive.google.com/drive/folders/1qmUE-A9N3ul0XhFpkImN8dLqU9ZXvUU-):
  `M1_D1_Colab/runs/d1_s2_seed_20261019_r1`. Bản chép local đã so SHA-256
  từng file trước/sau ở thư mục bị Git bỏ qua
  `tmp/d1_s2_seed_20261019_r1_state/`.
- Archive 41,303,680 byte, SHA-256
  `c9367603c67650968514d00699d73bc0202fb7e1b69c4a6af413b34f60b2164e`;
  manifest 1,986 byte, SHA-256
  `b771a58996f75257f2a58adcb684273dff637be28b5d66606a66a721694e172e`.
  Archived `best.pt` SHA-256
  `046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce`;
  `last.pt` `05935508454e77150a6accf15248e8d6e44ad6ce76f423b17155364f6c3ea40c`;
  `results.csv` `237a6efd574e5d49c4c4611f09c2344ae75885d600c3bd70a069232f5860f4c0`.
  Không dùng lẫn hash weight archive với full recovery checkpoint.

## Validation R3 chung, confidence cố định 0,20

Roster 376 ảnh / 624 GT, chín group D-02. Hiệu số và CI là seed 19 trừ
seed 18; CI 95% ghép cặp 1.000 bootstrap theo group.

| Chỉ số | Seed 18 | Seed 19 | Hiệu | CI 95% |
| --- | ---: | ---: | ---: | ---: |
| Recall vị trí | 547/624 = 87,66% | 507/624 = 81,25% | −6,41 điểm % | −16,34 đến +0,83 điểm % |
| Recall đúng lớp | 457/624 = 73,24% | 379/624 = 60,74% | −12,50 điểm % | −23,56 đến −1,42 điểm % |
| FP/ảnh | 150/376 = 0,399 | 127/376 = 0,338 | −0,061 | −0,365 đến +0,145 |
| mAP50 đúng lớp | 0,8521 | 0,7309 | −0,1212 | −0,1816 đến −0,0365 |
| mAP50–95 đúng lớp | 0,6089 | 0,5209 | −0,0880 | −0,1433 đến −0,0389 |

Lớp derived 7: 66/111→75/111; 32: 18/29→16/29; 41: 12/26→10/26.
Key 32 chỉ có GT trong một group nên CI theo group của lớp này không có
thông tin hữu ích.

**Trả lời câu hỏi FP/ảnh 0,399 của pilot:** seed 19 cho 0,338, nhưng CI của
hiệu số còn rộng và chứa 0. Hai seed không đủ để xác lập FP/ảnh ổn định.
Recall đúng lớp và mAP giảm trên cùng roster; không gọi đây là cải tiến.
Đây chỉ là validation đo dao động giữa các seed, chưa khóa ngưỡng, chưa đưa
ra D-05 GO/NO-GO mới, không chấm sealed test.

## Record và commit local

| Record / output | Commit local hoặc SHA-256 |
| --- | --- |
| `docs/review/d1_s2_r1_execution_record.md` | `1ce850f745950e9c9088d687d75dc91a253491be` |
| `docs/review/d1_s2_r1_live_smoke_independent_qa_record.md` | `5eb198d01447af0980584ab8265d6908f322a161` · `Verdict: PASS` |
| `docs/review/d1_s2_r1_result_independent_qa_record.md` | `dec11bb98505abfb092428c04470a1948f8b7b8b` · `Verdict: PASS` |
| `docs/review/d1_s2_r1_common_validation_report_r1.md`, result QA và generated CI JSON | `288a09b72caf8a7bdcd185c368d384b5a25ff456` · result `Verdict: PASS` |
| Local `results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/s2_predictions.csv` | SHA-256 `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8` |
| Local `results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/comparison_s2_r1.json` | SHA-256 `0d76dc34eaa8dfe4c155dfb16a0d150862ae2e568c623319f3a65db45c5a46b4` |
| `docs/review/generated/d1_s2_pilot_paired_ci_r1.json` | SHA-256 `57b386e3c1396449992a77e020200a953d3759b9d03968ac893d377a8ea37760` |

Các file dirty khác của Owner được giữ nguyên. Không commit weights, dữ liệu
hay `results/experiments/`; không push các commit mới. Claude có thể dùng
báo cáo và QA record trên để cập nhật deck/báo cáo 07/11, nhưng cần giữ ranh
giới validation và chờ quyết định ngưỡng riêng.
