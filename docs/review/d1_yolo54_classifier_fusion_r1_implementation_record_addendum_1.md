# D1 YOLO54 + CompactCNN classifier fusion R1 — implementation record, Addendum 1 (source-QA corrections R1–R5)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), side session started by the fusion coordinator session.
Status: **AWAITING_DELTA_SOURCE_QA**

This is an append-only addendum. It does **not** edit the original implementation record
`docs/review/d1_yolo54_classifier_fusion_r1_implementation_record.md`
(`51e69893fec4733dbe1cd336f600ecc6538d0843835ed42db93d7ef22f924e54`, unchanged). It answers the independent
source-QA record `docs/review/d1_yolo54_classifier_fusion_r1_source_independent_qa_record.md`
(`c40f1c585c66601b781bdbd049ae133d463d349b0dce9c476aabb30342abd01c`, verdict PARTIAL), corrections R1–R5.

**Never executed on real data:** `run`, `latency`, `measure_latency`, `load_classifier`, any classifier
forward pass on a real crop, MPS inference and `verify` on real outputs. No arm-B or fusion number
exists. The only real-data command was the pilot-only `step0` (arm A), which the brief allows.
`sealed_test_accessed=false`.

## 1. Files and SHA-256

| File | Pre-fix (QA'd) | Post-fix |
| --- | --- | --- |
| `detector/m1/classifier_fusion_r1.py` | `90359373a38752d09c2bc7a8206c53f66c726d99b18cf2d7e6da5fe45b9eaf24` | `c28033cf3494ef5c6e01af30fdb4aec49dc1470a760565c6bf28744ca836c271` |
| `detector/tests/test_classifier_fusion_r1.py` | `de949559a69ad404ee7833e3ded20646dc508daf1014d90559a83cc53bc893af` | `7ef2a45aa4fb151dbc69108792e0e64c9d2eb8ef32e276aa999c05a583fb05be` |

Both pre-fix SHAs were verified before editing. Byte copies of the pre-fix files and the two
`diff -u` delta files were kept outside the repository, in the session scratchpad:
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/db7deed3-35de-4ef3-95e4-7aa2a55ad92c/scratchpad/prefix/`
(`classifier_fusion_r1.py.prefix`, `test_classifier_fusion_r1.py.prefix`, `module.delta.diff`,
`tests.delta.diff`). Diffstat: module +220/−26 lines (net), tests +368 lines. The delta QA can also
rebuild the diff from the pre-fix SHAs above.

The source-QA gate (`check_source_qa`) needs a new QA record that quotes the **post-fix** module SHA
`c28033cf…c271`. The PARTIAL record quotes the pre-fix hash, so the gate refuses it. That is correct.

## 2. Disclosure of R1

The pre-fix `manifest()` hashed `TESTS = detector/tests/test_classifier_fusion_r1.py` through
`regular_file` → `val_reeval_r2.guard_path`. That function refuses every path component containing
`test`. `run` therefore raised `refused sealed-test path` at pre-fix line 1778, after Step 0, the
CPU and MPS classifier passes, the latency arm and the full `build_eval` had all run, and before
`publish`. The original implementation record did not disclose this because no test called
`manifest()` or drove `run` past its refusal gates (QA gap G-a). The defect was never triggered on
real data: `run` was never invoked.

## 3. Fixes (post-fix file:line)

No scoring rule, threshold, pair, τ, outcome table, bootstrap, crop rule or latency protocol was
changed. `relabel`, `decide`, `crop_input`, `classify`, `guards`, `assign_outcome`,
`paired_bootstrap`, `latency_protocol`, `summarize_latency`, `build_eval` and `step0_check` are
byte-unchanged.

### R1 (blocking): manifest hashes its own test file; source hashes at the start of `run`

- `SOURCE_FILES = (MODULE, TESTS)` at `detector/m1/classifier_fusion_r1.py:115`.
- `_source_file` at `detector/m1/classifier_fusion_r1.py:319`. It refuses any path not in
  `SOURCE_FILES`. It walks every component from the repo root and refuses a symlink, then requires
  `S_ISREG` under `lstat`, and reports a missing file. It does not apply the `test`-substring rule,
  and is allow-listed to exactly those two constant, repo-relative paths.
- `source_hashes` at `detector/m1/classifier_fusion_r1.py:341`.
- `guard_path`, `guard` and `regular_file` are unchanged, so every data input keeps the
  `test`-substring refusal. A test asserts that `regular_file(REPO_ROOT, TESTS)` is still refused.
- `run` computes `sources = source_hashes(repo_root)` at `detector/m1/classifier_fusion_r1.py:1878`,
  right after `check_source_qa` (line 1876) and before `refuse_existing_outputs` and `load_state`.
  At line 1879 it requires the module hash to equal the one the source-QA gate checked. A path or
  hash error now refuses before any input is read.
- `manifest(repo_root, files, sources=None)` at `detector/m1/classifier_fusion_r1.py:1830` uses the
  `sources` captured at the start (`run`, line 1942), or fresh `source_hashes` when called alone.
- Verified: `manifest(REPO_ROOT, {})` on the real checkout returns the module and test hashes
  (tested, see §4).

### R2: pins re-verified before every write

`recheck_before_write` at `detector/m1/classifier_fusion_r1.py:1774` does four things, and any
mismatch raises before the write:

1. `verify_pins(repo_root)` re-hashes all 22 `PINS`;
2. `source_hashes` must equal the start-of-run `sources` (module and tests);
3. the classifier `best.pt` must still hash to `CLASSIFIER_SHA256`;
4. `verify_bundle(repo_root, full=False)` re-checks the used bundle members: validation images,
   `labels54`, `val_groups.json` and the bundle pilot CSV.

`run` calls it at line 1943, immediately before `refuse_existing_outputs` (1944) and `publish`
(1945). It returns the re-check summary as `recheck_before_write`. `stop_invalid` (R4) also calls it
before writing a stop report.

### R3: end-to-end synthetic run

This is a test-only change. The `E2E` harness and the end-to-end test are described in §4.

### R4: the three post-Step-0 raises

| Raise (pre-fix) | Treatment | Where |
| --- | --- | --- |
| CPU/MPS crop-set mismatch (pre-fix line 1753) | **Pre-checked by construction.** `crop_plan` (`:1411`) computes every C4 crop once. It is model-free and runs at `run:1887`, before Step 0 and before any classifier is loaded. Both passes get the same plan (`classify_candidates(..., plan=plan)` at `:1443`, used at `run` lines 1899–1900 and 1909). The remaining comparison (lines 1910–1917) can no longer differ. If it ever does, it returns `INVALID` through `stop_invalid` instead of raising. | `:1411`, `:1443`, `run:1887`, `:1910–1917` |
| G5 zero support (`guards`) | **Pre-checked.** `precheck_g5_support` (`:1469`) counts GT per G5 class. This equals arm A's `per_class_support` in `metrics.operating_point`, which depends only on GT. `run:1886` calls it before Step 0, so a failure refuses rather than consumes the run. The `guards` raise is kept, unchanged and now unreachable. | `:1469`, `run:1886` |
| `parse_probs_csv` sum tolerance | **INVALID with a written stop report.** `softmax_ok` (`:722`) is the predicate `parse_probs_csv` uses, now shared at line 757: finite, non-negative, \|Σ−1\| ≤ `SOFTMAX_SUM_TOLERANCE` = 1e-5 (`:719`), the same value and comparison. `softmax_violations` (`:731`) applies it to the in-memory CPU probabilities at `run:1902`. On any violation, `run` returns `INVALID` (stage `crop_probabilities`) before the CSV is written, the MPS model is loaded or latency is measured. | `:719–737`, `:757`, `run:1902–1905` |

- `stop_invalid` (`:1787`) writes only `fusion_r1_stop_report.json` (`STOP_REPORT_NAME`, `:113`), using
  the same write-once `publish` (O_EXCL / O_NOFOLLOW, exclusive rename) after `recheck_before_write`
  and `refuse_existing_outputs`.
- The report records `outcome INVALID`, `outcome_row 1`, the stage and detail, Step 0, the
  source-QA result, `sources`, the preflight, `result_files_written=false`,
  `fusion_metric_computed=false` and `FLAGS`. No result file is written.
- The returned `written` is `[]`, so `main` exits 2. The output directory then exists, so the run
  cannot be repeated.
- `verify` (`:1995`, line 1999) reports `verified=false` with an explicit error when a stop report
  is present.

### R5

This addendum.

## 4. Tests added (synthetic only; 14 new test cases, 42 → 56)

All new tests use synthetic roots under `tmp_path`, except the first, which only hashes the
module and test file of the real checkout. One existing helper changed: `write_gate_files` also
writes the synthetic `TESTS` file (line 705), because `run` now hashes it before the output gate.

| Test (post-fix line) | Covers |
| --- | --- |
| `test_manifest_hashes_module_and_tests_on_the_real_checkout` (881) | R1 regression on the real checkout; the data guard still refuses `TESTS` |
| `test_source_file_is_allow_listed_and_keeps_symlink_and_regular_checks` (895) | R1 on a synthetic root with `detector/tests/…`: allow-list, symlinked file, symlinked directory, missing, non-regular |
| `test_run_hashes_sources_before_any_input_is_read` (933) | R1: a missing test file refuses before `load_state` |
| `E2E` harness (950) | Injects synthetic state with real PNGs, a fake evaluator (crop + AP), a fake classifier, fake latency and a forced Step 0 pass. The source-QA gate (synthetic record), source hashes, `verify_pins` (synthetic `PINS`), `crop_plan`, `classify_candidates`, `deterministic_cpu`, `build_eval`, `manifest`, `recheck_before_write`, `publish` and `verify` run unmodified |
| `test_end_to_end_run_publishes_and_verifies` (1069) | R3 / G-a: `run` reaches `publish`, the five outputs exist, `verify()` returns `{"verified": true, "errors": []}`, manifest sources, inputs and outputs are checked, call order is crop plan < Step 0 < classifier, the bundle re-check uses `full=False` after latency, tampering is detected and a second run is refused |
| `test_a_pin_changed_mid_run_blocks_every_write` ×6 (1125) | R2 / G-c: a pinned input, the classifier (via `PINS` and via the explicit check), the module, the tests or the bundle changes during the latency arm. Each raises with no output directory and no staging directory |
| `test_cpu_softmax_violation_is_invalid_with_a_stop_report_only` (1152) | R4: sum tolerance gives `INVALID` with only the stop report. No MPS load, no latency, the pre-write re-check ran, `verify` is false, a re-run is refused |
| `test_cpu_mps_crop_set_mismatch_is_invalid_with_a_stop_report_only` (1181) | R4: one shared plan object for both passes; a forced mismatch gives `INVALID` with only the stop report |
| `test_g5_zero_support_refuses_before_step0_and_the_classifier` (1207) | R4: zero G5 support refuses before Step 0 and the classifier, with no output |
| `test_softmax_predicate_matches_parse_probs_csv` (1222) | R4: `softmax_violations` agrees with `parse_probs_csv` at 1 + 5e-6 (accepted) and 1 + 5e-5 (refused), and on NaN and float64 input |

The E2E harness replaces `load_state`, `load_evaluator`, `latency_preflight`, `load_classifier`,
`step0_check` (wrapping the real one and forcing `passed=True`), `measure_latency` and
`verify_bundle` (with a spy). It also routes `classify` to CPU and passes `rounds=30`. These remain
untested end to end on real artifacts (QA gap G-b) and are covered only by the source QA.

## 5. Gate results (2026-11-05)

| Command | Result |
| --- | --- |
| `(cd detector && uv run pytest -q tests/test_classifier_fusion_r1.py)` | `56 passed in 4.33s`, exit 0 |
| `(cd detector && uv run ruff check m1 tests)` | `All checks passed!`, exit 0 |
| `(cd detector && uv run ruff format --check …fusion module and tests)` | `2 files already formatted` |
| `uv run ruff check src tests` (root) | `All checks passed!`, exit 0 |
| `uv lock --check` (root) | `Resolved 201 packages`, exit 0 |
| `(cd detector && uv lock --check)` | `Resolved 66 packages`, exit 0 |
| AST comparison of top-level functions, pre-fix vs post-fix (`ast.get_source_segment`) | byte-identical: `relabel`, `decide`, `crop_input`, `classify`, `guards`, `assign_outcome`, `paired_bootstrap`, `latency_protocol`, `summarize_latency`, `build_eval`, `step0_check`, `verify_pins`, `verify_bundle`, `check_source_qa`, `publish`, `refuse_existing_outputs`, `load_state`. Changed: `classify_candidates`, `manifest`, `parse_probs_csv`, `run`, `verify`. New: `_source_file`, `source_hashes`, `softmax_ok`, `softmax_violations`, `crop_plan`, `precheck_g5_support`, `recheck_before_write`, `stop_invalid` |
| `graft build . && graft check .` | build parsed 2 changed files; `graph check: OK — the wiring graph is in sync with the code` |
| `graft callers classify_candidates` / `graft callers manifest` | the only caller is `run` in the same module (blast radius stays inside the module) |
| `(cd detector && uv run python -m m1.classifier_fusion_r1 step0)` (pilot-only, allowed) | exit 0, `passed=true`, 22 pins, bundle 8,579/8,579 members; TP 547, FP 150, hits 457, yolo 7/33/42/48/40 = 66/18/12/55/14, mAP50 `0.8520835680058519`, mAP50-95 `0.6088678434901063` (unchanged); `fusion_metric_computed=false`, `classifier_loaded=false`; nothing written |
| `ls <pilot run dir> \| grep fusion` | no `classifier_fusion_r1` output directory |

## 6. Residual points for the delta source QA

- **[P] Pre-Step-0 crop plan.** `crop_plan` now opens the 376 bundle images and applies the pinned
  crop rule before Step 0, instead of after it. It is model-free and produces no metric. Any
  failure there refuses the run instead of consuming it.
- **[P] Other post-Step-0 raises outside R4's list.** They remain raises:
  - `load_classifier` checks (SHA before and after, epoch and config);
  - the `classify` output-shape assertion;
  - `build_eval`'s "MPS relabel rows must be cropped source candidates";
  - a `recheck_before_write` mismatch, which is required to abort without writing.

  The classifier SHA is pinned and was verified at `load_state`. The payload layout was resolved
  by the source QA (S6). The delta QA should judge whether any of these needs the stop-report
  treatment.
- **[P] Step 0 failure path unchanged.** It still returns `INVALID` with no file written, as the
  source QA accepted in S1. Only the three R4 paths write a stop report.

## 7. Flags

`sealed_test_accessed=false`, `training_authorized=false`, `run_invoked=false`,
`latency_measured=false`, `classifier_loaded_on_real_crops=false`, `fusion_metric_computed=false`,
`threshold_lock_written=false`, `d05_changed=false`, `app_enable_authorized=false`,
`original_implementation_record_edited=false`, `other_existing_files_edited=false`,
`commit_or_push=false`.
