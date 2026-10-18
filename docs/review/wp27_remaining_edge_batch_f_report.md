# M0-WP27 — D02-D remaining-edge manual reconciliation, Batch F

Status: `WP27_AWAITING_QA_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_F_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This append-only package records one PM/Codex provisional visual pass over the exact next 250
review-eligible canonical residual PENDING edges after the QA-passed WP22, WP23-R1, WP24,
WP25-R1 and WP26 overlays. It does not approve D-02, create final/transitive group truth or a
split, or authorize training.

## Selection and review protocol

- Exact predecessor residual: 896 unique non-cross-split PENDING edges after removing the
  canonical cross-split overlays and the five QA-passed remaining-edge prefixes.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but stay outside
  WP27 because they touch stem `0248`.
- Selection: first 250 of 894 eligible residual rows in canonical WP5 order,
  `edge_001851` through `edge_002213`.
- Source coverage: 500 endpoint rows, 306 unique stems,
  1069 endpoint bbox occurrences and
  650 unique-stem bbox occurrences.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-16T10:31:20+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP27 atlas.
  Sequence evidence remained context-only and never derived an edge decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, all 50 JPEG pages and layout regenerate in isolation and byte/deep-compare.
- Trusted review-notes SHA-256 `2635a14140fb4d7dd82c2a0118707db1553babfafb322285ac36722d5f6a7ff8` pins exact outcomes and
  exceptional IDs; QA-passed WP26 and its full immutable predecessor lineage are hash-pinned.

## Provisional capture outcomes

- `NOT_RELATED`: 3
- `SAME_CAPTURE_CANDIDATE`: 247

## Provisional physical-sign outcomes

- `NOT_RELATED`: 21
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 229

## Confidence

- `HIGH`: 250

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside the reviewed edge overlays, 646 PENDING
  edges remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp27_remaining_edge_review_annotations_batch_f.json`.
- Selection: `docs/review/generated/wp27_remaining_edge_batch_f_selection.csv`.
- Source lineage: `docs/review/generated/wp27_remaining_edge_batch_f_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp27_remaining_edge_batch_f_layout_audit.json`.
- Atlas: `docs/review/assets/wp27/remaining_edge_batch_f/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp27_remaining_edge_batch_f_manifest.json`.
