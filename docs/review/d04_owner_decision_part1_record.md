# D-04 owner decision, part 1 — rare classes kept with data enrichment

Status: `OWNER_APPROVED_PART_1_OF_D04`
Decision date: `2026-10-17` (`Asia/Ho_Chi_Minh`)
Decision table: `docs/review/generated/d04_owner_decisions_part1.csv`

The owner rejected the WP34 proposal `DROP_FROM_V1_COLLECT_MORE` for the 12 WP33 classes with one
independent D-02 group and fewer than 30 images (W.205c, W.203c, P.117 2,2 m and 2,5 m, W.203b,
W.202b, R.301e, W.239b 2,5 m and 2,7 m, W.233, P.124b, W.246c). Reason: for a Vietnamese
driver-assistance system, missing a sign type entirely is worse than an imperfect detector.

## Decision

- All 12 classes are trained, with their training data enriched by synthetic images
  (QCVN 41:2024 template rendering and real-crop copy-paste with augmentation, package M0-WP35).
- Evaluation status: `EVAL_PENDING_REAL_INDEPENDENT_DATA`. Synthetic images are never used for
  validation or test. Each class needs real images from at least one other physical location
  before its accuracy can be reported.
- Behaviour gate: predictions of these classes are shown as "unverified" and must not trigger
  automatic simulated vehicle behaviour until the class has been evaluated on real independent data.
- Split constraint: the D-02 groups holding these classes, and every group used as a background
  for their synthetic images, must be placed in the training split.

## Not decided here

The other 42 classes (WP34 options `KEEP_FULL`, `KEEP_TRAIN_AND_TEST_NO_VAL`,
`KEEP_TRAIN_ONLY_UNVERIFIED`) remain pending, and WP34 must still be corrected (WP34-R1) for its
QA findings. G0.8 stays BLOCKED until every class has an owner decision. No split was generated and
training is not authorized.

## Revision 2026-10-17 (append-only): enrichment method

The owner rejected pasting signs (QCVN templates or real crops) onto other frames, because it
creates implausible scenes such as signs on vehicles or floating in the sky. Enrichment for the 12
classes is limited to transformations of the original DATASET01 frames that contain them: small
rotation, zoom-in crops with offset, rescaling, colour, brightness, contrast, gamma, haze, noise,
Gaussian and motion blur, and JPEG re-compression. No horizontal flip and no synthetic sign
insertion. Bounding boxes are transformed with the image. All other conditions above are unchanged.
