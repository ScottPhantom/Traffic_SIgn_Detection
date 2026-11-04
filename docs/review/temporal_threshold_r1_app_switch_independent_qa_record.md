# Temporal DT R1 experimental app switch — independent QA (UI + source), 2026-11-04

Verdict: **PASS** — all seven Owner requirements hold for the display-only, default-off switch. There are three non-blocking findings (F1–F3); none changes exports, behavior safety or D-05.

Scope: the switch "Ngưỡng động theo thời gian (thử nghiệm)" in "Ứng dụng Model cho Cam Hành
trình", as recorded in `docs/review/temporal_threshold_r1_app_switch_record.md`. The QA session
did not write this code and did not edit any file under review. It also did not touch
`app_pages/07_demo.py`, `views.py`, D-05 or the sealed test. Nothing was committed, pushed,
stashed or branch-switched. Every claim below is **VERIFIED** in this checkout on 2026-11-04
unless marked otherwise.

## Reviewed artifacts (SHA-256 recomputed; all match the hand-over)

| File | SHA-256 |
| --- | --- |
| `src/cpv301_autodrive/review2_temporal_dt_r1.py` (new) | `936b2cdd1310c069b047a000034cae1191e3b955a58e8f6bcb4e08c4377f9591` |
| `src/cpv301_autodrive/review2_front_demo_r1.py` | `af5a843b2d6ffa5c34e2a99209d391ac5abe129d6303b64a66fc721288d32f1e` |
| `src/cpv301_autodrive/review2_upload_video_r1.py` | `b8d368d7f70ef1d73db7a28a999e19320212b59ba959f9e92e434aa4d59eff1a` |
| `src/cpv301_autodrive/review2_video_seek_r1.py` | `c0bfda8141869e863e40ce497c0072954ba2faa0560c0643e28a6b2fc03a3b4b` |
| `tests/test_review2_temporal_dt_r1.py` | `e16dde962dcadb9f280f8250f68cf900af61862d2c56e2d7ae46168dc4bc3d79` |
| `.claude/launch.json` | `19a66a83857fb81b31317808c8994a5f28d3ba789e5d33509bd0a33982470e94` |
| `src/cpv301_autodrive/temporal_threshold.py` (must be unchanged) | `a519066abc6106ae0e729d09d846847997a1d9b584efc769c88d4b03308e9fdc` |
| `docs/review/temporal_threshold_r1_app_switch_record.md` | `c8f28b9d83a4a568dca86a75c45aa58a77b685f92de9fe5cb50389078c2ca4e1` |

## Requirements

| # | Requirement | Result |
| --- | --- | --- |
| R1 | Default OFF, separate keys, disabled for Cascade | **PASS** (see F2) |
| R2 | OFF behaves exactly as before the edit | **PASS** |
| R3 | ON panel, keep/drop table, exact Owner note, exports at 0.20, candidate sources | **PASS** (see F1) |
| R4 | ON disables behavior with the Temporal message; `vehicle_action` none; R13 unchanged | **PASS** |
| R5 | Default 0.20, D-05, raw predictions, pinned manifests, still-image modes, `temporal_threshold.py` unchanged | **PASS** |
| R6 | Stale `session_state` does not crash; ruff, pytest, lock and graft gates | **PASS** (see F3) |
| R7 | Real browser on a free port, OFF and ON, preview and upload | **PASS** |

### R1 — toggle default, keys, Cascade

- `temporal_toggle()` calls `st.toggle(TOGGLE_LABEL, value=False, key=…)`. The label is exactly
  "Ngưỡng động theo thời gian (thử nghiệm)".
- The keys are `review2_temporal_dt_r1_precomputed` and `review2_temporal_dt_r1_upload`. Neither
  is used anywhere else.
- In the upload flow, `disabled=architecture != "d1_54"`, and the function returns
  `bool(value) and not disabled`.
- `process_uploaded_video(temporal_candidates=True, architecture="cascade_b0_r1")` raises
  `ValueError`.
- Browser on 8651, fresh session: both switches had `checked=false, disabled=false`, and there
  was no panel or note.
- With Cascade selected, the upload switch had `disabled=true` and no panel was shown.

### R2 — OFF is unchanged

The `review2_*` files are untracked in git, so no committed original exists. QA ran the author's
`revert.py` on a scratch copy and anchored the result in three independent ways:

1. **Hash anchor.** The reconstructed `review2_front_demo_r1.py` has SHA-256
   `b1ebd638327dc9d261ded57e4be522f9df71f0c6ce263dad983af0e518486690`. The display-rename session
   recorded exactly that value as the file's state just before this work
   (`docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md`, line 51).
2. **Full diff read.** QA read every hunk of the diff between the reconstruction and the current
   file for all three files. Every addition is gated on `temporal_dt_on` or
   `temporal_candidates`, except the toggle widget and the new `disabled_reason` argument.
   - With behavior enabled, `disabled_reason` is never read.
   - Its default `CASCADE_DISABLED_REASON` is byte-equal to the old Cascade string.
   - The reconstructed original runs without `review2_temporal_dt_r1.py` present at all.
3. **QA's own probe.** QA wrote `probe.py` instead of reusing `offcheck.py`. It ran in separate
   processes against a scratch root holding the reconstructed originals (other paths symlinked
   to the repo) and against the current tree.
   - **Upload:** `process_uploaded_video` with real D1 on the Mini clip `1fab7593…`. The video
     `027097f5…`, prediction CSV, tracks CSV `ec7de99f…`, events CSV `7d7a2e96…` and manifest
     `2090eb76…` are **byte-identical** between the original and the new code with the switch
     off. The prediction CSV is `343e00c3…`, the upload hash pinned before this work, which
     independently anchors the upload path.
   - **Preview:** with the switch off, the AppTest element tree of the pre-built preview is
     identical: 43 elements and tree SHA-256 `37525ddc…` once the two new toggles are left out.
     There were no exceptions, and the metrics are the same (200 / 206 / 68 / 8).

Limit, as the author also notes: OFF equivalence was measured on the Mini clip and the pre-built
preview only. For `review2_upload_video_r1.py` and `review2_video_seek_r1.py`, the original is a
reconstruction anchored by the diff read and the pinned upload CSV, not by a recorded file hash.

### R3 — ON content and exports

- **Note text:** the `NOTE` constant is character-for-character the Owner text. The browser
  string check is `true` in both the preview and upload panels.
- **Panel:** it shows "Trước · ngưỡng cố định 0,20" next to "Sau · Temporal DT R1 (0,35 / 0,15 /
  N=5 / max_miss=2)", with Box / Track / Lần đổi nhãn metrics and a reasons caption. Pre-built
  preview in the browser: 54→55 boxes, 10→10 tracks, 11→4 label switches.
- **Reasons and keep/drop table:** reasons are `below_keep_floor=185, kept_confirmed_track=55,
  tentative_evidence_below_enter=6` over 103 frames and 246 candidates. These equal QA's
  independent Mini recount from the R1 package QA (185 / 55 / 6). The keep/drop table, "Bảng
  giữ/bỏ từng candidate theo Temporal DT R1", has the columns frame, giữ/bỏ, nhãn_thô, điểm_thô,
  fixed_0.20, lý_do_temporal, track, trạng_thái, nhãn_track, điểm_track.
- **Locked parameters:** `run_sequence(…, PRIMARY)` is called with `temporal_threshold.PRIMARY`,
  which is 0.35 / 0.15 / 5 / 2. No parameter is exposed in the UI.
- **Candidate sources:**
  - The preview reads the hash-checked Mini CSV `67b714a7…` and manifest `8145ef27…`, which pin
    the clip, the 2-frame step and `sealed_test_accessed=false`.
  - An upload with the switch on calls `model.detect(conf=0.001)` once and feeds the boxes
    ≥ 0.20 to the unchanged pipeline.
- **Exports with the switch on:** QA's probe shows the video and all three CSVs identical to the
  OFF run. The manifest is identical except for the added `temporal_dt_r1_display` block:
  `enabled`, `candidate_conf 0.001`, `candidate_rows 246`, `exports_use_fixed_conf 0.2`,
  `behavior_simulation_disabled true`, `status EXPERIMENTAL_DISPLAY_ONLY_NOT_D05`. The browser
  upload with the switch on also showed 54 prediction rows.

### R4 — behavior safety

- With the switch on, `behavior_enabled=not temporal_dt_on` in the preview and
  `not cascade and not temporal_dt_on` in the upload flow. The reason passed is
  `BEHAVIOR_DISABLED_REASON` unless Cascade is selected.
- Browser, preview event P.130 at 9.1 s (track 5):
  - switch off: the conditional explanation shows as before ("Nếu biển áp dụng cho làn xe…");
  - switch on: "Mô phỏng hành vi tạm tắt vì công tắc Temporal DT (thử nghiệm) đang bật; không
    phát lệnh điều khiển xe."
- Same result in the upload flow (event P.130 at 9.8 s, track 8). The Cascade string was absent
  in both cases.
- `review2_behavior_r1.py`, which holds the R13 conflict gate and `vehicle_action: "none"`, and
  the linker `review2_temporal_r1.py` were last modified 2026-11-01, so this work did not change
  them. The new module emits no events and no actions.

### R5 — unchanged items

- `temporal_threshold.py` is still `a519066a…`.
- `detector_d1_r3.DEFAULT_CONF = 0.20`.
- The Mini candidate CSV is still `67b714a7…`, and the pinned R1 prediction CSV `343e00c3…` is
  reproduced with the switch off.
- No new code writes raw predictions or pinned manifests. An upload result's manifest is built
  in memory and gains the extra block only when the switch is on.
- The still-image D1/S1 modes are not imported by the new module, and `test_web_app.py` and
  `test_s1_demo.py` pass.
- `07_demo.py` and `views.py` do not reference the new module. Their changes come from other
  sessions; `07_demo.py` was changed at 13:55 by the display-rename work.
- No D-05 document or gate file is touched.

### R6 — tests and gates

- `uv run pytest` on the ten related files (temporal_dt, temporal_overlay, temporal_r1,
  upload_video, video_seek, behavior, temporal_threshold_r1, web_app, s1_demo,
  dynamic_threshold_product): **94 passed, 0 skipped**. That includes the 11 new tests, among
  them stale values `"on"`, `1`, `None` and `["x"]`.
- Extra QA check (`cascade_stale.py`):
  - upload key = True while Cascade is selected: no exception, and the switch is disabled with
    no effect;
  - upload key = `"yes"`: reset to False, no exception.
- `uv run ruff check src tests scripts`: All checks passed.
- `uv lock --check`: OK.
- `graft build . && graft check .`: in sync.

### R7 — real browser

- QA started its own server on `127.0.0.1:8651` (`uv run python main.py --headless --port
  8651`), the same command as the author's launch config, which QA did not edit. The author's
  8641 server and 8631 were left alone.
- The in-app browser checked, in order:
  1. pre-built preview, switch off;
  2. switch off with event P.130 selected (behavior shown);
  3. switch on (panel, note, table);
  4. switch on with the same event (Temporal disabled message);
  5. upload with the switch off. The clip was fetched from the page's own media URL and
     hash-checked in the browser as `1fab7593…` (23,713,392 bytes); the run gave 103 frames,
     54 rows and no panel;
  6. switch on before re-running: "Kết quả hiện tại được tạo khi công tắc đang tắt…";
  7. re-run with the switch on: panel "Clip vừa tải … 103 frame, 246 candidate", 54/55, 10/10,
     11/4, reasons 185/55/6;
  8. switch on with an upload event selected: Temporal disabled message;
  9. Cascade selected: switch disabled, no panel.
- No browser console errors. The server log has no error or traceback.

## Findings (non-blocking)

- **F1. The panel's "before" tracks are only correct for 10-fps clips.** `compare()` links the
  fixed boxes with `hold = round((10/step)·0.4)`, which assumes a 10-fps source. The app's own
  track CSV uses `round(output_fps·0.4)` with `output_fps = fps/step`. The two agree for 10 fps
  (hold 2, which covers the Mini clip and everything QA measured). For 24/25/30/60-fps uploads,
  the panel uses hold 1 while the app uses hold 2. The "Trước" track count and label-switch
  count can then differ from the app's own track CSV, even though the caption says "liên kết
  R12". It is display-only and labelled as not accuracy; exports are unaffected. Suggested fix
  (PROPOSAL): pass `output_fps` or `hold_samples` into `compare()`.
- **F2. A disabled switch can still look ON.** If the upload switch was on with D1 and the user
  then picks Cascade, the switch renders checked and disabled (browser:
  `checked=true, disabled=true`). It correctly has no effect, but it reads as "on". Suggested
  fix (PROPOSAL): reset the key, or render `value=False`, when disabled.
- **F3. Test gaps.** No test covers Cascade with a stale True value, or the non-10-fps hold in
  F1. The F2 behavior was checked by QA's script only.
- **Already known (author §5), confirmed:** the comparison counts boxes and tracks, not accuracy;
  the pre-built comparison samples every 2nd frame, unlike the R14/R1 video (the UI says so);
  and the Mini clip is processed without scene breaks in the preview.

## Decision boundary

- PASS authorizes only the default-off, display-only experimental switch as built.
- It does not change the default 0.20, D-05, exports or behavior simulation, and it is not an
  accuracy or video-gate claim.
- `PROJECT_MEMORY.md` and `docs/product_roadmap.md` updates remain for the author or PM.

## Evidence

Shared notes folder (outside the repo):
`side-session-notes/local_0f8736ca-…/temporal_dt_r1_app_switch_qa_evidence/`.

| File | SHA-256 |
| --- | --- |
| `probe.py` (QA's OFF/ON probe) | `027c9630c2b79494ba8fc315a643c9f732c55b1ec0fe29275ad121cc619e69b9` |
| `cascade_stale.py` | `337dd4f547f160dde70815ca886ff125242d480bbf240dd707b1bbf434a2178a` |
| `orig_off.json` / `new_off.json` / `new_on.json` | `b13c4a40…3c28` / `f8cb3f78…4353` / `10c653a5…76a9` |
| `orig_off.json.tree.json` = `new_off.json.tree.json` | `cedb69c421689c335794ddd533a50f109ce5ef7c50a1b51fcc4346d48c1ab217` (identical) |
| `reconstructed_review2_upload_video_r1.py` | `8f2da4ab359c0c2ab781dcc39856fe234d65320aad72a1802144f8557774a5da` |
| `b1_preview_off.jpg` | `375969654dd25db8d6a8408e114f9b4c6c2967b1c6d79541f06855dd70ffa6f0` |
| `b2_preview_off_event_behavior.jpg` | `76c1d171b714254b3f69179b27eb93d3555b785f8164c49e90f3ce899fbd0b93` |
| `b3_preview_on_panel.jpg` | `25bd65fc4fd1fa984f0d9221894f2b398093effe44975688f0cb4b478f9bff61` |
| `b4_preview_on_table_behavior_disabled.jpg` | `d52ebb6e080e61f6b02da062437254762c90205bd051079d1f9ecf6fac3d45e5` |
| `b5_upload_off_processed.jpg` | `dfe408b386680883ccd028240493a77c1eb398e0c6b06945db6342434bfddc99` |
| `b6_upload_on_panel_behavior_disabled.jpg` | `2c16b873fe51e373cb0048cafe2cdcbaabeef9656a95211e991df792d36f1d79` |
| `b7_upload_cascade_switch_disabled.jpg` | `7cc50adf595c3b3436ecc4fcfae2ff4ec6ccc21bc18415226e28ba91e5c87c78` |

The reconstructed originals of `review2_front_demo_r1.py` (`b1ebd638…`) and
`review2_video_seek_r1.py` (`626005d8…`) can be regenerated with the author's `revert.py`
(`tmp/temporal_dt_r1_ui_evidence/`).
