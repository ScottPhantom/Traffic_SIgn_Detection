# D1-VRL-R3 — derived validation labels, successor of D1-VRL-R2 — implementation record

Date: 2026-10-23 (`Asia/Ho_Chi_Minh`)
Status: **IMPLEMENTED AND BUILT — AWAITING INDEPENDENT QA**
Author: Claude Code session (the D1-VRL-R1/R2 author)
Boundary: `DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

D1-VRL-R3 supersedes D1-VRL-R2, whose QA passed with one Medium finding (M1). It is authorized by
the owner decision `docs/review/d1_vrl_r2_owner_decision_r3.md`. No model was loaded and no
inference was run.

## Source

| File | SHA-256 |
| --- | --- |
| `detector/m1/val_relabel_r3.py` | `34b89e320775abb8bf6186558ce03666c221331969c978836b01342e2e0d72ec` |
| `detector/tests/test_val_relabel_r3.py` | `8467d181b3317fc9ff71b0ef19d7ac21fdd2d73f05ea377a1105849ded5766d7` |
| `docs/review/d1_vrl_r3_box_review_notes.csv` (trusted, pinned) | `b653abb393fa278a4737cf3e08160e1c312d5b1b11d96cba029da8f3e4f4a385` |
| `docs/review/d1_vrl_r2_owner_decision_r3.md` (pinned) | `34ad3fd303e0bd935352405506ce9d6af505be445d9520d70f458b2fd4e267f8` |

Also pinned:
- every D1-VRL-R2 pin;
- the D1-VRL-R2 module `2d707625…`, manifest `e23b725f…` and QA record `07584056…`.

**Outputs:**

| File | Contents |
| --- | --- |
| `docs/review/generated/d1_vrl_r3_added_boxes.csv` | 64 rows, `e6d19d490e308cc301c03b68c14a12216951e2ec3a788a8118ee17ff3be4a59e` |
| `docs/review/generated/d1_vrl_r3_ignore_regions.csv` | 40 rows, `ec102253…` (byte-identical to R2) |
| `docs/review/generated/d1_vrl_r3_manifest.json` | `87dd0fd9ecea85745f613a788ef70ae830d396fc9e747f233db0c6fc536b8e07` |
| `docs/review/d1_vrl_r3_report.md` | report |
| `data/processed/m1_yolo_val_vrl_r3/labels/val/*.txt` | 376 files, roster hash `dc72ebd944a38535d4f766ba4f8babc60cb6732dfcd253ed0e8d79dc86eb8343` (git-ignored) |
| `data/processed/m1_yolo_val_vrl_r3/ignore_regions.json` | 40 regions (git-ignored) |
| `docs/review/assets/d1_vrl_r3/added_page_01…04.jpg` | git-ignored |

## What changed from D1-VRL-R2

| Item | Change |
| --- | --- |
| **M1, R039** (1223, "60") | Left edge 0 → **6**. Row profiles at y = 54/57/60 change from the sky (about 240) to the rim at x = 6. IoU with the model box is 0.778. |
| **L1, R046** (1229, "60") | Bottom edge 23 → **28**. Column profiles at x = 128/135/142 turn bright at y = 27/28/28. The box is drawn through the bracket, like R045. IoU with the model box is 0.863. |
| **L3** | `check_notes` refuses a `HAND_DRAWN` row without integer eye columns. It also refuses a final box more than 1 px from its eye estimate on any side, or more than 0 px on the unsnapped dark frames 1823–1837. For R039 and R046 the eye columns record the R3 re-draw itself, and the notes say so. |
| **Author-found defect** | In the R2 notes, row R097 had an unquoted comma: 15 fields, with its note truncated and the box unaffected. R3 rewrites the notes with correct quoting, and `check_notes` refuses any row with a wrong field count. |
| Unchanged | L2: R090/R091 bottoms about 3 px short, recorded as a limit in the report. L4: the QA pins remain the external anchor. All other 62 added boxes and all 40 ignore regions are identical to R2. |

## Result

- Added ground truth: 64 boxes (38 hand-drawn, 23 re-fitted, 3 re-fitted and tightened).
- Ignore regions: 40.
- Derived labels: R4 plus exactly 64 lines. Versus R2, only the lines for 1223 (R039) and 1229
  (R046) differ.
- Diagnostic at conf 0.20, unchanged from R2:

  | Stage | FP | FP/image | Basis |
  | --- | ---: | ---: | --- |
  | R10 baseline | 214 | — | — |
  | After the added boxes | **150** | 0.399 | independent of the model geometry |
  | After the ignore regions | **110** | 0.293 | circular by construction |

  - Recall is 0.8766.
  - The corrected R039 and R046 boxes are still matched, as the R2 QA predicted.

**Not a gate result.** The independent FP/image, 0.399, is above the 0.30 gate. The critical
classes 7, 32 and 41 are untouched.

## Local verification

- `ruff check` and `ruff format` are clean.
- `test_val_relabel_r3.py`, `_r2.py` and `_r1.py`: 15 passed.
- `uv run python -m m1.val_relabel_r3 verify` returns `valid=true`, and a second `build` refuses.
  The R1 and R2 verifiers are still valid.
- `detector/`: `uv run pytest` 230 passed; `uv lock --check` OK. Root: `ruff check src tests` clean; `uv lock --check` OK. `graft build . && graft check .`: OK.
- The root test suite was not re-run, because no file outside `detector/` and `docs/` changed. The
  last root run, for D1-VRL-R2, ended with exit 0.
