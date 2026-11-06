# D1 two-seed R3 validation threshold record — result report

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Status: `AWAITING_OWNER_APPROVAL`.
Scope: YOLO11s-54 pilot seeds 20261018 and 20261019, validation R3 only
(376 images, 624 ground-truth boxes, nine D-02 groups). `sealed_test_accessed=false`.

## Result

The R3 writer and verifier reproduced the earlier two-seed provisional selection:
**confidence 0.19, class-aware NMS IoU 0.70**. The generated record has status
`LOCKED_ON_VAL`, but it is **not effective** until a separate Owner approval record
binds the independently QA-passed record and proof hashes. This report does not
authorize applying the setting to the app or opening the sealed test.

| Measure at confidence 0.19 / class-aware IoU 0.70 | Seed 20261018 | Seed 20261019 | Mean | Difference 19 − 18 |
| --- | ---: | ---: | ---: | ---: |
| Class-agnostic recall | 0.88942 | 0.82051 | **0.85497** | −0.06891 |
| False positives per image | 0.41223 | 0.34840 | **0.38032** | −0.06383 |
| Exact-class mAP50–95, full candidate pool | 0.60887 | 0.52086 | **0.56486** | −0.08801 |

Seed 20261019 alone is below the 0.85 recall marker. The two-seed mean is above
that marker, but its FP/image is above the 0.30 marker. These are validation
measurements, not a claim of improved weights or driving-scene safety.

## Selection and controls

| Configuration | Confidence | Mean recall | Mean FP/image | Decision |
| --- | ---: | ---: | ---: | --- |
| Class-aware NMS IoU 0.70 | 0.20 | 0.84455 | 0.36835 | Mean recall below 0.85 |
| Class-aware NMS IoU 0.70 | 0.19 | **0.85497** | **0.38032** | Selected fallback |
| Across-class NMS IoU 0.80 | 0.19 | 0.85497 | 0.24734 | Rejected by mAP change condition |

The unrestricted 0.19 / across-class 0.80 cell lowers FP/image by 0.13298
relative to 0.19 / class-aware 0.70. Its paired 95% group-bootstrap interval
for the FP/image difference is [−0.20055, −0.08253]. However, its mAP50–95
difference is −0.06000, with interval [−0.13119, −0.03448], wholly below
zero. The prespecified change rule therefore rejects this NMS change despite
the 9/9 leave-one-group-out votes for the across-class configuration.

## Verification and boundaries

- The pilot result archive and manifest were copied from the Owner's locally
  synced Drive into Git-ignored `tmp/` without modifying Drive. Both pilot and
  seed-19 archives passed `run_d1_colab.verify_result_archive`; both manifests
  report terminal `SUCCEEDED` and `sealed_test_accessed=false`.
- All 22 existing prediction CSV hashes matched their independently QA-passed
  generated JSONs. The original inference path used `conf=0.001` and
  `imgsz=1280`; the lowest CSV candidate scores were at or above 0.001. No
  model inference or training was performed for this record.
- The R3 `build-report`, `write`, and `verify` commands completed. Independent
  result QA recomputed the selected cell, two controls, paired 1,000-draw
  intervals and all nine leave-one-group-out folds from the stored CSVs.
- Versioned record: `docs/review/generated/d1_threshold_lock_r1.json`, SHA-256
  `d39b0466a5285979c3da63546ebbd56d26d0030081f4df9fa6c75fc8ee96167d`.
  R3 proof: `docs/review/generated/d1_threshold_lock_r1_r3_proof.json`, SHA-256
  `2d2fbd7cf99ee9e8b1349a55cf40b0182764efe9f7d4cd5078c06c5f8aa72e77`.
  Result QA: `docs/review/d1_threshold_lock_r1_result_independent_qa_record.md`,
  SHA-256 `c113a80ef295c3ec43ef86ad07e28ad95d3a6ce2ab61fe30b5cae1392b308261`
  (`Verdict: PASS`).

This analysis uses **two training seeds** and a common validation roster.
The 95% intervals resample intact D-02 image groups, not training seeds; they
do not quantify variation over future seeds or new camera scenes. The setting
remains `AWAITING_OWNER_APPROVAL`; a separate approval record must bind the
record and proof hashes before a final evaluator may read it. No app threshold,
D-05 rule, or sealed-test status was changed.
