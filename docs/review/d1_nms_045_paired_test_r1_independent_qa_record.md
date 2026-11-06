# D1 NMS IoU 0.45 vs 0.70 paired test R1: independent QA record

Date: 2026-11-06 (`Asia/Ho_Chi_Minh`). Reviewer: an independent Claude Code QA agent (Opus 5.5). This agent did not write the contract, script, tests or output.
Scope: validation R3 only, offline, from the two pinned prediction CSVs. The QA ran no inference or training and downloaded nothing. It changed no threshold, app setting or D-05 value, and it did not edit or run git on the checkout.
`sealed_test_accessed=false` · `thresholds_locked=false` · `inference_run=false`

Verdict: PASS giới hạn — every reported number reproduces exactly from the CSVs with independent code, and `NOT_SUPPORTED` (only c1 failed) is the correct result under the frozen §4 rule. There are two limits. The box audit omits the per-box listing and TP/FP classification that §3 requires; this QA supplies them below. Condition c7 passed only because it had nothing to test, so the report must call the stacked-sign risk untested, not passed.

## 1. Files reviewed (SHA-256, verified 2026-11-06)

| File | SHA-256 | Matches brief/pin |
| --- | --- | --- |
| `docs/review/d1_nms_045_paired_test_r1_contract.md` | `fe80ce78ac2523d9f98245336e7bbb98699d0876d7312dc1437b10f3c5a463ff` | yes |
| `detector/m1/nms_045_paired_test_r1.py` | `056e21b5f22213351fadfd361cd4ee67fddf4d607ec92bea212941044a0c2c76` | yes |
| `detector/tests/test_nms_045_paired_test_r1.py` | `fed9702a1489d075ce177d6759e1dfadcf6d4623bc2b816049e4fb23f1d5f979` | yes |
| `docs/review/generated/d1_nms_045_paired_test_r1.json` | `5a499b2d030344201a1f923bb15e9ba2b00760a68a7f5a557f8b48e6c43a22ee` | yes |
| `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.45.csv` | `eb95a5021e685c7ba60b173a184fd29535f114bcb8269916ba594e6c404261a5` | yes (contract §1) |
| `results/experiments/d1_nms_sweep_r1/predictions_classaware_0.70.csv` | `d4ae12e3116ad9ee80fb39f00174cdb44daf29ded7ada14ea2086b926e477a11` | yes (contract §1) |
| `docs/review/generated/d1_nms_sweep_r1.json` | `6be704d21edacd92aeb142f9fc4a5ffb6988686f24ebda9321224634f5460057` | yes |
| `docs/review/d1_nms_sweep_r1_report.md` | `cad83325fccddf31b8c05c7610c33bf008020389e5651b7a56dfa21ba17244e7` | yes |
| `detector/m1/nms_sweep_r1.py` | `0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e` | yes |
| `detector/m1/a3_pilot_paired_ci_r1.py` | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` | yes |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` | yes |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` | yes |

## 2. Was the contract frozen before computation? (plausible, evidence is mtime only)

- **File mtimes:**
  - sweep JSON: 10:59:53
  - sweep report: 11:04:47
  - **contract: 11:12:18**
  - script and tests: 11:14:16
  - **output JSON: 11:14:47**

  The script opens its output with mode `"x"`, so it never overwrites an existing JSON. The contract therefore predates the only output file.
- **Contract content:** the only numbers it cites come from the already-QA'd sweep:
  - the gate 0 values TP 547/FP 150/correct 457/mAP 0.8521/0.6089 and 547/135/457/0.8543/0.6095;
  - "15 FP (150 → 135)".

  It cites none of the paired-test outputs: no CI, per-group split, LOGO count, box-audit count or GT-pair count.
- **Limit:** mtimes are not cryptographic evidence. Under the read-only rule this QA did not inspect git history. The finding is therefore "plausibly frozen", not "proven frozen".

## 3. Does the script follow the contract? (§3 design, §4 decision rule)

| Contract item | Script | Result |
| --- | --- | --- |
| GT via `ci.gt_frames(tmp/yolo11n_n1_extract_r2)`, 376/624/9 | `load_frames` | conforms |
| Predictions via `ci.with_predictions(..., "class_id", "confidence")`, hashes first | `check_pins` (CSV, sweep JSON/report/module, paired-CI module, and `sweep.check_pins()` bundle/scorer/metrics) | conforms; also checks that the sweep JSON's CSV hashes and `sealed_test_accessed=false` agree |
| Gate 0 with tolerance 1e-4, stop on mismatch | `gate()` raises | conforms; both passed |
| Operating point is conf 0.20 for both | `CONF = 0.20`; the sweep JSON records `selected.confidence = 0.2` for both `classaware_0.45` and `classaware_0.70` | conforms |
| Bootstrap: 1000 rounds, seed 20261018, identical group draws | one `ci.resample_indices(base, 1000, 20261018)` list reused for every metric and both settings | conforms; no extra freedom |
| Differences are 0.45 − 0.70 for FP/img, correct-class recall, agnostic recall, mAP50, mAP50-95; point, percentile CI95, share < 0 | `paired()`; mAP from `_correct_matrices` and a single `ap_per_class` call, the same as `ci._map50_95` | conforms; point mAP equals `common.average_precision` to full precision |
| Per-group FP/correct/agnostic | `per_group()` | conforms |
| Two-setting LOGO at fixed conf 0.20. Eligible if recall ≥ 0.85, then lowest FP/img, then higher mAP50-95, then the setting closer to 0.70 | `_choose`: tuple `(fp_per_image, -map50_95, 0 if 0.70 else 1)` | conforms; "recall" is read as class-agnostic recall (see F3) |
| Box audit: **list** removed boxes and classify each as TP/correct-class TP/FP at 0.70; GT-pair exposure at IoU ≥ 0.45 | `box_audit` returns **counts only**; `gt_pair_exposure` conforms | **deviation, see F1** |
| Focus keys 7/32/41 (yolo 7/33/42) | `sweep.point(...)["focus"]` | conforms |
| §4 c1–c7 | `decide()` maps each condition literally (c1 uses a strict `< 0`, c4 uses `>= 0`) | conforms |

## 4. Independent recomputation (own code, no project imports)

Script: `/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/bbab7d87-7388-4298-a733-728a73efc2cf/scratchpad/qa_nms045/recompute.py`. It was run with `detector/.venv/bin/python -I` and imports only numpy, PIL and Ultralytics `ap_per_class`. It does the following:

- rebuilds GT from `labels54/val`, using image sizes and `val_groups.json`;
- uses its own greedy matcher, identical in logic to `m1.metrics.match` (IoU 0.5, conf ≥ 0.20, FP counted class-agnostically);
- uses its own re-implementation of the Ultralytics `match_predictions` correct matrix. A cross-check against the library matcher gave 0/752 frames with any mismatch;
- uses its own group bootstrap: `default_rng(20261018).choice(sorted(groups), size=9, replace=True)` per round, 1000 rounds;
- runs its own LOGO, box audit and GT-pair scan.

Every value below **matches the JSON exactly** (to float equality where printed).

**Full set, conf 0.20**

| Setting | TP | FP | Correct-class | FP/img | Correct recall | Agnostic recall | mAP50 | mAP50-95 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.45 | 547 | 135 | 457 | 0.359043 | 0.732372 | 0.876603 | 0.854254 | 0.609501 |
| 0.70 | 547 | 150 | 457 | 0.398936 | 0.732372 | 0.876603 | 0.852084 | 0.608868 |

**Paired bootstrap (0.45 − 0.70)**

| Metric | Point | CI95 | Share < 0 |
| --- | --- | --- | --- |
| FP/image | −0.039894 | [−0.104237, 0.000000] | 0.894 |
| Correct-class recall | 0 | [0, 0] | 0 |
| Agnostic recall | 0 | [0, 0] | 0 |
| mAP50 | +0.002170 | [+0.0000815, +0.004595] | 0 |
| mAP50-95 | +0.000633 | [−0.000736, +0.001668] | 0.173 |

**Per group (0.45 / 0.70)**

| Group | Frames | GT | FP | Correct | Agnostic |
| --- | --- | --- | --- | --- | --- |
| D02-C0001 | 69 | 69 | 16/16 | 24/24 | 65/65 |
| D02-C0009 | 68 | 155 | 13/13 | 105/105 | 117/117 |
| D02-C0011 | 17 | 17 | 0/0 | 17/17 | 17/17 |
| D02-C0020 | 35 | 64 | 9/9 | 49/49 | 59/59 |
| D02-C0031 | 38 | 133 | **33/41** | 112/112 | 127/127 |
| D02-C0034 | 39 | 33 | **53/60** | 27/27 | 31/31 |
| D02-C0042 | 13 | 25 | 5/5 | 21/21 | 24/24 |
| D02-C0044 | 83 | 114 | 5/5 | 90/90 | 94/94 |
| D02-C0045 | 14 | 14 | 1/1 | 12/12 | 13/13 |

**LOGO.** 0.45 is selected in **9/9** folds. In every fold both settings are eligible, with identical agnostic recall (0.855–0.917). 0.45 has strictly lower FP/img in every fit set, so the decision never reaches the mAP or "closer to 0.70" tie-breaks. Held-out FP and correct-class hits equal the JSON values.

**Why the FP CI upper bound is exactly 0.0.** Every group's FP difference is ≤ 0, and only D02-C0031 (−8) and D02-C0034 (−7) are non-zero. A bootstrap round therefore has difference exactly 0 when it draws neither group. In this draw sequence that happens in **106/1000** rounds; the theoretical rate is (7/9)^9 = 0.1042. All other rounds are < 0, which gives share < 0 = 0.894. Because more than 2.5 % of rounds sit at the maximum value 0, the 97.5th percentile is exactly 0.0.

Structurally, with no group gaining FP, c1 can pass only if the FP reduction appears in at least 4 of the 9 groups: (6/9)^9 = 0.026 > 0.025, while (5/9)^9 = 0.005. So c1 behaves as a breadth-of-effect requirement. That is a legitimate property of the pre-registered rule, not a defect.

## 5. Box audit and the NMS chain effect

- At conf ≥ 0.20, **18 boxes are removed** and **3 boxes are added** by 0.45. That is a net 15, consistent with FP 150 → 135. No frame changes any GT match, class-aware or class-agnostic. All boxes are in D02-C0031 and D02-C0034.
- **Classification (missing from the JSON; supplied here):**
  - All 18 removed boxes were **FP at 0.70**: 0 agnostic TP and 0 correct-class TP. They are 15 boxes of yolo class 12, two of class 32 and one of class 8, in stems 1237, 1240×2, 1241–1244, 1245×2 (C0031) and 1335, 1350, 1352–1356, 1357×2 (C0034).
  - All 3 added boxes are **FP at 0.45**: 1240 class 32 conf 0.330, 1352 class 12 conf 0.282, and 1357 class 12 conf 0.700.
- **How a lower IoU adds boxes (greedy-NMS chain).** Example frame 1357, class 12. A is conf 0.788, B is conf 0.729 and C is conf 0.700.
  - At IoU 0.70: IoU(A,B) = 0.560 < 0.70, so B survives. Then IoU(B,C) = 0.805 > 0.70, so B suppresses C.
  - At IoU 0.45: A suppresses B, because 0.560 ≥ 0.45. B is no longer there to suppress C, and IoU(A,C) = 0.449 < 0.45, so C survives.

  Frames 1352 (IoU(A,C) = 0.428) and 1240 (IoU(A,C) = 0.397) follow the same pattern. Across all confidences, 15 of the 1,832 rows in the 0.45 CSV are absent from the 0.70 CSV, which confirms that the effect is real and not a coordinate-rounding artifact.

## 6. Condition c7: vacuous

Validation contains **0 GT–GT pairs at IoU ≥ 0.45**. It also has 0 pairs at IoU ≥ 0.05; the maximum GT–GT IoU in any frame is 0.0334. c7 (`matched_at_0_70_but_not_0_45 == 0`) is true because nothing was tested. The validation set has no overlapping same-class neighbouring signs, so it gives **no evidence** about whether per-class IoU 0.45 suppresses one of two real stacked or adjacent signs. The report and any later lock record must state "stacked-sign risk untested (no exposure in validation)" and must not count c7 as a pass (see F2).

## 7. Findings

| ID | Severity | Finding | Evidence | Fix |
| --- | --- | --- | --- | --- |
| F1 | Minor | The box audit does not implement §3 in full. The contract says to "list predictions … and record whether each was a TP, a correct-class TP or an FP at 0.70". The script outputs counts only. | `box_audit()` returns two integers and a frame list; the JSON has no per-box entries. | Put the listing from §5 above (all 18 FP at 0.70; 3 added FP) in the report, marked as supplied by QA. The JSON must not be rewritten (it is opened with mode `"x"`), so use a separate addendum file if a machine-readable list is needed. Outcome-neutral: the box audit is not a §4 condition. |
| F2 | Minor (reporting) | c7 is vacuous. The JSON shows `c7_no_paired_gt_lost: true`, which could be read as evidence of safety for stacked signs. | 0 pairs at IoU ≥ 0.45; maximum GT–GT IoU 0.0334. | The report must state the risk is **untested**. Any replication or lock proposal needs data that contains overlapping same-class signs, or an explicit risk acceptance. |
| F3 | Info | The LOGO rule's "recall ≥ 0.85" does not say which recall. The script uses class-agnostic recall, consistent with D-05 (`metrics.select_threshold`, `nms_sweep_r1.select`). Under correct-class recall (0.73) no setting would be eligible, c5 would fail, and the decision would still be `NOT_SUPPORTED`. | `_choose` uses `p["agnostic_recall"]`. | State the D-05 meaning explicitly in the §5 replication contract. |
| F4 | Info | c1 needs an FP reduction in at least 4 of 9 groups (see §4). The report should explain that the CI upper bound of 0.0 reflects an effect confined to 2 groups (C0031, C0034), not noise around a large effect. | 106/1000 rounds draw neither group. | Explain this in the report. |
| F5 | Info | The tests cover `decide`, GT-pair exposure, box-audit counting and pins. They do not cover `paired()` (draw identity), `per_group` or the LOGO tie-break order. | Test file. | Optional: add tests for these in a future revision. The recomputation here covers them for R1. |
| F6 | Info | The freeze is evidenced by mtime only (contract 11:12:18 < output 11:14:47) plus contract content. | `stat`. | Commit the contract before the output in future runs, so the order is recorded in git. |

No finding changes any number or the decision.

## 8. Commands and results

- `shasum -a 256 <12 files>`: all match (§1).
- `detector/.venv/bin/python -I .../qa_nms045/recompute.py <repo>`: exit 0. All values equal the JSON (§4–§6). Own vs library correct matrix: 0 frame mismatches.
- `detector/.venv/bin/python -I .../qa_nms045/chain.py <repo>`: confirms the chain effect in frames 1357, 1352 and 1240, and 15/1832 rows of the 0.45 CSV are absent at 0.70.
- From `detector/`: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. uv run --no-sync pytest -p no:cacheprovider -q tests/test_nms_045_paired_test_r1.py`: **16 passed**.
- From `detector/`: `uv run --no-sync ruff check m1/nms_045_paired_test_r1.py tests/test_nms_045_paired_test_r1.py`: **All checks passed!**
- Data read: bundle `data/images/val` (sizes only), `data/labels54/val`, `data/val_groups.json`, and the two CSVs. No test split or sealed-test path was listed or opened. `sealed_test_accessed=false`.

## 9. Claim classification

| Claim | Class |
| --- | --- |
| Point values, per-group table, paired CIs, LOGO 9/9, box audit 18/3 with no GT match change, 0 GT pairs | **Verified artifact/result** (independently recomputed) |
| Decision `NOT_SUPPORTED`, failed = [c1] only | **Verified result under the contract.** c1 fails because CI95 upper = 0.0 is not < 0. c2–c6 hold. c7 holds only vacuously. |
| The FP reduction from 0.45 is real but confined to D02-C0031/C0034, and all removed boxes were FP | **Verified artifact/result** (in-sample, post hoc, one checkpoint) |
| 0.45 does not lose stacked or adjacent real signs | **Unknown** (no exposure in validation) |
| 0.45 would generalize to new data or to the seed 20261019 model | **Unknown** (§5 replication not run) |
| Contract frozen before computation | **Plausible**: mtime order and content; not cryptographically proven |
| Any change to NMS, thresholds, app or D-05 | **None made; none supported** |
