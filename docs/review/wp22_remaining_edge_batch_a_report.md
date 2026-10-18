# M0-WP22 — D02-D remaining-edge manual reconciliation, Batch A

Status: `WP22_AWAITING_QA_REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_A_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This package records one PM/Codex provisional visual pass over the first 250 review-eligible
canonical residual PENDING edges after exact WP7/WP12-WP15 overlay removal. It does not approve
D-02, create final/transitive group truth or a split, or authorize training.

## Selection and review protocol

- Exact canonical residual: 2,146 unique PENDING edges after excluding six WP5-reviewed rows and
  the exact 1,026 QA-passed cross-split overlay rows; every residual edge has `cross_split=False`.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but are excluded
  because they touch stem `0248`; no quarantined source enters WP22 lineage.
- Selection: first 250 of the 2,144 review-eligible residual rows in canonical WP5 order,
  `edge_000002` through `edge_000378`.
- Source coverage: 500 endpoint rows with 903 total boxes.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-12T01:50:32+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP22 atlas.
  WP16-WP21 sequence evidence is pinned context/risk information only and never derives an edge
  decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, 50 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `c49c00bc85bbc0bc1cfc4683d9dbbd6403705a42600a1251e46e7ade949c6a27` pins exact outcomes and exceptional
  IDs; predecessor edge and sequence packages are hash-pinned.

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
- Outside WP7/WP12-WP15/WP22 overlays, 1896 PENDING edges
  remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp22_remaining_edge_review_annotations_batch_a.json`.
- Selection: `docs/review/generated/wp22_remaining_edge_batch_a_selection.csv`.
- Source lineage: `docs/review/generated/wp22_remaining_edge_batch_a_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp22_remaining_edge_batch_a_layout_audit.json`.
- Atlas: `docs/review/assets/wp22/remaining_edge_batch_a/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp22_remaining_edge_batch_a_manifest.json`.
