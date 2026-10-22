# D1-VLA-R1 — correction R1 after independent QA

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: `CORRECTION_APPENDED_AFTER_INDEPENDENT_QA_PASS`
Author: the D1-VLA-R1 author session (Claude Code)
Boundary: `VALIDATION_LABEL_AUDIT_PROPOSAL_ONLY_NO_RELABEL_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

This append-only record corrects `docs/review/d1_vla_r1_implementation_record.md`
(SHA-256 `08b3de3e…`) and the report following the independent QA
`docs/review/d1_vla_r1_independent_qa_record.md` (SHA-256 `5e856b77…`).

- **Verdict:** PASS, 0 Critical, 0 High, 1 Medium, 6 Low. The QA found 0 disagreements with any
  proposed box or class.
- **Unchanged:** the package, its code and its artifacts.
- **Anchors (QA L1):** the module `3826fa57…` and the manifest `3fbbe7fd…`.
- **Superseded:** where the implementation record and this file disagree, this file wins.

## M1: the what-if is an upper bound, not a conditional pass

The implementation record said FP/image "would then fall below the 0.30 D-05 gate". The report
said recall rises because the added labels are ground truth "that the model must also match".
Both statements are wrong. Every proposed box is the model's own box, so it matches its own
prediction at IoU 1.0 by construction. The added boxes therefore inflate recall and deflate
FP/image artificially.

Corrected statement:

- **0.293 is an upper bound** on the improvement from completing the labels. It is not an expected
  value.
- The recall gain of 0.8625 → 0.884 is an artifact of the method and carries no evidence.
- The margin is thin. 110 FP against the ≤ 112 FP allowed is a 2 FP margin. 28 of the 104
  proposals are ≤ 15 px and 52 are ≤ 20 px.

  The QA's sensitivity check shifts every proposed box diagonally by a uniform offset:

  | Setting | FP | FP/image |
  | --- | ---: | ---: |
  | 2 px offset | 111 | 0.295 |
  | 3 px offset | 149 | 0.396 |
  | HIGH-confidence proposals only | — | 0.519 |

**What can be concluded:** label incompleteness is a substantial part of the R10 false positives,
and a validation relabel is worth doing.

**What cannot be concluded:** that the model meets the FP/image gate. That requires all of:

1. an owner-approved derived validation relabel;
2. boxes redrawn independently of the model;
3. independent QA of that relabel;
4. re-evaluation under a QA-passed evaluator.

## Low findings recorded for the relabel worklist

- **L2.** `d1_vla_r1_proposed_val_labels.csv` stores **derived keys**, not YOLO ids. Keys 23, 39
  and 41 map to YOLO ids 25, 40 and 42, which affects 45 of the 104 rows. Any relabel must map
  through `docs/review/generated/m1_yolo_classes.csv`.
- **L3.** The "3.5t" disc at 1328/1332 is the P.106b form ("> 3.5t" truck). However, the existing
  ground truth already labels the same disc class 14 on 1329 and 1331, so class 14 follows the
  dataset convention. The P.106a/P.106b question goes to the Track A taxonomy audit.
- **L4.** Accepted:
  - V069 (1321) should be `NOT_A_SIGN` (a hotline/information board).
  - V076 (1330) is the occluded R.415a board of 1329/1331, a real in-taxonomy sign whose box is a
    sub-panel.

  Neither changes any number.
- **L5.** The MEDIUM pole proposals (1208–1229 and 1342–1357) rest on layout and neighbour-frame
  consistency. Keep them MEDIUM and redraw and re-verify them during the relabel.
- **L1, L6.** These are recorded for a successor: an external hash anchor, end-to-end tamper
  tests, and the dependency on Pillow 13.0.0.

## Next state

- Allowed, with an owner decision and its own QA: a derived validation relabel package in the
  WP33/WP34 style (redrawn boxes, YOLO-id mapping, append-only).
- Still NO-GO: using the what-if to pass any gate, training, smoke runs, new seeds, using
  validation pixels for training, and the sealed test.
