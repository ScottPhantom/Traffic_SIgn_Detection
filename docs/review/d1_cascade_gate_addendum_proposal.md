# D1 cascade baseline gate addendum proposal

Status: `PROPOSAL_NOT_OWNER_APPROVED`
Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

## Scope

The Owner approved a comparison baseline consisting of a one-class traffic-sign detector followed
by a crop classifier. This proposal defines how that cascade could be evaluated. It does not amend
D-05, authorize sealed-test access or approve a classifier architecture.

The primary 54-class YOLO baseline remains governed by the existing D-05 record. Results from the
cascade may not be substituted for the primary baseline's per-class detector gates.

## Components and evidence units

1. **Detector:** YOLO with one class, `traffic_sign`, trained on the exact M1 train/validation
   frames and boxes. It measures localization without class identity.
2. **Classifier:** a new 54-output crop classifier trained on
   `data/processed/dataset01_crops/train.p`. The retained E0 model is not eligible because it is a
   43-class GTSRB model and does not implement the WP33 taxonomy.
3. **Cascade:** detector boxes are cropped from the original frame and classified. A ground-truth
   sign is correct only when one predicted box matches at IoU >= 0.50 and its predicted WP33 class
   is exact.

Every component must have its own run contract, seed, dataset/split hashes, thresholds, metrics and
latency. The cascade report must retain the detector-versus-classifier failure decomposition.

## Proposed validation protocol

These are validation targets for feasibility review, not final gates:

| Component | Validation evidence |
| --- | --- |
| One-class detector | mAP50, mAP50-95, AP-small, class-agnostic recall, FP/image, resolution breakdown and M1 Pro p95 latency |
| Crop classifier | top-1 accuracy, macro-F1, balanced accuracy, per-class recall/support and calibration error on the 19 classes represented in validation |
| Cascade | exact-label recall per ground-truth box, wrong-box/wrong-class/missed decomposition, false labeled signs per image and full-pipeline p95 latency |

Thresholds may be selected only on validation. The 35 classes absent from validation cannot drive
classifier selection or threshold tuning. WP35 is train-only and may not be counted as independent
validation evidence. Three fixed seeds (`20261018`, `20261019`, `20261020`) are proposed for any
candidate promoted beyond smoke.

## Proposed sealed-test prerequisites

The cascade remains ineligible for the sealed test until the Owner approves an append-only
successor containing numeric gates. Before that decision, PM must provide:

- one-class detector pilot metrics on validation;
- 54-class classifier pilot metrics on validation with support-aware limitations;
- cascade validation metrics and failure decomposition;
- locked detector, classifier and rejection thresholds;
- a full-pipeline latency report on the M1 Pro;
- an explicit policy for the 22 classes without sealed-test support and all classes that fail an
  approved gate.

UNKNOWN/OOD behavior is not established by this baseline. Classes without evidence must remain
`unverified` and may not trigger simulated vehicle behavior. No real-vehicle or safety claim is
permitted.

## Decision requested later

After the validation pilot exists, the Owner must either approve numeric cascade gates, revise
them once without seeing test results, or keep the cascade as a validation-only comparison. Until
then, no cascade test crop, test label, test metric or final comparison may be produced.
