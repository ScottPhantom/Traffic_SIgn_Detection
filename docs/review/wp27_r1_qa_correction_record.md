# M0-WP27-R1 QA correction record

Status: `CORRECTION_SOURCE_FOR_WP27_R1_AWAITING_INDEPENDENT_QA`

This append-only record preserves the initial M0-WP27 package as an immutable QA-failed audit
record. Independent QA reported exactly one `P2` finding and zero `P0`/`P1`/`P3` findings:
`wp27_remaining_edge_batch_f_layout_audit.json` records `pair_count=250` and `page_count=50`, but
its status is the inherited stale value
`PASS_COMPLETE_176_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`.

The initial manifest SHA-256 is
`9f45437cbe47ec5968955dac4471eb0f33b8e43debd973428208facd431628e8`; the initial layout SHA-256
is `5b0c938465b5af1c44cf276f0633692a2769b8db49eaac9cd9dbc221dc19c506`; the initial builder and
test SHA-256 values are respectively
`831ad27ab3fba6fc2f78b121db752654306586a8bbfffc315f5a6c6869b2ab73` and
`fe73fc42df74a99ea0b20f24f9622d54f01c1338f3c48150042ab20471e7b9ce`.

The effective correction changes exactly the layout-audit `/status` field to
`PASS_COMPLETE_250_PAIR_COVERAGE_TEXT_BOUNDS_AND_BBOX_CONTEXT`. It does not change any semantic
decision, selection row, source-lineage row, annotation, atlas index or atlas JPEG pixel. It does
not approve D-02, create final or transitive group truth, authorize a split or training, start
WP28, upload, deploy, publish or control a real vehicle.

The canonical WP5 boundary remains 3,172 PENDING edges and 589 PENDING sequences. After the
provisional WP27 overlay, 646 residual PENDING edges remain, including two quarantined edges that
touch stem `0248`; 644 are review-eligible. D-02 remains `PENDING`, Gate 0 remains `BLOCKED`, and
`split_authorized=false` plus `training_authorized=false` remain in force.
