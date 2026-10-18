# M0-WP30 independent QA record

Status: `QA_FAIL_WP30_ONE_P1_DECISION_CORRECTION_REQUIRED_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP30)`
Reviewed at: `2026-10-17T14:00:00+07:00`
Boundary: `QA_OF_PROVISIONAL_EDGE_OVERLAY_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record reports independent QA of M0-WP30 final remaining-edge Batch I. It does
not modify the hash-pinned package; WP30 keeps its `WP30_AWAITING_QA_REVIEW` status string.

## Verdict

- WP30 Batch I: **FAIL**: 0 P0, **1 P1**, 0 P2, 1 P3.
- 143 of 144 decisions are agreed. One capture decision is disagreed with: `edge_003047`
  (P1-1 below). Correct it in a WP30-R1 successor, following the WP28 → WP28-R1 precedent.

## Package bytes reviewed

- Manifest `c906e22fc48678308e54ace0363735a97d7f482eb13135822e39bd67b2ad54f0`.
- Selection `5e185c6aa55cc2b279c7e503b0b7ee80880ad15edfc31541e63b19d60edb3a93`.
- Annotations `a85a6b24e4962a76a17240815d501bddcf3795ff38955293c683565e0d2cf590`.
- Review notes `488c69d1f5c9b59838bbde57e9861be7c1fb431749f7fc6e78608ff0fe28551c`.
- Layout audit `86100a038982b18cac1bd90a8e65c690244f3ceee3e6b521f33f989e58425a7c`.
- Builder `ca35511cc932c776ec9ea49dc6c9a6fa04edd8da7c9201734a8b8ad9e58acb9a`.
- Test `74d622591656ff8aef7790987a7497fd0c56ff5330315c86e7dfc0326883c9f1`.

## Checks performed

1. Independent selection derivation, using a QA-only script and not the builder. Canonical WP5 has
   3,178 edges, 3,172 of them PENDING. Removing the five cross-split overlays (WP7, WP12–WP15;
   1,026 edges) leaves 2,146 non-cross-split PENDING edges. Removing `edge_000242` and
   `edge_000243` (stem `0248`) leaves 2,144 eligible. WP22, WP23-R1, WP24, WP25-R1, WP26, WP27,
   WP28-R2 and WP29 (8 × 250) are exactly the prefix `eligible[0:2000]`, with no duplicates.
   WP30 is exactly `eligible[2000:2144]`: 144 edges, `edge_002973`…`edge_003176`, positions
   1–144 in canonical order. It does not overlap the cross-split overlays, the eight prefixes or
   the quarantined edges. All 144 rows are `cross_split=False`. Stems, splits, class ids, proxy
   sequence ids and the four SHA-256 values per row equal canonical WP5. There are 288 endpoints
   and 172 unique stems.
2. Raw binding: every endpoint image and label was re-hashed from the local byte-identical
   DATASET01 copy against the WP1 inventory. That is 576 endpoint files (344 unique) with
   0 mismatches, and every path equals the inventory path.
3. Notes vs annotations: the 144 notes CSV rows equal the 144 annotation decisions field by field
   and in order. Every decision has exactly three `evidence_refs`: the two `#sha256=` raw refs
   matching the selection, and `docs/review/assets/wp30/remaining_edge_batch_i/page_NNN.jpg#slot=k`
   matching the selection's atlas page and slot. None cites a predecessor atlas. The atlas has
   29 pages (28 × 5 + 1 × 4). Recorded totals are capture 140 `SAME_CAPTURE_CANDIDATE` /
   4 `NOT_RELATED`, physical sign 139 `SAME_PHYSICAL_SIGN_CANDIDATE` / 5 `NOT_RELATED`, and
   confidence 143 `HIGH` / 1 `MEDIUM`. These match the report.
4. Visual review: all 29/29 atlas pages and 144/144 pair panels were read directly, and each
   judgment was formed before reading the recorded decision. Raw full frames were opened for
   stems 3000, 3004, 3012–3016, 3030, 3076, 3084, 3085, 3087, 3100 and 3125 (rider and plate
   crops).
   - Agreed exceptions:
     - `edge_002977` (3014/3015): `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `MEDIUM`. Raw frames
       confirm that 3015 matches the 3000–3004 segment, with the same Vietnam Post raincoat rider
       and orange-white helmet rider. Stem 3014 is the cls13 bridge approach. The frames are out
       of filename order within one ride.
     - `edge_003092` (3129/3130): dry, overcast pylon road against a heavy-rain city street with
       a dark-raincoat rider (plate 59-F1 257.28). No shared riders or signs.
     - `edge_003128` (3165/3166): a pickup on a shop street against an overpass approach with
       yellow/blue raincoat riders. No shared riders or signs.
     - `edge_003153` (3190/3191): rainy overpass junction against a sunny, empty tree-lined road.
   - Borderline pairs, all agreed:
     - `edge_002999`: large camera yaw, but the same cls6 curve sign, blue cls38 board and riders.
     - `edge_003008`: the same blue board relabelled cls41, with cls10 shared.
     - `edge_003088`: cls48 leaves the frame, while cls45 and the CHU Y QUAN SAT plate are shared.
     - `edge_003089`: cls45 is at the same position in both frames.
     - `edge_003146`: cls32 leaves the frame, while cls47 is shared.
     - `edge_003116`: cls14 is shared.
5. Package verifier and tests:
   - `build_wp30_remaining_edge_review_batch.py verify` returns `valid=true`, 123 sources,
     35 artifacts and `WP30_AWAITING_QA_REVIEW`.
   - `run_parallel_checks.py tests --skip-serial --jobs 3 -- tests/test_wp30_remaining_edge_review_batch.py`
     reports 10 passed.
6. Tampering attacks: these ran on a staged copy in the QA scratchpad. Each run started from a
   fresh copy of the pinned bytes, and the baseline and restored runs were both `valid=true`.
   All seven attacks failed closed:
   - A1: flip `edge_003047` to SAME/MEDIUM coherently in the notes and annotations, then re-hash
     the manifest. Rejected with `tampered sources file` on the pinned notes.
   - A2: change layout `row_count` from 5 to 5.0 and re-hash. Rejected because the layout no
     longer matches its regeneration.
   - A3: inject a duplicate `training_authorized` key into the manifest. Rejected with
     `duplicate JSON key`.
   - A4: set `training_authorized=true` in canonical form. Rejected as an invalid manifest.
   - A5: convert the annotations to CRLF and re-hash. Rejected as non-canonical.
   - A6: add an extra `page_030.jpg` to the atlas. Rejected on the atlas roster check.
   - A7: inject a duplicate key into the annotations and re-hash. Rejected with
     `duplicate JSON key`.

## Findings

### P1-1: `edge_003047` capture decision contradicted by raw frames

- Batch position 53, WP5 order 3087, stems 3084/3085, atlas `page_011.jpg` slot 3.
- Recorded: `NOT_RELATED` / `NOT_RELATED` / `HIGH`. The rationale says there are "no shared
  riders, vehicles or physical signs".
- Raw evidence: from stem 3085 onwards (the tree-lined road with the cls48 sign) the camera
  rider's companions are the same group seen in 3000–3004 and 3010–3076:
  - the Vietnam Post raincoat rider is visible ahead in 3085 and 3087, as in 3016 and 3030;
  - an orange-white helmet rider and a cream-helmet grey-raincoat rider appear in both blocks;
  - a pink-hoodie passenger with two white helmets appears in both, as in 3012/3014.

  In 3085/3087 the cream-helmet grey-raincoat rider and the companion motorbike (plate
  60-F4 377.83) are directly ahead. The weather and light are continuous. The scene does change
  at 3084→3085, but this is the same out-of-order or gapped single-ride pattern that WP29
  `edge_002967` and WP30 `edge_002977` record as same capture.
- Expected decision: `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `MEDIUM`. The physical-sign
  relation (cls6 curve sign against a cls48 sign) is agreed as `NOT_RELATED`.
- Why it is P1: the error falls in the leak-risk direction. The 3085–3129 block is reached only
  through `edge_003047` and `edge_003092`. With both recorded as `NOT_RELATED`, that block would
  be separated from the rest of one ride session, and a group-aware split could then place
  frames with the same riders in different splits. The recorded rationale is also factually
  contradicted.
- With this correction the expected totals become capture 141 `SAME_CAPTURE_CANDIDATE` /
  3 `NOT_RELATED`, physical sign unchanged at 139 / 5, and confidence 142 `HIGH` / 2 `MEDIUM`.

### P3-1: inherited verifier error strings name WP12 (non-blocking)

The roster and layout errors raised through the reused WP12 core read `WP12 atlas directory
roster differs from exact 51-file contract` and `WP12 layout bytes differ…`. The enforced WP30
contract is the 30-file roster: the baseline verifies with 30 files and the extra-file attack
fails. Only the message text is stale, so this is cosmetic and was inherited by earlier packages.

## Observation (non-blocking)

Stems roughly 2995–3129 look like one continuous ride session with segments out of filename
order: the bridge approach, the cls6/10/23/38 road, the cls6 pylon close-ups and the cls48
tree-lined road. Group derivation must not treat a scene discontinuity between adjacent stems as
evidence of a different capture without checking for shared riders.

## Governance

Canonical WP5 remains at 3,172 PENDING edges, and all 589 sequences remain PENDING. Only the two
quarantined stem-`0248` edges remain outside the edge overlays. D-02 remains PENDING and Gate 0
remains BLOCKED. `split_authorized=false` and `training_authorized=false` stay in force. No
split, group truth, training, upload, push or publication was performed. This record did not
modify the WP30 package, builders, tests, manifests, `PROJECT_MEMORY.md` or the roadmap.
