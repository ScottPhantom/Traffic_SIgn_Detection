# D1-A2-R1 common validation report R1 — A2 versus the YOLO11s-54 pilot

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.

**Scope:**
- Single-seed **validation** description: R3 roster, 376 frames, 624 boxes, 9 D-02 groups.
- Not compute-matched: A2 takes about 26 % more optimizer steps than the pilot.
- No D-05 change, no threshold selected or locked. `sealed_test_accessed=false`.

## 1. Evidence chain

| Step | Record | Verdict |
| --- | --- | --- |
| Run integrity: archive, checkpoint, two L4 runtimes, logs, attestation | `d1_a2_r1_result_independent_qa_record.md` (`4d810f27…a66b`) | PASS |
| Evaluator source | `d1_a2_r1_evaluator_source_independent_qa_record.md` (`1ec37fc3…84be5`) plus implementation addendum 1 | PASS giới hạn. Conditions met: `PYTHONPATH=.`, standard two-attempt package. |
| Comparison result, recomputed independently | `d1_a2_r1_common_validation_result_independent_qa_record.md` (`d2917378…66e6`) | PASS |

**Inputs:**
- archive `ea7dba03…a609`
- manifest `7a4e1856…d343`
- `best.pt` `9781f7d8…0b0b` (training best epoch 36)
- authorization `1a11b283…21c9`
- checkout `f3f7571…`
- corrected train/val bundle manifest `8e6ffe77…`

**Outputs:**
- `results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1/a2_predictions.csv` (`c45dcf1d…d7f1`)
- `comparison_a2_r1.json` (`d7872b87…641b`)
- `docs/review/generated/d1_a2_pilot_paired_ci_r1.json` (`2687a30e…aa04`), where `verify` reports PASS

**Bundle path (QA L1).** The evaluator was run with `--bundle ../tmp/yolo11n_n1_extract_r2`. The older
extraction `tmp/yolo11n_n1_extract_r1` was refused by the reused bundle verifier, because it now contains
an extra `detector/.venv` with symlinks and a `.pyc` file.
- `_r2` has the byte-identical manifest `8e6ffe77…`; all 8,579 members match and none is a link.
- No number depends on which copy was used.
- `_r1` was left untouched (QA L2). Cleaning it needs Owner approval.

## 2. Results at confidence 0.20 (paired group bootstrap, 1,000 rounds, seed 20261018)

| Metric | Pilot | A2 | A2 − pilot | Paired 95 % CI |
| --- | ---: | ---: | ---: | --- |
| Class-agnostic recall | 0.8766 (547/624) | 0.7612 (475/624) | −0.1154 | [−0.2413, +0.00004] |
| FP per image | 0.3989 | 0.2447 | −0.1543 | [−0.3882, 0.0] |
| Correct-class recall | 0.7324 | 0.6506 | −0.0817 | [−0.2153, +0.1302] |
| Exact-class mAP50 | 0.8521 | 0.7642 | −0.0879 | [−0.1450, −0.0087] |
| Exact-class mAP50-95 | 0.6089 | 0.5547 | −0.0541 | [−0.0920, −0.0124] |
| Recall, derived key 7 (yolo 7, 111 boxes, 2 groups) | 0.595 | 0.676 | +0.081 | [0.015, 0.186] |
| Recall, derived key 32 (yolo 33, 29 boxes, 1 group) | 0.621 | 1.000 | +0.379 | single group, interval not informative |
| Recall, derived key 41 (yolo 42, 26 boxes, 2 groups) | 0.462 | 0.615 | +0.154 | [0.143, 0.167], low support |

**Validation-selected point (diagnostic, not a lock).** The rule is recall ≥ 0.85, then the fewest
FP per image. Under it, A2 selects conf 0.05 and reaches recall 0.8478, which is below the target.
FP per image there is 0.566; the paired difference to the pilot is [+0.005, +0.274], which excludes 0.
The pilot meets the target at conf 0.20.

**Reading the CIs (QA I1).**
- The recall and FP intervals touch 0, so those two changes are **not called significant**.
- The lower exact-class mAP50 and mAP50-95 do not depend on any threshold, and their CIs exclude 0.
  Together with A2 failing its own selected point, this shows more than a confidence-score shift.

## 3. Contract §3 criteria (R3 §5, unchanged)

| Criterion at conf 0.20 | Result |
| --- | --- |
| Recall of classes 7, 32 and 41 each up by ≥ 0.05 | Met at the point estimate. Class 32 rests on one group; class 41 on two. |
| FP/image up by ≤ 0.03 | Met (−0.154) |
| Overall recall ≥ 0.85 | **Not met (0.7612)** |
| Paired CIs reported | Yes |

**Disposition: A2 does not meet its pre-registered success criterion.**
- Keep the 100-epoch pilot as the YOLO11s-54 reference.
- Preserve A2 and all its artifacts for review.
- A2 is not a candidate for the extra seeds or the final evaluation.
- A2 is not a causal test of class repetition alone, because the step count also differs.

**Observation (proposal, not a result).** Repeating the 7/32/41 images moved the model toward those
classes and away from the rest: fewer FP, higher focus-class recall, lower recall overall. Any follow-up
would need its own contract, for example a compute-matched variant or a different repeat factor, plus
Owner authorization. Nothing here authorizes it.

## 4. Classification

- **Verified artifact:** every number in §2 and §3, independently recomputed by the comparison QA.
- **Verified current behavior:** evaluator and CI tests, 120 passed; ruff clean.
- **Proposal:** the observation in §3.
- **Unknown:** behavior on the sealed test and on other seeds.
