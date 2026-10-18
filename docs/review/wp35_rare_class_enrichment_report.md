# M0-WP35 — real-frame augmentation for the 12 rare classes

Status: `WP35_REAL_FRAME_AUGMENTATION_AWAITING_QA`
Boundary: `TRAIN_ONLY_AUGMENTED_REAL_FRAMES_NOT_EVALUATION_EVIDENCE_NO_SPLIT_NO_TRAINING_RUN`

Implements D-04 part 1 as revised on 2026-10-17 (`docs/review/d04_owner_decision_part1_record.md`): the 12 one-group rare
classes are enriched only by transforming the original DATASET01 frames that contain them. No sign
is pasted or synthesised.

## Method

- **Geometry**: rotation ±5° and a zoom-in crop window of 55–95 % of the frame at a
  random offset, resized back to the original resolution. The window must stay inside the rotated
  frame (no padding or mirroring), must contain the target box (≥ 12 px) and must not cut
  any labelled sign: each box is fully inside or fully outside.
- **Photometry**: brightness, contrast, gamma, saturation, small hue shift (±4), haze (25 %),
  Gaussian or motion blur (50 %), Gaussian noise (40 %), JPEG quality 50–95.
- **No horizontal flip.** Boxes are transformed with the image and re-fitted axis-aligned.
- Labels keep every train-eligible WP33 box inside the window; excluded and UNKNOWN boxes stay
  unlabelled, exactly as in the source frame.
- When a sign sits at the frame edge and no window fits, the generator first drops the rotation
  and then falls back to photometry only (crop scale 1.000 in the lineage).
- Deterministic: seed `20261017`; `verify` regenerates every image and label byte-for-byte.

## Output

1800 augmented images, written to `data/processed/wp35_enrichment/` (git-ignored).

| Class | Real source frames | Augmented images |
| --- | --- | --- |
| `1` | 22 | 150 |
| `15` | 29 | 150 |
| `16:2.2` | 18 | 150 |
| `16:2.5` | 9 | 150 |
| `21` | 11 | 150 |
| `33` | 19 | 150 |
| `42` | 21 | 150 |
| `43:2.5` | 22 | 150 |
| `43:2.7` | 5 | 150 |
| `44` | 3 | 150 |
| `47` | 16 | 150 |
| `51` | 5 | 150 |

Source groups (10): D02-C0010, D02-C0013, D02-C0014, D02-C0015, D02-C0016, D02-C0019, D02-C0021, D02-C0022, D02-C0049, D02-C0053.
Preview: `docs/review/assets/wp35/preview.jpg` (original frame, then three augmented variants; target box in green).

## Limits

- Every augmented image shows the same physical sign as its source frame; augmentation widens
  viewing conditions but adds no new sign instance. Classes with 3–5 source frames (W.233,
  W.246c, W.239b 2,7 m) remain weak.
- Augmented images are **training only** and must never be used for validation, test, thresholds
  or any reported accuracy.
- The source groups above must be in the training split.
- The 12 classes stay `EVAL_PENDING_REAL_INDEPENDENT_DATA` and must not trigger automatic
  simulated vehicle behaviour until evaluated on real images from another location.

## Governance

D-04 part 1 only. Gate 0 remains BLOCKED (D-04 for the other 42 classes, G0.7, G0.9, D-05).
No split was generated and no training was run.
