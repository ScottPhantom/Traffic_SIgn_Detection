# M0-WP27-R2 QA correction record

Status: `CORRECTION_SOURCE_FOR_WP27_R2_AWAITING_INDEPENDENT_QA`

This append-only record preserves the M0-WP27-R1 layout-status correction as an immutable
QA-failed audit record. Independent QA of WP27-R1 reported exactly one `P2` finding and zero
`P0`/`P1`/`P3` findings.

## Finding P2-1 — R1 verifier fails open on JSON type confusion under coherent refresh

- `semantic_diff` compares leaves with Python `==`, so `250 == 250.0 == True`-style type changes
  are reported as no change.
- `validate_effective_layout` checks `pair_count`, `page_count`, `pairs_per_page`, `page`,
  `row_count`, `slot` and `batch_position` with `!=`; only `bool` is excluded for the two count
  fields, and floats are not excluded at all.
- `verify` does not pin the corrected-layout SHA-256 and does not require byte equality with the
  canonical serialization of `corrected_layout(initial_layout)`.
- Reproduction: an effective layout carrying `pair_count=250.0`, `pages[0].page=true`,
  `pages[0].rows[0].slot=true`, `pages[0].rows[0].batch_position=true` or float row bounds,
  followed by a refresh of the R1 delta, roster, report and manifest with the R1 helpers, returns
  `valid=true` with `errors=[]`, while the delta still claims that `/status` is the only change.

The shipped R1 bytes are not affected: the R1 corrected layout is exactly the canonical
serialization of `corrected_layout(initial_layout)`, and a type-strict diff against the immutable
initial layout yields exactly `/status`.

## Pinned predecessor bytes

- Initial WP27 manifest SHA-256 `9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`.
- WP27-R1 manifest SHA-256 `6992625b062649ba979a39eb7e4ef8fd00eadad666558fb40886d520390d96fc`.
- WP27-R1 corrected layout SHA-256 `d7af4b260985215ff70ca8567369f75f96bc63f4bfe8b58f6d5849b77e00e7f3`.
- WP27-R1 semantic delta SHA-256 `a3bb4ced80bae9b3c4124af7e53e16fe1673ca3f1794fdd249f9218accc8fe6e`.
- WP27-R1 effective roster SHA-256 `c4b25036ea12820f7d0a9434d93bcea1b2e0461f7dc83878964a69255c8bc741`.
- WP27-R1 report SHA-256 `b20719298e8efe95d136f38b3024f0b4edb3bb1ee6bff22d601687b3385c1e44`.
- WP27-R1 builder SHA-256 `9bfc963f207876cbd431e48e2184252e962a8f473182a70148e026033314cdd7`.
- WP27-R1 test SHA-256 `f406d316b6068d28f724a4e9f5e19ee2b61364b362cf647902760952f310f36e`.

## Correction scope

WP27-R2 is verifier hardening only. It adds a type-strict verifier that pins the exact R1 bytes,
requires the effective layout to equal the canonical serialization of
`corrected_layout(initial_layout)`, compares JSON leaves type-strictly and requires exact `int`
types for every count/position field. It reuses the R1 corrected layout unchanged and changes no
initial WP27 or WP27-R1 byte, semantic decision, selection row, lineage row, annotation, atlas
index or atlas JPEG pixel.

It does not approve D-02, create final or transitive group truth, authorize a split or training,
start WP28, upload, deploy, publish or control a real vehicle. Canonical WP5 remains 3,172 PENDING
edges and 589 PENDING sequences; 646 residual PENDING edges remain outside the overlays, including
two quarantined edges that touch stem `0248`, leaving 644 review-eligible edges. D-02 remains
`PENDING`, Gate 0 remains `BLOCKED`, and `split_authorized=false` plus
`training_authorized=false` remain in force.
