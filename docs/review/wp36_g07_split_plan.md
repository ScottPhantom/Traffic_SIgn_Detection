# M0-WP36 — G0.7 group-aware split: plan

Status: `PROPOSAL_PLAN_NOT_A_SPLIT`
Date: `2026-10-18`
Boundary: no split file, no training. This plan sets the rules and lists the owner choices that
the split builder needs.

## G0.7 criteria (roadmap)

Train/val/test are generated per D-02 group, with no group in two splits. The test split is sealed
before any tuning, and every split has a manifest with SHA-256.

## Inputs (all already approved or QA PASS)

| Input | Use |
| --- | --- |
| `docs/review/generated/d02_group_id_registry.csv` | 3,215 frames → 54 groups (0248 quarantined) |
| `docs/review/generated/wp33_derived_boxes.csv` | train-eligible boxes per derived class |
| `d04_owner_decisions_part1.csv` / `part2.csv` | per-class split requirement |
| `d04_owner_negative_frames.csv` | 0544 background; 24 frames excluded everywhere |
| `scripts/build_d02_owner_decision.py check-candidate` | existing guard: no shared group, no 0248, no unknown stem |

The Kaggle vendor split (2,551 train / 639 test / 25 unassigned) is **not** used: it mixes groups.

## Measured constraints (verified on the current files)

- **Forced train: 15 groups, 1,579 frames (49 %).** These groups hold the 12 enriched rare classes
  (part 1) and the 9 `TRAIN_ONLY_UNVERIFIED` classes. With only one group, these classes must be
  in train. The two largest are C0051 (513 frames: 35, 48) and C0038 (226 frames: 29).
- **Free: 39 groups, 1,636 frames.** All val and test frames must come from these groups.
- At 15 % val and 15 % test of 3,215 frames, about 480 frames each are needed. The free pool
  covers that, but it limits per-class coverage:

| Problem | Classes | Reason |
| --- | --- | --- |
| Only 1 free group, so val **or** test, not both | 17, 18, 19, 30, 40, 45, 50 (`TRAIN_VAL_TEST`) | Their other groups are forced to train |
| 0 free groups, so no test possible | 38 P.127 (`TRAIN_AND_TEST_NO_VAL`) | Both groups are forced to train |
| Very few free boxes | 28 (1 box), 50 (8), 17 (10) | A test on them is close to meaningless |
| Solvable, but needs an exact search | 22 | 2 free groups |

A trial seeded search (not a deliverable) reached train 2,170 / val 563 / test 482 frames. It
satisfied 84 of 93 class requirements; the 9 unmet are exactly the rows above.

## Owner choices needed before building (proposal: option A)

1. **Classes with one free group (17, 18, 19, 30, 40, 45, 50).**
   - **A (recommended):** put the free group in **test**. Report these classes as "no val";
     tuning must not use them. Test evidence is the one that counts for the release decision.
   - B: put it in val; these classes then have no sealed test.
2. **Class 38.** No test is possible without breaking part 1. Proposal: treat it as
   `TRAIN_ONLY_UNVERIFIED` (same behaviour gate as part 1). The alternative is to move one forced
   group out of train, which would leave a part 1 rare class untrained.
3. **Target ratio.** Proposal: about 70 / 15 / 15 by frames, ±3 points tolerance. Class coverage
   outranks the exact ratio.
4. **Ranking used by the search.** Proposal, in order:
   1. hard rules;
   2. the per-class requirements above;
   3. at least 2 groups in test for `TRAIN_VAL_TEST` classes where possible;
   4. ratio;
   5. balance of box counts.

## Build plan (after the choices)

1. `scripts/build_wp36_group_split.py`, in the same style as the earlier WP builders:
   - pins every input by SHA-256;
   - a deterministic exact search over the 39 free groups (fixed seed, recorded objective);
   - no new dependency, because `pyproject.toml` and `uv.lock` stay pinned.
2. Outputs in `docs/review/generated/`:
   - `wp36_split_frames.csv` (stem, group_id, split, use = TRAIN / VAL / TEST / BACKGROUND /
     QUARANTINED);
   - `wp36_split_groups.csv`;
   - `wp36_class_coverage.csv` (per class: groups, boxes, frames per split; requirement met or
     not);
   - `wp36_split_manifest.json` (SHA-256 of each split list and of the inputs);
   - a report.
3. Hard checks inside `verify`, which fails closed on any violation:
   - no shared group;
   - 0248 and the 24 quarantined negatives absent from every split;
   - every forced group in train;
   - WP35 enriched images listed as train-only;
   - `check-candidate` accepts the result;
   - byte-for-byte re-derivation.
4. **Test seal.**
   - The manifest stores the SHA-256 of the sorted test stem list.
   - The future M1 loader must refuse TEST frames unless it runs in an explicit final-evaluation
     mode, and must log that run.
   - Any change to the test list is a new, append-only split version.
5. Tests, a `wp36` runner entry, and an independent QA session for the split.
6. Owner approval recorded append-only. Then **G0.7 PASS**, and D-05 (thresholds) can be set on
   the val split.

## Known limits to disclose

- The groups come from AI visual review. The same physical sign at the same place can still
  appear in two capture groups (D-02 known limit), so test scores may be optimistic.
- 22 of 54 classes (12 enriched + 9 train-only + 38) have no sealed test. Their accuracy stays unknown
  until real independent images are collected.
