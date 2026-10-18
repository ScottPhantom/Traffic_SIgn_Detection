# M0-WP28-R2 and M0-WP29 independent QA record

Status: `QA_PASS_WP28_R2_AND_WP29_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP28-R2 or WP29)`
Reviewed at: `2026-10-17T10:00:00+07:00`
Boundary: `QA_OF_PROVISIONAL_EDGE_OVERLAYS_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record closes independent QA for the two remaining-edge overlays that were
awaiting it. It does not modify either hash-pinned package; both keep their historical
`*_AWAITING_QA_REVIEW` status strings.

## Verdict

- WP28-R2 Batch G: **PASS**, 0 P0/P1/P2, 0 new P3.
- WP29 Batch H: **PASS**, 0 P0/P1/P2, 0 new P3.

## Checks performed

1. Independent selection derivation (own script, not the builders): canonical WP5 has 2,146
   non-cross-split PENDING edges after the five cross-split overlays; removing `edge_000242` and
   `edge_000243` (stem `0248`) leaves 2,144 eligible. WP22, WP23-R1, WP24, WP25-R1, WP26 and WP27
   are the exact prefix `eligible[0:1500]`; WP28-R2 is exactly `eligible[1500:1750]`
   (`edge_002214`…`edge_002587`) and WP29 is exactly `eligible[1750:2000]`
   (`edge_002588`…`edge_002972`). 144 eligible edges remain (`edge_002973`…`edge_003176`).
2. Raw binding: every endpoint image and label of both batches (1,000 files) re-hashed against
   the WP1 inventory from the local byte-identical DATASET01 copy: 0 mismatches.
3. WP28-R2 fixes of the WP28-R1 QA findings:
   - all 250 decisions are field-identical to WP28-R1 (capture, physical sign, confidence,
     outcome, rationale, stems), including corrected `edge_002306`
     (`SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `HIGH`);
   - every `evidence_refs` entry cites `docs/review/assets/wp28_r2/…` and none cites the
     superseded `wp28/` or `wp28_r1/` atlas; the selection binds row 65 to
     `wp28_r2/…/page_013.jpg`;
   - manifest and annotations are LF-only canonical bytes;
   - visual readback of WP28-R2 pages 001–004 and 013 agrees with the recorded decisions.
4. WP29 visual review: all 50/50 atlas pages and 250/250 pair panels were read directly. All 250
   decisions are agreed, including the three exceptions: `edge_002591` (discontinuous scene,
   `NOT_RELATED`/`NOT_RELATED`/`HIGH`), `edge_002825` (large viewpoint jump but same riders and
   shared cls2/cls3 post, `SAME`/`SAME`/`MEDIUM`) and `edge_002967` (stem 3005 belongs to the
   earlier bridge approach, so frames are out of filename order; same capture, different labeled
   signs, `MEDIUM`). The WP29 notes CSV equals the annotations field by field.
5. Package verifiers: `run_parallel_checks.py verifiers` reports WP28-R2 and WP29 `valid=true`
   (33/33 package verifiers pass).
6. Targeted suites: `test_wp28_r2_remaining_edge_review_batch.py` and
   `test_wp29_remaining_edge_review_batch.py` ran 82 tests: 80 passed, 2 failed. Both failures
   are the known immutable "no successor exists" assertions
   (`test_no_wp29_artifacts_or_authorization_are_created` in WP28-R2 and
   `test_no_wp30_artifacts_or_authorization_are_created` in WP29), which became false once the
   next package was started; they are not package defects.

## Observation (non-blocking)

`edge_002967` shows that numeric filename order is not always capture order. Group derivation
must not assume that adjacent stems are temporally adjacent.

## Governance

Canonical WP5 remains 3,172 PENDING edges and all 589 sequences remain PENDING. D-02 remains
PENDING, Gate 0 remains BLOCKED, `split_authorized=false` and `training_authorized=false`.
