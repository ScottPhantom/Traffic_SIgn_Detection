# M0-WP28-R2 QA correction record

Status: `CORRECTION_SOURCE_FOR_WP28_R2_AWAITING_INDEPENDENT_QA`

This append-only record preserves both the initial M0-WP28 Batch G package and the M0-WP28-R1
reissue as immutable QA-failed audit records. Independent QA of WP28-R1 reported zero `P0`/`P1`,
one `P2` and three `P3` findings. It agreed with every decision, including the corrected
`edge_002306` (`SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `HIGH`).

## P2-1 — R1 decisions cite the superseded initial atlas

- The initial builder fills `wp12_atlas_page` and `evidence_boundary` from its own module globals.
  WP28-R1 only reconfigured the shared chain, so those globals kept the initial values and the
  R1 path replacement in `derive_selection` was a no-op.
- Result: the R1 selection CSV is byte-identical to the initial selection, and all 250 R1
  `evidence_refs` cite `docs/review/assets/wp28/remaining_edge_batch_g/page_NNN.jpg`, including
  `edge_002306` at `page_013.jpg#slot=5`, a page that still shows the superseded decision. The
  corrected R1 atlas was never referenced, and the cited initial atlas was not an R1 source.
- The R1 test used a subset assertion that passed when nothing differed.

## P3 findings

- P3-1: `load_canonical_json` read text with universal newlines, so CRLF/CR variants of the
  manifest and annotations still verified. WP28-R2 compares raw bytes.
- P3-2: the vacuous subset assertion (test side of P2-1). WP28-R2 requires exactly
  `wp12_atlas_page` and `evidence_boundary` to differ on every row and every atlas
  `evidence_refs` entry to cite the WP28-R2 atlas.
- P3-3: inherited "cross-split" index wording; cosmetic, recorded without change.

## Pinned QA-failed bytes

- Initial WP28 manifest `d5933d813a8788c2cb367b99b92d54eee7aa8e8ebbe171e424ce2834da6fdc0f`.
- WP28-R1 manifest `2dc57da89791e13602a0a6be04b8464cbc64727c84199571e921d7e414aab83b`.
- WP28-R1 builder `215272e412107044281f18d6100a267bd72faf0eca2fca74bd8d5dafc4d9ed5f`.
- WP28-R1 test `094dff55efe3ba86c1b3014339baf3140dd0b49ae7f7ee7242e4c8e42c1052f5`.
- WP28-R1 annotations `f5a75679c84393c15bbafcef7db53946f9cb463348b08df96796bd614ef601c6`.
- WP28-R1 one-row overlay `0fdf1ed29f62919650fe121fa7d87d5905f9732fa1cd06458dde01a114b5a0a4`
  (reused unchanged by WP28-R2 as its trusted decision source).

## Boundary

WP28-R2 changes no decision: it reissues the R1 decisions with evidence references bound to the
WP28-R2 atlas, the WP28-R2 evidence boundary and byte-exact canonical JSON checks. It keeps the
exact same 250 canonical rows (`edge_002214` through `edge_002587`). It does not approve D-02,
create final or transitive group truth, authorize a split or training, start WP29, upload,
deploy, publish or control a real vehicle. Canonical WP5 remains 3,172 PENDING edges and 589
PENDING sequences; 396 residual PENDING edges remain after this batch, including the two
quarantined stem-`0248` edges. D-02 remains `PENDING`, Gate 0 remains `BLOCKED`, and
`split_authorized=false` plus `training_authorized=false` remain in force.
