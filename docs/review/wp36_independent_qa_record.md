# M0-WP36 independent QA record

Status: `QA_PASS_WP36_WITH_ONE_P2_OWNER_RANKING_CLARIFICATION_REQUIRED_PROVISIONAL_EVIDENCE_ONLY`
Reviewer: `Claude Code QA session (did not author WP36)`
Reviewed at: `2026-10-18T08:00:00+07:00`
Boundary: `QA_OF_G07_SPLIT_PROPOSAL_ONLY_NOT_OWNER_ACCEPTANCE_NO_TRAINING`

This append-only record reports independent QA of M0-WP36, the G0.7 group-aware split built
under owner option A. It modifies no builder, input, output, owner record, `PROJECT_MEMORY.md`
or roadmap file. WP36 keeps its `WP36_AWAITING_QA_REVIEW` status string.

## Verdict

- **WP36: PASS.** 0 P0, 0 P1, **1 P2**, 3 P3.
- All hard rules hold, and the class coverage table re-derives exactly. Both structural
  conflicts are real.
- The package is the best assignment **for its own objective**: my independent optimizer reaches
  exactly the same objective value.
- **P2-1 must be settled before the owner accepts and seals the split.** The objective ranks
  the ±3-point ratio band **above** "at least 2 test groups per `TRAIN_VAL_TEST` class". The
  owner's G0.7 ranking lists the test-group depth third and the ratio fourth.
- **Test seal of the current bytes:** `01bdb9890036a44659e809af88d465c5ae67aefbd39f39d770e5ba4bcd575681`.
  The value `f506d5c7…` quoted in the QA request does not match any WP36 artifact. I checked it
  as the SHA-256 of the sorted test stems, with and without a trailing newline, and against the
  file hashes, and searched the repository for it.

## Package bytes reviewed

- Builder `5fd5b4c189d0815f…`, test `270b9d399c03d9fa…`, report `8e04ab229c64edd4…`.
- Manifest `1012b223f7f1d9ff…`, candidate `964b447715aa4c95…`.

## Checks performed

1. **Hard rules (QA-only script; does not import the builder).**
   - The frames CSV has 3,215 rows, equal to the D-02 registry, and every row's group matches the
     registry. Stem 0248 is absent.
   - No group appears in two splits, in either the frames CSV or the candidate JSON.
   - Forced groups were derived independently. The derivation starts from the WP35 lineage source
     groups and adds every group that holds a class with one of these decisions:
     - D-04 part 1 TRAIN_WITH_ENRICHMENT (12 classes);
     - D-04 part 2 TRAIN_ONLY_UNVERIFIED (9 classes);
     - class 38, revised to train-only by G0.7.

     This gives exactly the package's 15 groups: C0002, 0010, 0013, 0014, 0015, 0016, 0019, 0021,
     0022, 0027, 0038, 0040, 0049, 0051 and 0053. All are in train.
   - The 24 quarantined negatives are marked `QUARANTINED` and appear in no candidate list. 0544
     is `BACKGROUND` in train (group C0014).
   - Usable frames: train 2,114 / val 372 / test 705. The test seal re-computes to `01bdb989…`.
   - `scripts/build_d02_owner_decision.py check-candidate` accepts the candidate. It rejects a stem
     moved across a group boundary and the quarantined stem 0248.
2. **Class coverage.**
   - Re-derived from the WP33 boxes, the registry and D-04 parts 1 and 2. All 54 rows match:
     group counts, box counts per split and `requirement_met`.
   - The only unmet requirement is class 25, which has no test group.
   - Option A's one-free-group classes were derived independently, not taken from the builder's
     constant. The `TRAIN_VAL_TEST` classes with at most one non-forced group are exactly 17, 18,
     19, 30, 40, 45 and 50, matching the builder's `ONE_FREE_TEST`.
3. **Structural conflicts.**
   - **(a) Ratio band: real.**
     - Test must contain C0048 (411 frames, the only free group of 18, 40 and 45).
     - It must also contain C0017 (40 frames, 17 and 19), C0030 (63, the only free group of 28
       and 30), C0041 (49, class 50) and C0018 (25, class 20).
     - It needs one group each for 9 and 11; the smallest options are C0033 (16) and C0006 (15).

     That is at least 619 of 3,191 usable frames, 19.4% (20.7% if class 25 also gets C0032). The
     test ceiling is 18%, so no assignment that meets the class requirements can satisfy the
     band.
   - **(b) Classes 22 and 25: real.**
     - C0030 must be test for 28 and 30, so 22's val can only be C0032.
     - Class 25 has only C0032 and C0036, and needs one in train and one in test.
     - At least one requirement therefore fails in every assignment, so the minimum is
       `unmet = 1`.

     Which class fails is a tie. The package fails class 25; the owner may prefer to fail
     class 22's val instead.
   - **Optimality check.** My own simulated-annealing optimizer (40 restarts) used the package's
     objective ordering, on both registry and usable frame counts. It found the same objective
     value, `(-1, -0.048569, 7, …)` on registry counts. The package is therefore optimal for its
     objective.
     - Other score-neutral assignments exist that move C0001, C0008, C0020, C0025, C0031, C0035
       and C0046 between train and val. The package's choice among them is deterministic and set
       by its tie-break.
4. **Objective against the owner ranking.** See P2-1.
5. **Determinism and fail-closed behaviour.**
   - `uv run python scripts/build_wp36_group_split.py verify --repo-root .` returns `valid=true`
     with 6 artifacts in about 11 s, all regenerated byte for byte.
   - `uv run pytest -q -p no:cacheprovider tests/test_wp36_group_split.py` reports 7 passed.
   - Tampering attacks on a staged copy. The baseline and restored runs were both `valid=true`,
     and all six failed closed:
     - J1: append to the G0.7 record. Rejected because the pinned source changed.
     - J2: change a quarantined negative to background in the negatives CSV. Rejected because the
       pinned source changed.
     - J3: move one stem to test in the frames CSV. Rejected because the artifact differs.
     - J4: append quarantined 0060 to val in the candidate. Rejected because the artifact differs.
     - J5: edit the seal in the manifest. Rejected because the artifact differs.
     - J6: edit the pinned D-02 checker. Rejected because the pinned source changed.

## Findings

### P2-1: the objective ranks the ratio band above the test-group depth

The G0.7 record ranks the search criteria as follows:

1. hard rules;
2. per-class requirements;
3. at least 2 test groups for `TRAIN_VAL_TEST` classes where possible;
4. ratio;
5. box balance.

`Scorer.score` returns `(-unmet, -band, deep, -ratio, -balance)`, so the band, which is part of
"ratio", outranks criterion 3. The report describes the objective as following the owner's
ranking without noting this.

The choice matters:

| Ordering | Classes with ≥2 test groups | Train / val / test (usable) |
| --- | --- | --- |
| Package (band first) | 7 | 66.2 / 11.7 / 22.1 % |
| G0.7 record, literally | 17 | about 59.8 / 11.6 / 28.6 % |

With the literal ordering, the unmet class becomes 22 (no val) instead of 25. The test seal makes
this choice permanent, so before accepting the split the owner should either:

- confirm that the ±3-point band (decision item 3) outranks test-group depth, and record that as
  an append-only clarification; or
- have WP36 rebuilt with criterion 3 ranked before the ratio.

The report should state the deviation and show both outcomes.

### P3 findings

- **P3-1: the objective uses registry frames, the report shows usable frames.** The band and
  ratio terms use registry group sizes, which include the 24 quarantined negatives (3,215
  frames). The report shows usable shares (3,191 frames). My optimizer reaches the same optimum
  under both counts, so the result is unaffected, but the objective should use the usable counts
  that are reported.
- **P3-2: `check-candidate` does not reject quarantined negatives.** The D-02 checker accepted a
  candidate with quarantined 0060 added to val, because 0060 is in group C0001, which is in val.
  WP36 `verify` catches this through the byte comparison, but a downstream M1 loader that relies
  only on `check-candidate` would not. The loader should check every list against
  `split_list_sha256` in the WP36 manifest, or against `use` in the frames CSV.
- **P3-3: `verify` writes into the repository.** `render` writes a temporary
  `.wp36_candidate_check.json` into `docs/review/generated/` and deletes it afterwards. Two
  concurrent runs could collide. Use a temporary directory instead.

## Governance

- The split is a proposal. It becomes G0.7 only after the owner resolves P2-1 and accepts it.
- `split_authorized=false` and `training_authorized=false`. G0.9 and D-05 remain open, and
  Gate 0 remains BLOCKED.
- No training, upload, push or publication was performed. This record modifies no WP36 file,
  input, owner record, `PROJECT_MEMORY.md` or roadmap file.
