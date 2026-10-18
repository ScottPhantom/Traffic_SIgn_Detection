# M0-WP27-R1 — layout-status correction

Status: `WP27_R1_AWAITING_INDEPENDENT_QA`  
Boundary: `WP27_R1_LAYOUT_STATUS_ONLY_CORRECTION_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_FINAL_GROUP_ID_NO_SPLIT_NO_TRAINING`

Independent QA failed the initial WP27 package with exactly one `P2` finding and zero
`P0`/`P1`/`P3` findings. The initial layout correctly records 250 pairs over 50 pages, but its
status retained the inherited WP15 value `PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`. The historical WP27 verifier
also explicitly accepted and required that stale value.

## Append-only correction

- Initial WP27 manifest remains immutable at SHA-256 `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`.
- Initial WP27 layout remains immutable at SHA-256 `5b0c938465b5af1c44cf276f0633692a2769b8db49eaac9cd9dbc221dc19c506`.
- Initial builder/test remain immutable at SHA-256 `831ad27ab3fba6fc2f78b121db752654306586a8bbfffc315f5a6c6869b2ab73` and
  `fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce`.
- Effective layout SHA-256 is `d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3` and its exact status is
  `PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT` with `pair_count=250` and `page_count=50`.
- Semantic delta SHA-256 is `a3bb4ced80bae9b3c4124af7e53e16fe1673ca3f1794fdd249f9218accc8fe6e`; it proves the only JSON-value change is `/status`.
- Effective 56-artifact roster SHA-256 is `c4b25036ea12820f7d0a9434d93bcea1b2e0461f7dc83878964a69255c8bc741`; 55 artifacts retain their exact
  initial path/hash and only `layout_audit` resolves to the corrected layout evidence.

The immutable semantic decisions, selection, source lineage, annotations, atlas index and all 50
atlas JPEGs are the same initial files and hashes. No pixel, edge decision, rationale, source path,
raw image, raw label or provenance artifact was changed.

## Governance boundary

- Canonical WP5 remains 3,172 PENDING edges and all 589 sequences remain PENDING.
- 646 residual PENDING edges remain outside the provisional overlays; two touch quarantined stem
  `0248`, leaving 644 review-eligible residual edges.
- D-02 remains PENDING; Gate 0 remains BLOCKED; `split_authorized=false` and
  `training_authorized=false`.
- This correction does not create final/transitive group truth and does not authorize WP28,
  upload, deploy, publish or real-vehicle control.

Initial package roster: 88 sources and
56 non-manifest artifacts.
