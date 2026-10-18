# M0-WP23 — D02-D remaining-edge manual reconciliation, Batch B

Status: `WP23_AWAITING_QA_REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_B_PM_PROVISIONAL_VISUAL_REVIEW_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This package records one PM/Codex provisional visual pass over the next 250 review-eligible
canonical residual PENDING edges after exact WP7/WP12-WP15 and WP22 overlay removal. It does not
approve D-02, create final/transitive group truth or a split, or authorize training.

## Selection and review protocol

- Exact canonical residual: 1,896 unique PENDING edges after excluding six WP5-reviewed rows, the
  exact 1,026 QA-passed cross-split overlay rows, and the exact 250-row WP22 Batch-A roster; every
  residual edge has `cross_split=False`.
- Quarantine exclusion: `edge_000242` and `edge_000243` remain residual/PENDING but are excluded
  because they touch stem `0248`; no quarantined source enters WP23 lineage.
- Selection: first 250 of the 1,894 review-eligible residual rows in canonical WP5 order,
  `edge_000379` through `edge_000760`.
- Source coverage: 500 endpoint rows with 1556 total boxes.
- Reviewer: `PM/Codex provisional visual reviewer` at `2026-10-12T03:40:28+07:00`.
- All 250 pairs/500 raw frames were directly inspected in the dedicated 50-page WP23 atlas.
  WP16-WP21 sequence evidence is pinned context/risk information only and never derives an edge
  decision or group truth.

## Hardened verifier contract

- Exact 51-file atlas roster; extra/missing/wrong-type/symlink/path attacks fail closed.
- Index, 50 JPEG pages and layout are regenerated in isolation and byte/deep-compared.
- Trusted review-notes SHA-256 `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8` pins exact outcomes and exceptional
  IDs; predecessor edge and sequence packages are hash-pinned.

## Provisional capture outcomes

- `NOT_RELATED`: 17
- `SAME_CAPTURE_CANDIDATE`: 233

## Provisional physical-sign outcomes

- `NOT_RELATED`: 17
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 233

## Confidence

- `HIGH`: 250

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside WP7/WP12-WP15/WP22/WP23 overlays,
  1646 PENDING edges remain, including the two quarantined
  stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Decisions: `docs/review/wp23_remaining_edge_review_annotations_batch_b.json`.
- Selection: `docs/review/generated/wp23_remaining_edge_batch_b_selection.csv`.
- Source lineage: `docs/review/generated/wp23_remaining_edge_batch_b_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp23_remaining_edge_batch_b_layout_audit.json`.
- Atlas: `docs/review/assets/wp23/remaining_edge_batch_b/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp23_remaining_edge_batch_b_manifest.json`.
