# D-04 owner decision, part 2 — the remaining 42 classes and the negative frames

Status: `OWNER_APPROVED_PART_2_OF_D04`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)
Decision tables:
- `docs/review/generated/d04_owner_decisions_part2.csv` (42 rows, sha256 `8030f4fd7098b971…`)
- `docs/review/generated/d04_owner_negative_frames.csv` (25 rows, sha256 `af1bd4eb314a33ef…`)

Evidence: M0-WP34-R1 (`docs/review/wp34_r1_d04_support_and_negative_audit_report.md`), independent
QA PASS (`docs/review/wp34_r1_independent_qa_record.md`: 0 P0/P1/P2, 2 wording-only P3). The owner
approved on condition of that QA PASS. Part 1 (`docs/review/d04_owner_decision_part1_record.md`, 12
rare classes trained with WP35 enrichment) is unchanged.

## Decision — classes

The owner accepts the WP34-R1 proposal for every one of the 42 pending classes:

| WP34-R1 option | Owner decision | Classes | Evaluation status | Behaviour gate |
| --- | --- | --- | --- | --- |
| `KEEP_FULL` (≥ 3 D-02 groups) | `TRAIN_VAL_TEST` | 27 | `EVAL_ON_HELD_OUT_D02_GROUPS` | simulation only, after held-out evaluation |
| `KEEP_TRAIN_AND_TEST_NO_VAL` (2 groups) | `TRAIN_AND_TEST_NO_VAL` | 6 | `TEST_ONLY_WEAK_EVIDENCE` | simulation only, after held-out evaluation |
| `KEEP_TRAIN_ONLY_UNVERIFIED` (1 group, ≥ 30 images) | `TRAIN_ONLY_UNVERIFIED` | 9 | `EVAL_PENDING_REAL_INDEPENDENT_DATA` | no automatic vehicle behaviour until evaluated |

- Classes flagged `dominated` (largest group > 80 % of boxes): 11 I.409, 14 P.106a, 28 S.505a,
  38 P.127. Their evaluation status carries `_DOMINATED_GROUP`: any metric on them comes mostly
  from one capture and is weak evidence.
- `TRAIN_AND_TEST_NO_VAL` classes have no validation group; model selection and threshold tuning
  must not depend on them.
- `TRAIN_ONLY_UNVERIFIED` classes (including P.117 2,0 m) are handled like the part 1 classes:
  shown as "unverified", never used for automatic simulated behaviour, and need real images from
  another location before their accuracy can be reported.
- Height families P.117 and W.239b: all value classes are trained; the printed value stays
  unverified for behaviour (WP34-R1 P2-1 resolution).

With parts 1 and 2 every one of the 54 WP33 trainable classes now has an owner decision.

## Decision — negative frames

- `0544` is the only frame approved as detector background (no sign visible).
- The other 24 empty-label frames (0060, 0061, 0187, 1514, 1515, 1703–1708, 2015–2017, 2031, 2051,
  2723, 2766, 2793–2797, 2999) show signs that are not labelled. They are quarantined from all
  training, validation and test use until relabelled in a derived label set. Raw labels stay
  unchanged.

## Not decided here

- No split was generated. G0.7 (group-aware split) still has to place the part 1 rare-class groups
  in train and satisfy the per-class options above.
- G0.9 (dataset card) and D-05 (thresholds) remain open; Gate 0 is not open and training is not
  authorized by this record.
