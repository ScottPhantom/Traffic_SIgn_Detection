# D1 NMS IoU 0.45 vs 0.70 — paired validation test R1, report

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.

**Decision under the frozen contract: `NOT_SUPPORTED`.** Only condition c1 failed: the FP/image CI does
not lie wholly below 0.

**Scope:**
- validation R3, one pilot checkpoint, in-sample and post hoc (contract §2);
- no inference, training, threshold lock or app change;
- `sealed_test_accessed=false`.

| File | SHA-256 |
| --- | --- |
| Contract `d1_nms_045_paired_test_r1_contract.md` | `fe80ce78ac2523d9f98245336e7bbb98699d0876d7312dc1437b10f3c5a463ff` |
| Script `detector/m1/nms_045_paired_test_r1.py` | `056e21b5f22213351fadfd361cd4ee67fddf4d607ec92bea212941044a0c2c76` |
| Tests `detector/tests/test_nms_045_paired_test_r1.py` (16 passed) | `fed9702a1489d075ce177d6759e1dfadcf6d4623bc2b816049e4fb23f1d5f979` |
| Result `generated/d1_nms_045_paired_test_r1.json` | `5a499b2d030344201a1f923bb15e9ba2b00760a68a7f5a557f8b48e6c43a22ee` |
| Independent QA `d1_nms_045_paired_test_r1_independent_qa_record.md` — PASS giới hạn; every number recomputed from the CSVs | `08e9c47f12457ffb6de02274ca4deffaa5a340c0bd3ebeb6e782480fb6e89684` |

## Results at confidence 0.20 (paired group bootstrap, 1,000 rounds, seed 20261018)

| Metric | IoU 0.45 | IoU 0.70 | Difference | CI95 |
| --- | ---: | ---: | ---: | --- |
| FP per image | 0.3590 (135) | 0.3989 (150) | −0.0399 | [−0.1042, 0.0] |
| Correct-class recall | 0.7324 | 0.7324 | 0 | [0, 0] |
| Class-agnostic recall | 0.8766 | 0.8766 | 0 | [0, 0] |
| Exact-class mAP50 | 0.8543 | 0.8521 | +0.0022 | [+0.0001, +0.0046] |
| Exact-class mAP50-95 | 0.6095 | 0.6089 | +0.0006 | [−0.0007, +0.0017] |

**Conditions:**

| Condition | Result |
| --- | --- |
| c1: FP CI upper bound < 0 | **Failed** (upper bound 0.0) |
| c2: no group loses correct-class hits | Passed |
| c3: agnostic recall ≥ 0.85 and not lower | Passed |
| c4: mAP50-95 CI not wholly below 0 | Passed |
| c5: leave-one-group-out picks 0.45 in ≥ 7/9 folds | Passed (9/9, on lower FP alone) |
| c6: no group gains FP | Passed |
| c7: no paired GT lost | **Passed vacuously**; see below |

## Why the FP interval reaches 0 (QA F4)

- All 15 removed false positives are in **two of nine groups**: D02-C0031 (41 → 33) and D02-C0034
  (60 → 53).
- The other seven groups are identical on FP, correct-class hits and agnostic hits.
- A bootstrap round that draws neither of those two groups has a difference of exactly 0. That
  happened in 106 of 1,000 rounds, close to the expected (7/9)^9 ≈ 0.104. With more than 2.5 % of
  rounds at 0, the 97.5th percentile is 0.

So the signal is consistent (no group gets worse) but concentrated. It is too narrow to establish
with nine groups.

## Box audit (QA F1)

At confidence ≥ 0.20, IoU 0.45 removes 18 boxes and adds 3, and no ground-truth match changes. The
independent QA classified every box; its record lists each one:
- all 18 removed boxes were false positives at 0.70;
- all 3 added boxes are false positives at 0.45.

**Why a lower NMS IoU can add a box:** greedy NMS has a chain effect. In frame 1357, box A (score
0.788) overlaps B (0.729) at IoU 0.56, and B overlaps C (0.700) at 0.805.
- At 0.70, B survives A and then suppresses C.
- At 0.45, A removes B, and C (IoU 0.449 with A) is no longer suppressed by anything.

Frames 1352 and 1240 show the same pattern.

## Stacked-sign risk is untested, not passed (QA F2)

Condition c7 asked whether real neighbouring signs, such as a main sign with a supplementary plate,
lose a detection at the lower IoU. **Validation has no pair of ground-truth boxes overlapping at
IoU ≥ 0.45.** The largest overlap between two GT boxes is 0.033. The condition therefore passed only
because nothing could be tested. A lower NMS IoU suppresses overlapping boxes more aggressively, so
this risk remains open for data with stacked signs.

## Disposition

- Keep per-class NMS IoU **0.70**. No app, Dynamic Threshold, D-05 or lock change.
- 0.45 stays a recorded exploratory signal: fewer FP with no measured loss on validation. It is
  **not** a lock candidate.
- **Re-check is pre-registered:** run the same contract on the seed 20261019 model once that model
  has a QA-passed result. It would need its own inference authorization. Two consistent seeds still
  would not test stacked signs.
- **QA F3:** the leave-one-group-out recall is class-agnostic recall, as in the D-05 rule. Reading it
  as correct-class recall would not change the decision.

## Claim classification

- **Verified artifact:** every number above, recomputed independently from the two CSVs.
- **Verified current behavior:** 16 tests passed; ruff clean.
- **Proposal:** the seed 20261019 re-check.
- **Unknown:** behaviour on stacked signs, on other seeds and on the sealed test.
