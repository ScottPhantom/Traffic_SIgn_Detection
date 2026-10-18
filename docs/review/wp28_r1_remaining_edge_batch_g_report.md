# M0-WP28-R1 — D02-D remaining-edge manual reconciliation, Batch G correction

Status: `WP28_R1_AWAITING_QA_REVIEW`
Boundary: `REMAINING_EDGE_BATCH_G_R1_ONE_EDGE_QA_CORRECTION_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This R1 reissue preserves the immutable QA-failed M0-WP28 package and changes only the reviewed
decision/rationale for `edge_002306`. It also hardens JSON verification. It does not approve D-02,
create final/transitive group truth or a split, authorize training, or start WP29.

## QA failure and R1 correction lineage

- Initial independent QA verdict: **FAIL** with one `P1`, one `P2` and two `P3` findings and zero
  `P0`.
- Initial manifest SHA-256: `d5933d813a8788c2cb367b99b92d54eee7aa8e8ebbe171e424ce2834da6fdc0f`.
- Initial annotations SHA-256: `71be309b9a82d6f839dc875d71a74ab0072e2c1849b4d2eb60de1a677b578267`.
- Initial review-notes SHA-256: `56f02f8a70063ced5dfa9b259d41bfd8c10fc3a99b0071d4d0b42aa27c4122f9`.
- QA record: `docs/review/wp28_r1_qa_correction_record.md`.
- Trusted one-row correction-overlay SHA-256: `0fdf1ed29f62919650fe121fa7d87d5905f9732fa1cd06458dde01a114b5a0a4`.
- Corrected edge: `edge_002306`, Batch position 65, WP5 order 2599, stems 2331/2332, page 013
  slot 5. The labelled near standalone pole stack in 2331 has been passed; 2332 labels a smaller
  cls10 on a distinct arm structure with two round speed-limit discs.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED`, confidence `HIGH`. The other 249
  review decisions are unchanged.
- P2 hardening: layout, annotations and manifest must be canonical JSON bytes with no duplicate
  keys. P3: page `row_count` is checked explicitly.

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP28,
  `edge_002214` through `edge_002587`, with 500 endpoints and
  1464 bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage;
  `proxy_sequence_0050` is not selected.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R1 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Corrected capture outcomes

- `SAME_CAPTURE_CANDIDATE`: 250

## Corrected physical-sign outcomes

- `NOT_RELATED`: 15
- `SAME_PHYSICAL_SIGN_CANDIDATE`: 235

## Confidence

- `HIGH`: 249
- `MEDIUM`: 1

## Remaining workload and governance

- Canonical WP5 remains unchanged at 3172 PENDING edges.
- Outside the reviewed edge overlays, 396 PENDING
  edges remain, including the two quarantined stem-0248 adjacency edges; zero are cross-split.
- All 589 WP5 sequences remain PENDING.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.

## Artifacts

- Corrected decisions: `docs/review/wp28_r1_remaining_edge_review_annotations_batch_g.json`.
- Immutable selection reissue: `docs/review/generated/wp28_r1_remaining_edge_batch_g_selection.csv`.
- Source lineage: `docs/review/generated/wp28_r1_remaining_edge_batch_g_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp28_r1_remaining_edge_batch_g_layout_audit.json`.
- Atlas: `docs/review/assets/wp28_r1/remaining_edge_batch_g/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp28_r1_remaining_edge_batch_g_manifest.json`.
