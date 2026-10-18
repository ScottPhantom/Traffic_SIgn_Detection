# M0-WP30-R1 independent QA record

Status: `QA_PASS_WP30_R1_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP30 or WP30-R1; authored the WP30 QA record)`
Reviewed at: `2026-10-17T16:00:00+07:00`
Boundary: `QA_OF_PROVISIONAL_EDGE_OVERLAY_ONLY_NOT_D02_APPROVAL_NOT_GROUP_TRUTH_NO_SPLIT_NO_TRAINING`

This append-only record closes independent QA for M0-WP30-R1, the one-edge correction of the
QA-failed M0-WP30 Batch I. It does not modify the hash-pinned package. WP30-R1 keeps its historical
`WP30_R1_AWAITING_QA_REVIEW` status string, and the initial WP30 keeps
`WP30_AWAITING_QA_REVIEW`.

## Verdict

- WP30-R1 Batch I: **PASS**: 0 P0, 0 P1, 0 P2 and 0 new P3.
- The WP30 P1-1 finding (`edge_003047`) is resolved exactly as the WP30 QA record expected.
- The WP30 P3-1 finding (inherited WP12/WP15 error-message text) is carried over unchanged, as
  the R1 package declares. It is still non-blocking.

## Package bytes reviewed

- R1 manifest `6de144e898dcc6b48f6a4629237afe2964595deff7d514a2e85c28b55c45e2fd`.
- R1 one-row correction overlay `46e7325abede0f864006372b7fdc8962f1404c77bc10e0768834168a5264d3c3`.
- WP30 QA record pinned as a source: `f9147fd604dbb17c85fb07ea69faad89c1fe188e2554791a52c3eebe86a7136d`.

## Checks performed

1. **R1 vs initial annotations, compared field by field with a QA-only script.**
   - Of the 144 decisions, exactly one differs semantically: `edge_003047`. Its
     `provisional_outcome` and `capture_hypothesis` change from `NOT_RELATED` to
     `SAME_CAPTURE_CANDIDATE`, its `confidence` changes from `HIGH` to `MEDIUM`, and it gets a new
     rationale. Its `physical_sign_hypothesis` stays `NOT_RELATED`.
   - The other 143 keep identical outcomes, hypotheses, confidence, rationale and stems.
   - Fields that change on every decision, as expected for a reissue:
     - `evidence_boundary` becomes the R1 boundary;
     - the atlas ref changes from `assets/wp30/` to `assets/wp30_r1/` with the same page and slot;
     - `reviewed_at` becomes `2026-10-17T15:00:00+07:00`.

     The raw `#sha256` refs are unchanged. Restamping `reviewed_at` on every decision matches the
     WP28-R1 and WP28-R2 precedent.
   - Totals: capture 141 `SAME_CAPTURE_CANDIDATE` / 3 `NOT_RELATED`; physical sign 139 / 5;
     confidence 142 `HIGH` / 2 `MEDIUM`. These match the report and the WP30 QA expectation.
   - The overlay CSV has one row, and it equals the R1 `edge_003047` decision field by field.
   - The new rationale is consistent with the raw evidence recorded in the WP30 QA record.
2. **Selection and lineage.**
   - The R1 selection has the same header and the same 144 rows in the same order as the
     initial selection. Only two fields differ, each on 144/144 rows:
     - `wp12_atlas_page`, which is exactly the `wp30/` → `wp30_r1/` rebinding;
     - `evidence_boundary`, which becomes the R1 boundary.
   - The lineage has 288/288 rows, with the same two fields rebound and nothing else changed.
   - No decision ref, selection row or lineage row cites `assets/wp30/`. Every decision's atlas
     ref equals its selection page and slot.
3. **R1 atlas.**
   - The roster has 30 files.
   - I read pages 001, 011, 018 and 029 directly. Page 011 slot 3 (`edge_003047`, 3084/3085) shows
     `SAME_CAPTURE_CANDIDATE` / `NOT_RELATED` / `MEDIUM` and the corrected rationale.
   - The neighbouring slots and the other spot-checked pages carry the unchanged decisions under
     the R1 header, boundary and status. That includes the exceptions `edge_002977` and
     `edge_003092`.
   - The R1 pages differ in bytes from the initial pages because the header and status text
     change.
4. **Initial WP30 bytes are unchanged and still verify.**
   - These files are byte-identical to the hashes pinned in the WP30 QA record:
     - manifest `c906e22f…`, selection `5e185c6a…`, annotations `a85a6b24…`, notes `488c69d1…`;
     - layout `86100a03…`, builder `ca35511c…`, test `74d62259…`.
   - The initial `verify` still returns `valid=true`.
5. **Verifiers and tests.**
   - `build_wp30_r1_remaining_edge_review_batch.py verify` returns `valid=true`, with 130 sources,
     35 artifacts and status `WP30_R1_AWAITING_QA_REVIEW`.
   - `run_parallel_checks.py tests --skip-serial --jobs 3 -- tests/test_wp30_r1_remaining_edge_review_batch.py tests/test_wp30_remaining_edge_review_batch.py`
     reports 18 passed.
6. **Tampering attacks.**
   - Every attack ran on a staged copy in the QA scratchpad, starting from fresh pinned bytes.
     The baseline and restored runs were both `valid=true`.
   - All nine attacks failed closed:
     - B1: change a second edge (`edge_003092` to SAME/MEDIUM) and re-hash the manifest coherently.
       Rejected because the capture counts break the correction contract.
     - B2: revert `edge_003047` in both the annotations and the overlay, then re-hash. Rejected
       because the overlay's pinned hash no longer matches.
     - B3: rebind one decision's atlas ref to `assets/wp30/` and re-hash. Rejected with an
       evidence-refs mismatch.
     - B4: rebind one selection row's page to the initial atlas and re-hash. Rejected because the
       selection no longer matches its independent derivation.
     - B5: change the initial WP30 notes and re-hash. Rejected because the pinned
       `wp30_failed_review_notes` hash no longer matches.
     - B6: append text to the pinned WP30 QA record and re-hash. Rejected because the pinned
       `wp30_qa_record` hash no longer matches.
     - B7: inject a duplicate `split_authorized` key into the manifest. Rejected with
       `duplicate JSON key`.
     - B8: swap capture outcomes between `edge_003092` and `edge_003093` so the counts stay the
       same, then re-hash. Rejected because the NOT_RELATED edge IDs break the contract.
     - B9: change the rationale of an otherwise unchanged edge and re-hash. Rejected because the
       annotations no longer match the bound notes.

## Carried-over P3 (non-blocking, unchanged)

The reused verifier still raises some errors with stale predecessor text, for example
`WP12 evidence refs mismatch…` and `WP15 selection differs from independently derived canonical
final 176` (B4). The enforced contracts are the WP30-R1 ones: 144 rows, 30 atlas files and the R1
atlas binding. Only the message text is stale.

## Governance

- Canonical WP5 remains at 3,172 PENDING edges, and all 589 sequences remain PENDING.
- With WP30-R1, zero review-eligible edges remain outside the edge overlays. Only the two
  quarantined stem-`0248` edges (`edge_000242` and `edge_000243`) remain residual.
- D-02 remains PENDING and Gate 0 remains BLOCKED. `split_authorized=false` and
  `training_authorized=false` stay in force.
- No split, group truth, training, upload, push or publication was performed. This record did not
  modify any WP30 or WP30-R1 package file, builder, test, manifest, `PROJECT_MEMORY.md` or the
  roadmap.
