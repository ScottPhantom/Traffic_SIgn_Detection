# M0-WP28-R1 QA correction record

Status: `CORRECTION_SOURCE_FOR_WP28_R1_AWAITING_INDEPENDENT_QA`

This append-only record preserves the initial M0-WP28 Batch G package as an immutable QA-failed
audit record. Independent QA reported one `P1`, one `P2` and two `P3` findings and zero `P0`.
The PM independently re-inspected the raw frames/labels and accepts the P1.

## P1-1 — edge_002306 physical-sign decision contradicted by raw frames

- Batch position 65, WP5 order 2599, stems 2331/2332, initial atlas page 013 slot 5.
- Initial decision: `SAME_CAPTURE_CANDIDATE` / `SAME_PHYSICAL_SIGN_CANDIDATE` / `MEDIUM`.
- Raw evidence: stem 2331 labels a near standalone pole stack, cls10 `0.482812 0.273148 0.028125
  0.05` above cls23 `0.483333 0.328704 0.020833 0.05` with a plate, plus cls18 at x `0.815625`.
  Stem 2332 labels a smaller cls10 `0.526563 0.388889 0.019792 0.033333` hanging from an arm that
  also carries two round speed-limit discs; that structure is visible far down the road in 2331.
  The labelled 2331 stack has been passed, the cls10 shrinks instead of growing, the arrangement
  differs and cls18 does not carry over.
- Corrected decision: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `HIGH`. The same SUV,
  red-cargo motorbike and red container truck keep the capture relation. The other 249 decisions
  are unchanged.

## P2-1 — duplicate keys and non-canonical JSON accepted

The initial WP28 verifier parses the manifest and annotations with plain `json.loads` and checks
canonical serialization only for the layout, so duplicate keys (for example a leading
`"training_authorized": true`) and reformatted bytes still verify. WP28-R1 rejects duplicate keys
and requires canonical `json.dumps(indent=2, sort_keys=True, ensure_ascii=False) + "\n"` bytes for
its layout, annotations and manifest.

## P3 findings

- P3-1: the initial strict layout check used a chained `row_count != len(rows) != 5` comparison;
  WP28-R1 checks `row_count == len(rows) == 5` explicitly. The inherited WP15 check already caught
  this end to end.
- P3-2: the inherited atlas index header wording says "cross-split manual review"; cosmetic and
  inherited, recorded without change.

## Pinned QA-failed WP28 bytes

- Manifest `d5933d813a8788c2cb367b99b92d54eee7aa8e8ebbe171e424ce2834da6fdc0f`.
- Selection `556de19cf71ea1d15727df2f5f2fb64bc36e732ced3ba8a791b11c129b167a6f`.
- Annotations `71be309b9a82d6f839dc875d71a74ab0072e2c1849b4d2eb60de1a677b578267`.
- Review notes `56f02f8a70063ced5dfa9b259d41bfd8c10fc3a99b0071d4d0b42aa27c4122f9`.
- Builder `0b9e19dba0722d77725332be0ae6db3cffe93c92fe374c426f12eb6ab0fe819c`.
- Test `cc6cdcbf92da82e8f250368a17cbd0dbae1f8eee3fbdc9b1bebdea501445c5da`.

## Boundary

WP28-R1 keeps the exact same 250 canonical rows (`edge_002214` through `edge_002587`). It does not
approve D-02, create final or transitive group truth, authorize a split or training, start WP29,
upload, deploy, publish or control a real vehicle. Canonical WP5 remains 3,172 PENDING edges and
589 PENDING sequences; 396 residual PENDING edges remain after this batch, including the two
quarantined stem-`0248` edges. D-02 remains `PENDING`, Gate 0 remains `BLOCKED`, and
`split_authorized=false` plus `training_authorized=false` remain in force.
