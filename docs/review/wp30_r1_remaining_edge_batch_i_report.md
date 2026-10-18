# M0-WP30-R1 — D02-D remaining-edge manual reconciliation, final Batch I correction

Status: `WP30_R1_AWAITING_QA_REVIEW`
Boundary: `REMAINING_EDGE_BATCH_I_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This R1 reissue preserves the immutable QA-failed M0-WP30 package and changes only the reviewed
decision/rationale for `edge_003047`. It does not approve D-02, create final/transitive group
truth or a split, or authorize training.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL** with one `P1` and one non-blocking `P3` (inherited
  WP12 error-message text) and zero `P0`/`P2`.
- Initial manifest SHA-256: `c906e22fc48678308e54ace0363735a97d7f482eb13135822e39bd67b2ad54f0`.
- Initial annotations SHA-256: `a85a6b24e4962a76a17240815d501bddcf3795ff38955293c683565e0d2cf590`.
- Initial review-notes SHA-256: `488c69d1f5c9b59838bbde57e9861be7c1fb431749f7fc6e78608ff0fe28551c`.
- QA record: `docs/review/wp30_independent_qa_record.md` (SHA-256 `f9147fd604dbb17c85fb07ea69faad89c1fe188e2554791a52c3eebe86a7136d`).
- Trusted one-row correction-overlay SHA-256: `46e7325abede0f864006372b7fdc8962f1404c77bc10e0768834168a5264d3c3`.
- Corrected edge: `edge_003047`, Batch position 53, WP5 order 3087, stems 3084/3085, page 011
  slot 3. The scene changes, but the same ride companions seen in stems 3000–3076 continue in
  3085, so the frames are a gapped single ride as in WP29 `edge_002967`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED`, confidence `MEDIUM`. The other
  143 review decisions are unchanged.
- Every selection row and evidence reference is bound to the R1 atlas and R1 boundary.

## Selection and evidence boundary

- Selection remains the exact same 144 canonical rows as initial WP30,
  `edge_002973` through `edge_003176`, with 288 endpoints and
  888 bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage;
  `proxy_sequence_0050` is not selected.
- All 144 pairs/288 raw frames remain represented in the deterministic 29-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Corrected capture outcomes

- `NOT_RELATED`: 3
- `SAME_CAPTURE_CANDIDATE`: 141

## Corrected physical-sign outcomes

- `NOT_RELATED`: 5
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 139

## Confidence

- `HIGH`: 142
- `MEDIUM`: 2

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside the reviewed edge overlays, 2 PENDING
  edges remain: only the two quarantined stem-0248 adjacency edges; zero are review-eligible.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `docs/review/wp30_r1_remaining_edge_review_annotations_batch_i.json`.
- Selection reissue bound to the R1 atlas: `docs/review/generated/wp30_r1_remaining_edge_batch_i_selection.csv`.
- Source lineage: `docs/review/generated/wp30_r1_remaining_edge_batch_i_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp30_r1_remaining_edge_batch_i_layout_audit.json`.
- Atlas: `docs/review/assets/wp30_r1/remaining_edge_batch_i/index.html` and 29 JPEG pages.
- Manifest: `docs/review/generated/wp30_r1_remaining_edge_batch_i_manifest.json`.
