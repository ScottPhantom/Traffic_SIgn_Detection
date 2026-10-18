# M0-WP25 — D02-D remaining-edge manual reconciliation, Batch D

Status: `WP25_AWAITING_QA_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_D_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This append-only package records one PM/Codex provisional visual pass over the exact next 250
review-eligible canonical residual PENDING edges after the QA-passed WP22, WP23-R1 and WP24 overlays.
It does not approve D-02, create final/transitive group truth or a split, or authorize training.

## Selection and review protocol

- Exact predecessor residual: 1,396 unique non-cross-split PENDING edges after removing the
  canonical cross-split overlays, WP22, WP23-R1 and WP24.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but stay outside
  WP25 because they touch stem `0248`.
- Selection: first 250 of 1,394 eligible residual rows in canonical WP5 order,
  `edge_001155` through `edge_001502`.
- Source coverage: 500 endpoint rows, 307 unique stems,
  1090 endpoint bbox occurrences and
  671 unique-stem bbox occurrences.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-14T03:08:58+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP25 atlas.
  Sequence evidence remained context-only and never derived an edge decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, all 50 JPEG pages and layout regenerate in isolation and byte/deep-compare.
- Trusted review-notes SHA-256 `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8` pins exact outcomes and
  exceptional IDs; predecessor packages are hash-pinned.

## Provisional capture outcomes

- `NOT_RELATED`: 10
- `SAME_CAPTURE_CANDIDATE`: 240

## Provisional physical-sign outcomes

- `NOT_RELATED`: 10
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 240

## Confidence

- `HIGH`: 250

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside the reviewed edge overlays, 1146 PENDING
  edges remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp25_remaining_edge_review_annotations_batch_d.json`.
- Selection: `docs/review/generated/wp25_remaining_edge_batch_d_selection.csv`.
- Source lineage: `docs/review/generated/wp25_remaining_edge_batch_d_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp25_remaining_edge_batch_d_layout_audit.json`.
- Atlas: `docs/review/assets/wp25/remaining_edge_batch_d/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp25_remaining_edge_batch_d_manifest.json`.
