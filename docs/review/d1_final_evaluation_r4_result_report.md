# D1 final evaluation — one-time sealed-test result (R4)

Date: 2026-11-07 (`Asia/Ho_Chi_Minh`).
Author: Claude Code (Opus 5.5), coordinating session.
Status: **`AWAITING_INDEPENDENT_RESULT_QA`**. Do not publish or present this as an acceptance result
until an independent result QA passes.
`sealed_test_accessed=true`.

## Run

- **Approval:** `docs/review/d1_final_evaluation_r4_owner_open_approval.md`, commit `c7b661c`.
- **Command:** the pinned R4 command, run from `detector/`. Exit 0. Run log in the session scratchpad,
  SHA-256 `418a5c17f33c70e99b0cc0a07fce69191489cfedc94164bfa903785777c5bd4b`.
- **Access event:** `d1-final-evaluation-r4-open` at `20261107T055038`, bound to plan `2c463b61…` and
  contract `d241011c…`. The access log now has 4 lines, SHA-256
  `4ae685690893dc1520f6a9356bf2d2e74c3d218c64204ce022b8aff4836180e0`.
- **Fixed inputs:**
  - lock: confidence 0.19, class-aware NMS IoU 0.70;
  - weights: seed 20261018 `5d5815a9…`, seed 20261019 `046cfea2…`;
  - `imgsz=1280`;
  - current test labels (`CURRENT_LABELS`);
  - Q4 gates.
- **Test set:** 903 images, 2,315 ground-truth boxes; 32 classes have test boxes, 22 of them have
  ≥ 20 boxes.

Output files, all under the Git-ignored `results/experiments/d1_final_evaluation_r1/`:

| File | SHA-256 |
| --- | --- |
| `d1_final_evaluation_r1.json` | `a6ea31b5947ceba82113b0856d2b8d2867d185e8ef0bc1a825a099f908abf23c` |
| `d1_final_evaluation_r1.md` | `9cddf82732f27b4a72a205df036fb93b2cb7e72d90f0ff994b4483b3d0a6ff09` |
| `predictions_seed_20261018.json` | `10e00a3860c9370a3eed2dcd9a7514c4f23d797d1f6789b366add5a9e76666ff` |
| `predictions_seed_20261018_manifest.json` | `4b7aac50b35e6134219d6e27fd39fc039f20ccb0ec0e9dde974d79ec66aeea18` |
| `predictions_seed_20261019.json` | `9d7347781030d9fd98b4d7fd0d3386167858c0186f5e49bf78f682e76cf2da65` |
| `predictions_seed_20261019_manifest.json` | `ab07564c4124eb070306cfaf3253f3fe0aecf77eefa412ecfa002a109e89fc91` |

## Result (copied from the scorer JSON)

| Gate (D-05 Q2/Q5) | Seed 20261018 | Seed 20261019 | Mean of 2 seeds | Group CI 95 % of mean | Marker | Verdict |
| --- | ---: | ---: | ---: | --- | --- | --- |
| mAP50 (classes with test boxes) | 0.4393 | 0.3648 | **0.4020** | 0.363 – 0.549 | ≥ 0.60 | **FAIL** |
| mAP50-95 | 0.3169 | 0.2547 | **0.2858** | 0.255 – 0.395 | ≥ 0.40 | **FAIL** |
| Class-agnostic recall at conf 0.19 | 0.6704 | 0.6631 | **0.6667** | 0.567 – 0.746 | ≥ 0.85 | **FAIL** |
| FP per image | 0.4540 | 0.3976 | **0.4258** | 0.244 – 0.808 | ≤ 0.40 (recalibrated) | **FAIL** |
| FP per image | | | 0.4258 | | ≤ 0.30 (original) | **FAIL** |
| Critical classes ≥ 20 boxes: recall ≥ 0.70 | | | 0 of 10 pass | | | **FAIL** |
| Latency p95, M1 Pro MPS | 47.28 ms | 48.09 ms | **47.68 ms** | | ≤ 100 ms | PASS |

**Overall D-05 verdict: FAIL**, under both the recalibrated and the original FP marker.

TP/FP counts:

| Seed | TP | FP | Precision |
| --- | ---: | ---: | ---: |
| 20261018 | 1,552 | 410 | 0.791 |
| 20261019 | 1,535 | 359 | 0.810 |

Critical-class recall, mean of 2 seeds (box counts in brackets):

| Class | Recall | Class | Recall |
| --- | ---: | --- | ---: |
| 0 (95) | 0.642 | 32 (71) | 0.085 |
| 2 (94) | 0.138 | 39 (206) | 0.692 |
| 7 (53) | 0.642 | 40 (143) | 0.545 |
| 13 (131) | 0.615 | 41 (83) | 0.488 |
| 22 (31) | 0.032 | 45 (70) | 0.171 |

These 16 classes are excluded from simulated behaviour: 0, 2, 3, 7, 9, 13, 14, 18, 20, 22, 30, 32,
39, 40, 41, 45.

### Validation → test

The two-seed mean dropped sharply from validation R3 to the test set:

| Measure | Validation | Test |
| --- | ---: | ---: |
| mAP50 | 0.791 | 0.402 |
| Recall | 0.855 | 0.667 |
| FP per image | 0.380 | 0.426 |

The cause is **not established** by this run. Possible contributors, none of them tested here:
- classes with test boxes but no validation boxes (D-05 Q4 excluded 13 classes from tuning);
- the current-label asymmetry below;
- a scene shift between the validation and test groups.

## Mandatory disclosures

1. **Gate recalibration.** The FP marker was recalibrated once, before the test, from 0.30 to 0.40
   (Q4, `8726d8c`), after the validation results were known. The test FP/image of 0.426 fails both
   markers.
2. **Label asymmetry.** The test was scored with its current labels. Validation labels were partly
   corrected in R3 (64 boxes and 40 ignore regions added, from the pilot's false positives); the test
   labels were not. Unlabelled real signs in the test count as FP. This report does **not** attribute
   any gate miss to label noise: no evidence for that was collected.
3. **Earlier attempts:**
   - **Attempt 1 (R1)** was refused at preflight, before access.
   - **Attempt 2 (R2)** logged an opening but stopped before any test payload was read.
   - **Attempt 3 (R3)** exported the test and ran a full prediction pass with both weights. Scoring
     then crashed, and the predictions were lost unseen.
   - **Attempt 4 (R4)** is this result. It used the same weights, threshold, gates and labels as
     before; nothing was changed after any test number was seen.
4. **Uncertainty.** The CIs resample D-02 image groups with both weights fixed. They do not measure
   training-seed variation; two seeds are too few for that.
5. **Scope.** These are offline measurements on the 903 sealed-test images. They make no safety or
   real-vehicle claim. Behaviour output stays simulation only.

## Next gate

An independent result QA must do the following:
- recompute the headline numbers from the saved predictions and the test labels;
- confirm both FP verdicts and every disclosure above;
- write exactly one `Verdict:` line.

Until then this report is a draft for the Owner, not a publishable result.
