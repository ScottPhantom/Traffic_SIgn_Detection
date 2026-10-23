# D1-VRL-R2 — derived validation labels, hand-drawn successor — implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: **IMPLEMENTED AND BUILT — AWAITING INDEPENDENT QA**
Author: Claude Code session (the D1-VRL-R1 author)
Boundary: `DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

D1-VRL-R2 supersedes D1-VRL-R1, which failed independent QA on H1. It is authorized by the owner
re-decision recorded in `docs/review/d1_vrl_r1_correction_r1.md`. No model was loaded and no
inference was run. This record does not make the derived labels the evaluation authority and
changes no gate.

## Source

| File | SHA-256 |
| --- | --- |
| `detector/m1/val_relabel_r2.py` | `2d70762550dd6e7752e122b31c3628256a8eafebf3ca14f7be6facfc5ca12710` |
| `detector/tests/test_val_relabel_r2.py` | `a6cc320adc24e9d15a0f408352608ad85c1ad8919c38528aa3ba9ecd790a1baa` |
| `docs/review/d1_vrl_r2_box_review_notes.csv` (trusted, pinned) | `a9c05fa8ad578de0eaa819e123e5a89c055576d2c28853cf529708d5407eda2e` |
| `docs/review/d1_vrl_r1_correction_r1.md` (H1 correction and owner re-decision, pinned) | `d3376ec32b13ea33ec94a43b124d6738d541ab2c1b35a465fa07361ce4b318d0` |

**Also pinned:**

- every D1-VRL-R1 pin;
- the D1-VRL-R1 module `9fba1008…`, manifest `3fd91263…` and QA record `e168b6bf…`;
- the WP38-R1 R4 manifest `6982a76f…`;
- the R4 validation labels by content, `labels_sha256` `e64345bb…` (QA L4).

**Outputs:**

| File | Contents |
| --- | --- |
| `docs/review/generated/d1_vrl_r2_added_boxes.csv` | 64 rows, `f8d364bdab9b578c297029076b851808ad9986d0ae95def3e87664b4e5922688` |
| `docs/review/generated/d1_vrl_r2_ignore_regions.csv` | 40 rows, `ec102253b3b049186a966254b2ad54fe6cdefb7251e486632f30b82cf4c2bf4e` |
| `docs/review/generated/d1_vrl_r2_manifest.json` | `e23b725f711ae6f9a15f8db4d00e13ec8048a392f8db10296972113573c008ff` |
| `docs/review/d1_vrl_r2_report.md` | report |
| `data/processed/m1_yolo_val_vrl_r2/labels/val/*.txt` | 376 files, roster hash `f772bae26ac93ac0fa594177cf00afb65dd1ceb6f5fd31793808f04bf39b9373` (git-ignored) |
| `data/processed/m1_yolo_val_vrl_r2/ignore_regions.json` | 40 regions (git-ignored) |
| `docs/review/assets/d1_vrl_r2/added_page_01…04.jpg` | git-ignored; frames 1823–1837 brightened 3.5× |

## What changed from D1-VRL-R1

| QA item | Resolution |
| --- | --- |
| **H1** | Every proposal is re-classified by measured locator size. The 38 proposals > 17.5 px without an accepted re-fit (32 of the old 72 plus the 6 partial re-fits) are **hand-drawn**. The 40 proposals ≤ 17.5 px stay ignore regions, each with its measured size as the reason. The builder enforces the rule: `IGNORE_REGION` only ≤ 17.5 px, `HAND_DRAWN` only > 17.5 px. |
| **L1** | R095 right 348 → 345, R097 right 335 → 331, R103 bottom 489 → 485 (`ACCEPT_REFINED_ADJUSTED`; the builder only allows tightening the re-fit, by at most 6 px). R092 is kept at 360: its red-ring column profile peaks at 356–357 and ends at 359. This disagreement with L1 is recorded in the notes. |
| **L2** | The report states that geometry is guaranteed by the visual check, not the colour fit, and that a re-evaluation must keep IoU 0.5. |
| **L3** | `verify` rejects any file, symlink or empty directory anywhere under `data/processed/m1_yolo_val_vrl_r2/` or the atlas directory that is not an artifact (`stray_paths`). |
| **L4** | The R4 validation labels are pinned by content. The mapping test now sees real rows: keys 23/39/41 → YOLO 25/40/42. |
| **L5** | Not addressed by code. The pins in the QA record remain the external anchor. |

## Hand-drawing method (38 boxes)

1. **Crops.** Zoomed crops with absolute pixel ticks. The crop window was centred on the locator,
   but the model box was **not** drawn, and the eye estimate was read off the tick grid. Dark
   frames 1823/1824 were read on a 3.5× brightened crop.
2. **Snap.** Each edge was snapped to the strongest luminance step along the central half of the
   sign, kept only if that step lay within 1 px of the eye estimate; otherwise the eye estimate was
   kept. 1823/1824 were not snapped. Both the eye estimate and the final box are in the notes.
3. **Check.** Every final box was overlaid on its crop and checked by eye.

**IoU of the hand-drawn boxes with the model box:** min 0.64, median 0.81, max 0.96.

## Result

- Added ground truth: 64 boxes:
  - 23 re-fitted;
  - 3 re-fitted and tightened;
  - 38 hand-drawn.
- Ignore regions: 40.
- Derived labels: R4 plus exactly 64 lines (560 → 624 boxes).
- Diagnostic at conf 0.20:
  - FP 214 → **150** after the added boxes. This step is independent of the model geometry:
    FP/image 0.399.
  - FP 150 → **110** after the ignore regions. This step is circular by construction: FP/image
    0.293.
  - Agnostic recall 0.8625 → 0.8766.

  All 64 added boxes are matched by a prediction at IoU ≥ 0.5.

**Not a gate result.** The independent FP/image, 0.399, is still above the 0.30 gate. The critical
classes 7, 32 and 41 are untouched.

## Local verification

- `ruff check` and `ruff format` are clean.
- `tests/test_val_relabel_r2.py` and `test_val_relabel_r1.py`: 10 passed.
- `uv run python -m m1.val_relabel_r2 verify` returns `valid=true`. A second `build` refuses.
  `m1.val_relabel_r1 verify` is still valid.
- `detector/`: `uv run pytest` 225 passed; `uv lock --check` OK.
- Root: `ruff check src tests` clean; `uv lock --check` OK; `run_parallel_checks.py tests --jobs 6` exit 0.
- `graft build . && graft check .`: OK.

## Limits

- Only signs the model detected were audited.
- The 1823/1824 discs are dark and partly occluded, so their edges carry about ±2 px.
- The hand boxes are the author's. Independent QA should re-draw a sample.
