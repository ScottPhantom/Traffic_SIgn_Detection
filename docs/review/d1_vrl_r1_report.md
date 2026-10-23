# D1-VRL-R1 — derived validation labels with ignore regions

Status: `D1_VRL_R1_AWAITING_INDEPENDENT_QA`
Boundary: `DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

Built from the owner scope `docs/review/d1_vrl_r1_owner_scope_record.md` on the 104 D1-VLA-R1 proposals. Raw, WP38-R1 R4, train and
test labels are unchanged. The derived validation labels are written to `data/processed/m1_yolo_val_vrl_r1/labels/val/`
(git-ignored) and ignore regions to `data/processed/m1_yolo_val_vrl_r1/ignore_regions.json`; every file is hashed in the manifest. These
labels are **not yet the evaluation authority**: that needs independent QA of this package, an
owner acceptance record and a QA-passed re-evaluation contract.

## Boxes

- Added ground truth: **26** re-fitted boxes (key 2: 2, key 3: 1, key 10: 13, key 12: 8, key 14: 2).
  Each is re-fitted from the sign's red/blue pixels (HSV saturation > 0.15) around the
  model's locator box and visually checked. IoU with the model box: min 0.66, median
  0.87, max 0.96 — the re-evaluation does not match the model
  against its own boxes (D1-VLA-R1 QA M1).
- Ignore regions: **78** (small low-saturation sign: 72, partial re-fit: 6). Locator box
  expanded by 25% per side; an unmatched prediction with ≥ 50% of its area
  inside a region is not a false positive. No ground truth is added for them.
- Ids are YOLO ids mapped from derived keys through `docs/review/generated/m1_yolo_classes.csv`.

## Diagnostic at conf 0.2 (re-scoring the D1-EA-R1 exported predictions)

| Labels | GT | FP | FP in ignore regions | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (WP38-R1 R4) | 560 | 214 | — | 0.569 | 0.8625 | 0.6930 |
| D1-VRL-R1 | 586 | 110 | 78 | 0.293 | 0.8686 | 0.8223 |

This is a diagnostic, not an evaluation: it uses only predictions with confidence ≥ 0.2, so it
cannot select a threshold or compute mAP, and it changes no gate. The critical classes 7, 32 and 41
are untouched. A D-05 decision needs a QA-passed evaluator run on the derived labels.

## Limits

- **The ignore-region FP drop is circular by construction.** Each region is the model's own locator
  box expanded by 25%, so the 78 ignored false
  positives are those same predictions. The drop from 188 to
  110 FP restates the owner's ignore decision; it is not evidence that the model
  is right on those discs. Only the 26 re-fitted boxes are independent of the model geometry.
- Only signs the model detected were audited (D1-VLA-R1); unlabelled signs it missed remain.
- Ignore regions remove the small pole discs from both recall and false positives; per-class recall
  for classes 10/23/39/41 on those frames is therefore not measured.
- Review pages: `docs/review/assets/d1_vrl_r1/` (git-ignored).
