# D1 corrected validation R10 — error analysis and improvement decision packet

Date: 2026-10-22  
Status: `ANALYSIS_COMPLETE_DECISION_REQUIRED_BEFORE_NEW_EXPERIMENT`

## Evidence boundary

This packet is derived only from the independently QA-passed R10 validation report with content
SHA-256 `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5`.
It does not use the sealed test, does not relabel validation, does not add validation pixels to
training and does not authorize a new run.

The report stores a full confusion matrix and bounded stem samples, not every predicted box or a
visual false-positive atlas. Therefore the counts below are verified; explanations of visual root
cause remain hypotheses until a separate validation-only prediction/atlas package is built and QA
reviewed.

## Confirmed failure structure at confidence 0.20

The selected operating point has 483 class-agnostic detections, 214 false positives and 77 missed
ground-truth boxes over 376 images / 560 boxes. It meets recall 0.8625 but fails FP/image 0.5691.
Because the selector chooses the lowest-FP grid point among those with recall at least 0.85,
threshold adjustment on the existing grid alone did not find an operating point satisfying both
current D-05 constraints.

### Background false positives

| Predicted class | Background FP | Share of 214 |
| --- | ---: | ---: |
| 10 | 53 | 24.8% |
| 12 | 44 | 20.6% |
| 23 | 35 | 16.4% |
| 30 | 19 | 8.9% |
| 46 | 13 | 6.1% |
| 39 | 12 | 5.6% |

These six classes account for 176/214 = 82.2% of background false positives. This concentration
supports targeted training-only hard-negative investigation rather than a blind global epoch
increase.

### Supported critical classes

| GT class | Support | Correct-class gate recall | Confusion evidence |
| --- | ---: | ---: | --- |
| 7 | 111 | 0.5946 | 36 paired as background; 10 predicted 17, 2 predicted 18, 1 predicted 49 |
| 32 | 29 | 0.6207 | 6 predicted 7; 5 paired as background |
| 41 | 21 | 0.5714 | 6 predicted 39; 2 predicted 40; 2 paired as background |

The confusion matrix uses a score-ordered class-agnostic one-to-one pairing for diagnostics, while
the D-05 per-class recall uses a separate class-aware matcher. Exact diagonal/miss counts therefore
need not numerically reproduce `gates.classes[*].hits`; both are valid under their documented
matching contracts.

### Other high-impact confusion

- GT class 46: 58/104 pairs are predicted as class 10; only 42 are on the class-46 diagonal and 4
  pair to background. The class-aware gate recall is 0.5288 and passes only the non-critical 0.50
  threshold narrowly.
- GT class 8: 6/51 are predicted as class 12 and 15 pair to background.
- Training-label support is not absent: current train labels contain 228 boxes for class 7, 138 for
  class 32, 610 for class 41, 1,431 for class 10 and 427 for class 46. Quantity alone therefore
  does not establish that more copies of the same distribution will solve the confusions.

## Required next evidence package — D1-EA-R1

Build a validation-only, immutable error-analysis package before changing training:

1. Export every prediction at the locked diagnostic point (`conf=0.20`, NMS IoU 0.70), with stem,
   predicted class, confidence, box, matched GT class/IoU or background disposition.
2. Produce contact sheets for all 214 background FP and all errors involving classes 7, 32, 41,
   plus the 46→10 and 8→12 pairs. Show source image, predicted box, GT box, labels and confidence.
3. Pin the R10 report, weight, corrected-val manifest and class map; preserve raw/corrected inputs.
4. Keep the package validation-only. It may diagnose but must never copy validation images,
   predictions or crops into train.
5. Independent QA must verify complete row/atlas coverage, geometry reconstruction, hash lineage,
   no test material and `sealed_test_accessed=false`.

## Candidate improvement tracks after D1-EA-R1 QA

### Track A — single-stage YOLO11s 54-class successor

- Mine hard negatives only from the existing training split or separately approved new training
  scenes, prioritizing visual patterns that resemble classes 10/12/23/30/46/39.
- Audit taxonomy/label consistency for the pairs 7↔17/18/49, 32↔7, 41↔39/40, 46↔10 and 8↔12.
- Add only train-derived, semantics-preserving augmentations; keep `fliplr=0` and never use val
  pixels for augmentation or pseudo-labeling.
- Freeze one change matrix before training, retain YOLO11s/1280/pretrained weight authority and use
  the QA-passed L4 capacity runner. First run a one-epoch smoke, then one pilot seed; do not launch
  three seeds until corrected validation passes the single-seed checks.

### Track B — one-class detector plus crop classifier baseline

- Detect `traffic_sign` independent of taxonomy, then classify each crop with a dedicated 54-class
  VN classifier and an explicit reject/unknown policy.
- This can separate localization from the large 46→10 and critical-class classification errors,
  but it changes the D-05 architecture/scope and needs an Owner decision plus classifier gates.
- It does not automatically fix background FP; the detector and classifier/reject stages each need
  validation evidence and end-to-end latency measurement.

## Recommendation

Proceed with D1-EA-R1 first. After visual QA, prepare two frozen smoke contracts: A as the primary
continuation and B as the comparison baseline already requested by the Owner. Do not spend L4 time
on unchanged seeds `20261019`/`20261020`. No new 100-epoch run is GO until the selected contract,
data delta, stop/resume behavior and acceptance criteria receive independent QA and the Owner
explicitly authorizes that run.
