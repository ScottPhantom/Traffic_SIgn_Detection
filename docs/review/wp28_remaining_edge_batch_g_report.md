# M0-WP28 — D02-D remaining-edge manual reconciliation, Batch G

Status: `WP28_AWAITING_QA_REVIEW`
Boundary: `REMAINING_EDGE_BATCH_G_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This append-only package records one PM provisional visual pass over the exact next 250
review-eligible canonical residual PENDING edges after the QA-passed WP22, WP23-R1, WP24,
WP25-R1, WP26 and WP27-R2 overlays. It does not approve D-02, create final/transitive group
truth or a split, or authorize training.

## Selection and review protocol

- Exact predecessor residual: 646 unique non-cross-split PENDING edges after removing the
  canonical cross-split overlays and the six QA-passed remaining-edge prefixes.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but stay outside
  WP28 because they touch stem `0248`; `proxy_sequence_0050` is not selected.
- Selection: first 250 of 644 eligible residual rows in canonical WP5 order,
  `edge_002214` through `edge_002587`.
- Source coverage: 500 endpoint rows, 305 unique stems,
  1464 endpoint bbox occurrences and
  889 unique-stem bbox occurrences.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-16T17:40:00+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP28 atlas.
  Sequence evidence remained context-only and never derived an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Hardened verifier contract

- Layout status is the exact `PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`; the inherited verifier is reused with
  only its stale 176-pair status constant replaced, and layout/annotation JSON is checked
  type-strictly before the inherited byte/deep comparison.
- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, all 50 JPEG pages and layout regenerate in isolation and byte/deep-compare.
- Trusted review-notes SHA-256 `56f02f8a70063ced5dfa9b259d41bfd8c10fc3a99b0071d4d0b42aa27c4122f9` pins exact outcomes and
  exceptional IDs; QA-passed WP27 Batch F with its R1/R2 corrections and full immutable
  predecessor lineage are hash-pinned.

## Provisional capture outcomes

- `SAME_CAPTURE_CANDIDATE`: 250

## Provisional physical-sign outcomes

- `NOT_RELATED`: 14
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 236

## Confidence

- `HIGH`: 248
- `MEDIUM`: 2

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside the reviewed edge overlays, 396 PENDING
  edges remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp28_remaining_edge_review_annotations_batch_g.json`.
- Selection: `docs/review/generated/wp28_remaining_edge_batch_g_selection.csv`.
- Source lineage: `docs/review/generated/wp28_remaining_edge_batch_g_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp28_remaining_edge_batch_g_layout_audit.json`.
- Atlas: `docs/review/assets/wp28/remaining_edge_batch_g/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp28_remaining_edge_batch_g_manifest.json`.
