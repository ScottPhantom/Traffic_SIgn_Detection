# D1 final evaluation R4 — independent result QA

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`). Reviewer: a Codex agent separate from the R4 scorer operator and result-report author. Scope: the existing R4 outputs and committed report, not a new test run.

Verdict: PASS

## Immutable evidence

The committed report is `docs/review/d1_final_evaluation_r4_result_report.md`, SHA-256 `1983367728eef0da36044274e90ae05956195608f5bd60476aacdc707b700d13`, at commit `003e1e1`. Its Owner opening approval is the unchanged file in commit `c7b661c`, SHA-256 `d3572cafdd6b50422318a33a83156005e79fcf1f7a173eee8b9d3cb4fbc4663d`; its contents bind the R4 contract `d241011c…`, plan `2c463b61…`, and the exact plan reason. The report cites the approval commit rather than printing its file hash; the committed approval and bindings were verified directly.

The six files under `results/experiments/d1_final_evaluation_r1/` have exactly the SHA-256 values stated in the report:

| File | SHA-256 |
| --- | --- |
| `d1_final_evaluation_r1.json` | `a6ea31b5947ceba82113b0856d2b8d2867d185e8ef0bc1a825a099f908abf23c` |
| `d1_final_evaluation_r1.md` | `9cddf82732f27b4a72a205df036fb93b2cb7e72d90f0ff994b4483b3d0a6ff09` |
| `predictions_seed_20261018.json` | `10e00a3860c9370a3eed2dcd9a7514c4f23d797d1f6789b366add5a9e76666ff` |
| `predictions_seed_20261018_manifest.json` | `4b7aac50b35e6134219d6e27fd39fc039f20ccb0ec0e9dde974d79ec66aeea18` |
| `predictions_seed_20261019.json` | `9d7347781030d9fd98b4d7fd0d3386167858c0186f5e49bf78f682e76cf2da65` |
| `predictions_seed_20261019_manifest.json` | `ab07564c4124eb070306cfaf3253f3fe0aecf77eefa412ecfa002a109e89fc91` |

Each prediction manifest names the hash of its raw prediction file and the corresponding pinned weight hash. The append-only access log stayed at **four lines**, SHA-256 `4ae685690893dc1520f6a9356bf2d2e74c3d218c64204ce022b8aff4836180e0`, before and after this QA. The result JSON says `split=test`, `label_mode=CURRENT_LABELS`, `sealed_test_accessed=true`, 903 images and 2,315 GT boxes.

## Independent recomputation

I read the two saved prediction JSON files, the already-exported `labels/test` and `data_test.yaml`. Because labels are normalized YOLO coordinates while predictions use pixel coordinates, I read only each exported test image's **width and height from its header** with PIL; I did not decode pixels for inference, copy images or labels, or run the final scorer. The roster was 903 image-label pairs: 769 at 960×540 and 134 at 1920×1080; the labels contained 2,315 boxes, 32 classes with boxes and 22 classes with at least 20 boxes.

I converted label xywh coordinates to pixel xyxy and implemented a separate score-descending greedy matcher. A prediction is eligible at locked confidence ≥0.19; it matches at IoU ≥0.50 to one unmatched GT box. Class-agnostic matches give TP/FP and recall. A separate class-aware pass gives class recall. This procedure read saved predictions only; it performed **no new model inference**.

| Seed | TP | FP | Recall | FP/image | Precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20261018 | 1,552 | 410 | 0.67041037 | 0.45404208 | 0.7910 |
| 20261019 | 1,535 | 359 | 0.66306695 | 0.39756368 | 0.8105 |
| Two-seed mean | — | — | **0.66673866** | **0.42580288** | — |

These counts and rates equal the saved scorer JSON and the report after rounding. FP/image 0.42580288 fails **both** the recalibrated ≤0.40 gate and the original ≤0.30 marker. Recall 0.66673866 fails ≥0.85.

I also rebuilt `Frame` values from the saved predictions and exported GT, then called only the QA-pinned AP postprocessor `evaluate_cascade_b0_r1.average_precision` (source SHA-256 `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42`). This did not call the final scorer or any model. It reproduced:

| Seed | mAP50 | mAP50–95 | Classes with GT |
| --- | ---: | ---: | ---: |
| 20261018 | 0.43930046 | 0.31690800 | 32 |
| 20261019 | 0.36476549 | 0.25465472 | 32 |
| Two-seed mean | **0.40203297** | **0.28578136** | 32 |

Both means fail their ≥0.60 and ≥0.40 gates. The ten D-05 critical classes all have at least 20 GT boxes. Independent class-aware hits and two-seed mean recalls are:

| Derived key (YOLO ID) | GT boxes | Seed-18 hits | Seed-19 hits | Mean recall |
| --- | ---: | ---: | ---: | ---: |
| 0 (0) | 95 | 59 | 63 | 0.642105 |
| 2 (2) | 94 | 10 | 16 | 0.138298 |
| 7 (7) | 53 | 46 | 22 | 0.641509 |
| 32 (33) | 71 | 11 | 1 | 0.084507 |
| 13 (13) | 131 | 79 | 82 | 0.614504 |
| 22 (24) | 31 | 0 | 2 | 0.032258 |
| 45 (47) | 70 | 14 | 10 | 0.171429 |
| 39 (40) | 206 | 139 | 146 | 0.691748 |
| 40 (41) | 143 | 63 | 93 | 0.545455 |
| 41 (42) | 83 | 47 | 34 | 0.487952 |

All ten means are below the critical-class gate of 0.70, as the report says. The saved JSON also lists the same 16 classes excluded from simulated behaviour as the report. The stored latency p95 values are 47.27885 ms and 48.08720 ms; their arithmetic mean is 47.68302 ms, below 100 ms. **Latency was not rebenchmarked** in this QA; its verdict is checked against the retained measurement, not independently measured. With every non-latency gate failing, the stored and reported overall D-05 verdict **FAIL** follows.

## Disclosure and wording audit

The report shows both FP markers and explains the one-time recalibration after validation. It discloses that R3 validation labels received corrections while the current test labels did not; it does not assign the observed gate failures to label noise. It records attempt 1's preflight refusal, attempt 2's logged opening without payload, and attempt 3's full prediction pass whose in-memory outputs were lost unseen after a scoring crash. It states that a validation-to-test drop exists while its cause is unestablished. The reported 95% intervals match the saved JSON after rounding; they resample D-02 groups with fixed weights and do not estimate seed variation. The report makes no safety or real-vehicle acceptance claim and keeps behaviour as simulation.

This PASS validates the retained R4 result and report within the fixed, already-authorized test evaluation. It does not authorize another test run, alter any gate, or validate deployment safety. The report's own `AWAITING_INDEPENDENT_RESULT_QA` status remains unchanged by this append-only QA record; publication should cite this record and update presentation status separately.
