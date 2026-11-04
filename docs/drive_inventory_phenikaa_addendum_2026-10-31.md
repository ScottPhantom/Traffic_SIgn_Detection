# Drive inventory addendum — PHENIKAA mini (2026-10-31)

Chuyển nguyên văn từ `docs/drive_inventory.md` ngày 2026-11-04, vì file gốc bị WP6 pin hash
(`docs/review/generated/wp6_e0_compute_manifest.json`); ghi chú thêm vào đó làm verifier WP6 fail.
Nội dung bên dưới không đổi.

## Nguồn PHENIKAA mini riêng cho Review 2 (2026-10-31)

Nguồn Drive Owner cung cấp: `https://drive.google.com/drive/folders/1urAVZQCL5RozBYVSRkMrrM0I22PEI1t9`. Chỉ nhập `Mini Dataset/ROUNDABOUT/camera/CAM_P_F` (camera pinhole phía trước), folder ID `16_QTipsvf4ndd4sfnaHkDDqpgTldaJO6`; **không nhập toàn bộ mini dataset hoặc Full Dataset**. 200 JPEG gốc, tổng 31.351.576 byte, độ phân giải 1920×1536, được giữ bất biến trong `data/raw/phenikaa_mini_front_r1/ROUNDABOUT/CAM_P_F/` ngoài Git. `data/raw/phenikaa_mini_front_r1/ROUNDABOUT/drive_inventory.json` lưu từng Drive file ID và byte; SHA-256 inventory `32ff48f16cd16b206a622cb46f82959242578e5854fe4c5573a898fb087961d4`. Manifest clip ở `data/processed/phenikaa_front_demo_r1/ROUNDABOUT_CAM_P_F.manifest.json` lưu SHA-256 từng JPEG và ánh xạ frame, để xác minh bản nhập lại.

Sản phẩm dẫn xuất cục bộ ngoài Git: `ROUNDABOUT_CAM_P_F.mp4` SHA-256 `1fab75937ceba286abbc308138a814a7d9548b722184d4735b802f29d4b1f5ac` và `ROUNDABOUT_CAM_P_F_D1.mp4` SHA-256 `fabbb2796d6b212291093aff3ecf48337734d3bf0e80a5b86316c55e227ea4b5` trong `data/processed/phenikaa_front_demo_r1/`. Điều khoản nguồn công bố là CC BY-NC-SA 4.0; thư xin full dataset và quyền chiếu clip dẫn xuất tại lớp vẫn đang chờ phản hồi. Không có nhãn ground truth biển báo cho clip này; status `DEMO_ONLY`, `sealed_test_accessed=false`. Xem `docs/review/review2_dashcam_video_r1_plan_and_status.md` §6 để biết gate còn thiếu.
