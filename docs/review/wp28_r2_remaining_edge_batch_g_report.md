# M0-WP28-R2 — D02-D remaining-edge manual reconciliation, Batch G evidence-binding reissue

Status: `WP28_R2_AWAITING_QA_REVIEW`  
Boundary: `REMAINING_EDGE_BATCH_G_R2_EVIDENCE_BINDING_REISSUE_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

This R2 reissue preserves the immutable QA-failed M0-WP28 and M0-WP28-R1 packages. It keeps the
R1 decisions unchanged (only `edge_002306` differs from initial WP28) and binds every selection
row and evidence reference to the WP28-R2 atlas. It does not approve D-02, create
final/transitive group truth or a split, authorize training, or start WP29.

## QA failure and R2 correction lineage

- Initial WP28 QA: **FAIL** (one `P1` on `edge_002306`, one `P2`, two `P3`).
- WP28-R1 QA: **FAIL** with zero `P0`/`P1`, one `P2` and three `P3`; QA agreed with every
  decision. P2: all R1 evidence references still cited the superseded initial atlas because the
  initial builder stamps atlas paths from its own module globals.
- Initial manifest SHA-256: `d5933d813a8788c2cb367b99b92d54eee7aa8e8ebbe171e424ce2834da6fdc0f`.
- WP28-R1 manifest SHA-256: `2dc57da89791e13602a0a6be04b8464cbc64727c84199571e921d7e414aab83b`.
- QA records: `docs/review/wp28_r1_qa_correction_record.md` and `docs/review/wp28_r2_qa_correction_record.md`.
- Trusted one-row correction overlay reused from WP28-R1, SHA-256 `0fdf1ed29f62919650fe121fa7d87d5905f9732fa1cd06458dde01a114b5a0a4`.
- Corrected edge (unchanged from R1): `edge_002306`, Batch position 65, WP5 order 2599, stems
  2331/2332, page 013 slot 5: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED`, confidence `HIGH`.
- R2 hardening: every row differs from the initial selection in exactly `wp12_atlas_page` and
  `evidence_boundary`; every atlas evidence reference cites `docs/review/assets/wp28_r2/remaining_edge_batch_g`; layout,
  annotations and manifest must match canonical JSON bytes exactly (no duplicate keys, no CRLF/CR).

## Selection and evidence boundary

- Selection remains the exact same 250 canonical rows as initial WP28,
  `edge_002214` through `edge_002587`, with 500 endpoints and
  1464 bbox occurrences.
- `edge_000242` and `edge_000243` remain quarantined/PENDING and outside lineage;
  `proxy_sequence_0050` is not selected.
- All 250 pairs/500 raw frames remain represented in the deterministic 50-page R2 atlas.
- Sequence evidence remains context only and never derives an edge decision or group truth.
  Capture relation and physical-sign relation are recorded separately.

## Capture outcomes

- `SAME_CAPTURE_CANDIDATE`: 250

## Physical-sign outcomes

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

- Decisions: `docs/review/wp28_r2_remaining_edge_review_annotations_batch_g.json`.
- Selection reissue: `docs/review/generated/wp28_r2_remaining_edge_batch_g_selection.csv`.
- Source lineage: `docs/review/generated/wp28_r2_remaining_edge_batch_g_source_lineage.csv`.
- Layout audit: `docs/review/generated/wp28_r2_remaining_edge_batch_g_layout_audit.json`.
- Atlas: `docs/review/assets/wp28_r2/remaining_edge_batch_g/index.html` and 50 JPEG pages.
- Manifest: `docs/review/generated/wp28_r2_remaining_edge_batch_g_manifest.json`.
