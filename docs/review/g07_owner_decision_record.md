# G0.7 owner decision — split rules (option A)

Status: `OWNER_APPROVED_SPLIT_RULES`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
Plan: `docs/review/wp36_g07_split_plan.md`

The owner approved option A of the WP36 plan and asked for the WP36 split package to be built.

## Decision

1. **Classes 17, 18, 19, 30, 40, 45, 50** (D-04 `TRAIN_VAL_TEST`, but only one D-02 group not
   forced into train): that free group goes to **test**. These classes have no validation group;
   model selection and threshold tuning must not depend on them.
2. **Class 38 (P.127)**: both of its groups are forced into train, so no test is possible. It
   becomes `TRAIN_ONLY_UNVERIFIED`, with the same behaviour gate as D-04 part 1: shown as
   "unverified", no automatic simulated behaviour until it is evaluated on real independent data.
   This revises the D-04 part 2 row for class 38 (`TRAIN_AND_TEST_NO_VAL`) append-only; the part 2
   table is not rewritten.
3. **Ratio**: about 70 / 15 / 15 train / val / test by frames, with a ±3-point tolerance on each
   split.
4. **Search ranking**, in order:
   1. hard rules;
   2. per-class requirements;
   3. at least 2 test groups for `TRAIN_VAL_TEST` classes where possible;
   4. ratio;
   5. balance of box counts.

## Hard rules carried from earlier decisions

- No D-02 group appears in two splits, and stem 0248 is absent.
- Every group holding a D-04 part 1 class, a `TRAIN_ONLY_UNVERIFIED` class or class 38 is in train.
- WP35 enriched images are train-only, and their source groups are in train.
- `0544` is the only background frame. The 24 quarantined negatives are excluded from every split
  until they are relabelled.

## Not decided here

The split itself is approved only after WP36 passes independent QA and the owner accepts it.
G0.9 (dataset card) and D-05 (thresholds) remain open. Training is not authorized.
