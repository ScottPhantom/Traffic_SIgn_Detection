# D1-A3 versus YOLO11s-54 pilot: paired validation bootstrap CIs (R1)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)  
Status: `AWAITING_INDEPENDENT_QA`  
Package: `D1-A3-PILOT-PAIRED-CI-R1`  
Boundary: validation only, from existing prediction CSVs. No inference, no training, no threshold
or D-05 change, and no access to the sealed test (`sealed_test_accessed=false`).

## Why this exists

The append-only addendum to the YOLO54 improvement R3 contract (commit `5e3fa2a`) recorded that A3
does not meet R3's success criteria. It also listed one point as UNKNOWN: whether a **paired**
A3 − pilot interval excludes 0. Only per-model bootstrap CIs had been reported. This package
computes the paired intervals. It does not edit the addendum, the contract or any other record.

**Scope of the claim.** This is a single-seed description on validation. It is **not** a causal
test of `cos_lr`, because A3 (40 epochs, `cos_lr=True`) and the pilot (100 epochs, default
schedule) differ in both epoch count and LR schedule. It is also not a sealed-test result.

## Inputs (each SHA-256 verified before use)

| Input | Path | SHA-256 |
| --- | --- | --- |
| A3 prediction CSV | `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/a3_predictions.csv` | `e6a25b017bc94a3cf75220fcce1acdfd7bfacb088ca375143e3f0e5046b99ada` |
| A3 result JSON | `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/comparison_a3_r1.json` | `98b8947e379e2dbf88066884ee4540bc669f8402d459b1891b071b53ee2c2c73` |
| Common evaluator | `detector/colab/evaluate_d1_a3_r2_common_r1.py` | `5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6` |
| Common validation report | `docs/review/d1_a3_r2_common_validation_report_r1.md` | `2c893e0222275d735dbbafb4d7a8e74146e9906dfa16054e087cc507608e5494` |
| Validation bundle manifest | `tmp/yolo11n_n1_extract_r1/manifest.json` (git-ignored local extract) | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` |
| Pilot prediction CSV (bundle `data/yolo54_predictions_val.csv`) | same bundle | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` |
| D-02 group map (bundle `data/val_groups.json`) | same bundle | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682` |
| Class map (bundle `data/classes.csv`) | same bundle | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` |

How the pilot CSV, GT and groups were chosen: the evaluator calls
`common.verify_evaluation_scope(root, root / PINNED_YOLO54_PREDICTIONS, PINNED_YOLO54_SHA256)` and
`common.load_pinned_baseline(...)` from `evaluate_cascade_b0_r1.py`. Those pin
`data/yolo54_predictions_val.csv` (SHA `87884c53…`) inside the bundle with manifest SHA
`8e6ffe77…`. GT comes from that bundle's `data/labels54/val/*.txt` and groups from its
`data/val_groups.json`. The module reuses exactly these files. Every one of the 376 validation
images, 376 label files, the group map, the class map and the pilot CSV is checked against the
manifest's per-member SHA-256. Images are opened only for their pixel size, which is needed to
convert normalized labels to pixels. The bundle manifest records `test_included=false` and
`sealed_test_accessed=false`; no test path is read.

## Method

- **Matcher.** `detector/m1/metrics.py` (`match` / `operating_point`): greedy, IoU ≥ 0.5,
  descending score, the same as the common evaluator's D-05 operating points. Exact-class
  mAP50-95 uses the evaluator's pinned Ultralytics 8.4.172 `BaseValidator.match_predictions` +
  `ap_per_class`, copied from `evaluate_cascade_b0_r1.average_precision`.
- **Reproduction gate (passed).** Before any CI is computed, the module requires an exact match
  to the QA-passed result JSON. The checks are:
  - TP, FP, GT, recall, FP/image, per-class hits and per-class support at conf 0.20, and at each
    model's validation-selected point;
  - the selected confidence on the evaluator's grid (0.05 to 0.95);
  - both per-model `group_bootstrap` CIs;
  - exact-class mAP50-95, to 1e-12.

  Any difference aborts the run.

  | Model | TP@0.20 | FP@0.20 | Correct-class@0.20 | Recall@0.20 | FP/img@0.20 | Selected conf | Recall@sel | FP/img@sel |
  | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
  | Pilot | 547 | 150 | 457 | 0.8766 | 0.3989 | 0.20 | 0.8766 | 0.3989 |
  | A3 | 489 | 86 | 376 (0.6026) | 0.7837 | 0.2287 | 0.05 | 0.8670 | 0.5452 |

  These match every reference value in the task brief.
- **Paired group bootstrap.** 1000 rounds, NumPy `default_rng(20261018)`. Each round draws 9 of
  the 9 intact D-02 validation groups with replacement. Both models are scored on the **same**
  resampled frames, and the per-round difference (A3 − pilot) is recorded. The draw sequence is
  the same as `m1.metrics.group_bootstrap`, so the marginal CIs in the JSON equal the per-model
  CIs already published (`bootstrap_fixed_020`). The interval is the 95% percentile (NumPy
  linear). "Excludes 0" means lower > 0 or upper < 0.
- **Per-class keys.** The R3 contract's focus classes 7, 32 and 41 are **derived keys**, as in
  `yolo54_improvement_r3.FOCUS_KEYS`, not raw `yolo_id`s. The bundle class map resolves them to
  `yolo_id` 7 (P.123a), 33 (P.123b) and 42 (P.127, 40 km/h). In a round where a class has no
  sampled support, its difference is undefined and that round is skipped. The JSON records the
  number of rounds kept.

## Results

Group sizes (frames): 83, 69, 68, 39, 38, 35, 17, 14, 13. With only 9 clusters, percentile
cluster-bootstrap intervals are coarse and may under-cover. Read the borderline rows with that in
mind.

| # | Metric | A3 | Pilot | A3 − pilot | Paired 95% CI | Excludes 0? |
| --- | --- | ---: | ---: | ---: | --- | --- |
| 1 | Correct-class recall @0.20 | 0.6026 | 0.7324 | −0.1298 | [−0.2263, +0.0033] | **No** (upper bound just above 0; 2.7% of rounds > 0) |
| 2 | Class-agnostic recall @0.20 | 0.7837 | 0.8766 | −0.0929 | [−0.1832, +0.0291] | **No** (6.0% of rounds > 0) |
| 3 | FP/image @0.20 | 0.2287 | 0.3989 | −0.1702 | [−0.4136, +0.00005] | **No** (upper bound ≈ 0; 2.5% of rounds > 0) |
| 4a | Correct-class recall, validation-selected (A3 0.05 / pilot 0.20) | 0.6779 | 0.7324 | −0.0545 | [−0.1484, +0.0578] | **No** |
| 4b | Class-agnostic recall, validation-selected | 0.8670 | 0.8766 | −0.0096 | [−0.1136, +0.0716] | **No** |
| 4c | FP/image, validation-selected | 0.5452 | 0.3989 | +0.1463 | [−0.0360, +0.2812] | **No** (93.1% of rounds > 0) |
| 5a | Class key 7 (yolo 7) correct-class recall @0.20, support 111 in 2 groups | 0.4144 | 0.5946 | −0.1802 | [−0.3382, +0.0698] | **No**. LOW SUPPORT (2 groups; 892/1000 rounds defined) |
| 5b | Class key 32 (yolo 33) @0.20, support 29 in 1 group | 0.9655 | 0.6207 | +0.3448 | [+0.3448, +0.3448] | Arithmetically yes, but **not informative**: one group means zero resampling variance. Treat as UNKNOWN. LOW SUPPORT (647/1000 rounds defined) |
| 5c | Class key 41 (yolo 42) @0.20, support 26 in 2 groups | 0.5385 | 0.4615 | +0.0769 | [+0.0000, +0.1429] | **No** (lower bound = 0). LOW SUPPORT (874/1000 rounds defined) |
| opt | Exact-class mAP50-95 (pinned Ultralytics integrator) | 0.5633 | 0.6089 | −0.0456 | [−0.1017, −0.0161] | **Yes** (A3 lower; 0/1000 rounds > 0) |

Rows 4a–4c use a **validation-selected** operating point. Each model's confidence was chosen on
this same validation set to reach recall ≥ 0.85, so these rows are diagnostic only and not an
unbiased comparison.

The mAP50-95 interval averages over the classes present in each resample (Ultralytics
`ap_per_class` behavior), so the class set varies between rounds but is identical for both models
within a round. Per-group point differences at 0.20 are in the JSON under
`per_group_point_difference_fixed_020`. In correct-class recall, A3 is worse on groups C0001,
C0009, C0031 and C0034 and equal or better on the other five.

### Reading

- At conf 0.20, A3's point estimates are lower recall (exact-class and agnostic) and fewer
  FP/image. None of the three paired intervals excludes 0. The exact-class recall and FP/image
  upper bounds sit at about +0.003 and +0.00005, so both are borderline.
- At each model's validation-selected recall ≥ 0.85 point, no paired interval excludes 0.
- The only interval that clearly excludes 0 is exact-class mAP50-95: A3 is lower by about 0.046,
  with CI [−0.102, −0.016].
- The per-class focus results are too thin to support a conclusion. Each is carried by one or two
  capture groups.

This fills the UNKNOWN in the R3 addendum descriptively. It does not change the addendum's
disposition (A3 does not meet R3 criteria; do not replace the pilot), and it does not create any
new acceptance or promotion claim.

## Claim classification

| Claim | Class |
| --- | --- |
| Input SHA-256s above match, and the matcher reproduces the QA-passed A3/pilot numbers exactly | Verified artifact/result (this run) |
| Paired CIs and point differences in the table, recomputable with `verify` | Verified artifact/result (this run; awaiting independent QA) |
| CI for metrics 1–3 and 4a–4c includes 0; mAP50-95 CI excludes 0 | Verified artifact/result, conditional on the 9-group percentile bootstrap |
| Class key 32 difference has a meaningful CI | UNKNOWN (single supporting group) |
| `cos_lr` causes any of the differences | UNKNOWN (confounded with epochs; single seed) |
| Behavior on the sealed test or on other domains | UNKNOWN (not accessed) |

## Commands and results

Run from the repository root unless noted:

```bash
git log --oneline -3   # 5e3fa2a (HEAD), 724bf0c, 02ed548
graft check .          # OK — wiring graph in sync
(cd detector && uv run python -m m1.a3_pilot_paired_ci_r1 write)
# wrote docs/review/generated/d1_a3_pilot_paired_ci_r1.json sha256=19782743…b2f7
(cd detector && uv run python -m m1.a3_pilot_paired_ci_r1 verify)
# VERIFY PASS (~37 s, CPU; NumPy 2.5.4, Ultralytics 8.4.172, torch 2.14.1)
(cd detector && uv run pytest -q tests/test_a3_pilot_paired_ci_r1.py)   # 12 passed
(cd detector && uv run ruff check m1 tests)
uv run ruff check src tests
uv lock --check
graft build . && graft check .
```

The gate outcomes are listed in the handoff for this package. `verify` exits non-zero if the
recomputed canonical JSON differs from the stored file by even one byte.

## Files created

| File | SHA-256 |
| --- | --- |
| `detector/m1/a3_pilot_paired_ci_r1.py` | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` |
| `detector/tests/test_a3_pilot_paired_ci_r1.py` | `194a8f557af32ebdc734abf5fa61662175847307dd82a4af1a4fd0b6b11ae88b` |
| `docs/review/generated/d1_a3_pilot_paired_ci_r1.json` | `19782743d75d336be88cebf1e5558e1477b4f03ef4d929eaeb5230313b69b2f7` |
| `docs/review/d1_a3_pilot_paired_ci_r1_report.md` | this file (hash reported in handoff) |

The JSON is canonical: sorted keys, 2-space indent, `allow_nan=False`, trailing newline, and
finite values only. Undefined values would be `null`; none occur in this run. It records
`sealed_test_accessed=false`, `inference_run=false`, `training_run=false` and
`thresholds_changed=false`.

No existing file was edited. No git add, commit, stash, reset, checkout or push was run.

Status: `AWAITING_INDEPENDENT_QA`
