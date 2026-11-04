# Temporal DT R1 app switch — R2: fixes for QA findings F1–F3

File **append-only**; successor of `docs/review/temporal_threshold_r1_app_switch_record.md`
(not edited). Date 2026-11-04 (Asia/Ho_Chi_Minh). The Owner approved fixing F1–F3 from
`docs/review/temporal_threshold_r1_app_switch_independent_qa_record.md` (SHA-256
`0780b85dfbbdff7f1e69a3ae3ccfb47b96a5c117f81f7956a56bad837248b864`).
Status: **independent QA of these changes PENDING**; the author does not record PASS. No commit
or push.

## §1 Changes

- **F1, fps-aware "before" tracks.**
  - New `hold_samples(source_fps, step) = max(1, round(source_fps / step · 0.4))`. This is the
    same formula the app uses for its R12 track CSV (`round(output_fps · 0.4)`, with
    `output_fps = fps / step`).
  - `compare()` now requires `source_fps`, uses it for the hold and for `time_ms_nominal`, and
    returns `hold_samples`.
  - Upload passes the manifest's `source_fps_nominal`. The pre-built preview passes the raw
    manifest's `output_fps` (10).
  - Upload also refuses to show the panel (`st.error`) if the computed hold differs from the
    manifest's `track_hold_max_samples`.
  - The caption now states the hold ("giữ tối đa N frame lấy mẫu").
- **F2, a disabled switch never looks on.** `temporal_toggle` sets `session_state[key] = False`
  before rendering whenever the switch is disabled (Cascade) or holds a non-bool value. The
  toggle no longer passes `value=`, so Streamlit shows no warning about a widget default plus a
  Session State value. A stale `True` is therefore never shown or reused.
  - Consequence (by design): after D1 → Cascade → D1, the switch comes back **off** and must be
    turned on again.
- **F3, tests added** (`tests/test_review2_temporal_dt_r1.py`, now 15 tests):
  - `hold_samples` for 10/30/60/25 fps, plus a reject case;
  - a synthetic 30-fps upload (step 6) with a sign missing on two sampled frames: the panel's
    "before" track count, box count and hold equal the app's own track CSV and manifest
    (1 track, 3 boxes, hold 2). Under the old 10-fps formula this test **fails** (hold 1 ≠ 2),
    verified by monkeypatching the pre-fix formula;
  - Cascade with a stale `True` in `session_state`: the switch renders disabled and off, the
    state becomes `False`, and there is no Session State warning;
  - AppTest D1 on → Cascade → D1: off and disabled, then off and enabled.

## §2 Files (SHA-256)

| File | SHA-256 |
| --- | --- |
| `src/cpv301_autodrive/review2_temporal_dt_r1.py` | `4d4c782859f6bd9c32165b701141f813cba4f98d11406524ba15f09179bc85f3` |
| `src/cpv301_autodrive/review2_front_demo_r1.py` | `a52d0d45e1b44534ffdbd8c811d29e6597d6d40bbc121137860769fa6c5ce223` |
| `src/cpv301_autodrive/review2_upload_video_r1.py` | `8c25247e51b441c05b859935696707bbf55d79c1e528f4e9eaece0a9d6b2c493` |
| `src/cpv301_autodrive/review2_video_seek_r1.py` (unchanged since R1) | `c0bfda8141869e863e40ce497c0072954ba2faa0560c0643e28a6b2fc03a3b4b` |
| `tests/test_review2_temporal_dt_r1.py` | `c5cdd858f3142d000d45b9440117a6dbdc23e376c576126fbf63ee21addd696a` |
| `src/cpv301_autodrive/temporal_threshold.py` (unchanged) | `a519066abc6106ae0e729d09d846847997a1d9b584efc769c88d4b03308e9fdc` |

## §3 Verification (VERIFIED)

- **Off equals the pre-switch source.** I re-ran the R1 `revert.py`/`offcheck.py` method on the
  new code. Upload of the Mini clip with real D1 gives byte-identical video, CSVs and manifest,
  and the pre-built preview renders the same AppTest element tree (35 elements, no exception).
  Both result JSONs are byte-identical to the R1 check (`a6abc55d…` / `c32a72b3…`), so off
  behavior did not move.
- **Gates:** `uv run ruff check src tests scripts` PASS; 107 related tests PASS (13 files:
  review2, temporal, web_app, DT product, S1); `uv lock --check` PASS; `git diff --check` PASS;
  `graft build . && graft check .` in sync.
- **Real browser** on `127.0.0.1:8641` (restarted after the changes; 8599/8611/8612/8631 not
  touched; no server errors):
  1. Upload, D1, switch turned on: `checked=true, disabled=false`.
  2. Switch to Cascade B0: `checked=false, disabled=true`. F2 no longer occurs.
  3. Back to D1: `checked=false, disabled=false`.
  4. Switch on, Mini clip (`1fab7593…`, fed through DataTransfer as in R1), regenerate: panel
     with 103 frames and 246 candidates, caption "giữ tối đa 2 frame lấy mẫu", mismatch guard
     not triggered, counts 54/55 boxes, 10/10 tracks, 11/4 switches (same as R1).
- Evidence (ignored) in `tmp/temporal_dt_r1_ui_evidence/r2/`:

| File | SHA-256 |
| --- | --- |
| `01_upload_d1_on.jpg` | `f5a953c1b2c16687ad104ee4930aab9dca173f7d6212a1153a8d34cbd854e628` |
| `02_upload_cascade_forced_off.jpg` | `86b0e7cee86e9d647f3ece0085828b0be6edbc91d7fcefbe159620fa557c003a` |
| `03_upload_back_to_d1_off.jpg` | `cac7ff9af64c7a3837d8eb467f2ce1aa78bf6f39a9c4fa3a2c7e773e14e781c7` |
| `04_upload_on_hold2_caption.jpg` | `15ce86e1823155cbc090898fa8173b1d742b33b95292b84153673d11dd38d23a` |
| `off_orig3.json` / `off_new3.json` | `a6abc55d…7005` / `c32a72b3…2ff2d` |

## §4 Unchanged and limits

- Unchanged: off behavior and exports, the display-only scope, behavior simulation disabled
  while on, default 0.20, D-05, raw predictions, pinned manifests, the D1/S1 still-image modes,
  `07_demo.py`, `views.py`.
- UNKNOWN: a real non-10-fps clip has not been run in the browser; the 30-fps case is covered
  by a synthetic clip in the tests.
