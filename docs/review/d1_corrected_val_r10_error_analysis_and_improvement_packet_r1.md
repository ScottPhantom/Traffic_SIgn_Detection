# D1 corrected validation R10 — error analysis and improvement packet R1

Date: 2026-10-22  
Status: `REMEDIATED_AWAITING_INDEPENDENT_QA`

R1 supersedes the immutable QA-failed initial packet. It corrects the prediction-count wording and
the already-approved scope of the dual-baseline Owner decision.

Pinned predecessor evidence:

- Initial packet SHA-256:
  `2ce6d44458bedc4692edf38380748aa1652c6a5d0d7a80fa0b4dbf9c1d26feac`
- Initial packet QA FAIL record SHA-256:
  `89ebb22aeb8b21f38e4fcea3d4ae49d40a188642cf3f56afb11d7ab917c5a984`
- Dual-baseline Owner decision SHA-256:
  `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2`
- R10 result SHA-256:
  `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5`
- R10 result QA PASS record SHA-256:
  `9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2`

## Evidence boundary

This packet uses only the independently QA-passed R10 validation report. It does not use the
sealed test, relabel validation, add validation pixels to training or authorize a new run.

The report stores a full confusion matrix and bounded stem samples, not every predicted box or a
visual false-positive atlas. Counts below are verified; visual root-cause explanations remain
hypotheses until a separate validation-only prediction/atlas package is built and QA reviewed.

## Confirmed failure structure at confidence 0.20

At the selected operating point there are **697 retained predictions**: 483 class-agnostic
true-positive matches plus 214 false positives. There are 77 unmatched ground-truth boxes over 376
images / 560 boxes. Recall is 0.8625 and FP/image is 0.5691.

The selector chooses the lowest-FP grid point among candidates whose class-agnostic recall is at
least 0.85. Therefore the existing threshold grid did not contain a point satisfying both the
current recall and FP/image gates.

### Background false positives

| Predicted class | Background FP | Share of 214 |
| --- | ---: | ---: |
| 10 | 53 | 24.8% |
| 12 | 44 | 20.6% |
| 23 | 35 | 16.4% |
| 30 | 19 | 8.9% |
| 46 | 13 | 6.1% |
| 39 | 12 | 5.6% |

These six classes account for 176/214 = 82.2% of background false positives. This supports a
targeted training-only hard-negative investigation instead of a blind epoch increase.

### Supported critical classes

| GT class | Support | Correct-class gate recall | Confusion diagnostic |
| --- | ---: | ---: | --- |
| 7 | 111 | 0.5946 | 36 paired as background; 10 predicted 17, 2 predicted 18, 1 predicted 49 |
| 32 | 29 | 0.6207 | 6 predicted 7; 5 paired as background |
| 41 | 21 | 0.5714 | 6 predicted 39; 2 predicted 40; 2 paired as background |

The confusion matrix uses score-ordered class-agnostic one-to-one pairing for diagnostics. D-05
per-class recall uses a separate class-aware matcher. Exact confusion diagonal/miss counts therefore
need not reproduce `gates.classes[*].hits`; both follow their documented contracts.

### Other high-impact evidence

- GT class 46: 58/104 pairs are predicted as class 10; 42 are on the class-46 diagonal and 4 pair
  to background. Its class-aware gate recall 0.5288 only narrowly passes the non-critical 0.50 gate.
- GT class 8: 6/51 are predicted as class 12 and 15 pair to background.
- Current train labels contain 228 boxes for class 7, 138 for class 32, 610 for class 41, 1,431 for
  class 10 and 427 for class 46. More copies of the same distribution are not by themselves an
  evidence-backed remedy.

## Required next evidence package — D1-EA-R1

Before changing training, build a validation-only immutable package that:

1. Exports every prediction at the locked diagnostic point (`conf=0.20`, NMS IoU 0.70), including
   stem, predicted class, confidence, box, matched GT class/IoU or background disposition.
2. Produces contact sheets covering all 214 background FP, all class 7/32/41 errors, and the 46→10
   and 8→12 pairs with source image, predicted/GT boxes, labels and confidence.
3. Pins the R10 report, weight, corrected-val manifest and class map; preserves all inputs.
4. Remains diagnosis-only: no validation image, crop, prediction or pseudo-label may enter train.
5. Passes independent QA for complete roster/atlas coverage, geometry reconstruction, hash lineage,
   no test material and `sealed_test_accessed=false`.

## Authorized improvement tracks after D1-EA-R1 QA

### Track A — primary 54-class YOLO11s successor

- Mine hard negatives only from the training split or separately approved new training scenes,
  prioritizing patterns visually similar to classes 10/12/23/30/46/39.
- Audit taxonomy/label consistency for 7↔17/18/49, 32↔7, 41↔39/40, 46↔10 and 8↔12.
- Use only train-derived, semantics-preserving augmentation; keep `fliplr=0`; never use val pixels
  for augmentation or pseudo-labeling.
- Freeze a one-change matrix before training, preserve YOLO11s/1280/pretrained authority and use
  the QA-passed L4 runner. One-epoch smoke precedes one pilot seed. Three seeds remain blocked until
  the corrected single-seed validation checks pass.

### Track B — Owner-approved comparison baseline

The Owner decision dated 2026-10-18 already authorizes building and validating a one-class traffic
sign detector plus crop classifier on train/validation data. No new architecture approval is needed
for that bounded comparison baseline.

- The detector localizes `traffic_sign`; the classifier predicts the VN class and applies an
  explicit reject/unknown policy.
- This separates localization from large classification confusions such as 46→10, but does not
  automatically solve background FP. Detector, classifier/reject and end-to-end latency each need
  validation evidence.
- Before any final/sealed-test evaluation, an append-only Owner-approved addendum must still define
  classifier taxonomy, acceptance gates, threshold protocol and sealed-test eligibility. Track B
  does not inherit 54-class D-05 per-class gates silently.

## Recommendation and authorization boundary

Proceed with D1-EA-R1 first. After visual QA, freeze two smoke contracts: Track A as the primary
continuation and Track B as the already Owner-approved comparison baseline. Do not spend L4 time on
unchanged seeds `20261019`/`20261020`.

This packet does not authorize smoke, training, new seeds or sealed-test access. A new run is GO only
after its exact data delta, experiment contract, recovery behavior and validation acceptance rules
pass independent QA and the existing run-authorization workflow is satisfied. The sealed test
remains closed.
