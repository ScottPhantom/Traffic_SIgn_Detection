# Independent QA record — D1-A3-PILOT-PAIRED-CI-R1

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)  
Reviewer: independent Claude Code QA session. This session did not author the package and did not
import or reuse the author's module for any recomputation.  
Package under review: `D1-A3-PILOT-PAIRED-CI-R1` (paired A3 − pilot validation bootstrap CIs)  
Boundary: validation only, from existing prediction CSVs. No inference, no training, no threshold
or D-05 change, no edit to any existing file, and no git add, commit, stash, reset, clean,
checkout or push. `sealed_test_accessed=false`.

Verdict: PASS

Every reviewed SHA-256 and every input SHA-256 matches. An independently written scorer
reproduces all point values and all paired and marginal CIs in the report to **0.0** absolute
difference. That covers rows 1–3, 4a–4c, 5a–5c and exact-class mAP50-95, so the 1e-9 tolerance
holds with no slack used. Every "excludes 0?" statement matches its numbers, and the scope and
caveat language is correct. The non-blocking observations below need no change to the report.

## Starting state

- HEAD: `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`, which is
  the expected HEAD. Previous commits: `724bf0c`, `02ed548`.
- `git status --short | head -60` at start: the Owner's 12 modified tracked files
  (`PROJECT_MEMORY.md`, `docs/product_roadmap.md`, `docs/review_index.md`,
  `scripts/run_parallel_checks.py`, five `src/cpv301_autodrive/*` files and three `tests/*`
  files), followed by untracked `detector/colab/*`, `detector/m1/*` and `detector/tests/*` files.
  These include the package's `detector/m1/a3_pilot_paired_ci_r1.py` and
  `detector/tests/test_a3_pilot_paired_ci_r1.py`. None of these files were touched by this QA.
- `graft check .` at start: `graph check: OK — the wiring graph is in sync with the code`
  (meaning tier not built; wiring graph authoritative).

## Q1–Q7

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| Q1 | Inputs: SHA-256s, evaluator pins, no test path | **PASS** | All 8 input SHAs in the report match, plus `m1/metrics.py` `d24570f8…` and the AP source `evaluate_cascade_b0_r1.py` `8bedb4c1…`. The evaluator pins the bundle via `verify_package(root, BUNDLE_SHA256)` with `BUNDLE_SHA256 = 8e6ffe77…` (`evaluate_d1_a3_r2_common_r1.py:26,177`). It pins the pilot CSV via `common.verify_evaluation_scope(root, root / PINNED_YOLO54_PREDICTIONS, PINNED_YOLO54_SHA256)` with `data/yolo54_predictions_val.csv` = `87884c53…` (`evaluate_cascade_b0_r1.py:43-44`, `:247-289`). My scorer checked 755 bundle members against the manifest's per-member SHA: 376 val images, 376 `labels54/val` files, the group map, the class map and the pilot CSV. All matched. Manifest: `test_included=false`, `sealed_test_accessed=false`. No manifest member has a `test` path component, and the bundle `data/` has only `train`/`val` (images, labels) and `val` (labels54). The module reads only `data/images/val`, `data/labels54/val`, `val_groups.json`, `classes.csv` and the pilot CSV. |
| Q2 | Independent reproduction of operating points | **PASS** | Pilot @0.20: TP 547, FP 150, correct-class 457, recall 0.8766, FP/img 0.3989; selected conf 0.20. A3 @0.20: 489 / 86 / 376 (0.6026), 0.7837, 0.2287. A3 selected conf 0.05: recall 0.8670, FP/img 0.5452, correct-class 423 (0.6779). TP, FP, recall, FP/img, per-class hits and per-class support at 0.20, and the selected conf/recall/FP at the selected point, are exactly equal to `comparison_a3_r1.json` (`98b8947e…`). |
| Q3 | Independent paired bootstrap | **PASS** | Own implementation: `default_rng(20261018)`, 1000 rounds, `rng.choice(sorted(9 group names), 9, replace=True)`, and the same draw indices for both models. Rows 1–3 and 4a–4c paired CIs, point differences and share-of-rounds > 0 all equal the author's JSON (max \|Δ\| = 0.0). My per-round marginals equal `m1.metrics.group_bootstrap` for both models at both operating points (max \|Δ\| = 0.0). At 0.20 they also equal the published `bootstrap_fixed_020` in `comparison_a3_r1.json`, so the draw sequence is the same. |
| Q4 | Per-class keys, support, groups, rounds | **PASS** | From `classes.csv`, derived keys 7, 32 and 41 map to `yolo_id` 7 (P.123a), 33 (P.123b) and 42 (P.127, 40 km/h). Raw `yolo_id` 32 and 41 (derived keys 30 and 40) have 0 validation support. The R3 contract states focus supports "111, 29, 26" (`d1_yolo54_improvement_r3_contract.md:143`), which matches only the derived-key reading. Support and groups: key 7 has 111 in 2 groups (C0009: 68, C0044: 43); key 32 has 29 in 1 group (C0020); key 41 has 26 in 2 groups (C0031: 12, C0045: 14). Rounds defined: 892, 647, 874, matching the author. Key 32 takes the single value +0.3448 in every defined round. That is a zero-variance interval and carries no information about uncertainty, so reporting it as UNKNOWN is correct. |
| Q5 | mAP50-95 integrator, point and CI | **PASS** | `evaluate_cascade_b0_r1.average_precision` (Ultralytics 8.4.172 `BaseValidator.match_predictions` + `ap_per_class`) imported directly gives A3 0.5633040246174713 and pilot 0.6088678434901063, exactly equal to the common JSON. Own paired CI: per-frame `match_predictions` matrices are precomputed and `ap_per_class` is called on each round's concatenation, after checking that this equals the full-set `average_precision` to 1e-12. Result: [−0.1016516308, −0.0161464310], 0/1000 rounds > 0, equal to the author's JSON (\|Δ\| = 0.0). CPU time is about 6 s. |
| Q6 | Claims | **PASS** | Every "excludes 0?" cell matches its interval under "lower > 0 or upper < 0". Rows 1–3, 4a–4c and 5a are No. Row 5c is No because its lower bound is exactly 0.0. Row 5b is arithmetically yes but flagged UNKNOWN. mAP is Yes. Rows 4a–4c are explicitly labelled validation-selected and diagnostic-only, and the JSON label is `VALIDATION_SELECTED_DIAGNOSTIC_ONLY`. The report says it is "not a causal test of `cos_lr`" and classifies causality as UNKNOWN. It makes no sealed-test claim, and it states that it does not change the R3 addendum's disposition. The 9-cluster coarseness and under-coverage caveat is present. Group sizes 83/69/68/39/38/35/17/14/13 are reproduced. The per-group statement (A3 worse in correct-class recall on C0001, C0009, C0031, C0034; equal or better on the other five) was independently recomputed and is correct. |
| Q7 | Determinism, gates, module hygiene | **PASS** | All gates are green; see the commands below. `verify` byte-compares the recomputed canonical JSON with the stored file. `canonical()` uses `sort_keys=True` and `allow_nan=False`. `write` opens with mode `"x"`, so it is write-once and never overwrites. `_require` rejects symlinks and non-files and checks the SHA. The output path is fixed under `REPO_ROOT`. A `--bundle` override still has to pass the pinned manifest SHA and every per-member SHA. |

## Non-blocking observations (no report correction required)

1. **Row 5c is close to degenerate as well.** Of its two supporting groups, C0031 has
   A3 = pilot = 0/12, so it adds a difference of 0. C0045 has A3 14/14 vs pilot 12/14. The
   difference is therefore ≥ 0 by construction in every defined round, and the lower bound of
   exactly 0 is a resampling artefact, not evidence of a tie. Row 5a likewise mixes only two
   groups that point in opposite directions (C0009 −0.338, C0044 +0.070). The report already
   flags both rows LOW SUPPORT and says the focus results "are too thin to support a
   conclusion". That is adequate. A future revision could add the per-group composition shown
   here.
2. **`with_predictions` does not check the CSV header**, unlike the evaluator's
   `load_pinned_baseline`. The SHA pin on both CSVs makes this moot for this package.
3. **Gate outcomes are not in the report itself.** The report's "Commands and results" section
   defers gate outcomes to the handoff. This record supplies them.

## Commands and results

Run from the repository root unless noted. The independent scorer is outside the repo:
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/1c56fa21-9f39-4b08-89fd-9b3c898ffd93/scratchpad/qa_paired_ci.py`
(`8f4fc0f8af150ffbb0f49ab442910b6b603245fbf976db7cef4b2cdd4dc6669a`), plus a per-group helper
`qa_pergroup.py` (`3869157dd480f5674fd20015506212e3ca97bd5647c0f79cd091b9232b67d13d`) in the
same folder. Environment: NumPy 2.5.4, Ultralytics 8.4.172, torch 2.14.1 (detector venv).

| Command | Result |
| --- | --- |
| `git log --oneline -3` | `5e3fa2a`, `724bf0c`, `02ed548` |
| `graft check .` (start and end) | `graph check: OK — the wiring graph is in sync with the code` |
| `shasum -a 256` on the 4 reviewed files (start and end) | all match the brief; unchanged at end |
| `(cd detector && uv run python <scratchpad>/qa_paired_ci.py)` | exit 0, ~71 s CPU; all reproduction checks True; `FINAL MAX \|deviation\| vs author JSON: 0.000e+00` |
| `(cd detector && uv run python <scratchpad>/qa_pergroup.py)` | per-group differences equal `per_group_point_difference_fixed_020` |
| `(cd detector && uv run python -m m1.a3_pilot_paired_ci_r1 verify)` | `VERIFY PASS … sha256=19782743…b2f7`, exit 0, 37 s |
| `(cd detector && uv run pytest -q tests/test_a3_pilot_paired_ci_r1.py)` | 12 passed, exit 0 |
| `uv run ruff check src tests` | `All checks passed!` |
| `(cd detector && uv run ruff check m1/a3_pilot_paired_ci_r1.py tests/test_a3_pilot_paired_ci_r1.py)` | `All checks passed!` |
| `uv lock --check` (root) | `Resolved 201 packages`, exit 0 |
| `(cd detector && uv lock --check)` | `Resolved 66 packages`, exit 0 |

## Reproduced values (independent scorer)

| Row | A3 | Pilot | A3 − pilot | Paired 95% CI | Excl. 0 |
| --- | ---: | ---: | ---: | --- | --- |
| 1 Correct-class recall @0.20 | 0.6026 | 0.7324 | −0.1298 | [−0.2263091354, +0.0033473193] | No |
| 2 Agnostic recall @0.20 | 0.7837 | 0.8766 | −0.0929 | [−0.1832275255, +0.0291433157] | No |
| 3 FP/image @0.20 | 0.2287 | 0.3989 | −0.1702 | [−0.4136323537, +0.0000496032] | No |
| 4a Correct-class, val-selected | 0.6779 | 0.7324 | −0.0545 | [−0.1484280152, +0.0577663487] | No |
| 4b Agnostic, val-selected | 0.8670 | 0.8766 | −0.0096 | [−0.1135502401, +0.0715663348] | No |
| 4c FP/image, val-selected | 0.5452 | 0.3989 | +0.1463 | [−0.0360003244, +0.2811802293] | No |
| 5a key 7 → yolo 7 | 0.4144 | 0.5946 | −0.1802 | [−0.3382352941, +0.0697674419] | No |
| 5b key 32 → yolo 33 | 0.9655 | 0.6207 | +0.3448 | [+0.3448275862, +0.3448275862] | UNKNOWN (single group) |
| 5c key 41 → yolo 42 | 0.5385 | 0.4615 | +0.0769 | [0.0000000000, +0.1428571429] | No |
| mAP50-95 (exact class) | 0.5633 | 0.6089 | −0.0456 | [−0.1016516308, −0.0161464310] | Yes |

## SHA-256 of reviewed files and inputs

| File | SHA-256 | Match |
| --- | --- | --- |
| `detector/m1/a3_pilot_paired_ci_r1.py` | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` | yes |
| `detector/tests/test_a3_pilot_paired_ci_r1.py` | `194a8f557af32ebdc734abf5fa61662175847307dd82a4af1a4fd0b6b11ae88b` | yes |
| `docs/review/generated/d1_a3_pilot_paired_ci_r1.json` | `19782743d75d336be88cebf1e5558e1477b4f03ef4d929eaeb5230313b69b2f7` | yes |
| `docs/review/d1_a3_pilot_paired_ci_r1_report.md` | `1bdaa290ea44a7020804cce5913410bf13f8e49b7da919e272eef4c3034b4a70` | yes |
| `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/a3_predictions.csv` | `e6a25b017bc94a3cf75220fcce1acdfd7bfacb088ca375143e3f0e5046b99ada` | yes |
| `results/experiments/d1_a3_seed_20261018_r2/evaluation_common_r1/comparison_a3_r1.json` | `98b8947e379e2dbf88066884ee4540bc669f8402d459b1891b071b53ee2c2c73` | yes |
| `detector/colab/evaluate_d1_a3_r2_common_r1.py` | `5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6` | yes |
| `docs/review/d1_a3_r2_common_validation_report_r1.md` | `2c893e0222275d735dbbafb4d7a8e74146e9906dfa16054e087cc507608e5494` | yes |
| `tmp/yolo11n_n1_extract_r1/manifest.json` | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` | yes |
| `tmp/yolo11n_n1_extract_r1/data/yolo54_predictions_val.csv` | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` | yes |
| `tmp/yolo11n_n1_extract_r1/data/val_groups.json` | `fdb2ef8ff2cc684970b6330747d7746ccfe6dfd77d60903d10233de66697d682` | yes |
| `tmp/yolo11n_n1_extract_r1/data/classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | yes |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` | yes |
| `detector/colab/evaluate_cascade_b0_r1.py` (AP integrator source) | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` | recorded |

## Claim classification

| Claim | Class |
| --- | --- |
| Inputs and package files match the stated SHA-256s | Verified artifact/result (this QA) |
| Paired and marginal CIs, point values and per-class figures reproduce exactly | Verified artifact/result (this QA, independent implementation) |
| Only the exact-class mAP50-95 paired CI excludes 0 | Verified artifact/result, conditional on the 9-group percentile bootstrap |
| Class key 32 has an informative CI | UNKNOWN (single supporting group) |
| `cos_lr` causes any difference | UNKNOWN (confounded with epochs; single seed) |
| Sealed-test or other-domain behavior | UNKNOWN (not accessed) |

The R3 addendum's disposition (A3 does not meet R3 criteria; do not replace the pilot) is
unchanged by this QA. No D-05 gate, threshold or app setting was changed.

`sealed_test_accessed=false` · `inference_run=false` · `training_run=false` ·
`thresholds_changed=false` · `existing_files_edited=false`
