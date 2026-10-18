# M0-WP36 — G0.7 group-aware split

Status: `WP36_AWAITING_QA_REVIEW`
Boundary: `G07_SPLIT_PROPOSAL_NOT_OWNER_ACCEPTED_NO_TRAINING`

Built from the owner's G0.7 decision (`docs/review/g07_owner_decision_record.md`, option A). Every
D-02 group is in exactly one split. Nothing here authorizes training; the split becomes the
G0.7 split only after independent QA and owner acceptance.

## Splits (usable frames: quarantined negatives excluded, 0544 counted as train background)

| Split | Groups | Frames | Share |
| --- | --- | --- | --- |
| train | 33 | 2114 | 66.2% |
| val | 11 | 372 | 11.7% |
| test | 10 | 705 | 22.1% |

- 15 groups are forced into train (single-group classes, class 38, WP35 sources).
- 24 quarantined negatives are listed in
  `wp36_split_frames.csv` with `use=QUARANTINED` and left out of every split list; stem 0248 is absent.
- **Test seal:** SHA-256 of the sorted test stem list = `01bdb9890036a44659e809af88d465c5ae67aefbd39f39d770e5ba4bcd575681`. Any change
  to the test list needs a new append-only split version. The M1 loader must refuse TEST frames
  outside an explicit, logged final-evaluation run.
- Search: seed 20261018, 120 restarts; objective {"unmet_requirements": 1, "band_violation": 0.048569, "classes_with_2plus_test_groups": 7, "ratio_deviation": 0.138569, "box_balance_deviation": 0.146321}.

## Owner review points (structural, not search artifacts)

- **Ratio band.** Usable shares are train 66.2% / val 11.7% / test
  22.1%; band violation 0.049. Option A sends
  D02-C0048 (411 frames, the only free group of classes 18, 40 and 45) to test. Together with the
  single free groups of 17/19, 20, 28/30 and 50 and one test group each for 9, 11 and 25, the test
  split needs at least about 20 % of the frames, so the ±3-point band cannot be met under option A.
- **Classes 22 and 25 compete for D02-C0032.** 22 needs val, and its only other free group (C0030)
  must be test for 28 and 30. 25 has only C0032 and C0036, and needs one in train and one in test.
  At least one requirement fails whatever the search does; this build leaves
  25 unmet.
- Owner choices: accept as built; or accept a smaller test for 18/40/45 (C0048 to val, giving
  them no sealed test); or move class 25 to train-only.

## Class coverage

- Requirements not met: 25.
- No validation, so not for tuning: 9, 11, 17, 18, 19, 20, 25, 28, 30, 40, 45, 50.
- Train only (no sealed test, accuracy unknown): 1, 15, 16:2.0, 16:2.2, 16:2.5, 21, 24, 27, 29, 33, 35, 36, 37, 38, 42, 43:2.5, 43:2.7, 44, 47, 48, 49, 51.
- `TRAIN_VAL_TEST` classes with a single test group (weaker test evidence):
  4, 6, 7, 8, 12, 14, 22, 23, 26, 32, 34, 39, 46.

| Class | D-04 | Required | Groups train/val/test | Boxes train/val/test | Met |
| --- | --- | --- | --- | --- | --- |
| 0 | TRAIN_VAL_TEST | train val test | 7/1/3 | 233/13/66 | yes |
| 1 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 22/0/0 | yes |
| 2 | TRAIN_VAL_TEST | train val test | 8/1/2 | 376/4/90 | yes |
| 3 | TRAIN_VAL_TEST | train val test | 8/1/2 | 375/4/75 | yes |
| 4 | TRAIN_VAL_TEST | train val test | 1/1/1 | 12/12/9 | yes |
| 5 | TRAIN_VAL_TEST | train val test | 6/2/4 | 130/27/99 | yes |
| 6 | TRAIN_VAL_TEST | train val test | 3/1/1 | 156/22/4 | yes |
| 7 | TRAIN_VAL_TEST | train val test | 3/2/1 | 126/112/9 | yes |
| 8 | TRAIN_VAL_TEST | train val test | 3/1/1 | 150/51/12 | yes |
| 9 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 14/0/29 | yes |
| 10 | TRAIN_VAL_TEST | train val test | 11/3/5 | 658/80/333 | yes |
| 11 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 21/0/5 | yes |
| 12 | TRAIN_VAL_TEST | train val test | 3/3/1 | 166/61/53 | yes |
| 13 | TRAIN_VAL_TEST | train val test | 8/1/3 | 241/11/120 | yes |
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
| 22 | TRAIN_VAL_TEST | train val test | 1/1/1 | 100/11/20 | yes |
| 23 | TRAIN_VAL_TEST | train val test | 6/1/1 | 280/18/167 | yes |
| 24 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 56/0/0 | yes |
| 25 | TRAIN_AND_TEST_NO_VAL | train test | 1/1/0 | 7/18/0 | **NO** |
| 26 | TRAIN_VAL_TEST | train val test | 2/1/1 | 61/1/18 | yes |
| 27 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 36/0/0 | yes |
| 28 | TRAIN_AND_TEST_NO_VAL | train test | 1/0/1 | 26/0/1 | yes |
| 29 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 45/0/0 | yes |
| 30 | TRAIN_VAL_TEST | train test | 2/0/1 | 93/0/45 | yes |
| 32 | TRAIN_VAL_TEST | train val test | 5/1/1 | 105/29/52 | yes |
| 33 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 19/0/0 | yes |
| 34 | TRAIN_VAL_TEST | train val test | 3/1/1 | 60/21/1 | yes |
| 35 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 87/0/0 | yes |
| 36 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 75/0/0 | yes |
| 37 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 47/0/0 | yes |
| 38 | TRAIN_ONLY_UNVERIFIED | train | 2/0/0 | 189/0/0 | yes |
| 39 | TRAIN_VAL_TEST | train val test | 5/1/1 | 253/54/152 | yes |
| 40 | TRAIN_VAL_TEST | train test | 2/0/1 | 67/0/143 | yes |
| 41 | TRAIN_VAL_TEST | train val test | 10/1/2 | 210/23/42 | yes |
| 42 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 21/0/0 | yes |
| 43:2.5 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 22/0/0 | yes |
| 43:2.7 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 5/0/0 | yes |
| 44 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 3/0/0 | yes |
| 45 | TRAIN_VAL_TEST | train test | 4/0/1 | 125/0/70 | yes |
| 46 | TRAIN_VAL_TEST | train val test | 3/4/1 | 220/168/47 | yes |
| 47 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 16/0/0 | yes |
| 48 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 41/0/0 | yes |
| 49 | TRAIN_ONLY_UNVERIFIED | train | 1/0/0 | 219/0/0 | yes |
| 50 | TRAIN_VAL_TEST | train test | 2/0/1 | 113/0/8 | yes |
| 51 | TRAIN_WITH_ENRICHMENT | train | 1/0/0 | 5/0/0 | yes |

## Groups

| Group | Frames | Split | Assignment | Classes |
| --- | --- | --- | --- | --- |
| D02-C0001 | 71 | val | SEARCH | 46 |
| D02-C0002 | 120 | train | FORCED_TRAIN | 49 |
| D02-C0003 | 9 | test | SEARCH | 4 7 |
| D02-C0004 | 12 | train | SEARCH | 5 |
| D02-C0005 | 41 | test | SEARCH | 0 2 3 5 8 9 |
| D02-C0006 | 15 | test | SEARCH | 10 11 |
| D02-C0007 | 21 | train | SEARCH | 11 |
| D02-C0008 | 17 | val | SEARCH | 5 12 |
| D02-C0009 | 68 | val | SEARCH | 5 6 7 8 |
| D02-C0010 | 21 | train | FORCED_TRAIN | 6 42 |
| D02-C0011 | 17 | train | SEARCH | 13 |
| D02-C0012 | 21 | val | SEARCH | 10 34 |
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
| D02-C0028 | 2 | val | SEARCH | 26 |
| D02-C0029 | 3 | train | SEARCH | 10 |
| D02-C0030 | 63 | test | SEARCH | 0 5 10 13 22 28 30 32 |
| D02-C0031 | 38 | train | SEARCH | 10 12 23 26 39 41 |
| D02-C0032 | 41 | val | SEARCH | 10 13 22 23 25 41 |
| D02-C0033 | 16 | train | SEARCH | 9 |
| D02-C0034 | 39 | val | SEARCH | 12 14 |
| D02-C0035 | 44 | val | SEARCH | 7 10 46 |
| D02-C0036 | 65 | train | SEARCH | 5 8 10 23 25 32 41 |
| D02-C0037 | 13 | train | SEARCH | 0 4 |
| D02-C0038 | 226 | train | FORCED_TRAIN | 10 14 20 23 29 32 34 38 39 40 46 |
| D02-C0039 | 18 | train | SEARCH | 2 3 41 |
| D02-C0040 | 75 | train | FORCED_TRAIN | 13 30 36 37 |
| D02-C0041 | 49 | test | SEARCH | 13 50 |
| D02-C0042 | 13 | val | SEARCH | 0 4 |
| D02-C0043 | 28 | train | SEARCH | 5 13 |
| D02-C0044 | 83 | train | SEARCH | 2 3 7 10 34 |
| D02-C0045 | 14 | train | SEARCH | 41 |
| D02-C0046 | 72 | train | SEARCH | 0 5 6 32 41 |
| D02-C0047 | 10 | train | SEARCH | 0 5 |
| D02-C0048 | 411 | test | SEARCH | 2 3 5 10 12 13 18 23 26 34 39 40 41 45 |
| D02-C0049 | 115 | train | FORCED_TRAIN | 2 3 8 10 12 32 33 39 45 |
| D02-C0050 | 23 | val | SEARCH | 2 3 12 39 46 |
| D02-C0051 | 513 | train | FORCED_TRAIN | 0 2 3 6 8 10 12 13 17 23 28 30 35 38 39 40 41 45 46 48 50 |
| D02-C0052 | 36 | test | SEARCH | 14 46 |
| D02-C0053 | 25 | train | FORCED_TRAIN | 32 45 47 |
| D02-C0054 | 26 | train | SEARCH | 2 3 |

## Known limits

- D-02 groups come from AI visual review. The same physical sign can still appear in two groups,
  so test scores may be optimistic.
- Train-only classes have no sealed test; their accuracy is unknown until real independent images exist.
- Box counts per split are uneven per class; small test counts (for example class 28 or 50) give
  wide confidence intervals.
