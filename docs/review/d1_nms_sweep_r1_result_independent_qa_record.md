# D1 NMS sweep R1 — independent result QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh). The reviewer was a separate Codex agent from the implementation, inference run, and source QA. This review read existing local validation artifacts; it did not run model inference, train, upload, or open a sealed test.

Verdict: PASS

## Artifact binding and scope

- Result JSON: `docs/review/generated/d1_nms_sweep_r1.json`, SHA-256 `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057` at review time.
- All 11 input SHA-256 pins in the JSON match the current files, including the pilot `best.pt`, validation R3 bundle manifest, pinned pilot CSV, common scorer, package verifier, D-05 decision, class map and group map.
- The package manifest declares `test_included=false` and `sealed_test_accessed=false`; the result declares `scope="validation R3 only"`, 376 images, 624 GT boxes, 9 groups, `sealed_test_accessed=false`, and `thresholds_locked=false`. The review loaded only the 376 validation images' dimensions, validation labels and prediction CSVs from the pinned train/val bundle. No sealed-test member was opened.
- Exactly 11 `predictions_*.csv` files exist under Git-ignored `results/experiments/d1_nms_sweep_r1/`; each recomputed SHA-256 matches `prediction_csv_sha256` in the result JSON. These CSVs must stay out of the commit.

## Independent replay

- Rebuilt the validation `Frame` roster from `tmp/yolo11n_n1_extract_r2` using the existing pinned GT loader and attached each CSV with schema, range and stem checks. Recomputed all 20 confidence points for every one of 11 configurations: **220/220** cells match TP, FP, correct-class hits, precision, class-agnostic recall, correct-class recall, FP/image and derived-key 7/32/41 class support/hits/recall. Recomputed class-aware mAP50 and mAP50-95 for all 11 configurations with the common scorer; all match the JSON.
- Baseline `classaware_0.70` at confidence 0.20 reproduces **547 localization TP, 150 FP, 457 correct-class hits**, mAP50 ≈ **0.8521** and mAP50-95 ≈ **0.6089**. The JSON's pinned-CSV comparison and baseline gate are consistent.
- Independently recomputed the per-configuration eligible confidence point and global ranking. The lowest-FP eligible setting is `agnostic_0.80` at confidence 0.20: FP/image ≈ **0.2899**, versus ≈ **0.3989** at baseline. However, correct-class hits fall from **457 to 433** and mAP50-95 from ≈ **0.6089 to 0.5385**. The other agnostic variants' correct-class losses of 23 and 22 also match the JSON.
- Recomputed each of nine leave-one-group-out fits from the remaining eight D-02 groups, including the common scorer's mAP tie breaker and held-out recall/FP. All nine folds choose `agnostic_0.80` and their held-out metrics match the JSON.
- Replayed 1,000 paired group draws with seed 20261018 from the two saved prediction sets. The FP/image difference 95% CI is **[-0.1640, -0.0588]** and the mAP50-95 difference CI is **[-0.1533, -0.0354]**, both matching the JSON. The mAP interval lies wholly below zero, so the contract's second change condition fails even though FP/image improves and 9/9 folds agree. The recorded decision **`KEEP_0_70`** follows the contract.

## Limits

This PASS verifies the local retrospective diagnostic and its arithmetic, not an improvement suitable for activation. The source QA already passed separately. The result does not lock NMS or confidence, alter D-05, establish multi-seed/generalization performance, or authorize an app change. A report and figures may now be prepared from this verified JSON; no sealed-test evaluation is authorized.
