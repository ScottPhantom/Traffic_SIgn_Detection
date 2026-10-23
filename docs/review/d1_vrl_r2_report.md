# D1-VRL-R2 — derived validation labels (hand-drawn successor of D1-VRL-R1)

Status: `D1_VRL_R2_AWAITING_INDEPENDENT_QA`
Boundary: `DERIVED_VALIDATION_LABELS_NOT_YET_EVALUATION_AUTHORITY_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

Built from the owner re-decision in `docs/review/d1_vrl_r1_correction_r1.md` after the D1-VRL-R1 QA FAIL (H1). Raw, WP38-R1
R4, train and test labels are unchanged; the R4 validation labels are pinned by content
(`labels_sha256` `e64345bb…`). Derived labels: `data/processed/m1_yolo_val_vrl_r2/labels/val/` (git-ignored) and
ignore regions `data/processed/m1_yolo_val_vrl_r2/ignore_regions.json`, all hashed in the manifest. These labels are **not yet the
evaluation authority**.

## Boxes

- Added ground truth: **64** — HAND_DRAWN: 38, REFINED: 23, REFINED_ADJUSTED: 3.
  Keys: 2: 2, 3: 1, 10: 27, 12: 8, 14: 2, 23: 12, 39: 7, 41: 5; ids are YOLO ids through `docs/review/generated/m1_yolo_classes.csv`.
- `HAND_DRAWN` boxes were drawn by eye on zoomed tick-grid crops that did not show the model box;
  each edge was snapped to the strongest luminance step only if that step lay within 1 px of the
  eye estimate (the dark 1823/1824 discs were not snapped). Eye estimates are kept in the notes.
- IoU of the added boxes with the model box: min 0.64, median 0.86, max 0.96.
- **Geometry is guaranteed by the visual check, not by the colour fit** (QA L2): on existing human
  boxes the colour fit agrees only loosely. A re-evaluation must keep the IoU-0.5 matching rule.
- Ignore regions: **40**, exactly the proposals whose locator is ≤ 17.5 px on the longer
  side (the builder refuses any other); locator expanded by 25% per side; an unmatched
  prediction with ≥ 50% of its area inside is not a false positive.

## Diagnostic at conf 0.2 (re-scoring the D1-EA-R1 exported predictions)

| Labels | GT | FP before ignore | FP in ignore regions | FP | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| R10 (WP38-R1 R4) | 560 | 214 | — | 214 | 0.569 | 0.8625 | 0.6930 |
| D1-VRL-R2 | 624 | 150 | 40 | 110 | 0.293 | 0.8766 | 0.8326 |

- **Independent of the model geometry:** 150 FP (0.399 per image),
  using only the 64 pixel-fitted or hand-drawn boxes.
- **Circular by construction:** the further 40 FP are predictions inside
  ignore regions built from those same predictions' boxes; that drop restates the owner's ignore decision
  and is no evidence that the model is right on the small discs.

This is a diagnostic, not an evaluation: only predictions with confidence ≥ 0.2 are used, so it
cannot select a threshold or compute mAP, and it changes no gate. The critical classes 7, 32 and 41 are
untouched. A D-05 decision needs a QA-passed evaluator run on the derived labels.

## Limits

- Only signs the model detected were audited (D1-VLA-R1); unlabelled signs it missed remain.
- The 40 small pole discs are removed from both recall and FP on their frames.
- The 1823/1824 discs are drawn on a dark, partly occluded scene; their edges carry about ±2 px.
- Review pages: `docs/review/assets/d1_vrl_r2/` (git-ignored; frames 1823–1837 shown brightened 3.5×).
