# D1-VRL-R1 — derived validation labels with ignore regions — implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: **IMPLEMENTED AND BUILT — AWAITING INDEPENDENT QA**
Author: Claude Code session (the D1-EA-R1 / D1-VLA-R1 author)
Boundary: `DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

Authorized by the owner instruction "Bắt đầu relabel val" and the owner geometry decision, both in
`docs/review/d1_vrl_r1_owner_scope_record.md`. No model was loaded and no inference was run. This
record does not make the derived labels the evaluation authority and changes no gate.

## Source

| File | SHA-256 |
| --- | --- |
| `detector/m1/val_relabel_r1.py` | `9fba10089ad23fc494b2548fec60acf4d07ae34feebcc8bfb530887b0ff5eff5` |
| `detector/tests/test_val_relabel_r1.py` | `1f6393685aa636a7cb56c79761075a4a5984c5130e66e4f036b232770e30dcf6` |
| `docs/review/d1_vrl_r1_box_review_notes.csv` (trusted, pinned) | `4458474f2c75830567bc094f43d46cad885fab4245d3347ad4f9790f78736101` |
| `docs/review/d1_vrl_r1_owner_scope_record.md` (pinned) | `a96e55f464dfd98c0a08ace0db11d589429a420b3f752d02f74584a04c4a103b` |

Also pinned: the D1-VLA-R1 proposals `70773b4b…`, manifest `3fbbe7fd…`, builder `3826fa57…`, QA
record `5e856b77…` and correction R1 `be06ee89…`; the D1-EA-R1 prediction CSV `cb3cb05f…`; and
`m1_yolo_classes.csv` `7cda296a…`.

**Outputs:**

| File | Contents |
| --- | --- |
| `docs/review/generated/d1_vrl_r1_added_boxes.csv` | 26 rows, `8a88e31b022b223cd4f13d1c7e6e9e8b1d3e8666b884ef6743a90806806c047d` |
| `docs/review/generated/d1_vrl_r1_ignore_regions.csv` | 78 rows, `b2cc664a2c54cf742131e45d40c0f6a6a8928e9fc69fb9d4f9e35b8d663f522c` |
| `docs/review/generated/d1_vrl_r1_manifest.json` | `3fd91263dabc775bf8967e604a589bb20143bfc43fb45f2e16fa814e973eb34f` |
| `docs/review/d1_vrl_r1_report.md` | report |
| `data/processed/m1_yolo_val_vrl_r1/labels/val/*.txt` | 376 derived label files, roster hash `152993d027dc3ecf29a54a1ace6a05a6bbc9632b83083f00e7f442e8d3064e5a` (git-ignored) |
| `data/processed/m1_yolo_val_vrl_r1/ignore_regions.json` | 78 regions (git-ignored, hashed in the manifest) |
| `docs/review/assets/d1_vrl_r1/added_page_01…02.jpg` | git-ignored |

## Method

1. **Re-fit.** For each of the 104 proposals, the model box is only a locator. `refine_box` crops the
   locator expanded by one box size per side, builds a red/blue HSV mask (saturation > 0.15),
   labels 8-connected components with a local BFS (no scipy, so the pinned lock is unchanged) and
   keeps the component whose box has the highest IoU with the locator, if that IoU ≥ 0.3.
2. **Visual check** (done before the build, recorded in the pinned notes): 32 proposals re-fit; 26
   are `ACCEPT_REFINED`; 6 cover only part of the sign and, with the 72 that do not re-fit, are
   `IGNORE_REGION`. The builder re-runs the re-fit and refuses if an accepted proposal no longer
   re-fits.
3. **Derived labels.** The WP38-R1 R4 validation labels plus the 26 boxes, ids mapped through
   `m1_yolo_classes.csv`. Raw, R4, train and test labels are untouched.
4. **Ignore regions.** Locator box expanded by 25 % per side. Rule: an unmatched prediction with
   ≥ 50 % of its area inside a region is not a false positive.
5. **Diagnostic.** The D1-EA-R1 exported predictions at conf 0.20 re-scored with the same greedy
   class-agnostic matching as `metrics.match`.

## Result

- 26 added boxes; IoU with the model box min 0.66, median 0.87, max 0.96. All 26 are matched by the model
  at conf 0.20 (recall 0.8625 → 0.8686).
- Diagnostic: FP 214 → 188 after the added boxes → **110 after ignore regions (FP/image 0.293)**.

**This is not a gate result.** The 78 ignored FP are, by construction, the model's own predictions
whose boxes define the regions; that drop restates the owner's ignore decision. Only the 26-box part
(214 → 188, FP/image 0.500) is independent of the model geometry. The critical classes 7, 32 and 41
are untouched and their recall gates still fail.

## Local verification

- `ruff check` and `ruff format` are clean.
- `detector/`: `uv run pytest` 220 passed (5 new in `test_val_relabel_r1.py`), `uv lock --check` OK.
- Root: `ruff check src tests` clean, `run_parallel_checks.py tests --jobs 6` 1,765 passed, 2 skipped, 7 xfailed, exit 0; `uv lock --check` OK.
- `graft build . && graft check .`: OK.
- `uv run python -m m1.val_relabel_r1 verify` returns `valid=true`; a second `build` refuses.

## Limits

- Only signs the model detected were audited; unlabelled signs it missed remain.
- Ignore regions remove the small pole discs (classes 10/23/39/41) from both recall and FP on those
  frames.
- The 3-px-shift sensitivity of D1-VLA-R1 QA does not apply to the 26 re-fitted boxes in the same
  way, but it was not re-run here.
