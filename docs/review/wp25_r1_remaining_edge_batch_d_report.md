# M0-WP25-R1 — D02-D remaining-edge manual reconciliation, Batch D correction

Status: `WP25_R1_AWAITING_QA_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_D_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This R1 reissue preserves the immutable QA-failed M0-WP25 package and changes only the reviewed
decision/rationale for `edge_001358`. It does not approve D-02, create final/transitive group truth
or a split, authorize training, or start WP26.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL**, exactly one `P1` finding and zero
  `P0`/`P2`/`P3` findings; technical/integrity checks remained PASS.
- Initial manifest SHA-256: `1d7b04d6432424297f2e14178dd59936526dec7d6293872fbda0010bb460e5e9`.
- Initial annotations SHA-256: `990d314a462a2279d9600f2b6b5e2b12c1da73dd7425e7ec07a388d883487cc5`.
- Initial review-notes SHA-256: `b3b97a12577351ef7019f2793a0b7b988f8e7ffddb5929ae7c255a0d7e69a6b8`.
- QA record: `docs/review/wp25_r1_qa_correction_record.md`.
- Trusted one-row correction-overlay SHA-256: `a1385c5a295b927887ffe73c29987d1c3487812d7d25b1a3aa9688c25f39ecd9`.
- Corrected edge: `edge_001358`, Batch position 144, WP5 order 1928, stems 1365/1366,
  page 029 slot 4.
- QA evidence: same moving camera advances within one road scene and the same class-5 physical
  sign remains visible; class-5 bbox center/size changes from
  `(0.388021, 0.303704)/(0.036458, 0.055556)` to
  `(0.406250, 0.313889)/(0.037500, 0.046296)`; same dimensions, `uncertain` proxy,
  MAE `12.005787`, dHash `18`, histogram `0.99375935`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence
  `HIGH`. The other 249 review decisions are unchanged.

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP25,
  `edge_001155` through `edge_001502`, with 500 endpoints and
  1090 bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.

## Corrected capture outcomes

- `NOT_RELATED`: 9
- `SAME_CAPTURE_CANDIDATE`: 241

## Corrected physical-sign outcomes

- `NOT_RELATED`: 9
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 241

## Confidence

- `HIGH`: 250

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside WP7/WP12-WP15/WP22/WP25-R1 overlays, 1146
  PENDING edges remain, including the two quarantined stem-0248 adjacency edges; zero are
  cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `docs/review/wp25_r1_remaining_edge_review_annotations_batch_d.json`.
- Immutable selection reissue: `docs/review/generated/wp25_r1_remaining_edge_batch_d_selection.csv`.
- Source lineage: `docs/review/generated/wp25_r1_remaining_edge_batch_d_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp25_r1_remaining_edge_batch_d_layout_audit.json`.
- Atlas: `docs/review/assets/wp25_r1/remaining_edge_batch_d/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp25_r1_remaining_edge_batch_d_manifest.json`.
