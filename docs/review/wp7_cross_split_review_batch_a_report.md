# M0-WP7 — Cross-split visual adjudication pilot, Batch A

Status: `WP7_AWAITING_QA_BATCH_A_PM_PROVISIONAL_REVIEW`  
Boundary: `BATCH_A_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This package records one PM/Codex provisional visual pass over exactly 100 canonical WP5 pending cross-split pairs. It does not approve D02-B, does not create final group truth or a split, and does not authorize training. D02-A creator/session metadata remains preferred.

## Selection and review protocol

- Selection: first 100 unique rows where canonical WP5 has `cross_split=True` and `review_status=PENDING`, preserving WP5 review order and excluding all six previously reviewed edges.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-11T06:20:00+07:00`.
- Every outcome was assigned only after both source images were visually inspected in the dedicated WP7 atlas. Proxy fields were context only.
- Creator/session/physical-sign identity metadata: unavailable for every record.

## Provisional outcomes

- `NOT_RELATED`: 2
- `SAME_CAPTURE_CANDIDATE`: 98

## Confidence

- `HIGH`: 99
- `MEDIUM`: 1

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges until this separate package receives QA review.
- Outside this 100-pair pilot, 3072 edges remain unreviewed; 926 of those are cross-split under the pilot overlay count.
- All 589 WP5 sequences remain PENDING.
- Any future PM/QA disagreement remains unresolved/uncertain and cannot form a positive component.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp7_visual_review_annotations_batch_a.json`.
- Selection: `docs/review/generated/wp7_batch_a_selection.csv`.
- Layout audit: `docs/review/generated/wp7_batch_a_layout_audit.json`.
- Atlas: `docs/review/assets/wp7/batch_a/index.html` and 20 JPEG pages.
- Manifest: `docs/review/generated/wp7_batch_a_manifest.json`.
