# D1-EA-R1 — hypothesis correction R1 and owner acknowledgement

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: `CORRECTION_APPENDED_AFTER_INDEPENDENT_QA_PASS`
Author: the D1-EA-R1 author session (Claude Code)
Boundary: `VALIDATION_ONLY_DIAGNOSIS_NO_TRAINING_NO_SEALED_TEST_NO_VAL_PIXELS_IN_TRAIN`

This append-only record corrects the author's hypotheses in
`docs/review/d1_ea_r1_implementation_record.md` (SHA-256 `1b086604…`) following the independent
QA `docs/review/d1_ea_r1_independent_qa_record.md` (SHA-256 `273c6356…`):

- **Verdict:** PASS, 0 Critical, 0 High, 3 Medium, 6 Low.
- **Unchanged:** the package, its code and every artifact (manifest
  `d87f090e11d7acc547fb49eeb76935e2e0bcc743f3bc3fba56ab23a1cd8e07ab`). That manifest is the
  evidence anchor (QA L1).
- **Superseded:** where the implementation record and this file disagree, this file wins.

## M3: inference ran before implementation QA (owner acknowledgement)

The packet-R1 QA record set "Execute D1-EA-R1 validation inference: NO-GO until the exact
implementation passes independent QA". The author ran `build`, a single MPS inference over the 376
validation frames, before that QA. This was a process error by the author: the owner's choice of
MPS as the device was read as permission to run.

**Owner acknowledgement (2026-10-22, in the Claude Code session):** the owner accepts the run as
performed. The outputs are kept and the inference is not re-run.

The impact is contained:

- validation only, with `test_included=false` and `sealed_test_accessed=false`;
- no training;
- predictions that reproduce R10 exactly;
- an implementation that has since passed independent QA.

## Corrected hypotheses

**H1 (duplicates and agnostic NMS), replacing the original H1.**

66 of the 214 background false positives (30.8 %) have IoU ≥ 0.5 with an already-paired ground
truth. They break down as follows:

| Kind | Count | Examples |
| --- | ---: | --- |
| Same-class duplicates | 11 | |
| Another wrong class | 29 | |
| Correct GT class behind a higher-scoring wrong box | 25 | p46 behind p10 in 0004–0055; p7 behind p17/18 in 0314 and 0338–0341; p8 behind p12 in 0334/0335; p4 behind p5 in 1721 |

A diagnostic re-NMS of the exported boxes gives:

| Setting | FP/image | Agnostic recall | Class 46 recall |
| --- | ---: | ---: | ---: |
| Baseline | 0.569 | 0.8625 | 55/104 = 0.529 |
| Agnostic NMS, IoU 0.7 | 0.434 | 0.8625 | 42/104 = 0.404 |
| Agnostic NMS, IoU 0.5 | 0.378 | 0.8625 | 42/104 = 0.404 |

With agnostic NMS, **class 46 falls below its 0.50 gate**. Class 7 drops 0.595 → 0.559, class 41
0.571 → 0.524 and class 8 0.627 → 0.588. FP/image still stays above 0.30. Agnostic NMS alone
therefore trades one failing gate for another.

This re-NMS is also an approximation. It runs on boxes that already passed class-wise NMS at
conf ≥ 0.20, which is not Ultralytics `agnostic_nms=True` on the raw candidates.

Any post-processing contract must gate per-class recall, including class 46, and needs its own QA.

**H2 (unlabelled real signs), now defined and stratified.** The "138" are the background false
positives whose best IoU with any ground truth is below 0.1; 132 of them have IoU exactly 0. They
mix four causes:

1. in-taxonomy real but unlabelled signs: P.130, P.111a+b and P.127 40/60 in 1208–1229 and
   1342–1357, and P.102 in 1820/1821/1827/1834;
2. out-of-taxonomy real boards: camera-surveillance boards 1215–1220 and 1324–1328, and the phone
   board 1321;
3. true non-sign false positives: the cafe logo in 0024/0046/0070/0071, the bus in 0313 and the
   shop sign in 0048;
4. an unresolved shadow run, 1823–1837 (p10).

A validation label-completeness audit must separate these four causes before any FP/image is
re-estimated.

**H3 (class 12 sub-panels)** is supported as written. In addition, p30 fires on the same R.415a
boards (1231–1243).

**H4 (class 7), replacing the original H4.** The 36 class-7 misses are:

| Where | Count | Size and conditions |
| --- | ---: | --- |
| 0279–0296 | 17 | GT width 11–17 px |
| 0301 | 1 | 14 px |
| 1777–1798 | 17 | mid-size 25–46 px, dark and backlit |
| 0345 | 1 | large, 114 px |
| 1817, 1818 | 2 | large, 98 and 110 px, backlit |

Small size explains at most 18 of the 36. Lighting/backlight and possibly label semantics explain
the rest.

The 0345 sign, the same one that 0336–0346 predict as 17 (P.124a), shows a motorbike pictogram
with a left-turn arrow under the slash. Its QCVN code should be checked against the D-03 taxonomy
before these boxes are counted as model errors.

## Low findings carried to a successor (not fixed here)

- L1: verify against the pinned manifest hash.
- L2: blank `best_retained_class` when IoU = 0. All 77 misses are total non-detections.
- L5: add end-to-end `verify()` tests.
- L6: the atlas bytes depend on Pillow 13.0.0 (informational).

L4 (weights directory not git-ignored) is fixed alongside this record by adding
`results/experiments/**/weights/` to `.gitignore`.

## Next state (unchanged from the QA "Bounded next state")

- Allowed, each with its own contract and QA:
  - a validation label-completeness audit, stratified as in H2;
  - a post-processing contract with per-class gates.
- Training, smoke, new seeds, using validation pixels or predictions for training, and the sealed
  test all remain **NO-GO**.
