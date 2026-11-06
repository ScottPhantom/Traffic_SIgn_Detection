# D1 confidence sweep R1 — validation R3 diagnostic

Status: `RESULT_PREPARED_AWAITING_INDEPENDENT_QA`  
Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)  
Scope: 376 validation R3 images, 624 GT boxes, 9 D-02 groups; model predictions already saved and QA-pinned. `sealed_test_accessed=false`; `thresholds_locked=false`.

## Main question: at the same false-positive budget, what happens?

The table gives **class-agnostic sign recall / correct-class recall** at the same FP per image. These values are *linear interpolation between adjacent confidence-grid points*, not an additional model run or a measured point at exactly that budget. All values are fractions of the 624 GT boxes. None of the reported budgets required extrapolation.

| Pipeline | FP/ảnh 0.20 | FP/ảnh 0.25 | FP/ảnh 0.30 |
| --- | ---: | ---: | ---: |
| YOLO11s-54 pilot (reference) | 0.679 / 0.572 | 0.743 / 0.622 | 0.794 / 0.664 |
| YOLO11s-54 A3 (40 epoch) | 0.760 / 0.590 | 0.791 / 0.606 | 0.808 / 0.616 |
| YOLO11s-54 A2 | 0.709 / 0.619 | 0.764 / 0.653 | 0.791 / 0.671 |
| Pilot + CompactCNN fusion | 0.679 / 0.566 | 0.743 / 0.617 | 0.794 / 0.661 |
| S1 + CompactCNN B0 | 0.874 / 0.537 | 0.914 / 0.547 | 0.917 / 0.550 |
| S1 + CompactCNN R2 | 0.858 / 0.539 | 0.902 / 0.560 | 0.917 / 0.569 |
| S1 + VGG16-54 | 0.879 / 0.512 | 0.906 / 0.520 | 0.914 / 0.522 |
| N1 + CompactCNN | 0.858 / 0.525 | 0.869 / 0.529 | 0.876 / 0.534 |
| N1 + CompactCNN R2 | 0.852 / 0.510 | 0.860 / 0.515 | 0.869 / 0.522 |
| N1 + VGG16-54 | 0.861 / 0.513 | 0.867 / 0.516 | 0.873 / 0.519 |

**Reading the tradeoff:** every Cascade curve is above the pilot for *finding a sign somewhere* in the low-FP region shown, but below it for *assigning the right sign class*. The two outcomes must be kept separate in any slide or product claim. A3 and A2 do not consistently dominate the pilot on both recalls. This is one validation roster and one seed per configuration, so it does not establish generalization or a winning architecture.

## Descriptive D-05 selection on the 0.05–1.00 grid

The rule takes the lowest FP/image among grid points with class-agnostic recall ≥ 0.85, breaking FP ties toward higher confidence. This table is **diagnostic**; it does not lock an app or final-candidate threshold. "Both markers" means a grid point has recall ≥ 0.85 and FP/image ≤ 0.30 on validation; it is not D-05 test acceptance.

| Pipeline | Confidence | Agnostic recall | Correct-class recall | FP/ảnh | Both markers? |
| --- | ---: | ---: | ---: | ---: | --- |
| YOLO11s-54 pilot | 0.20 | 0.8766 | 0.7324 | 0.3989 | No |
| YOLO11s-54 A3 | 0.05 | 0.8670 | 0.6779 | 0.5452 | No |
| YOLO11s-54 A2 | 0.05* | 0.8478 | 0.7196 | 0.5665 | No |
| Pilot + CompactCNN fusion | 0.20 | 0.8766 | 0.7308 | 0.3989 | No |
| S1 + CompactCNN B0 | 0.25 | 0.8670 | 0.5353 | 0.1968 | Yes |
| S1 + CompactCNN R2 | 0.25 | 0.8574 | 0.5385 | 0.1995 | Yes |
| S1 + VGG16-54 | 0.35 | 0.8558 | 0.5032 | 0.1676 | Yes |
| N1 + CompactCNN | 0.15 | 0.8558 | 0.5240 | 0.1915 | Yes |
| N1 + CompactCNN R2 | 0.15 | 0.8510 | 0.5096 | 0.1915 | Yes |
| N1 + VGG16-54 | 0.25 | 0.8526 | 0.5128 | 0.1463 | Yes |

\*A2 has **`NO_POINT_MEETS_RECALL_0_85`**. Its 0.05 row is the maximum-recall fallback, not an eligible optimal threshold.

## Inputs, calculation and evidence limits

- Pilot 20-point curve came **unchanged** from the QA-passed `classaware_0.70` cells in `docs/review/generated/d1_nms_sweep_r1.json` (SHA-256 `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057`). The existing QA step-0 record and this package both read 547 TP, 150 FP and 457 correct-class hits at 0.20. Pilot was not re-inferred or rescored for the curve.
- The other nine rows were scored from their QA-pinned prediction CSV or, for S1 + VGG16-54, the pinned embedded prediction list. Each point uses the existing `m1.metrics.operating_point`; the 0.20 point was checked against that model's pinned result JSON. The confidence score for Cascade is the original detector × classifier score used by its evaluator; for fusion, the original detector `conf` remains the operating score while `fused_id` is the class.
- The smallest observed candidate score is below 0.05 for every pipeline. This proves the 0.05 grid point is observable in these saved files; it does not recover boxes suppressed by the original inference/NMS stage. No S2 seed-20261019 prediction or model was read.
- The JSON stores all 200 model×grid cells, exact input hashes, the source confidence field, class 7/32/41 recalls with derived-key → YOLO-ID mapping 7/33/42, max-F1 diagnostic point, and 95% D-02 group-bootstrap intervals at the descriptive selected point. SVGs use common scales and are slide assets; the JSON is the authoritative table source.
- Lowering confidence can increase recall but also false positives. `confidence` is an uncalibrated model or pipeline score, not a probability of correctness. These curves do not change D-05, the app's 0.20 default, or the separate three-seed R3 threshold-lock contract.

Reproduce with `cd detector && PYTHONPATH=. uv run --no-sync python -m m1.threshold_sweep_r1 verify`. The `write` command creates outputs once and refuses overwrite. Independent result QA must rederive at least the pilot and A2 at three grid points, check every figure against JSON, and issue exactly one `Verdict:` line before this package is committed or cited as reviewed.
