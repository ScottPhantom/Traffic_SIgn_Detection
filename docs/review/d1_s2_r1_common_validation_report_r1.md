# D1-S2-R1 versus pilot: common R3 validation report

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Scope: variation between the pilot
seed 20261018 and its unchanged-configuration repeat seed 20261019. This is
validation only: 376 R3 images, 624 GT boxes, nine D-02 groups. Confidence
is fixed at 0.20 for the operating-point comparison. No threshold is locked.
`sealed_test_accessed=false`.

## Evidence and gates

- D1-S2-R1 Colab training completed 100 epochs on a fresh L4 smoke and a
  distinct L4 resume. Execution record:
  `docs/review/d1_s2_r1_execution_record.md` (commit `1ce850f`).
  Independent completed-run QA:
  `docs/review/d1_s2_r1_result_independent_qa_record.md` (commit `dec11bb`,
  SHA-256 `68ce90a9b34bb65b7bd85f3120ac96c064cbae1b36f7ddfd510a35a1187f0ec3`),
  `Verdict: PASS`.
- The source-QA-passed evaluator
  `detector/colab/evaluate_d1_s2_r1_common_r1.py` read the QA-pinned result
  archive/manifest and inferred only on the governed R3 validation bundle.
  `s2_predictions.csv` SHA-256
  `eb0ca49efde4a4c921c38e2eb00d7136a29c50d50e46cd49557356ca9c9a33b8`;
  `comparison_s2_r1.json` SHA-256
  `0d76dc34eaa8dfe4c155dfb16a0d150862ae2e568c623319f3a65db45c5a46b4`.
  Both are kept locally and uncommitted under
  `results/experiments/d1_s2_seed_20261019_r1/evaluation_common_r1/`.
- The source-QA-passed paired-CI command ran `write` and `verify` successfully.
  Its output is `docs/review/generated/d1_s2_pilot_paired_ci_r1.json`,
  SHA-256 `57b386e3c1396449992a77e020200a953d3759b9d03968ac893d377a8ea37760`.
  It uses 1,000 paired resamples of intact D-02 groups at seed 20261018,
  always comparing both models on the same resampled groups. The CI describes
  this validation roster and nine groups; it is not a confidence interval over
  model-training seeds in general.

## Fixed confidence 0.20 comparison

All differences are seed 20261019 minus seed 20261018. The 95% intervals are
paired nine-group bootstrap intervals; percentage-point units are used for
recall and mAP differences.

| Measure | Seed 20261018 | Seed 20261019 | Difference | Paired 95% CI |
| --- | ---: | ---: | ---: | ---: |
| Agnostic GT recall | 547/624 = 87.66% | 507/624 = 81.25% | −6.41 pp | −16.34 to +0.83 pp |
| Correct-class GT recall | 457/624 = 73.24% | 379/624 = 60.74% | −12.50 pp | −23.56 to −1.42 pp |
| False positives per image | 150/376 = 0.399 | 127/376 = 0.338 | −0.061 | −0.365 to +0.145 |
| Exact-class mAP50 | 0.8521 | 0.7309 | −0.1212 | −0.1816 to −0.0365 |
| Exact-class mAP50–95 | 0.6089 | 0.5209 | −0.0880 | −0.1433 to −0.0389 |

At this fixed operating point, S2 produces 23 fewer false positives but also
misses 40 more localized GT boxes and 78 more correct-class GT boxes. The
exact-class mAP measures decrease. This is the observed seed-to-seed variation
of the unchanged pilot configuration, not an improvement test.

## Derived critical keys

The project keys map to YOLO IDs 7→7, 32→33 and 41→42. Values below are
correct-class recall at confidence 0.20.

| Derived key (YOLO ID) | GT support | Seed 20261018 | Seed 20261019 | Difference |
| --- | ---: | ---: | ---: | ---: |
| 7 (7) | 111 | 66/111 = 59.46% | 75/111 = 67.57% | +8.11 pp |
| 32 (33) | 29 | 18/29 = 62.07% | 16/29 = 55.17% | −6.90 pp |
| 41 (42) | 26 | 12/26 = 46.15% | 10/26 = 38.46% | −7.69 pp |

All three have limited group support. In particular, key 32 has GT in only
one group; its paired bootstrap interval is degenerate and is not an
informative uncertainty estimate. The other two have support in only two
groups each.

## Direct answer and limits

The pilot's 0.399 false positives per image is **not established as stable**
by this second seed. S2 measures 0.338, a point difference of −0.061, but the
paired group interval spans −0.365 to +0.145 and includes zero. With two train
seeds and nine validation groups, the data do not tightly bound the FP rate's
seed-to-seed variation. Correct-class recall and exact-class mAP are lower for
S2 on this same roster, so a lower FP count alone must not be called a model
gain.

The S2 evaluator also reports an in-sample selected confidence of 0.15; this
report does not adopt it or compare it to the pilot's 0.20 as a locked policy.
The three-seed threshold-selection contract remains a separate task. No D-05
GO decision, application activation, sealed-test score, or deployment claim is
made here.

Independent QA of the comparison CSV, JSON and paired intervals is `PASS` in
`docs/review/d1_s2_r1_common_validation_result_independent_qa_record.md`,
SHA-256 `4fc33d5375e1cc9df14ab64c472242530b619081b8f48b0c3cf9e1898773ca3f`.
