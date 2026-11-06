# D1-A2-R1 common validation comparison (A2 vs YOLO11s-54 pilot) — independent result QA record

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent result QA sub-agent. I did not write the evaluator
or the paired-CI module, did not run them for the outputs under review, and did not run A2.
Scope: the A2 common-evaluator outputs and the A2 − pilot paired-CI JSON in the Desktop checkout
`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector` (read only), against
`docs/review/d1_a2_r1_run_contract.md` §3, §4 and §10.

Verdict: PASS — every placed file and output hashes as claimed, the headline numbers reproduce exactly from `a2_predictions.csv` and the pinned pilot CSV with my own matcher and resampler, the paired-CI JSON re-verifies byte-for-byte against the `_r2` bundle, and the `_r1` → `_r2` bundle swap is a legitimate equivalent that changes no number. Under contract §3 the evidence shows the R3 A2 criteria are **NOT met**: overall recall is 0.7612, below 0.85.

## 1. Disposition supported by the evidence (contract §3, conf 0.20, R3 roster)

| R3 §5 A2 criterion | Observed (A2 vs pilot) | Point readout |
| --- | --- | --- |
| Recall of derived key 7 (yolo 7, n=111) up by ≥ 0.05 | 0.5946 → 0.6757, +0.0811; paired CI [+0.0147, +0.1860], 2 groups | met (point) |
| Recall of derived key 32 (yolo 33, n=29) up by ≥ 0.05 | 0.6207 → 1.0000, +0.3793; CI [0.3793, 0.3793], **1 group, degenerate** | met (point); CI not informative |
| Recall of derived key 41 (yolo 42, n=26) up by ≥ 0.05 | 0.4615 → 0.6154, +0.1538; CI [+0.1429, +0.1667], 2 groups, low support | met (point) |
| FP/image up by ≤ 0.03 | 0.3989 → 0.2447, −0.1543; CI [−0.3882, 0.0000] | met |
| Overall (class-agnostic) recall ≥ 0.85 | **0.7612** (pilot 0.8766); difference −0.1154, CI [−0.2413, +0.00004] | **NOT met** |
| Paired CIs reported | yes (1000 rounds, seed 20261018, 9 intact D-02 groups) | met |

`all_point_criteria_met=false`. The A2 run therefore does **not** satisfy its frozen R3 success
rule. This is a validation description. It is not a D-05 decision, an acceptance or a rejection of
the model, and it selects or locks no threshold.

## 2. Findings

### Critical / High / Medium

None.

### L1 (Low) — the bundle-path substitution is recorded only in the coordinator's narrative

- **Evidence.**
  - The evaluator implementation record's command names `../tmp/yolo11n_n1_extract_r1`.
  - The run used `../tmp/yolo11n_n1_extract_r2`.
  - Neither `comparison_a2_r1.json` nor the CI JSON records a bundle path. They record only the
    manifest SHA `8e6ffe77…`.
- **Effect.** No number is affected (§4). A later reader cannot see from the artifacts which
  directory was used.
- **Fix.** State the deviation and the reason in the A2 common-validation report or execution
  record. The reason: `_r1` now carries an unlisted `detector/.venv` (19,639 files, 3 symlinks)
  plus one `__pycache__` file, so `verify_package` refuses it.

### L2 (Low, hygiene) — the `_r1` bundle directory has been polluted since extraction

- **Evidence.** All 8,579 `_r1` manifest members still match their hashes. The directory also
  holds:
  - an unlisted `detector/.venv` (mtime 2026-10-25 14:34);
  - `detector/colab/__pycache__/run_cascade_b0_r1.cpython-312.pyc`.
- **Effect.** The A3 paired-CI predecessor (`a3ci.BUNDLE` = `_r1`) still verifies, because it
  hashes only the members it uses. The stricter common evaluator now refuses `_r1`.
- **Fix.** Optional, and only with Owner approval. Leave `_r1` as is and treat `_r2` as the
  canonical extraction from now on. Do not delete data without approval.

### I1 (Info, interpretation) — wording guidance for the report

- **Agnostic recall.** The CI upper bound is +0.00004, so it touches 0. Report it as "lower at
  the point estimate; the 95% paired CI just includes 0". Do not call it a significant drop.
- **FP/image.** The CI upper bound is exactly 0.0, so it does not exclude 0.
- **mAP (no threshold involved).** Both exact-class mAP CIs exclude 0:
  - mAP50: 0.7642 vs 0.8521, difference −0.0879, CI [−0.1450, −0.0087];
  - mAP50-95: 0.5547 vs 0.6089, difference −0.0541, CI [−0.0920, −0.0124].
- **Confidence shift.** The fall in recall at 0.20 comes with fewer FPs, which is consistent with
  a lower confidence scale for A2. Two observations show it is not only calibration:
  - the threshold-free mAP is lower;
  - at A2's own val-selected point (conf 0.05, diagnostic only), recall 0.8478 still misses 0.85,
    and FP/image 0.5665 vs 0.3989 has a paired CI [+0.0049, +0.2737] that excludes 0.
- **Class gains.** The class-32 gain is a single-group degenerate interval. The class-41 interval
  is narrow only because just 2 groups and 26 boxes support it. Neither shows precision.

## 3. Hashes verified (SHA-256, observed = claimed)

| File | SHA-256 | Staged copy under `<wt>/tmp/a2_eval/` |
| --- | --- | --- |
| `detector/colab/evaluate_d1_a2_r1_common_r1.py` | `c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317` | identical |
| `detector/m1/a2_pilot_paired_ci_r1.py` | `2dc6088ccc9efc92fc85543960c028a5b1aadb8d23c321ff241a04d1deaf0e1d` | identical |
| `detector/tests/test_evaluate_d1_a2_r1_common_r1.py` | `cb41583457c7fe5975a79280cb1c60d3f1976aebbf4ae9adcb690a661af3ab5e` | identical |
| `detector/tests/test_a2_pilot_paired_ci_r1.py` | `673cab0249f36a1da3ed37d73ba6902533bc77c3fd1e2d1c4a0877f331beb46a` | identical |
| `results/…/evaluation_common_r1/a2_predictions.csv` (1,443 rows) | `c45dcf1dd5446b7e5afe3458afcd43f75b8b7b5afc5434d244d80a0e3e1dd7f1` | — |
| `results/…/evaluation_common_r1/comparison_a2_r1.json` | `d7872b872b4db01ec27662a323ad9edcf416cd318345a45a68038ebe2bef641b` | — |
| `docs/review/generated/d1_a2_pilot_paired_ci_r1.json` | `2687a30ebbffafe88d6568fed222f11c2c15fe29be50908b38f35c427f1aaa04` | — |
| A2 archive (`<wt>/tmp/a2_state/…_a2_r1_result.tar.gz`) | `ea7dba03b0a53cfea41fd876544715d783e56abf4837568df4e74f256a66a609` | — |
| A2 archive manifest | `7a4e18563ee0c16a8dd01506e48a5c9fe379e205b3af96db25b4cf933a07d343` | — |
| `best.pt` extracted from the archive (scratch) | `9781f7d840e48a140d6031dc2b388359093a06a2b6f8912ba31b6a300c0ebb0b` | — |
| Owner authorization record | `1a11b283da34848dc873b577b42240a5182b795654f5a3db9349369ae78221c9` | — |
| Bundle manifest `_r1` and `_r2` (byte-identical, `cmp`) | `8e6ffe7761b78ba4e44a86cd2caa9a3a155ba0874cbe39bb20669af3773bb6da` | — |
| Pilot CSV (bundle `data/yolo54_predictions_val.csv`, 1,999 rows) | `87884c536e16ac890c11114c85c7c12731571df15d244071a38e3d1db271c893` (CI pin) | — |

The result JSON binds:

- the run attestation `3047b09d…28c0`, which equals the result-QA recomputation;
- the checkout `f3f7571794a5…`;
- the authorization `1a11b283…`;
- the list `90d735d6…`;
- the outcome `COMPLETED`;
- `prediction_csv_sha256` equal to the CSV.

The result-QA record carries `Verdict: PASS`.

## 4. Bundle path `_r1` → `_r2`

- `_r2/manifest.json` is byte-identical to `_r1/manifest.json` (`8e6ffe77…`).
- My own full check of `_r2`:
  - all 8,579 manifest members exist and match their SHA-256;
  - 0 symlinks;
  - 0 unlisted files;
  - 0 members with a `test` path component;
  - `test_included=false` and `sealed_test_accessed=false`.
- This is the same rule as `run_yolo11n_n1_r1.verify_package`: exact roster, no links or
  hardlinks, full hash check.
- In `_r1`, every one of the 8,579 members also matches. The refusal comes only from the unlisted
  `.venv` and pycache payload (L1/L2).
- The scored inputs are the val images, `labels54/val`, `val_groups.json`, `classes.csv` and the
  pilot CSV. Their bytes are therefore identical in both directories.
- `verify` against `--bundle ../tmp/yolo11n_n1_extract_r2` reproduced the CI JSON byte-for-byte
  (§6). Neither output encodes the path.
- **Judgement:** a legitimate equivalent. No number changes.

## 5. Independent recomputation (own code; no `m1` import)

`indep_score.py` implements its own pieces:

- GT loading from `labels54/val`, with PIL for image sizes;
- CSV parsing;
- a pure-Python greedy IoU ≥ 0.5 matcher (stable descending score, class-aware and agnostic);
- val-grid selection (recall ≥ 0.85, then minimum FP, then highest confidence);
- a group resampler: `default_rng(20261018)`, `choice` over the sorted 9 group names, 1000
  rounds, the same draws for both models.

| Quantity | Recomputed | Claimed / JSON |
| --- | --- | --- |
| Roster | 376 frames / 624 boxes / 9 groups | same |
| Class map (bundle `classes.csv`) | 7→7, 32→33, 41→42 (46→48) | same |
| Supports yolo 7/33/42 | 111 / 29 / 26 | same |
| Agnostic recall @0.20, A2 / pilot | 0.761218 (475/624) / 0.876603 (547/624) | 0.7612 / 0.8766 |
| FP/image @0.20 | 0.244681 (92) / 0.398936 (150) | 0.2447 / 0.3989 |
| Correct-class recall @0.20 | 0.650641 / 0.732372 | 0.6506 / 0.7324 |
| Class recall 7 / 32 / 41 | 0.6757 / 1.0000 / 0.6154 vs 0.5946 / 0.6207 / 0.4615 | same |
| Paired CI, agnostic recall | [−0.241327, +0.0000421] | identical to full float |
| Paired CI, FP/image | [−0.388239, 0.0] | identical |
| Paired CI, correct-class recall | [−0.215321, +0.130158] | identical |
| Paired CI, class 7 / 32 / 41 | [0.0147, 0.1860] (892 rounds) / [0.3793, 0.3793] (647, 1 group) / [0.1429, 0.1667] (874) | identical |
| Val-selected A2 | conf 0.05, recall 0.847756, FP/image 0.566489, target not met | same |
| Val-selected pilot | conf 0.20, recall 0.876603 | same |

- **mAP.** Not recomputed with my own AP code. It was reproduced through the project scorer
  (pinned Ultralytics `ap_per_class` and matcher) inside `verify` (§6), which also asserts that
  the JSON's exact-class mAP holds to 1e-12.
- **Pilot side.** The A2 JSON's `pilot_common_method` equals the QA-passed A3 JSON's pilot side
  exactly.
- **Inference spot-check.** Inference ran on 4 frames only (0001, 0303, 0844, 1951) on MPS. I
  used `best.pt` extracted from the archive into scratch and the evaluator's arguments
  (`conf=0.001`, `iou=0.70`, `imgsz=1280`, clip). Row counts, classes, confidences and boxes
  equal the CSV exactly (max diff 0.0). No other inference was run.

## 6. Commands and results

| Command (no git; bytecode and pytest cache off) | Result |
| --- | --- |
| `shasum -a 256` on placed, staged, output, archive and manifest files | all match (§3) |
| `detector/.venv/bin/python -I <scratch>/indep_score.py` (bundle `_r2`) | §5 values; full member check 8,579/8,579 |
| `detector/.venv/bin/python -I <scratch>/r1_check.py` | `_r1`: 0 bad members, 3 symlinks, unlisted `.venv` 19,639 + 1 pyc |
| `detector/.venv/bin/python -I <scratch>/spot_infer.py spot mps` | best.pt hash OK; 4/4 frames identical to the CSV |
| `PYTHONPATH=. uv run --no-sync python -m m1.a2_pilot_paired_ci_r1 verify --a2-csv-sha256 c45dcf1d… --a2-json-sha256 d7872b87… --bundle ../tmp/yolo11n_n1_extract_r2` | `VERIFY PASS … sha256=2687a30e…a04` (includes `reproduction_check` and the mAP check) |
| `PYTHONPATH=. uv run --no-sync pytest -p no:cacheprovider -o addopts="" -q` on the 2 new test files + `test_a3_pilot_paired_ci_r1.py` + `test_run_d1_colab_a2_r1.py` | **120 passed** (119.7 s) |
| `uv run --no-sync ruff check --no-cache` on the 4 placed files | All checks passed |
| `find … -newer <scratch start>` over `detector/`, the A2 results directory and `docs/review/generated` | no file written in the main checkout |

Scratch directory:
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/qa_a2_compare/`.
Its files:

- `indep_score.py` `15757cf9…`
- `indep_r2.json` `51a5028a…`
- `spot_infer.py` `0f9ea537…`
- `r1_check.py` `a1e63acd…`
- `ci_verify_r2.log` `d4c046be…`
- `spot/best.pt`

**Not run:** the full repo gate (`uv run ruff check src tests && uv run pytest -q && uv lock
--check`) and Graft build/check. The placement-time gate is the coordinator's claim.

## 7. Claim-scope check

These outputs hold the required scope:

- the CI JSON `claim_scope` reads: single seed, validation only, not compute-matched (about 26%
  more steps), not a sealed-test result;
- `inference_run=false`, `training_run=false`, `thresholds_changed=false`;
- the criteria block is labelled `R3_A2_CRITERIA_POINT_READOUT_NOT_ACCEPTANCE` ("does not change
  D-05 or accept the model");
- the selected-point block is labelled `VALIDATION_SELECTED_DIAGNOSTIC_ONLY`.

**Overclaim check:** none in the coordinator's headline. I1 sets the wording for agnostic recall
and FP/image, whose CIs touch 0. The report should also restate, verbatim from contract §2.2/§10:
one seed, not compute-matched, validation only, no D-05 change, no threshold selected or locked,
sealed test closed.

`sealed_test_accessed=false` everywhere in the outputs:

- `comparison_a2_r1.json` at `/sealed_test_accessed`, `/a2_common_method/…` and
  `/pilot_common_method/…`;
- the CI JSON at `/sealed_test_accessed`;
- the bundle manifest;
- the archive manifest.

## 8. Flags

- `sealed_test_accessed=false`. The sealed test (`afa03d4b…`) was never opened, listed or scored.
  The token appeared only inside run names.
- No training, download, upload, threshold change or D-05 change. Inference ran on only 4
  validation frames, on MPS, for the spot-check.
- No write and no git command in the main checkout, and no output modified. This record is the
  only file written outside the scratchpad.

## 9. Claim classification

- **Verified artifact:**
  - every hash in §3;
  - `_r1`/`_r2` manifest identity;
  - the full member check of `_r2`;
  - the recomputed numbers in §5;
  - the byte-exact CI re-verification;
  - the 4-frame inference identity.
- **Verified current behavior:**
  - `verify` mode reproduces the CI JSON;
  - the 120 tests pass;
  - ruff is clean;
  - `verify_package` refuses `_r1` because of the unlisted symlinked payload, by code reading and
    the observed links.
- **Proposal:** the fixes for L1/L2 and the wording in I1.
- **Unknown:**
  - whether A2's shortfall would hold across seeds or with a compute-matched schedule;
  - any sealed-test behavior;
  - whether the full repo gate and Graft pass after placement (not run here).
