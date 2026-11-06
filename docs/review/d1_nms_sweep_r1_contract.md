# D1 NMS IoU × confidence sweep R1 contract

Status: authorized diagnostic, source QA required before inference. Date: 2026-11-06.

## Immutable inputs and scope

- Pilot `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/weights/best.pt`: SHA-256 `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`.
- Validation-only package `tmp/yolo11n_n1_extract_r2/manifest.json`: SHA-256 `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da`. The package verifier must pass; expected validation roster is 376 images, 624 boxes in 9 D-02 groups. Do not use `_r1`.
- Pilot predictions in that package, `data/yolo54_predictions_val.csv`: SHA-256 `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893`.
- Reused source pins: `detector/colab/evaluate_d1_a3_r2_common_r1.py` `5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6`; `detector/colab/evaluate_cascade_b0_r1.py` `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42`; `detector/m1/metrics.py` `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f`; `detector/m1/a3_pilot_paired_ci_r1.py` `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4`; package verifier `detector/colab/run_yolo11n_n1_r1.py` `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753`; D-05 decision `docs/review/d05_owner_decision_record.md` `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702`.
- Bundle class map `data/classes.csv`: `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242`; groups `data/val_groups.json`: `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682`.
- All inference is local MPS, with CPU fallback recorded if MPS fails. No train, upload, download, or sealed-test access. `sealed_test_accessed=false`.

## Inference and baseline gate

Use the common evaluator's input images, RGB conversion, labels, clipping and scorer. Call Ultralytics `detector.predict` with `conf=0.001`, `imgsz=1280`, batch 1, default `max_det=300`; vary only `iou` and `agnostic_nms`. Eight class-aware IoU values: 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80. Three agnostic-NMS values: 0.80, 0.85, 0.90. Save one CSV and SHA-256 per configuration under Git-ignored `results/experiments/d1_nms_sweep_r1/`.

First run 0.70/class-aware only. At confidence 0.20, require 547 class-agnostic TP, 150 FP, 457 exact-class hits; require mAP50 0.8521 and mAP50-95 0.6089 within 1e-4. Compare to the pinned pilot CSV using the same scorer. Any count or mAP failure stops all remaining inference. Tiny prediction-value drift on MPS is recorded if the metrics still pass.

## Selection and uncertainty

Confidence grid: 0.05, 0.10, …, 1.00 (20 values), for 220 cells. For every cell record class-agnostic recall, exact-class recall, precision, TP, FP, FP/image, and correct-class recall/support for derived keys 7/32/41 (YOLO IDs 7/33/42). For every configuration record exact-class mAP50 and mAP50-95 over the full candidate predictions, independent of the operating confidence.

Within a configuration, select a point with agnostic recall ≥ 0.85 and lowest FP/image, breaking ties toward higher confidence. Across configurations choose lowest FP/image, then highest mAP50-95, then closest IoU to 0.70. Ineligible configurations cannot win. If none are eligible, keep 0.70 and report the gate failure.

Compare the chosen configuration with the 0.70 class-aware baseline, each at its selected confidence. Use 1,000 paired cluster-bootstrap draws over 9 intact D-02 groups, seed 20261018 and shared group draws, for the difference in FP/image and mAP50-95. For each of nine leave-one-group-out folds, select configuration and confidence from the remaining eight groups by the same law, then report held-out recall and FP/image. A change from 0.70 is only a candidate if its FP/image difference CI lies wholly below zero, its mAP50-95 difference CI is not wholly below zero, and ≥7/9 folds select the same or immediately adjacent IoU (with matching NMS mode). Otherwise `KEEP_0_70`. Report agnostic-NMS settings separately and quantify exact-class hits lost at the selected point relative to the 0.70 baseline.

## Outputs and stop conditions

`docs/review/generated/d1_nms_sweep_r1.json` contains all cells, input/CSV hashes, baseline gate, CI, CV, decision, `thresholds_locked=false`, `sealed_test_accessed=false`. Figures: `docs/review/figures/d1_nms_sweep_r1_lines.svg` (viewBox 0 0 1100 520, required colors and accessible Vietnamese label) and `d1_nms_sweep_r1_heatmap.svg`. Summarize in `docs/review/d1_nms_sweep_r1_report.md`. Source and result QA each need a separate agent/session and one `Verdict:` line per record.

Stop if any pinned input differs, source QA or result QA fails, baseline gate fails, a non-val dataset/model is needed, or training would be needed. Do not activate a rule in the app, change D-05, or lock thresholds from this diagnostic alone.
