# M0-WP23-R1 — D02-D remaining-edge manual reconciliation, Batch B correction

Status: `WP23_R1_AWAITING_QA_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_B_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This R1 reissue preserves the immutable QA-failed M0-WP23 package and changes only the reviewed
decision/rationale for `edge_000664`. It does not approve D-02, create final/transitive group truth
or a split, authorize training, or start WP24.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL**, exactly one High finding and zero
  Critical/Medium/Low findings; technical/integrity checks remained PASS.
- Initial manifest SHA-256: `dec19a75bb2def4d29afabe36963f7cdfd474b5c2bdd556e8c40ec198a8f09dd`.
- Initial annotations SHA-256: `2720ac892a9f0ebe46dc027a722702031a8519aaa856965d560da99d85e2c7be`.
- Initial review-notes SHA-256: `c9159a36096f11c409e1c88ad49d15947ed052db7d5e4fddb310647f47a113c8`.
- QA record: `docs/review/wp23_r1_qa_correction_record.md`.
- Trusted one-row correction-overlay SHA-256: `f12ce41c8290bab9808522b24fa96e460f53ff81ba0b466240c21635b77994b8`.
- Corrected edge: `edge_000664`, WP5 order 1476, stems 0671/0672, page 039 slot 2.
- QA evidence: same camera advances slightly in one scene; identical annotated class sets
  `7 10 17 19 44`; `strong_candidate`, MAE `6.303241`, dHash `6`, histogram `0.99600903`.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE`, confidence
  `HIGH`. The other 249 review decisions are unchanged.

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP23,
  `edge_000379` through `edge_000760`, with 500 endpoints and
  1556 bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.

## Corrected capture outcomes

- `NOT_RELATED`: 16
- `SAME_CAPTURE_CANDIDATE`: 234

## Corrected physical-sign outcomes

- `NOT_RELATED`: 16
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 234

## Confidence

- `HIGH`: 250

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside WP7/WP12-WP15/WP22/WP23-R1 overlays, 1646
  PENDING edges remain, including the two quarantined stem-0248 adjacency edges; zero are
  cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `docs/review/wp23_r1_remaining_edge_review_annotations_batch_b.json`.
- Immutable selection reissue: `docs/review/generated/wp23_r1_remaining_edge_batch_b_selection.csv`.
- Source lineage: `docs/review/generated/wp23_r1_remaining_edge_batch_b_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp23_r1_remaining_edge_batch_b_layout_audit.json`.
- Atlas: `docs/review/assets/wp23_r1/remaining_edge_batch_b/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp23_r1_remaining_edge_batch_b_manifest.json`.
