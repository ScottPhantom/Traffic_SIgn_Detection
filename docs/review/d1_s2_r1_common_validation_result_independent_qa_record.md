# D1-S2-R1 common-validation result independent QA

- Date: 2026-11-06 (Asia/Ho_Chi_Minh).
- Reviewer: independent Codex QA agent. The evaluator and paired-CI outputs were operated by another agent; this reviewer did not run inference or training.
- Scope: validation R3 only, 376 images, 624 ground-truth boxes, nine D-02 groups. No sealed-test member was opened or scored; `sealed_test_accessed=false`.

## Input and binding checks

- S2 prediction CSV SHA-256: `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8` (2,611 prediction rows).
- S2 common comparison JSON SHA-256: `0d76dc34eaa8dfe4c155dfb16a0d150862ae2e568c623319f3a65db45c5a46b4`.
- Paired CI JSON SHA-256: `57b386e3c1396449992a77e020200a953d3759b9d03968ac893d377a8ea37760`.
- Both JSON outputs bind the exact S2 CSV, comparison, validation-only R3 manifest `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`, and pilot CSV `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`. The R3 manifest declares `test_included=false` and `sealed_test_accessed=false`; the used class map and group map match their manifest hashes.
- The comparison binds the Owner authorization SHA `4f394487f7c8d51c31c268414bc16aabc1baa57a41822563459489d0940d2f0c`, completed S2 run and its result-QA SHA `68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3`. The paired output also binds the S2 evaluator, metrics source, threshold-selection contract B and its QA; every referenced local hash checked here matched.

## Independent count and interval recomputation

I read the validation image sizes, YOLO label files, group map and both prediction CSVs directly. A separate per-image descending-confidence IoU 0.50 matcher at confidence 0.20 gave:

| Model | Agnostic TP / 624 | Correct-class TP / 624 | FP / 376 | Agnostic recall | Correct-class recall | FP/image |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Pilot seed 20261018 | 547 | 457 | 150 | 0.8766025641 | 0.7323717949 | 0.3989361702 |
| S2 seed 20261019 | 507 | 379 | 127 | 0.8125000000 | 0.6073717949 | 0.3377659574 |

The S2 JSON fixed-confidence counts, class hits, precision-derived values and both recalls agree. Pilot anchors are 547 agnostic TP, 150 FP and 457 correct-class TP. Its stored exact-class mAP50 `0.8520835680` and mAP50-95 `0.6088678435` agree with the pinned pilot anchor rounded to 0.8521 / 0.6089. The report labels S2 mAP50 `0.7308727207` and mAP50-95 `0.5208575558`.

The R3 derived-key map is `7 -> yolo_id 7`, `32 -> 33`, `41 -> 42`. Independent correct-class hits/support and recall at 0.20:

| Derived key | Pilot | S2 | S2 minus pilot |
| --- | ---: | ---: | ---: |
| 7 | 66/111 = 0.5945945946 | 75/111 = 0.6756756757 | +0.0810810811 |
| 32 | 18/29 = 0.6206896552 | 16/29 = 0.5517241379 | -0.0689655172 |
| 41 | 12/26 = 0.4615384615 | 10/26 = 0.3846153846 | -0.0769230769 |

I independently drew 1,000 paired nine-group bootstrap samples with NumPy seed `20261018`, aggregating per-image counts from the CSVs. Point differences and percentile 95% intervals exactly reproduce the stored values (floating-point tolerance `1e-14`):

| Metric | S2 minus pilot | Paired CI95 |
| --- | ---: | --- |
| Agnostic recall | -0.0641025641 | [-0.1634315849, 0.0083232281] |
| Correct-class recall | -0.1250000000 | [-0.2355848435, -0.0142027072] |
| FP/image | -0.0611702128 | [-0.3652202937, 0.1448998161] |

Both models' marginal intervals also reproduce. Focus-class paired intervals reproduce: key 7 `[0.0735294118, 0.0930232558]` (892 defined draws; two supporting groups), key 32 `[-0.0689655172, -0.0689655172]` (647 draws; one supporting group), key 41 `[-0.1428571429, 0.0]` (874 draws; two supporting groups). Key 32's single-group interval is correctly marked degenerate and not informative; all three classes are low-support under the report's group rule.

## Interpretation boundary

The output explicitly describes **seed variation** (20261019 minus 20261018), not an improvement test. It declares `split=val`, `inference_run=false`, `training_run=false`, `thresholds_locked=false`, and `sealed_test_accessed=false`. S2's validation-selected confidence is 0.15, whereas the paired operating-point comparison uses the common fixed confidence 0.20. The FP/image difference interval crosses zero, so these two seeds do not establish that pilot FP/image 0.399 is stable or that S2 has a lower population FP rate. No threshold lock or sealed-test conclusion follows from this QA.

Verdict: PASS
