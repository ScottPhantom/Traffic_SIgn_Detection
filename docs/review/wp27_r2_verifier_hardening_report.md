# M0-WP27-R2 — type-strict verifier hardening

Status: `WP27_R2_AWAITING_INDEPENDENT_QA`
Boundary: `WP27_R2_VERIFIER_HARDENING_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

Independent QA failed WP27-R1 with exactly one `P2` finding and zero `P0`/`P1`/`P3` findings:
the R1 verifier compared JSON leaves with `==` and did not pin the corrected-layout bytes, so a
type-confused layout (for example `pair_count=250.0` or `slot=true`) plus a coherent refresh of
the R1 delta, roster, report and manifest verified as valid. The shipped R1 bytes were correct.

## Append-only correction

- WP27-R1 remains immutable at manifest SHA-256 `6992625b062649ba979a39eb7e4ef8fd00eadad666558fb40886d520390d96fc`; its builder, test,
  layout, delta, roster and report are pinned by exact SHA-256 constants in the R2 verifier.
- The effective WP27 Batch F layout is reused unchanged at SHA-256 `d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3` with
  status `PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`, `pair_count=250` and `page_count=50`.
- R2 requires the effective layout bytes to equal the canonical serialization of
  `corrected_layout(initial_layout)`, a type-strict diff of exactly `/status`, and exact `int`
  type for 3704 count/position/bounds fields.
- Type-strict audit SHA-256 is `d04e74dd7d9d412b7d2108d044e7c4aac3e438f3ffaddd2a58f572217c6924f0`; it records 8 type-confusion
  probe classes that the R2 verifier rejects even after a coherent refresh.
- R2 also requires the immutable WP27-R1 verifier, and through it the initial WP27 verifier, to
  return `valid=true` on the pinned predecessor packages.

No semantic decision, selection row, source-lineage row, annotation, atlas index, atlas JPEG,
raw image, raw label or provenance artifact was changed.

## Governance boundary

- Canonical WP5 remains 3,172 PENDING edges and all 589 sequences remain PENDING.
- 646 residual PENDING edges remain outside the provisional overlays; two touch quarantined stem
  `0248`, leaving 644 review-eligible residual edges.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.
- This correction does not create final/transitive group truth and does not authorize WP28,
  upload, deploy, publish or real-vehicle control.
