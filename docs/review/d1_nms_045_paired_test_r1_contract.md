# D1 NMS IoU 0.45 vs 0.70 — paired validation test R1 (pre-registered contract)

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`) · Author: Claude Code (Opus 5.5), coordinating session.
Status: `FROZEN_BEFORE_COMPUTATION`. No number in §4 had been computed when this contract was written.
Boundary: validation R3 only, offline, existing prediction files. No inference, training, threshold
lock, app change or D-05 change. `sealed_test_accessed=false`, `thresholds_locked=false`.

## 1. Authority and question

Owner instruction in chat, 2026-11-06: "Lập kiểm định". This answered the question "Lập kiểm định ghép
cặp riêng cho NMS IoU 0,45?". The question arose from the NMS sweep R1 report.

| Input | SHA-256 |
| --- | --- |
| `docs/review/d1_nms_sweep_r1_report.md` | `cad83325fccddf31b8c05c7610c33bf008020389e5651b7a56dfa21ba17244e7` |
| `docs/review/generated/d1_nms_sweep_r1.json` (QA PASS) | `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057` |
| `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.45.csv` | `eb95a5021e685c7ba60b173a184fd29535f114bcb8269916ba594e6c404261a5` |
| `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.70.csv` | `d4ae12e3116ad9ee80fb39f00174cdb44daf29ded7ada14ea2086b926e477a11` |
| `detector/m1/nms_sweep_r1.py` (reused) | `0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e` |
| `detector/m1/a3_pilot_paired_ci_r1.py` (reused) | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` |

The sweep report states that per-class NMS IoU 0.45 removes 15 FP (150 → 135) and keeps 457
correct-class hits at confidence 0.20. It also states that no paired uncertainty exists for that
comparison. **Question:** on validation, does per-class IoU 0.45 reduce FP/image against 0.70 with
group-level uncertainty, without losing correct-class detections or AP?

## 2. What this test can and cannot show (declared before computing)

- **The test is in-sample and post hoc.** IoU 0.45 was noticed on these same 376 images. A positive
  result here shows the signal is consistent across the nine groups. It is **not** an independent
  confirmation. The only clean confirmation would be held-out data, and the sealed test may not be
  used for this.
- **0.45 is the edge of the tested grid.** The FP trend suggests that a lower IoU might remove more.
  This contract tests **0.45 against 0.70 only**. It does not open new IoU values, to avoid choosing
  among more options after seeing the data.
- **One checkpoint.** A partial replication is possible later on the D1-S2-R1 (seed 20261019) model:
  same validation images, different weights. It is pre-registered in §5, not run here.

## 3. Design (frozen)

- **Frames:** ground truth from the pinned bundle `tmp/yolo11n_n1_extract_r2`, through
  `a3_pilot_paired_ci_r1.gt_frames`. That gives 376 frames, 624 boxes and 9 D-02 groups.
- **Predictions:** the two CSVs above, loaded by `a3_pilot_paired_ci_r1.with_predictions`
  (`class_id`, `confidence`). Hashes are verified first.
- **Gate 0:** the 0.70 CSV must reproduce the QA'd sweep values at confidence 0.20: TP 547, FP 150,
  correct-class 457, mAP50 0.8521, mAP50-95 0.6089. The 0.45 CSV must reproduce TP 547, FP 135,
  correct-class 457, mAP50 0.8543, mAP50-95 0.6095. Tolerance on mAP is 1e-4. On any mismatch, stop.
- **Operating point:** confidence **0.20** for both settings. This is the point each setting selects
  on the full roster under the D-05 rule, as recorded in the sweep JSON. No other confidence is
  compared.
- **Matching and AP:** `m1.metrics.operating_point` and the common scorer's `average_precision`, as in
  `nms_sweep_r1.point` and `score_frames`.
- **Paired bootstrap:** 1,000 rounds, seed 20261018. Resample the 9 intact groups with identical draws
  for both settings, through `a3_pilot_paired_ci_r1.resample_indices`, `frame_stats` and `summarize`.
  Differences are 0.45 minus 0.70 for:
  - FP/image;
  - correct-class recall;
  - class-agnostic recall;
  - exact-class mAP50 and mAP50-95 (through `_correct_matrices` and `_map50_95`, plus the mAP50
    counterpart).

  Report the point difference, the 95 % percentile CI and the share of rounds below 0.
- **Per group:** for each of the 9 groups, report FP, correct-class hits and agnostic hits for both
  settings, with their differences.
- **Two-setting leave-one-group-out:** for each held-out group, choose between {0.45, 0.70} on the
  other 8 groups. The rule is FP/image at conf 0.20 if recall ≥ 0.85; then higher mAP50-95; then the
  setting closer to 0.70. Report the choice and the held-out FP and correct-class hits for both
  settings.
- **Box-level audit:** for each frame, list predictions at conf ≥ 0.20 present at 0.70 and absent at
  0.45, and record whether each was a TP, a correct-class TP or an FP at 0.70. Also count validation
  GT pairs whose boxes overlap at IoU ≥ 0.45. This is the "stacked or adjacent sign" exposure: a lower
  NMS IoU could suppress one of two real neighbouring signs. Report whether every such GT is still
  matched at 0.45.
- **Focus classes:** hits and recall of derived keys 7/32/41 (yolo 7/33/42) at both settings.

## 4. Decision rule (frozen)

**`SUPPORTED_ON_VALIDATION`** only if **all** of these hold:

1. The FP/image difference CI95 upper bound is < 0.
2. Correct-class hits at conf 0.20 are not lower at 0.45 in **any** of the 9 groups.
3. Class-agnostic recall at 0.45 is ≥ 0.85 and is not lower than at 0.70.
4. The mAP50-95 difference CI95 is not wholly below 0 (upper bound ≥ 0).
5. Leave-one-group-out chooses 0.45 in at least 7 of 9 folds.
6. No group has more FP at 0.45 than at 0.70.
7. Every validation GT in a pair overlapping at IoU ≥ 0.45 that is matched at 0.70 is still matched
   at 0.45.

Otherwise the result is **`NOT_SUPPORTED`**, with the failed conditions listed.

**Meaning of `SUPPORTED_ON_VALIDATION`:**
- 0.45 becomes a *candidate* to be considered in the final threshold-lock record for the final model.
- It must first replicate on the seed 20261019 model (§5).
- It does **not** change the app, Dynamic Threshold policy, D-05 or any locked value.

## 5. Pre-registered replication (not run here)

When D1-S2-R1 (seed 20261019) has a QA-passed result, run the same per-class NMS 0.45 and 0.70
inference on validation for that model. Apply §3–§4 unchanged. 0.45 may enter a lock proposal only if
both seeds give `SUPPORTED_ON_VALIDATION`. That run needs its own inference authorization.

## 6. Deliverables

| File | Content |
| --- | --- |
| `detector/m1/nms_045_paired_test_r1.py` and `detector/tests/test_nms_045_paired_test_r1.py` | Offline script and tests. Reuses the modules above by import and edits none. |
| `docs/review/generated/d1_nms_045_paired_test_r1.json` | All §3 outputs, the gate 0 result, input hashes, the decision, `sealed_test_accessed=false`, `thresholds_locked=false`, `inference_run=false` |
| `docs/review/d1_nms_045_paired_test_r1_independent_qa_record.md` | Independent QA by an agent that did not write the script. It recomputes at least the point differences, the per-group table and the FP CI. Exactly one `Verdict:` line. |
| `docs/review/d1_nms_045_paired_test_r1_report.md` | The result, framed by §2 |

Gate: `uv run ruff check src tests`, plus ruff and pytest on the new detector files.
