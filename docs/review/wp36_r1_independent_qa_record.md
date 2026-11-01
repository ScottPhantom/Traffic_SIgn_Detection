# M0-WP36-R1 independent QA record

Status: `QA_PASS_WP36_R1_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP36 or WP36-R1; authored the WP36 QA record)`
Reviewed at: `2026-10-18T09:30:00+07:00`
Boundary: `QA_OF_G07_SPLIT_PROPOSAL_ONLY_NOT_OWNER_ACCEPTANCE_NO_TRAINING`

This append-only record reports independent QA of M0-WP36-R1, the correction of WP36 under the
owner's G0.7 R1 clarification. It modifies no builder, input, output, owner record,
`PROJECT_MEMORY.md` or roadmap file. WP36-R1 keeps its `WP36_R1_AWAITING_QA_REVIEW` status
string.

## Verdict

- **WP36-R1: PASS.** 0 P0, 0 P1, 0 P2, 1 P3.
- All four WP36 findings are fixed:

  | WP36 finding | Fix in R1 |
  | --- | --- |
  | P2-1 | The objective order is now unmet > ≥2 test groups > band > ratio > balance, the literal G0.7 ranking confirmed in `g07_owner_decision_r1_record.md`. |
  | P3-1 | The ratio terms use the 3,191 usable frames. |
  | P3-2 | A loader guard (`check-candidate`) rejects quarantined negatives, a misplaced background frame and any list that is not the sealed one. |
  | P3-3 | The D-02 check runs in a temporary directory, and no file is left in `docs/review/generated/`. |
- **The result is optimal for the owner's ordering.** My independent optimizer does not beat it.
  No single-group or two-group change improves it, and 17 classes with ≥2 test groups is the
  maximum possible while only one requirement is unmet.
- **Test seal confirmed:** `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc`. It
  is the SHA-256 of the sorted test stems joined by `\n`, with no trailing newline.

## Package bytes reviewed

- Builder `147710f410314bcb…`, test `771a3fb49df6bb1d…`, report `ffe47d53d1aff909…`.
- Manifest `064259941895d350…`, candidate `869947559c5eda97…`.
- Owner R1 record `ddeae6a55cc819d3…`.

## Checks performed

1. **WP36 pins.**
   - All nine pinned WP36 files are byte-identical to the bytes recorded in my WP36 QA record:
     - builder `5fd5b4c1…`, test `270b9d39…`, report `8e04ab22…`;
     - candidate `964b4477…`, frames `1bbc0218…`, groups `27f81e6c…`;
     - manifest `1012b223…`, coverage `00216563…`;
     - WP36 QA record `116f85c0…`.
   - The initial WP36 `verify` still returns `valid=true`.
   - Both owner G0.7 records are pinned.
2. **Hard rules and coverage (QA-only script; does not import the builders).**
   - The frames CSV has 3,215 rows, equal to the registry, with every group matching. Stem 0248
     is absent, and no group appears in two splits.
   - The independently derived 15 forced groups are all in train.
   - The 24 quarantined negatives are `QUARANTINED` and appear in no candidate list. 0544 is
     the only background frame, in train.
   - Usable frames: train 1,912 / val 376 / test 903 (59.9 / 11.8 / 28.3 %), in 29/9/16 groups.
   - The seal re-computes to `afa03d4b…`.
   - All 54 coverage rows re-derive: group and box counts per split, and `requirement_met`. The
     only unmet requirement is class 22, which has no validation group, as the owner accepted.
3. **Optimality under the owner's ordering.**
   - The package objective is `(-1, 17, -0.175967, -0.265967, -0.258504)`.
   - My simulated-annealing optimizer (4 seeds × 60 restarts, usable frames, the same ordering)
     reached at best `(-1, 17, -0.177847, …)`, which does not beat the package.
   - An exhaustive check of every single-group change and every two-group change from the
     package assignment found none that improves the objective.
   - **17 is the maximum given one unmet requirement.** The `TRAIN_VAL_TEST` classes without two
     test groups are 4, 8 and 14, and none of them can get a second test group:
     - Class 4 has only three groups, and needs one each for train, val and test.
     - Class 8 has three free groups. C0036 must stay train because it is class 25's only train
       group, which leaves one free group for val and one for test.
     - Class 14 has only two free groups, one needed for val and one for test.
4. **Loader guard.**
   - `check-candidate` accepts the sealed candidate, and also accepts it with the test list
     reordered, since only list content matters.
   - It rejects every tampered candidate:
     - 0060 added to val (its own group's split): rejected as a quarantined stem and a list hash
       mismatch;
     - 0544 moved to val: rejected as a background frame outside train, a group in two splits and
       a hash mismatch;
     - one test stem dropped: rejected with a hash mismatch;
     - an unknown stem 9999: rejected as an unknown stem and a hash mismatch;
     - the val list missing: rejected because the candidate must have exactly train, val and test.
   - When the package itself has been tampered with, the guard refuses with `WP36-R1 package
     invalid` before it looks at the candidate.
5. **Determinism and fail-closed behaviour.**
   - `uv run python scripts/build_wp36_r1_group_split.py verify --repo-root .` returns
     `valid=true` with 6 artifacts regenerated byte for byte. No temporary file remains in
     `docs/review/generated/`.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp36_r1_group_split.py` reports 10 passed.
   - Tampering on a staged copy: the baseline and restored runs were both `valid=true`. K1–K8
     failed closed in `verify`:
     - K1: append to the owner R1 record. Rejected because the pinned source changed.
     - K2: append to the pinned WP36 QA record. Rejected because the pinned source changed.
     - K3: add a comment to the pinned WP36 builder. Rejected because the pinned source changed.
     - K4: add whitespace to the pinned WP36 candidate. Rejected because the pinned source
       changed.
     - K5: change 0060 from `QUARANTINED` to `VAL` in the R1 frames CSV. Rejected because the
       artifact differs.
     - K6: edit `usable_frames` in the R1 groups CSV. Rejected because the artifact differs.
     - K7: edit the R1 manifest seal. Rejected because the artifact differs.
     - K8: change a quarantined negative to background in the negatives CSV. Rejected because the
       pinned source changed.

     K9 combined the K5 frames edit with a candidate containing 0060. The guard refused it with
     `WP36-R1 package invalid`.

## Finding (P3, non-blocking)

### P3-1: the loader guard re-runs the whole build on every call

`check_candidate` calls `verify`, which repeats the full render: the search, the D-02 check and
all artifacts, taking about 11 s. That is correct and fails closed, but slow for an M1 loader
that checks splits at every run. A faster equivalent would be to verify the pinned manifest hash
and the three `split_list_sha256` values, and call `verify` only in CI.

## Governance

- The split is ready for owner acceptance as the G0.7 split.
- The owner has already accepted a test share of about 28 % and class 22 without validation.
- No-validation classes (9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50) must not drive model
  selection or threshold tuning. Train-only classes have no sealed test.
- `split_authorized=false` and `training_authorized=false` until the owner accepts. G0.9 and D-05
  remain open, and Gate 0 remains BLOCKED.
- No training, upload, push or publication was performed. This record modifies no WP36 or
  WP36-R1 file, owner record, input, `PROJECT_MEMORY.md` or roadmap file.
