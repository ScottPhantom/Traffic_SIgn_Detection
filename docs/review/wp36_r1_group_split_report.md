# M0-WP36-R1 — G0.7 group-aware split (owner ranking applied literally)

Status: `WP36_R1_AWAITING_QA_REVIEW`
Boundary: `G07_SPLIT_PROPOSAL_NOT_OWNER_ACCEPTED_NO_TRAINING`

Corrects WP36 (`docs/review/wp36_independent_qa_record.md`: PASS with 1 P2, 3 P3) under the owner's
clarification `docs/review/g07_owner_decision_r1_record.md`. WP36 stays byte-identical. Nothing
here authorizes training; the split becomes the G0.7 split only after independent QA and owner
acceptance.

## What changed from WP36

- **P2-1:** objective order is now unmet_requirements > classes_with_2plus_test_groups > band_violation > ratio_deviation > box_balance_deviation. Two or more test groups
  per `TRAIN_VAL_TEST` class now outranks the ±3-point band, as the G0.7 record lists.
- **P3-1:** ratio terms count usable frames (the 24 quarantined negatives excluded).
- **P3-2:** `check-candidate` in this builder rejects quarantined stems, a background frame outside
  train, and any list whose SHA-256 differs from `split_list_sha256`. The M1 loader must call it.
- **P3-3:** the D-02 candidate check runs in a temporary directory.

## Splits (usable frames)

| Split | Groups | Frames | Share |
| --- | --- | --- | --- |
| train | 29 | 1912 | 59.9% |
| val | 9 | 376 | 11.8% |
| test | 16 | 903 | 28.3% |

- Objective reached: 17 `TRAIN_VAL_TEST` classes with ≥2 test groups;
  ratio band violation 0.176 (the test split is above the 15 ± 3 % target,
  accepted by the owner in the R1 record).
- 15 groups are forced into train; 24 quarantined
  negatives are excluded; background frame(s): 0544 (train).
- **Test seal:** `afa03d4b6deb7567c5784b29122966d84599d4eb81fdbad37c3b20adaf7524bc` (sha256 of the sorted stems joined by '\n', no trailing newline). Any change to
  the test list needs a new append-only split version.

## Class coverage

- Requirements not met: 22. Class 22 and class 25 both depend on group
  D02-C0032; the owner accepted that 22 loses validation so that 25 keeps a test group.
- Not usable for model selection or threshold tuning (no validation group): 9, 11, 17, 18, 19, 20, 22, 25, 28, 30, 40, 45, 50.
- Train only (no sealed test, accuracy unknown): 1, 15, 16:2.0, 16:2.2, 16:2.5, 21, 24, 27, 29, 33, 35, 36, 37, 38, 42, 43:2.5, 43:2.7, 44, 47, 48, 49, 51.
- `TRAIN_VAL_TEST` classes with a single test group: 4, 8, 14, 17, 18, 19, 30, 40, 45, 50.

| Class | D-04 | Required | Groups train/val/test | Boxes train/val/test | Met |
| --- | --- | --- | --- | --- | --- |
| 0 | TRAIN_VAL_TEST | train val test | 6/1/4 | 204/13/95 | yes |
| 1 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 22/0/0 | yes |
| 2 | TRAIN_VAL_TEST | train val test | 7/1/3 | 371/5/94 | yes |
| 3 | TRAIN_VAL_TEST | train val test | 7/1/3 | 370/5/79 | yes |
| 4 | TRAIN_VAL_TEST | train val test | 1/1/1 | 12/12/9 | yes |
| 5 | TRAIN_VAL_TEST | train val test | 6/1/5 | 128/14/114 | yes |
| 6 | TRAIN_VAL_TEST | train val test | 2/1/2 | 145/22/15 | yes |
| 7 | TRAIN_VAL_TEST | train val test | 2/2/2 | 83/111/53 | yes |
| 8 | TRAIN_VAL_TEST | train val test | 3/1/1 | 150/51/12 | yes |
| 9 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 14/0/29 | yes |
| 10 | TRAIN_VAL_TEST | train val test | 9/2/8 | 637/21/413 | yes |
| 11 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 21/0/5 | yes |
| 12 | TRAIN_VAL_TEST | train val test | 3/2/2 | 150/57/73 | yes |
| 13 | TRAIN_VAL_TEST | train val test | 7/1/4 | 224/17/131 | yes |
| 14 | TRAIN_VAL_TEST | train val test | 2/1/1 | 9/3/73 | yes |
| 15 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 29/0/0 | yes |
| 16:2.0 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 43/0/0 | yes |
| 16:2.2 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 18/0/0 | yes |
| 16:2.5 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 9/0/0 | yes |
| 17 | TRAIN_VAL_TEST | train test | 3/0/1 | 95/0/10 | yes |
| 18 | TRAIN_VAL_TEST | train test | 2/0/1 | 151/0/62 | yes |
| 19 | TRAIN_VAL_TEST | train test | 2/0/1 | 16/0/13 | yes |
| 20 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 30/0/22 | yes |
| 21 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 11/0/0 | yes |
| 22 | TRAIN_VAL_TEST | train val test | 1/0/2 | 100/0/31 | **NO** |
| 23 | TRAIN_VAL_TEST | train val test | 5/1/2 | 264/16/185 | yes |
| 24 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 56/0/0 | yes |
| 25 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 7/0/18 | yes |
| 26 | TRAIN_VAL_TEST | train val test | 1/1/2 | 47/14/19 | yes |
| 27 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 36/0/0 | yes |
| 28 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 26/0/1 | yes |
| 29 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 45/0/0 | yes |
| 30 | TRAIN_VAL_TEST | train test | 2/0/1 | 93/0/45 | yes |
| 32 | TRAIN_VAL_TEST | train val test | 4/1/2 | 86/29/71 | yes |
| 33 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 19/0/0 | yes |
| 34 | TRAIN_VAL_TEST | train val test | 2/1/2 | 23/37/22 | yes |
| 35 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 87/0/0 | yes |
| 36 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 75/0/0 | yes |
| 37 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 47/0/0 | yes |
| 38 | TRAIN_ONLY_UNVERIFIED | train | 2/0/0 | 189/0/0 | yes |
| 39 | TRAIN_VAL_TEST | train val test | 4/1/2 | 245/8/206 | yes |
| 40 | TRAIN_VAL_TEST | train test | 2/0/1 | 67/0/143 | yes |
| 41 | TRAIN_VAL_TEST | train val test | 7/2/4 | 171/21/83 | yes |
| 42 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 21/0/0 | yes |
| 43:2.5 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 22/0/0 | yes |
| 43:2.7 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 5/0/0 | yes |
| 44 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 3/0/0 | yes |
| 45 | TRAIN_VAL_TEST | train test | 4/0/1 | 125/0/70 | yes |
| 46 | TRAIN_VAL_TEST | train val test | 3/2/3 | 220/104/111 | yes |
| 47 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 16/0/0 | yes |
| 48 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 41/0/0 | yes |
| 49 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 219/0/0 | yes |
| 50 | TRAIN_VAL_TEST | train test | 2/0/1 | 113/0/8 | yes |
| 51 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 5/0/0 | yes |

## Groups

| Group | Usable frames | Split | Assignment | Classes |
| --- | --- | --- | --- | --- |
| D02-C0001 | 69 | val | SEARCH | 46 |
| D02-C0002 | 119 | train | FORCED_TRAIN | 49 |
| D02-C0003 | 9 | test | SEARCH | 4 7 |
| D02-C0004 | 12 | train | SEARCH | 5 |
| D02-C0005 | 41 | test | SEARCH | 0 2 3 5 8 9 |
| D02-C0006 | 15 | test | SEARCH | 10 11 |
| D02-C0007 | 21 | train | SEARCH | 11 |
| D02-C0008 | 17 | train | SEARCH | 5 12 |
| D02-C0009 | 68 | val | SEARCH | 5 6 7 8 |
| D02-C0010 | 21 | train | FORCED_TRAIN | 6 42 |
| D02-C0011 | 17 | val | SEARCH | 13 |
| D02-C0012 | 21 | test | SEARCH | 10 34 |
| D02-C0013 | 29 | train | FORCED_TRAIN | 13 15 |
| D02-C0014 | 87 | train | FORCED_TRAIN | 0 1 2 3 13 41 50 51 |
| D02-C0015 | 44 | train | FORCED_TRAIN | 10 18 41 16:2.0 43:2.5 |
| D02-C0016 | 10 | train | FORCED_TRAIN | 19 16:2.5 |
| D02-C0017 | 40 | test | SEARCH | 10 17 19 41 |
| D02-C0018 | 25 | test | SEARCH | 10 20 |
| D02-C0019 | 45 | train | FORCED_TRAIN | 7 10 17 19 34 44 45 |
| D02-C0020 | 35 | val | SEARCH | 32 46 |
| D02-C0021 | 11 | train | FORCED_TRAIN | 13 21 |
| D02-C0022 | 68 | train | FORCED_TRAIN | 10 14 18 22 23 24 39 41 46 16:2.2 43:2.7 |
| D02-C0023 | 17 | train | SEARCH | 2 3 |
| D02-C0024 | 16 | test | SEARCH | 0 5 6 |
| D02-C0025 | 66 | train | SEARCH | 7 |
| D02-C0026 | 38 | train | SEARCH | 0 41 |
| D02-C0027 | 190 | train | FORCED_TRAIN | 0 2 3 5 10 13 17 23 26 27 |
| D02-C0028 | 2 | test | SEARCH | 26 |
| D02-C0029 | 3 | train | SEARCH | 10 |
| D02-C0030 | 63 | test | SEARCH | 0 5 10 13 22 28 30 32 |
| D02-C0031 | 38 | val | SEARCH | 10 12 23 26 39 41 |
| D02-C0032 | 41 | test | SEARCH | 10 13 22 23 25 41 |
| D02-C0033 | 16 | train | SEARCH | 9 |
| D02-C0034 | 39 | val | SEARCH | 12 14 |
| D02-C0035 | 44 | test | SEARCH | 7 10 46 |
| D02-C0036 | 65 | train | SEARCH | 5 8 10 23 25 32 41 |
| D02-C0037 | 13 | train | SEARCH | 0 4 |
| D02-C0038 | 218 | train | FORCED_TRAIN | 10 14 20 23 29 32 34 38 39 40 46 |
| D02-C0039 | 18 | train | SEARCH | 2 3 41 |
| D02-C0040 | 75 | train | FORCED_TRAIN | 13 30 36 37 |
| D02-C0041 | 49 | test | SEARCH | 13 50 |
| D02-C0042 | 13 | val | SEARCH | 0 4 |
| D02-C0043 | 28 | train | SEARCH | 5 13 |
| D02-C0044 | 83 | val | SEARCH | 2 3 7 10 34 |
| D02-C0045 | 14 | val | SEARCH | 41 |
| D02-C0046 | 67 | test | SEARCH | 0 5 6 32 41 |
| D02-C0047 | 10 | train | SEARCH | 0 5 |
| D02-C0048 | 411 | test | SEARCH | 2 3 5 10 12 13 18 23 26 34 39 40 41 45 |
| D02-C0049 | 115 | train | FORCED_TRAIN | 2 3 8 10 12 32 33 39 45 |
| D02-C0050 | 23 | test | SEARCH | 2 3 12 39 46 |
| D02-C0051 | 505 | train | FORCED_TRAIN | 0 2 3 6 8 10 12 13 17 23 28 30 35 38 39 40 41 45 46 48 50 |
| D02-C0052 | 36 | test | SEARCH | 14 46 |
| D02-C0053 | 25 | train | FORCED_TRAIN | 32 45 47 |
| D02-C0054 | 26 | train | SEARCH | 2 3 |

## Known limits

- D-02 groups come from AI visual review; the same physical sign can still appear in two groups,
  so test scores may be optimistic.
- Train-only classes have no sealed test; their accuracy is unknown until real independent images exist.
- Validation is small; per-class validation counts are thin, so tuning must use pooled metrics.
