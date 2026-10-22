# D1-VLA-R1 — validation label-completeness audit — implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: **IMPLEMENTED AND BUILT — AWAITING INDEPENDENT QA**
Author: Claude Code session (the D1-EA-R1 author)
Boundary: `VALIDATION_LABEL_AUDIT_PROPOSAL_ONLY_NO_RELABEL_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

This is step 3, item 1 of the plan agreed with the owner on 2026-10-22. It is authorized by the
D1-EA-R1 QA "Bounded next state" ("Validation label-completeness audit … YES — stratified per L3;
separate QA").

No model was loaded and no inference was run. The package reads only the QA-passed D1-EA-R1
export, the validation labels and images, and the pinned review notes.

This record does not authorize a validation relabel, a gate change, a smoke run, training or
sealed-test access.

## Source

| File | SHA-256 |
| --- | --- |
| `detector/m1/val_label_audit_r1.py` | `3826fa57a7cb8d7611c941ce590d7b9f785f4fc23e562842f9aa39c7a99838cf` |
| `detector/tests/test_val_label_audit_r1.py` | `c6683f44c481de9b69f8f9afbf55402761f95a0c91e12288eb656123409116d7` |
| `docs/review/d1_vla_r1_review_notes.csv` (trusted, pinned) | `7fd81195e50992dcf45c0b4fc22499f3a0104a26a8d46e305a1153a4e8d26cec` |

**Pinned inputs:**

- the D1-EA-R1 prediction CSV, `cb3cb05f…`;
- the D1-EA-R1 manifest `d87f090e…`, the anchor named by D1-EA-R1 QA L1;
- the D1-EA-R1 builder `6268c3fe…`;
- the D1-EA-R1 QA record `273c6356…`;
- the D1-EA-R1 hypothesis correction R1 `f0c63f99…`.

**Outputs:**

| File | Contents |
| --- | --- |
| `docs/review/generated/d1_vla_r1_background_fp_strata.csv` | 214 rows |
| `docs/review/generated/d1_vla_r1_decisions.csv` | 138 rows |
| `docs/review/generated/d1_vla_r1_proposed_val_labels.csv` | 104 rows |
| `docs/review/generated/d1_vla_r1_manifest.json` | `3fbbe7fd2b2bc44f632f676cfa60861f963a1cf31b193119c49049e9ed9c2e46` |
| `docs/review/d1_vla_r1_report.md` | report |
| `docs/review/assets/d1_vla_r1/review_page_01…12.jpg` | git-ignored |

## Method

1. **Stratify all 214 background false positives** by their geometry against the labelled boxes:
   - 66 overlap a labelled box at IoU ≥ 0.5: H1 duplicates;
   - 10 lie inside a labelled box: H3 sub-panels;
   - 138 have best IoU < 0.1 with every ground-truth box (`NO_LABEL_NEARBY_IOU_LT_0_1`).

   This is the QA-defined "138" (L3). Only these 138 can be missing labels.
2. **Visual review of all 138.** I rendered context crops at six times the box size (the same
   renderer now produces the package atlas). For dark frames I also checked a crop brightened 3.5×,
   for example 1830.

   Each candidate got exactly one decision, pinned in the notes CSV:

   | Decision | Meaning |
   | --- | --- |
   | `UNLABELLED_IN_TAXONOMY` | proposed derived class plus HIGH, MEDIUM or LOW confidence |
   | `OUT_OF_TAXONOMY_UNLABELLED` | a real board outside the 54 classes, not labelled |
   | `OUT_OF_TAXONOMY_LABELLED_UNKNOWN` | already a WP33 UNKNOWN box (IoU ≥ 0.64, computed with the WP38 rotation for corrected frames) |
   | `NOT_A_SIGN` | not a traffic sign |
   | `UNCLEAR` | cannot be decided from the frame |
3. **Duplicates.** A lower-scored in-taxonomy candidate with IoU ≥ 0.5 to a higher-scored one in
   the same frame is marked `duplicate_of`; it is the same physical sign.
4. **Proposals.** The unique in-taxonomy candidates with HIGH or MEDIUM class confidence are
   written as YOLO-normalized proposed validation boxes. These are the model's boxes, so a real
   relabel must redraw them.
5. **What-if.** The R10 operating point (conf 0.20) is recomputed with the proposed boxes added as
   ground truth. This is a diagnostic only.

## Result

| Decision | Count |
| --- | ---: |
| `UNLABELLED_IN_TAXONOMY` | 116 (112 unique after merging 4 same-sign duplicates) |
| `OUT_OF_TAXONOMY_UNLABELLED` | 9 (camera-surveillance boards 1215–1220, guide boards 0327/0329, phone board 1321) |
| `NOT_A_SIGN` | 7 (cafe logo, shop signs, bus, back of a sign) |
| `OUT_OF_TAXONOMY_LABELLED_UNKNOWN` | 4 (camera boards 1324–1328) |
| `UNCLEAR` | 2 (0839, 1330) |

The main sources of the unlabelled in-taxonomy signs are:

- **The 1208–1229 sign pole.** It carries 40 and 60 P.127 discs, a P.130 disc and a P.111a+P.111b
  disc. The ground truth in these frames labels only class 26. The model's speed values are partly
  wrong (it predicts 80 km/h for the 40 disc).
- **The same pole type on the corrected portrait frames 1342–1357.**
- **A P.130 sign in deep shadow, 1823–1837.** This resolves the QA's "unresolved shadow run": the
  blue disc with a red X is visible when brightened.
- **The P.102 + R.302a pair at 1820/1821**, and R.415a boards at 1208–1213 and 1329–1331.

**What-if at conf 0.20 (diagnostic, not a result):**

| Ground truth | Added boxes | FP | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| R10 labels | 0 | 214 | 0.569 | 0.8625 | 0.693 |
| + HIGH/MEDIUM proposals | 104 | 110 | **0.293** | 0.884 | 0.842 |
| + all, including LOW | 112 | 102 | 0.271 | 0.885 | 0.854 |

If the proposals are confirmed, about half of the R10 false positives are label incompleteness
rather than model error. FP/image would then fall below the 0.30 D-05 gate at the same operating
point.

This must not be used to pass any gate. It needs:

1. an owner decision on a derived validation relabel, in the WP33/WP34 style with redrawn boxes;
2. independent QA of that relabel;
3. re-evaluation under a QA-passed evaluator.

The critical classes 7, 32 and 41 are untouched by this audit, and their recall gates still fail.

## Local verification

- `ruff check` and `ruff format` are clean.
- `tests/test_val_label_audit_r1.py` (6 tests) and `tests/test_error_analysis_r1.py` (10 tests):
  16 passed.
- `uv run python -m m1.val_label_audit_r1 verify` returns `valid=true`. A repeated `build` refuses
  because the outputs already exist.
- `uv run python -m m1.error_analysis_r1 verify` still returns `valid=true`.

## Limits

- Only signs the model detected are audited. Unlabelled signs that the model also missed are not
  found here.
- MEDIUM classes on the two poles are read partly by consistency with sharper frames of the same
  pole.
- The "3.5t" truck disc (1328/1332) is proposed as class 14 (P.106a), but its exact QCVN variant
  must be confirmed.
- The 10 LOW warning triangles (1352–1357) are excluded from the proposals.
