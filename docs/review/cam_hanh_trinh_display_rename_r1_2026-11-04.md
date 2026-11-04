# Đổi tên hiển thị "Review 2" → "Ứng dụng Model cho Cam Hành trình" (R1, 2026-11-04)

Loại: verified current behavior (UI text only). Không đổi model, artifact, manifest, ngưỡng,
tên module/hàm/biến/khóa `session_state` (`review2_*`, `demo_model`) hay script.

## File đổi

| File | Chuỗi đổi | SHA-256 trước | SHA-256 sau |
| --- | ---: | --- | --- |
| `src/cpv301_autodrive/app_pages/07_demo.py` | 2 | `84e0a0ced9dc57bf4894985024fde688cec153dceeb6af86c885f4fe7b415e31` | `05d1a34637ffc6338afd1bbdde3634d56b2ced094fa187c2bdd80a4f848d3ab2` |
| `tests/test_web_app.py` | +1 test | `fd3f42810587d6eba25246ce691899ef86fc80cfb90ff8c157dcd061c4483bd7` | `b8b37ea270cd759269372074839ded99b70180e78250cede20a4f078eec88633` |
| `src/cpv301_autodrive/review2_front_demo_r1.py` | 8 | `fc55d9d65576f8ed50987a8c3b0874c5d45d3f647958ad0b7fb7315a8a3a46ac` | `40dcdf2690727dfb5ce5b6c0cb4901d5c9a21e42b213c270d69f729a069d7850` |

Tổng 10 chuỗi:

- `07_demo.py`: nhãn segmented control `Review 2 · video camera trước (thử nghiệm)` →
  `Ứng dụng Model cho Cam Hành trình (thử nghiệm)`, đặt trong hằng số `CAM_HANH_TRINH_MODE`;
  nhánh render đổi từ `startswith("Review 2")` sang `model == CAM_HANH_TRINH_MODE`.
- `review2_front_demo_r1.py`: subheader → `Ứng dụng Model cho Cam Hành trình · camera trước xe
  (bản thử nghiệm)`; 7 thông điệp `ValueError` (hiện qua `st.error` khi kiểm chứng thất bại)
  đổi tiền tố `Review 2 …` → `Ứng dụng Model cho Cam Hành trình: …`.

Cả hai hash "trước" không xuất hiện trong `docs/` (grep), nên không verifier nào bị vỡ. Docstring
module (`"""… Review 2 …"""`) trong `review2_*` không hiển thị trên app và được giữ nguyên.
Không test nào trong `tests/` assert chuỗi cũ. `demo_model` không bind query param (chỉ
`session_state`); test mới `test_demo_slide_ignores_stale_review2_mode_label` đặt giá trị cũ
`Review 2 · …` vào `demo_model` và xác nhận trang Demo không lỗi, quay về mode D1.

## Kiểm chứng

- `uv run ruff check src tests`: PASS.
- `uv run pytest -q tests/test_review2_*.py tests/test_web_app.py tests/test_detector_d1.py
  tests/test_s1_demo.py`: 142 passed.
- `uv run pytest -q` (toàn bộ) và `uv lock --check`: xem mục Kết quả bổ sung.
- `graft build . && graft check .`: OK.
- Trình duyệt thật (Streamlit `127.0.0.1:8631`, không đụng 8599/8611/8612): 8/8 trang có 0 lần
  khớp `/review\s?2/i` trong `innerText`; chế độ Cam Hành trình trên trang Demo hiển thị nhãn và
  subheader mới, 0 lỗi `st.error`, 0 khớp "Review 2". Ảnh:
  `docs/review/cam_hanh_trinh_label_r1_browser_2026-11-04.jpg`
  (SHA-256 `99995c6a7817bf65a08e7634fdb97fc6e1590b9733045875ac264d82ff08c9a5`).

## Chưa làm

- Không đổi chuỗi "Review 2" trong `scripts/`, docstring, tiêu đề HTML packet nội bộ, hay hồ sơ
  `docs/review/` (ngoài phạm vi / append-only).
- Nhánh `app-release-r1` trên GitHub chưa được cập nhật; không commit/push.

## Bổ sung: gỡ 6 khối chữ theo yêu cầu Owner (2026-11-04)

Theo yêu cầu trực tiếp của Owner, `src/cpv301_autodrive/review2_front_demo_r1.py` gỡ 6 khối chữ
hiển thị (SHA-256 `40dcdf26…7850` → `b1ebd638327dc9d261ded57e4be522f9df71f0c6ce263dad983af0e518486690`):

1. caption `PHENIKAA Mini Dataset · ROUNDABOUT · CAM_P_F. Clip được ghép…`;
2. warning `DEMO_ONLY: bộ dữ liệu cung cấp nhãn 3D Car/Rider/Pedestrian…`;
3. warning nhánh R1 `Video rõ nét không làm mờ hoặc che phương tiện…`;
4. caption `Nguồn: PHENIKAA OPEN DATASET… PHENIKAA không xác nhận kết quả model.` (cùng biến
   `transformation` chỉ dùng cho caption này);
5. caption `CenterCam trên video chú giải…`;
6. caption `P.127 là mã biển chung…`.

Giữ nguyên: expander "Nguồn, giấy phép và thay đổi của clip" (ghi nguồn PHENIKAA, CC BY-NC-SA 4.0,
thay đổi và cảnh báo quyền riêng tư), warning/caption R14, các lỗi `st.error`, chặn non-localhost.
Đây chỉ là bỏ chữ trên UI; trạng thái DEMO_ONLY, giới hạn localhost và việc chưa duyệt trình chiếu
không đổi. Không test nào assert các chuỗi đã gỡ.

Kiểm chứng: `ruff check src tests` PASS; 142 test liên quan PASS; `graft check` OK. Server 8631
khởi động lại (module thư viện không tự reload); ở cả R14 (mặc định) và R1, 0/7 chuỗi khóa
(6 khối + "Review 2") còn trong `innerText`, 0 lỗi, 2 video hiển thị. Ảnh R1:
`docs/review/cam_hanh_trinh_text_removal_r1_browser_2026-11-04.jpg`
(SHA-256 `9dd5a1b2fb6f01ccc8d82418d186b1d78fcce4be1c55f13ebc8f4e2591905a88`).

## Bổ sung 2: tách tab con trên trang Demo, bỏ E0 (2026-11-04)

Theo yêu cầu Owner, `src/cpv301_autodrive/app_pages/07_demo.py` (SHA-256 sau
`01a250ff79217746d8f0fbb0c5ae90140ef7e2fee14fa6b1528780869fb1f24c`) dùng `st.tabs` có
`key="demo_tab"`, `on_change="rerun"` (chỉ chạy tab đang mở) với hai tab con:

- `Model`: segmented control `demo_model` chỉ còn D1 và S1 (mặc định D1).
- `Ứng dụng Model cho Cam Hành trình (thử nghiệm)`: gọi `render_review2_front_demo()`.

Lựa chọn `E0 · GTSRB (ảnh crop)` và nhánh `render_simulator()` bị gỡ khỏi trang Demo.
`views.render_simulator` không còn nơi gọi nhưng được giữ (chưa xóa code). Các câu nhắc E0
dạng văn bản ở trang Tổng quan/Bài toán/`project_status.py` chưa đổi.

`tests/test_web_app.py` (SHA-256 sau `dca55789e35666b03c446e541250dd3366d0f68945383c8a573be52a49916e71`):
bỏ test E0; thêm `test_demo_slide_offers_only_d1_and_s1_models`,
`test_demo_slide_cam_hanh_trinh_is_a_subtab`; test giá trị cũ thành
`test_demo_slide_ignores_stale_mode_label` cho cả `Review 2 · …` và `E0 · …` → về D1.

Kiểm chứng: `ruff check src tests` PASS; 144 test liên quan PASS; `graft check` OK. Trình duyệt
(8631, server khởi động lại): tab Model chọn sẵn, chỉ D1/S1, không có chữ E0/GTSRB, 0 lỗi; tab
Cam Hành trình hiện subheader, 2 video, không có control `demo_model`, 0 lỗi, 0 "Review 2".
Ảnh: `docs/review/demo_subtabs_r1_model_tab_2026-11-04.jpg`
(`93743dd578b30033190a62f4dabc932ec8d5bc81428fad4e18ffecce3cc7d582`),
`docs/review/demo_subtabs_r1_cam_tab_2026-11-04.jpg`
(`e9d68c18b447edbbaa90f68ad259b4786b522dab0cb9426391fbb7acaff7a282`).
Ghi chú: trong lúc làm, một phiên khác đã thêm control "Ngưỡng động theo thời gian" vào
`review2_front_demo_r1.py`; hash file đó ở mục trên có thể không còn là hash hiện tại.

## Kết quả bổ sung: pytest toàn phần

`uv run pytest -q` (chạy trên bản sau khi đổi nhãn; bắt đầu trước khi đổi sang hằng số, gỡ 6 khối
chữ và tách tab): 1 FAILED `tests/test_root_env_r1.py::test_real_tree_wp6_without_e0_rerun`,
các test còn lại pass. Lỗi này chưa được điều tra; test kiểm môi trường WP6, không đụng chuỗi UI.
`uv lock --check`: PASS.

## Điều tra `test_real_tree_wp6_without_e0_rerun` (2026-11-04)

Kết luận: lỗi **có từ trước**, không do việc đổi nhãn/tách tab hay Temporal DT. Không sửa verifier
hay file bị pin.

- Chạy riêng: `WP6 reports errors beyond the re-pinned files: ['tampered sources file: uv.lock',
  'tampered sources file: pyproject.toml', 'tampered sources file: docs/drive_inventory.md']`.
- `scripts/verify_root_env_r1.py` chấp nhận sẵn lỗi của `uv.lock` và `pyproject.toml`
  (`WP6_ALLOWED_ERRORS`, đã re-pin); hai file này khớp HEAD (commit `4e5c798`, 2026-10-23).
  Lỗi thừa duy nhất là `docs/drive_inventory.md`.
- `docs/drive_inventory.md` đang dirty (+6 dòng, mục "Nguồn PHENIKAA mini riêng cho Review 2
  (2026-10-31)", mtime 2026-10-31 21:17), đã ở trạng thái `M` từ đầu phiên. SHA-256 bản HEAD
  `35feb56f…7c3f` có trong `docs/review/generated/wp6_e0_compute_manifest.json`; bản hiện tại
  `9b7bab5d…244d` thì không.
- Không file nào sửa hôm nay (`07_demo.py`, `review2_front_demo_r1.py`, `tests/test_web_app.py`,
  file Temporal DT) nằm trong tập file WP6 kiểm.

Cách gỡ cần Owner quyết: chuyển ghi chú PHENIKAA sang tài liệu không bị pin (ví dụ
`docs/review/review2_dashcam_video_r1_plan_and_status.md`), hoặc re-pin WP6 có QA.

## Gỡ lỗi WP6: tách ghi chú PHENIKAA khỏi `drive_inventory.md` (2026-11-04)

Theo quyết định Owner:

- 6 dòng ghi chú (mục "Nguồn PHENIKAA mini riêng cho Review 2 (2026-10-31)") chuyển nguyên văn
  sang `docs/drive_inventory_phenikaa_addendum_2026-10-31.md` (SHA-256 `9f9c81e03a93622385bb8ceb8a9ea76b9cd33ed6113a76533fb855b910790e64`), thêm phần đầu ghi nguồn và lý do chuyển.
- `docs/drive_inventory.md` trả về đúng bản HEAD bằng `git show HEAD:docs/drive_inventory.md`;
  SHA-256 `35feb56fddc3cc2f9d037643fe0fc6ff8b43b0de651952a9168e006c58577c3f`, khớp hash có trong
  `docs/review/generated/wp6_e0_compute_manifest.json`. `git status` không còn báo file này bị sửa.
- Tham chiếu: không tài liệu nào trỏ riêng tới ghi chú này; chỉ có tham chiếu chung tới
  `drive_inventory.md` (`PROJECT_MEMORY.md`, `AGENTS.md`). `PROJECT_MEMORY.md` thêm một dòng trỏ
  addendum và ghi rằng file gốc bị pin. `AGENTS.md` giữ nguyên.

Kiểm chứng: `tests/test_root_env_r1.py::test_real_tree_wp6_without_e0_rerun` PASS; toàn bộ
`tests/test_root_env_r1.py` và `tests/test_e0_compute_readiness.py` pass, có 5 xfail đã đánh dấu
sẵn "superseded by ROOT-ENV-R1 re-pin"; `uv run ruff check src tests` PASS. Không sửa verifier
hay file bị pin.
