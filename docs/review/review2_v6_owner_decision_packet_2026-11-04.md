# Review 2 V6 — hồ sơ quyết định cho Owner, 2026-11-04

**Loại tài liệu:** tổng hợp bằng chứng và phương án để Owner quyết định; không sửa nhãn, không cấp PASS V6. `sealed_test_accessed=false`. Chỉ đọc CSV/JSON và QA text sẵn có; không mở ảnh/video ngoài repo, không tải media.

## V6 là gì và hiện đã tới đâu

- Định nghĩa gốc: V6 yêu cầu gán nhãn độc lập keyframe/interval (mã, box, thời gian bắt đầu/kết thúc, negative frames), chạy các kiến trúc trên cùng frame và scorer; đầu ra gồm precision/recall/mAP đúng lớp khi GT đủ, event precision/recall, duplicate/flicker, latency decode/infer/render, FPS và QA CSV/hash/niêm phong (`docs/review/review2_dashcam_video_r1_plan_and_status.md:28`). Quy tắc so video và các kiến trúc ở cùng tài liệu `:30-32`.
- Contract chấm đề xuất chỉ cho dùng clip đã khóa; nhãn cuối cần manifest nguồn/A/B/C và QA thị giác; các model dùng cùng frame và threshold khóa trước trên validation (`docs/review/review2_video_scoring_contract_r1_proposal.md:5-21`).
- Verified artifact: R2 v2 có 74/103 frame, 29 frame loại; chỉ 33 box thuộc hai lớp (16 W.205c, 17 P.130). Quyết định hiện tại là `APPROVED_INTERNAL_TWO_CLASS_FRAME_DIAGNOSTIC`, không phải GT toàn clip hay benchmark 54 lớp (`docs/review/review2_frame_diagnostic_r2_scope_decision_2026-11-01.md:3-20`). Manifest lịch sử vẫn `ground_truth_approved=false`, `model_predictions_included=false`, `sealed_test_accessed=false`. V6 chưa PASS.

## Đối chiếu frame còn vướng

Bảng lấy trạng thái A/B/C trực tiếp từ ba CSV đã pin. Cột QA là **kết luận đã ghi trong record thị giác**, không phải lượt xem ảnh mới. 23 frame hỗn hợp được R2 giữ cho chẩn đoán hai lớp với hai vùng ignore (một ngoài taxonomy, một đĩa D chưa đọc được); các frame còn lại bị loại. Nguồn QA: `docs/review/review2_annotation_c_visual_qa_0_100_2026-11-01.md:26-85`, `docs/review/review2_frame_diagnostic_r2_content_independent_qa_2026-11-01.md:109-125`.

| Frame | A | B | C | Kết luận QA thị giác | R2 | Lý do |
| ---: | --- | --- | --- | --- | --- | --- |
| 0 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 2 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 4 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 6 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 8 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 10 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 12 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 14 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 16 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 18 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 20 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 22 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 24 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 26 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 28 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 30 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 32 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Biển tốc độ bị cắt, đĩa xa chưa đọc được |
| 34 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa xa và hình xanh quá nhỏ/bị che |
| 36 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 38 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 40 | POSITIVE | UNCERTAIN | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 42 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 44 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 46 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 48 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 50 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 52 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 54 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 56 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 58 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Đĩa đỏ/xanh xa chưa đọc được |
| 60 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 62 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 64 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 66 | POSITIVE | POSITIVE | POSITIVE | R1 NEEDS_RESOLUTION; R2 ignore QA giới hạn | Giữ + ignore OOS/D | Đĩa D xa chưa đọc được cạnh biển đã thấy |
| 68 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 70 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 72 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 74 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 76 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 78 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 80 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 82 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 84 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 86 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 88 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 90 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 92 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 94 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 96 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 98 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Không phân biệt một hay hai nét đỏ |
| 100 | UNCERTAIN | POSITIVE | POSITIVE | Chưa xác nhận P.130 từ pixel gốc | Loại, unresolved | Không đọc chắc hai nét chéo/X |
| 136 | UNCERTAIN | UNCERTAIN | UNCERTAIN | C UNCERTAIN phù hợp | Loại | Mảnh biển sát mép phải; thiếu box/mã chắc chắn |

**Kiểm phép cộng:** C có 28 `UNCERTAIN`; R2 loại đúng 28 frame đó **và** frame 100 (C `POSITIVE` nhưng QA không xác nhận), thành 29. Có 23 frame hỗn hợp riêng, không giao với 29 frame loại, nên bảng có **52 frame duy nhất**. 103 − 29 = 74 frame giữ; 74 = 40 C `POSITIVE` + 34 C `NEGATIVE`; 33 box đích = 16 W.205c + 17 P.130. Bảy frame C dương 36/38/40/60/62/64/66 chỉ có biển ngoài phạm vi và D, nên có **0 GT box đích**. Các số khớp manifest v2 và content QA `:111-117`.

## Các phương án để Owner chọn — proposal, chưa thực hiện

| Phương án | Hệ quả đối với V6 | Việc cần làm và rủi ro |
| --- | --- | --- |
| A. Giữ R2 74 frame/hai lớp làm chẩn đoán nội bộ | Có thể báo số TP/FP/FN hai lớp trên đúng clip Mini, nhưng V6 **không PASS đầy đủ**; không có 54-class mAP hay event GT. Đây là phạm vi đã được duyệt nội bộ, không cần đổi cờ manifest. | Giữ nguyên pin/QA và so scorer trên cùng frame; trình bày giới hạn rõ. Muốn hoàn tất V6 vẫn phải làm event GT, timing/duplicate/flicker và quyền/riêng tư. |
| B. Gán nhãn lại mức đối tượng cho toàn bộ 103 frame và interval | Có đường tới GT frame + event đủ phạm vi V6 nếu độc lập QA PASS. | Khóa schema object `known / out-of-scope / unreadable`, reviewer mù model phân xử frame 100/28 uncertain và 23 D; tạo manifest successor, QA 103/103, khóa scorer trước đánh giá. Tốn công; tránh chọn nhãn/ngưỡng theo output Mini. |
| C. Tìm/ghi clip camera trước khác với quyền rõ ràng | Có thể tạo tập đánh giá độc lập hơn và giải quyết vấn đề pixel thiếu ở Mini; V6 vẫn chờ nhãn/QA. | Xác nhận giấy phép, quyền trình chiếu và privacy, kiểm không trùng train/val/test; A/B/C gán nhãn mới, manifest hash, scorer và latency chạy lại. Tốn thời gian; clip mới có thể không đủ lớp/negative. |

**Decision gate cho Owner:** chọn A như minh họa chẩn đoán có giới hạn, hoặc đầu tư B/C để hướng đến V6 đầy đủ; không tự nâng 74 frame thành GT 54 lớp. Quyền dữ liệu và quyền chiếu là gate riêng, không được suy ra từ QA nhãn. Mọi chỉ số hiện có trên Mini là một clip và hai lớp, không phải hiệu năng hiện trường.

## Những gì chưa biết hoặc chưa được duyệt

- `privacy_clearance=false`; `presentation_rights_confirmed=false` theo hồ sơ Review 2. Owner từng xác định phạm vi dự kiến là chỉ chiếu trực tiếp trong lớp nhưng sau đó chưa duyệt bản trình chiếu cụ thể; không tự coi phạm vi này là quyền đã cấp.
- Thư xin full PHENIKAA được tài liệu ghi là chưa có phản hồi tại 2026-11-01; **tình trạng trả lời hiện tại UNKNOWN** vì lượt này không kiểm Gmail.
- Ground truth interval/event, độ chính xác đủ 54 lớp, split độc lập, quyền phát hành/trình chiếu và gate V6 còn UNKNOWN/chưa PASS. Bản R2 chỉ approved cho chẩn đoán nội bộ hai lớp. Không mở sealed test hoặc điều khiển xe thật.

## Hash nguồn đọc lại trong lượt này

| Nguồn | SHA-256 |
| --- | --- |
| `docs/review/review2_dashcam_video_r1_plan_and_status.md` | `850b1965a9485b59be6ecd75ed7adff1951d4c82c03c4261d56bb72fca48744e` |
| `docs/review/review2_video_annotation_pair_r1_report.md` | `26d816964f9d1cec7c5efdb1c51c885d54546ec9c1f8ef3874cca5d1d9b9509d` |
| `docs/review/review2_video_annotation_r2_candidate_report.md` | `c8b30ceca1383c9e135445e2db0854be628e385fca71cd232b0c834c57434244` |
| `docs/review/review2_video_annotation_r2_ignore_policy_proposal.md` | `39ed83b82007f7010faf21cac8129df18ac312d5603242c7a9c244c2e73b5f02` |
| `docs/review/review2_frame_diagnostic_r2_scope_decision_2026-11-01.md` | `2a7bd52a770180e978b1e2fa56dd80b994cc2fa97e32209fec42e66eb0c39b5d` |
| `docs/review/review2_video_scoring_contract_r1_proposal.md` | `25baf2db56c39a292219406b87fc85a0810e1ece253850addf42abe5182d34fa` |
| `docs/review/review2_annotation_c_visual_qa_0_100_2026-11-01.md` | `3c52f3af1aac94fa00b65d3e16725efd0e75534acf79c80319f134060f8b6b63` |
| `docs/review/review2_frame_diagnostic_r2_content_independent_qa_2026-11-01.md` | `3717ed2414515fdc2642ca33be3abbfc624a3bccf2a155d29fc64b2ae5bfb146` |
| `tmp/review2_annotation_packet_r1/annotator_A_frame_review.csv` | `002086b178c6e4ddfcd5833f5df01ca8ff0b151fcc3491609225c82612214b63` |
| `tmp/review2_annotation_packet_r1/annotator_B_frame_review.csv` | `d4b6d711c6700f34aaeaab7a22f0f3a50acdb61d368c1e6dfe1e7d19286a9745` |
| `tmp/review2_annotation_packet_r1/adjudicator_C_frame_review.csv` | `38d962277b4a884d7c63b1ac88158d14940a65428d91525405bbbb5db4afddde` |
| `tmp/review2_annotation_packet_r1/ignore_regions_r2.csv` | `d876cfbf553832cf92f7b09a9eb3529c98aaca184fbe574a42ef0c357dc24432` |
| `tmp/review2_annotation_packet_r1/unresolved_frames_r2.csv` | `e050c3705391c67773eac96ba5b0bc64a04c1eda1b817117939bfd85e66ebea1` |
| `tmp/review2_annotation_packet_r1/frame_diagnostic_candidate_r2_v2.json` | `b90710ee30d5d33bf42f751e8774a567b666dae17c3d4570183d1f4f1a2848c1` |
| `tmp/review2_annotation_packet_r1/adjudication_check.json` | `27c1492966c5c1bafd12ecd9e7b13707f68c3c3c23cb63a962a6245253bb97b9` |
| `tmp/review2_annotation_packet_r1/ignore_check_r2.json` | `fccab866a4a4e4523ea6358b1a76f1e10cba7260d69b08420c2e44ef1e2f388e` |

**File tạo mới:** `docs/review/review2_v6_owner_decision_packet_2026-11-04.md` (SHA-256 sau khi ghi được báo riêng khi bàn giao vì file không thể tự chứa hash cuối của chính nó). Không commit/push, không sửa A/B/C/R2 hay tài liệu đã pin.
