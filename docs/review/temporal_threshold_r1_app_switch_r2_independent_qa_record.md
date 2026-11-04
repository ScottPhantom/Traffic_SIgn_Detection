# Temporal DT R1 app switch R2 — independent QA of the F1–F3 fixes, 2026-11-04

Verdict: **PASS** — F1, F2 and F3 are fixed and the switch-off output is still byte-identical to the code before the switch existed; no new defect found.

Scope: the fixes for the findings in
`docs/review/temporal_threshold_r1_app_switch_independent_qa_record.md`, as described in the
author's successor record `docs/review/temporal_threshold_r1_app_switch_r2_record.md`. This QA
session did not write the code and did not edit the files under review, its own earlier record,
`07_demo.py`, `views.py`, D-05 or the sealed test. Nothing was committed, pushed, stashed or
branch-switched. Every claim below was run or read back in this checkout on 2026-11-04.

## Reviewed artifacts (SHA-256 recomputed before and after QA; all match the hand-over)

| File | SHA-256 |
| --- | --- |
| `src/cpv301_autodrive/review2_temporal_dt_r1.py` | `4d4c782859f6bd9c32165b701141f813cba4f98d11406524ba15f09179bc85f3` |
| `src/cpv301_autodrive/review2_front_demo_r1.py` | `a52d0d45e1b44534ffdbd8c811d29e6597d6d40bbc121137860769fa6c5ce223` |
| `src/cpv301_autodrive/review2_upload_video_r1.py` | `8c25247e51b441c05b859935696707bbf55d79c1e528f4e9eaece0a9d6b2c493` |
| `tests/test_review2_temporal_dt_r1.py` | `c5cdd858f3142d000d45b9440117a6dbdc23e376c576126fbf63ee21addd696a` |
| `src/cpv301_autodrive/review2_video_seek_r1.py` (unchanged since R1) | `c0bfda8141869e863e40ce497c0072954ba2faa0560c0643e28a6b2fc03a3b4b` |
| `src/cpv301_autodrive/temporal_threshold.py` (unchanged) | `a519066abc6106ae0e729d09d846847997a1d9b584efc769c88d4b03308e9fdc` |
| `docs/review/temporal_threshold_r1_app_switch_r2_record.md` | `bdb68f0ef2ff6b56ebe13636bcd5822ebd3b3ba6f1f329b9cef92691ba9bf3e0` |

## Results

| Item | Result |
| --- | --- |
| F1: the "before" track hold matches the app at any fps | **PASS** |
| F2: a disabled or stale switch is forced off | **PASS** |
| F3: new tests | **PASS** |
| Regression: switch off still matches the pre-switch code, display-only, behavior off while on, 0.20 and D-05 unchanged | **PASS** |
| Gates and real browser | **PASS** |

### F1 — the hold depends on fps

**Code.**

- `hold_samples(source_fps, step) = max(1, round(source_fps / step * 0.4))`. The app computes
  its track-CSV hold as `round(output_fps * 0.4)` with `output_fps = fps / step`
  (`review2_upload_video_r1.py:348`). The two use the same floating-point operations in the same
  order, so they agree for every fps, including the half-way cases where Python rounds to even.
- `compare()` now requires `source_fps` and uses it for the hold and for `time_ms_nominal`.
- Upload passes `manifest["source_fps_nominal"]`, which is the decoded `fps` (`:398`). It shows
  `st.error` and no panel if `summary["hold_samples"]` differs from
  `manifest["track_hold_max_samples"]`.
- The preview passes the raw manifest's `output_fps` (10) with step 2, so its hold is 2.

**QA's own check.** `f1check.py` does not reuse the author's test.

- It builds synthetic H.264 clips at 10, 15, 24, 25, 30 and 60 fps.
- A detector reports a moving sign with gap patterns of 1, 2 and 3 missed sampled frames.
- Each clip runs through `process_uploaded_video(temporal_candidates=True)`. The panel's
  `hold_samples` and "before" track count are then compared with
  `manifest["track_hold_max_samples"]` and with the number of distinct `track_id` values in the
  app's own track CSV.

| Formula | Matching cases (of 18) |
| --- | --- |
| New `hold_samples` | **18** (hold 2 everywhere; track counts 1 / 1 / 4–5 equal the app's) |
| Old `round((10/step)·0.4)` patched back in | 3 (only 10 fps). The other 15 mismatch; e.g. 30 fps with gap 2 gives hold 1 vs 2 and 5 tracks vs the app's 1. |

So the old bug is real, the fix removes it for every fps tried, and the check is sensitive to it.
The `st.error` guard did not trigger in any run, and QA could not trigger it without changing the
code. It is a defensive check only.

### F2 — the switch is forced off when disabled or stale

**Code.** `temporal_toggle()` sets `st.session_state[key] = False` before the widget is created
whenever `disabled` is true or the stored value is not a bool. It then calls
`st.toggle(label, key=…, disabled=…)` with no `value=` argument, so Streamlit has no default to
conflict with Session State, and assigning before the widget exists is allowed.

**Browser** (own server on `127.0.0.1:8652`):

| Step | Upload switch |
| --- | --- |
| D1, switch turned on | `checked=true, disabled=false` |
| Switch architecture to Cascade B0 | `checked=false, disabled=true` (screenshot c2) |
| Back to D1 | `checked=false, disabled=false` |

No text containing "Session State" appeared and there were no exceptions. The R1 defect, a
greyed-out switch that still looked on, no longer occurs. As the author notes, coming back from
Cascade leaves the switch off by design.

### F3 — tests

`tests/test_review2_temporal_dt_r1.py` now has 15 tests, all passing. The new ones are:

- `test_hold_matches_app_formula_for_any_fps` (10, 30, 60 and 25 fps, plus a rejection case);
- `test_30fps_before_tracks_match_the_app_track_csv` (hold 2 = manifest; 1 track = the track
  CSV; 3 boxes = `prediction_rows`);
- `test_cascade_with_stale_true_renders_switch_off_and_disabled` (stored value becomes `False`;
  no Session State warning);
- `test_switching_d1_on_then_cascade_turns_switch_off_and_back_stays_off`.

QA read each one and they assert what the record claims. QA's own `f1check.py` covers more fps
values and gap patterns than the 30-fps unit test.

### Regression

QA re-ran its own `probe.py` from the R1 QA, not the author's `offcheck.py`, on the current tree.
It compared the output with QA's own R1 run of the reconstructed pre-switch original
(`orig_off.json`), whose front-demo file was anchored to `b1ebd638…` by the rename session's
record.

- **Switch off, upload** (real D1, Mini clip `1fab7593…`): the video, prediction CSV
  (`343e00c3…`, the pinned upload), tracks CSV, events CSV and manifest are **byte-identical** to
  the original.
- **Switch off, pre-built preview:** the AppTest element-tree file is byte-identical to the
  original's (SHA-256 `cedb69c4…`, 43 elements without the two switches). There are no
  exceptions, and both switches are present and off.
- **Switch on, upload:** the exports are identical to the switch-off run. The manifest gains
  only the `temporal_dt_r1_display` block (`candidate_rows 246`,
  `exports_use_fixed_conf 0.2`, `behavior_simulation_disabled true`,
  `EXPERIMENTAL_DISPLAY_ONLY_NOT_D05`).
- **Switch on, preview:** metrics are 54→55 boxes, 10→10 tracks, 11→4 label switches, the same
  as R1.
- **Behavior gating** is unchanged: `behavior_enabled=not temporal_dt_on` in the preview, and
  `not cascade and not temporal_dt_on` in the upload flow with the Temporal reason.
  `review2_video_seek_r1.py` and `temporal_threshold.py` hashes are unchanged.
  `detector_d1_r3.DEFAULT_CONF` is still 0.20, and no D-05 file is touched.

### Gates and browser

- `uv run ruff check src tests scripts`: All checks passed.
- pytest on the ten related files (temporal_dt, temporal_overlay, temporal_r1, upload_video,
  video_seek, behavior, temporal_threshold_r1, web_app, s1_demo, dynamic_threshold_product):
  **98 passed, 0 skipped**.
- `uv lock --check`: OK.
- `graft build . && graft check .`: in sync.
- **Browser** on 8652, which QA started and then stopped. QA did not touch 8599, 8611, 8612,
  8631, 8641 or an unrelated listener found on 8651.
  - Fresh page: both switches off.
  - The F2 sequence above.
  - Upload of the Mini clip with the switch on. The clip was fetched from the page's own media
    URL and hash-checked in the browser (`1fab7593…`, 23,713,392 bytes).
  - The panel caption reads "… liên kết R12 trên box ≥0,20 (giữ tối đa 2 frame lấy mẫu) …".
    The guard did not fire. Counts were 54/55, 10/10, 11/4 with reasons 185/55/6, and prediction
    rows stayed at 54 (screenshot c3).
  - The server log has no errors.

## Limits

- A real non-10-fps clip was not run in the browser; non-10-fps behavior is covered by synthetic
  clips in QA's `f1check.py` and the author's test.
- The switch-off comparison still rests on the Mini clip and the pre-built preview, as in R1.
- The PASS covers only the default-off, display-only experimental switch. It changes nothing for
  0.20, D-05, exports or behavior simulation, and makes no accuracy claim.

## Evidence

Shared notes folder (outside the repo):
`side-session-notes/local_0f8736ca-…/temporal_dt_r1_app_switch_r2_qa_evidence/`.

| File | SHA-256 |
| --- | --- |
| `f1check.py` | `2260d696488b6e8875a763fa0e77ff5a48ec8e014f75e43650d91962360741ca` |
| `f1check_out.txt` (0 mismatches) | `13de2430d0a01499d76ee43feb64a9c914fc5510fcafa43d113120325820522e` |
| `f1check_oldformula.py` | `67a4275c14ffb7341f392e8aac21e78371d1a26dabc7152e3dd5659018751818` |
| `f1check_oldformula_out.txt` (15 mismatches) | `720651bf775e2256e7cf2c7da8ac10a5ad25bb2fae666042ec60ec4eb20d97b5` |
| `r2_off.json` | `f8cb3f78c65aaa671fa3e46a85ba2daeeaf1a8f4f9b6ef8bcb53c9b759964353` |
| `r2_off.json.tree.json` (= R1 original tree) | `cedb69c421689c335794ddd533a50f109ce5ef7c50a1b51fcc4346d48c1ab217` |
| `r2_on.json` | `ac817c9c8c134889e319fd3b93866e500fd8557416d90e60e7862cc706e2784c` |
| `c1_upload_d1_on.jpg` | `9dc9f8fd06c7cc6d10262f7ba77bfbda24fbb92e349a36010eaf237665191734` |
| `c2_upload_cascade_off_disabled.jpg` | `453ea7588c547e3f66b6c0c0c045748d281c7df93455801214e855ce4e485180` |
| `c3_upload_on_panel_hold2.jpg` | `68749685f1360de5fed39aa0919c8ee30b0cde3aad28a032ad5a7b8687775d3c` |

The baseline `orig_off.json` and `probe.py` are in the R1 QA evidence folder
(`temporal_dt_r1_app_switch_qa_evidence/`).
