# D1-EA-R1 — validation error evidence package

Status: `D1_EA_R1_AWAITING_INDEPENDENT_QA`
Boundary: `VALIDATION_ONLY_DIAGNOSIS_NO_TRAINING_NO_SEALED_TEST_NO_VAL_PIXELS_IN_TRAIN`

Built by `detector/m1/error_analysis_r1.py` as required by
`docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md`. Inference ran once
on the R10 reference device (`mps`, imgsz 1280, NMS IoU 0.7) with the pinned weights
`5d5815a96218759e…`; the build refuses to write unless the regenerated predictions reproduce
the pinned R10 report exactly. Validation only: `test_included=false`,
`sealed_test_accessed=false`. No validation image, crop or prediction may enter training.

## Reproduction of R10 at conf 0.2

| Quantity | Value |
| --- | ---: |
| Images | 376 |
| Ground-truth boxes | 560 |
| Retained predictions | 697 |
| Paired with ground truth | 483 |
| Background false positives | 214 |
| Unmatched ground truth | 77 |

The operating point, the full confusion matrix and the class-aware hits of every gated class equal
the R10 report.

## Background false positives by predicted class

| Class | Count | Share |
| --- | ---: | ---: |
| 10 | 53 | 24.8% |
| 12 | 44 | 20.6% |
| 23 | 35 | 16.4% |
| 30 | 19 | 8.9% |
| 46 | 13 | 6.1% |
| 39 | 12 | 5.6% |
| 5 | 9 | 4.2% |
| 7 | 6 | 2.8% |
| 8 | 4 | 1.9% |
| 40 | 4 | 1.9% |
| 0 | 4 | 1.9% |
| 2 | 4 | 1.9% |
| 4 | 3 | 1.4% |
| 14 | 1 | 0.5% |
| 17 | 1 | 0.5% |
| 3 | 1 | 0.5% |
| 41 | 1 | 0.5% |

## Atlas

Green box = ground truth, red box = prediction. Pages are in `docs/review/assets/d1_ea_r1/` (git-ignored: they
contain DATASET01 pixels); the page/slot roster is `docs/review/generated/d1_ea_r1_atlas_index.csv`.

| Category | Items | Pages |
| --- | ---: | ---: |
| `background_fp` | 214 | 8 |
| `critical_7` | 49 | 2 |
| `critical_32` | 11 | 1 |
| `critical_41` | 10 | 1 |
| `pair_46_to_10` | 58 | 2 |
| `pair_8_to_12` | 6 | 1 |

`critical_<c>` holds every ground-truth box of class c that the diagnostic pairing either assigns
to another class or leaves unmatched. Pairing is the score-ordered class-agnostic one-to-one
matching of the R10 confusion matrix; D-05 class-aware gate hits use a separate matcher.

## Not concluded here

Root causes are not stated by this package. The visual review that turns the atlas into
hypotheses, and the independent QA of this package, are separate steps.
