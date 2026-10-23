# D1-VRL-R1 — validation relabel: scope and owner authorization

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)
Status: `OWNER_AUTHORIZED_BUILD__ADOPTION_PENDING_QA_AND_OWNER_ACCEPTANCE`

## Authorization

On 2026-10-22, in the Claude Code session, the owner instructed "Bắt đầu relabel val" ("start the
validation relabel"). This followed the D1-VLA-R1 independent QA (PASS) and its correction R1. The
instruction authorizes **building** a derived validation label set, D1-VRL-R1.

It does **not** make the derived labels the evaluation authority. That requires, in order:

1. independent QA of D1-VRL-R1;
2. a separate owner acceptance record;
3. a QA-passed re-evaluation contract.

## Scope (the author's proposal, applied unless the owner objects)

- **Boxes added.** The 104 HIGH/MEDIUM in-taxonomy boxes of
  `docs/review/generated/d1_vla_r1_proposed_val_labels.csv`, across 59 frames.
- **Not added:**
  - the 10 LOW warning triangles (1352–1357), the 2 LOW partial P.102 boxes, and any `UNCLEAR`
    item;
  - out-of-taxonomy boards (camera boards, guide boards, the hotline board). These are a separate
    D-03/D-04 question.
- **Classes.** Use the D-03 derived keys from the D1-VLA-R1 notes, written as YOLO ids through
  `docs/review/generated/m1_yolo_classes.csv` (QA L2). The "3.5t" disc stays class 14, following
  the neighbouring ground truth (QA L3).
- **Box geometry (QA M1).**
  - The model's box is used only to locate the sign.
  - The written box is re-fitted from the image pixels: the sign's red or blue region near the
    locator.
  - Every re-fitted box is checked visually.
  - Boxes that cannot be re-fitted reliably are entered by hand, or dropped with a reason.
  - The IoU between each re-fitted box and the model's box is reported, so that a later
    re-evaluation is not matching the model against its own boxes.
- **Append-only.**
  - Raw labels and the WP38-R1 R4 export stay unchanged.
  - The derived validation labels are written as a new directory under `data/processed/`
    (git-ignored), with a tracked CSV, a manifest and hashes.
  - Train and test labels are not touched.
- **Validation only.** The derived labels are never used for training, augmentation or mining.
  The sealed test stays closed.

## Not decided here

- Whether D-05 evaluation switches to the derived validation labels.
- Any change to gates, NMS or confidence, any training run, and the sealed test.

## Owner decision on box geometry (2026-10-22, append-only)

Pixel re-fitting found a reliable red or blue region for 32 of the 104 proposals. The other 72 are
11–17 px low-saturation discs on the 1208–1229 and 1342–1357 poles. On the existing small
ground-truth boxes, a grayscale fallback agreed with the human box only 47 % of the time.

The owner decided:

- **The 72 small boxes become ignore regions.** No ground truth is added for them. An unmatched
  prediction whose area lies at least half inside an ignore region is not counted as a false
  positive.
- **The 32 re-fitted boxes are used only after a visual check.** The author checked them
  (`docs/review/d1_vrl_r1_box_review_notes.csv`):
  - 26 are accepted;
  - 6 re-fits cover only part of the sign (R040, R042, R044, R049, R090, R091). Following the same
    rule, these also become ignore regions.

Result: 26 added ground-truth boxes and 78 ignore regions.
