# D1 YOLO54 + CompactCNN classifier fusion R1 — scorer delta source QA record (fixes R1–R5)

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent side session. I did not write the scorer, its
tests, the R1–R5 fixes, either implementation record, the contract, Addendum 1, any earlier QA
record or the authorization record.
Scope: **delta source review only** of the R1–R5 fixes. I did not invoke `run` or `latency`, did
not call `measure_latency`, did not load the classifier, ran no classifier forward on any real
crop, and computed no arm-B or fusion metric. The only real-data computations were model-free:
`step0` (arm A only), `manifest(REPO_ROOT, {})`, `recheck_before_write` (hashing only),
`precheck_g5_support` (GT counts only) and `latency_preflight` (no inference).
Checkout: `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`, branch `yolo11n-dual-track-r1`,
HEAD `17db663`.

Verdict: PASS giới hạn — R1 and R2 are correctly fixed, R3 and R4 are implemented and tested, and the diff changes no scoring, crop, guard, outcome, bootstrap or latency rule. No correction is required before execution. The limits are that the real-artifact path cannot be exercised end to end before the single run (gap G-b, inherent), that a few environment-failure raises after Step 0 remain unrecorded raises, and that the addendum misstates the module diffstat.

**May the single real `run` proceed? Yes**, for the post-fix module
`detector/m1/classifier_fusion_r1.py` with SHA-256
`c28033cf3494ef5c6e01af30fdb4aec49dc1470a760565c6bf28744ca836c271`, the tests at
`7ef2a45aa4fb151dbc69108792e0e64c9d2eb8ef32e276aa999c05a583fb05be`, and only while both files
remain byte-identical to those hashes. This record lists **no correction that is required before
execution**, so under the authorization's reading rule (§3) this PASS giới hạn counts as a PASS.
The proposals P1–P4 below are advisory. Any edit to the module or the tests voids this
statement and needs a further delta QA.

## Under review (rehashed at start and at end; unchanged)

| Role | File | SHA-256 |
| --- | --- | --- |
| Prior source QA (PARTIAL) | `docs/review/d1_yolo54_classifier_fusion_r1_source_independent_qa_record.md` | `c40f1c585c66601b781bdbd049ae133d463d349b0dce9c476aabb30342abd01c` |
| Pre-fix module (byte copy in the fix session's scratchpad) | `…/prefix/classifier_fusion_r1.py.prefix` | `90359373a38752d09c2bc7a8206c53f66c726d99b18cf2d7e6da5fe45b9eaf24` |
| Pre-fix tests (byte copy) | `…/prefix/test_classifier_fusion_r1.py.prefix` | `de949559a69ad404ee7833e3ded20646dc508daf1014d90559a83cc53bc893af` |
| Post-fix module | `detector/m1/classifier_fusion_r1.py` | `c28033cf3494ef5c6e01af30fdb4aec49dc1470a760565c6bf28744ca836c271` |
| Post-fix tests | `detector/tests/test_classifier_fusion_r1.py` | `7ef2a45aa4fb151dbc69108792e0e64c9d2eb8ef32e276aa999c05a583fb05be` |
| Implementation record addendum 1 | `docs/review/d1_yolo54_classifier_fusion_r1_implementation_record_addendum_1.md` | `a1b6ad7a2b62976778d82fd5d79217f19c9077d077ff994090317c41983368e0` |
| Original implementation record (must be unchanged) | `docs/review/d1_yolo54_classifier_fusion_r1_implementation_record.md` | `51e69893fec4733dbe1cd336f600ecc6538d0843835ed42db93d7ef22f924e54` |

Pre-fix copies directory:
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/db7deed3-35de-4ef3-95e4-7aa2a55ad92c/scratchpad/prefix/`.
Both copies hash to the pre-fix SHAs above. I built my own `diff -u` of each pair. Apart from the
two header lines, my diffs are byte-identical to the fix session's `module.delta.diff`
(`e5deb1c6…`) and `tests.delta.diff` (`6b3ad371…`).

## Binding spec (rehashed; all match the brief)

| Document | SHA-256 |
| --- | --- |
| Contract `docs/review/d1_yolo54_classifier_fusion_r1_contract.md` | `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` |
| Addendum 1 `docs/review/d1_yolo54_classifier_fusion_r1_addendum_1.md` | `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9` |
| Addendum 1 QA record | `b483788d4056722ccb2a6e6192afced592cc887afbcc844e3527a956874e632c` |
| Owner authorization `…_owner_authorization_2026-11-05.md` | `9f8c5f20c4dab52258d64270d490fc720c941bc1478a22550a549560e3556fcd` |

## Start-of-task state

- I read `AGENTS.md` and `PROJECT_MEMORY.md` (routing only), the prior source-QA record, the
  addendum, the authorization and contract §8. I also read the sibling notes
  `fusion_r1_source_qa_notes.md` and `fusion_r1_fix_r1_r5_notes.md` as data.
- `graft check .` returned `graph check: OK — the wiring graph is in sync with the code`.
- `git log --oneline -3` returned:
  - `17db663 docs(review): pre-registered YOLO54+CompactCNN fusion R1 contract, QA PASS giới hạn`
  - `399bf70 feat(d1): paired A3−pilot validation CIs with independent QA PASS`
  - `5e3fa2a docs(review): R3 addendum — A3 executed via D1-A3-R2, criteria not met`
- `git status --short | head -60` returned 13 ` M` Owner files (`PROJECT_MEMORY.md`,
  `docs/product_roadmap.md`, `docs/review/cam_hanh_trinh_display_rename_r1_2026-11-04.md`,
  `docs/review_index.md`, `scripts/run_parallel_checks.py`, five `src/cpv301_autodrive/…` files
  and three `tests/…` files). It then listed `??` untracked files, including
  `detector/m1/classifier_fusion_r1.py`. None of these was touched.
- `results/experiments/<pilot run>/classifier_fusion_r1` does not exist (before and after).

## D1–D8 summary

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| D1 | R1: `manifest()` hashes module and tests through an allow-listed helper; `guard_path` not relaxed; source hashes at the start of `run`; tests | **PASS** | `_source_file` (`:319–338`) refuses any path not in `SOURCE_FILES = (MODULE, TESTS)` (`:115`), walks every component with `is_symlink()`, requires `S_ISREG` under `lstat`. `guard`, `regular_file` and `guard_path` are byte-unchanged (AST). `run` hashes sources at `:1878`, right after `check_source_qa` (`:1876`), before `refuse_existing_outputs` and `load_state`, and checks the module hash against the gate's at `:1879`. My call `manifest(REPO_ROOT, {})` returned `c28033cf…c271` / `7ef2a45a…05be`, equal to `shasum`. The pre-fix `manifest` still raises `refused sealed-test path` (R1 reproduced). `regular_file(REPO_ROOT, TESTS)` is still refused. `_source_file` refuses `detector/tests/conftest.py`, the contract, `../x.py` and `/etc/passwd`. Tests at `:881`, `:895`, `:933` cover the real checkout, a synthetic root (allow-list, symlinked file, symlinked directory, missing, non-regular) and refusal before `load_state` |
| D2 | R2: re-verification before refusal/publish; abort with no write; G-c test | **PASS** | `recheck_before_write` (`:1774–1784`) re-runs `verify_pins`, compares `source_hashes` to the start-of-run `sources`, re-hashes the classifier against `CLASSIFIER_SHA256`, and runs `verify_bundle(full=False)`. Each raises. `run` calls it at `:1943`, before `refuse_existing_outputs` (`:1944`) and `publish` (`:1945`). `stop_invalid` also calls it before its write (`:1813`). On the real checkout it returned `pins_verified=22` and bundle `members_verified=754` of 8,579 (`full=False`), with no output created. A stale module hash was refused. The G-c test `test_a_pin_changed_mid_run_blocks_every_write` (`:1125`) has 6 cases (pin, classifier through `PINS`, classifier explicit, module, tests, bundle). Each mutates during the latency arm and asserts no output and no staging directory |
| D3 | R3: synthetic E2E `run` → `publish` → `verify`; fakes cannot leak | **PASS** | `test_end_to_end_run_publishes_and_verifies` (`:1069`) reaches `publish`, finds the five outputs and gets `verify() == {"verified": True, "errors": []}`. It also checks manifest sources, inputs and outputs, call order, `verify_bundle(full=False)` after latency, tamper detection and refusal of a second run. All fakes go through the pytest `monkeypatch` fixture, which restores them per test. The module gained no injection hook: `run`'s signature is unchanged (`rounds` already existed), and the new `plan=` keyword of `classify_candidates` is used only by `run`. Limit G-b: `load_state`, `load_evaluator`, `latency_preflight`, `load_classifier`, `measure_latency` and `verify_bundle` are faked in the E2E. I covered `verify_bundle(full=False)`, `verify_pins`, `latency_preflight` and the pinned crop function with real model-free calls |
| D4 | R4: each of the three post-Step-0 raises pre-checked or INVALID + stop report, tested | **PASS** | (a) CPU/MPS crop set: one `crop_plan` (`:1411`) is built at `run:1887`, before Step 0, and passed to both passes. The residual comparison (`:1910–1917`) returns `stop_invalid`. Tested at `:1181` (same plan object, forced mismatch gives stop report only). (b) G5 zero support: `precheck_g5_support` (`:1469`) at `run:1886`, before Step 0. It equals arm A's GT-only support; on real GT the minimum is 22 over 7 keys. Tested at `:1207`. (c) Softmax tolerance: `softmax_violations` (`:731`) at `run:1902` returns `stop_invalid` before the CSV, the MPS load and latency. Tested at `:1152` and `:1222`. In my 4,000-trial old-vs-new check, `parse_probs_csv` gave identical results (2,216 accepted, 1,784 refused) and `softmax_violations` agreed in 4,000 of 4,000 trials. The stop report is written once via `publish` with no result file, `verify` reports it as not verified, and the output directory then blocks a re-run |
| D5 | No scope creep | **PASS** | AST comparison: 59 top-level functions/classes byte-identical, including `relabel`, `decide`, `crop_input`, `classify`, `guards`, `assign_outcome`, `paired_bootstrap`, `paired_map_bootstrap`, `resample_indices`, `latency_schedule`, `latency_protocol`, `summarize_latency`, `measure_latency`, `load_classifier`, `deterministic_cpu`, `build_eval`, `step0_check`, `probs_csv`, `predictions_csv`, `check_source_qa`, `publish`, `main`. Changed: `classify_candidates`, `manifest`, `parse_probs_csv`, `run`, `verify`. Added: 8 helpers. No module constant changed (TAU, PAIRS, PAIR_NAMES, SOURCE_PAIR, CONF, FLAGS, PINS, VERDICT_RE, CLASSIFIER_SHA256, G5_DERIVED_KEYS identical). Four constants were added. The only changed lines adjacent to scoring are `parse_probs_csv` (predicate refactor, shown equivalent above) and the crop path (plan split). The crop rule `crop_input` is unchanged. My old-vs-new check with the pinned `crop_prediction` and a fixed synthetic net gave byte-identical probabilities and invalid sets (66 probabilities, 1 invalid), across plan reuse and the `crop_fn` path, and the plan arrays are not mutated (`classify` copies). No F1/truth-table/bootstrap line changed, so the prior QA's 2,048/2,048 truth table and bootstrap equivalence still apply to byte-identical code |
| D6 | R5: addendum accuracy | **PASS giới hạn** (minor) | Every SHA matches. R1 is disclosed accurately (pre-fix line 1778, cause, timing, never triggered). Every file:line reference I checked is exact (module `:113`, `:115`, `:319`, `:341`, `:719`, `:722`, `:731`, `:757`, `:1411`, `:1443`, `:1469`, `:1774`, `:1787`, `:1830`, `:1876–1879`, `:1886–1887`, `:1899–1917`, `:1942–1945`, `:1995`, `:1999`; tests `:705`, `:881`, `:895`, `:933`, `:950`, `:1069`, `:1125`, `:1152`, `:1181`, `:1207`, `:1222`). The "14 new test cases, 42 → 56" count is correct. The not-run statement is honest. **Inaccuracy:** §1 gives the module diffstat as "+220/−26 lines (net)". `git diff --numstat` gives **+194/−26** (net +168, i.e. 1,876 → 2,044 lines). The tests' +368 is correct. This does not affect any code claim. The original record is unchanged (`51e69893…`) |
| D7 | Gates | **PASS** | See Commands run: 56 passed; ruff ×2 clean; `uv lock --check` ×2 OK; `graft check` OK; `step0` exit 0, `passed=true`, unchanged values |
| D8 | Readiness | **PASS** | Exact command under Readiness. I confirmed the gate's Verdict regex accepts this record's Verdict line form, and that the record quotes the full module, contract and Addendum 1 SHAs. The output directory is absent, MPS preflight passes and `recheck_before_write` passes on the real checkout |

## Detailed findings

### D1 — R1 fix

- The allow-list compares `Path(relative)` with the two constant repo-relative paths, so absolute,
  escaping and any other `detector/tests/…` path is refused before any filesystem access.
- The component walk starts at `repo_root` and checks each joined component with `is_symlink()`.
  It catches a symlinked file and a symlinked `detector/tests` directory (both tested).
  `os.lstat` plus `S_ISREG` refuses directories and other non-regular files.
- The redundant check at `:1879` (`sources[MODULE] == qa["module"]`) is harmless. It ties the
  manifest's module hash to the one the source-QA record quotes.
- `manifest()` still never pins a QA record (contract §8): its keys are `documents`, `flags`,
  `inputs`, `outputs`, `package` and `sources`.

### D2 — R2 fix

- `recheck_before_write` runs after `build_eval` and `manifest` and immediately before the second
  `refuse_existing_outputs` and `publish`, so the window between check and write is minimal.
  A mismatch raises, and the exception propagates out of `run` before `publish`, so nothing is
  staged.
- `verify_bundle(full=False)` re-hashes the members `run` used: validation images, `labels54`,
  `val_groups.json` and the bundle CSV. That is 754 members on the real bundle. It also checks the
  bundle manifest SHA and that the pilot CSV pin is unchanged.

### D3 — R3 test

The E2E harness runs the real source-QA gate (synthetic record), `source_hashes`, `verify_pins`
(synthetic `PINS`), `crop_plan`, `classify_candidates`, `deterministic_cpu`, `decide`,
`build_eval`, `manifest`, `recheck_before_write`, `publish` and `verify`. It routes the MPS pass
to CPU. None of this changes production code paths.

### D4 — R4 treatment, and the residual raises (addendum §6)

- **Pre-Step-0 crop plan.** This is acceptable. Contract §6 (Step 0, line 255) requires reproduction "before
  any arm-B number is computed or written". The crop plan computes crops, not an arm-B number,
  and loads no classifier. A failure there refuses the run instead of consuming it. The crops
  were previously built inside `deterministic_cpu()`. `crop_prediction` is PIL plus NumPy
  (`evaluate_cascade_b0_r1.py:62–66`) and does not use torch, so moving it out changes nothing
  (equivalence checked).
- **Stop report.** `fusion_r1_stop_report.json` is not in the contract §8 output table. It is
  written only on the two INVALID paths, carries `result_files_written=false` and
  `fusion_metric_computed=false`, and implements the prior QA's R4 option. I accept it. Result QA
  should treat its presence as an `INVALID` record (P3).
- **Residual post-Step-0 raises not in R4's list.** They are: `load_classifier` checks (SHA
  before and after, epoch, config, strict load); the `classify` shape/dtype assertion; an MPS
  runtime error in the recompute or the latency arm; `build_eval`'s MPS-row assertion; and a
  `recheck_before_write` mismatch, which must abort by design. I judge these **non-blocking**:
  - the classifier SHA is pinned, and the prior QA confirmed its layout with a load-only check;
  - MPS availability and versions pass preflight (re-run here);
  - the dtype/shape assertion holds for `CompactCNN` with a float32 softmax;
  - the `build_eval` assertion holds by construction, because the MPS rows come from the same
    plan.

  If any of them fires, the process exits with a traceback and writes no output, and authorization
  §4 then requires new written Owner authorization. P1 and P2 make that outcome recorded rather
  than silent.
- **Step 0 failure path.** It is unchanged. It still returns `INVALID` with no file and no output
  directory, as the prior QA accepted.

### D5 — scope

Constants, rules and protocols are unchanged; details in the D5 row. The `parse_probs_csv` predicate
was rewritten from "raise if `abs(Σ−1) > 1e-5`" to "accept if `abs(Σ−1) <= 1e-5`", with the same
finite and non-negative tests and the same float32 round-trip test. That is logically identical,
and my 4,000-trial old-vs-new comparison confirms it.

## Readiness (D8)

The single real `run`, after the coordinator confirms the module and tests still hash to
`c28033cf…c271` and `7ef2a45a…05be` and that the output directory is absent:

```bash
cd /Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/detector && uv run python -m m1.classifier_fusion_r1 run --source-qa-record docs/review/d1_yolo54_classifier_fusion_r1_source_delta_independent_qa_record.md --source-qa-sha256 <SHA-256 of this record>
```

- The record path is repo-relative. `check_source_qa` resolves it against `REPO_ROOT`
  (`/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector`) through `regular_file`, so `cwd`
  does not matter for the path. The command runs from `detector/` so that `m1` is importable in the
  detector uv project. No component of the path contains `test`.
- `<SHA-256 of this record>` is the `shasum -a 256` of this file as written. A file cannot quote
  its own hash. The reviewer reports the hash at hand-over and in the shared notes folder
  (`fusion_r1_delta_qa_notes.md`). The coordinator must recompute it before the run.
- **Gate acceptance.** `VERDICT_RE` (`:279`) is
  `^Verdict:\s*(?:\*\*)?(PASS giới hạn|PASS)(?:\*\*)?(?:\s|$|—|-|\.|,)`. This record has
  exactly one line starting with `Verdict:` (after NFC normalisation), of the form
  `Verdict: PASS giới hạn — …`. It quotes the full module SHA
  `c28033cf3494ef5c6e01af30fdb4aec49dc1470a760565c6bf28744ca836c271`, contract SHA
  `40cbe72ff095b8aea9d2253c02a52c013797b2148febc4bbbd647e68a77c700c` and Addendum 1 SHA
  `fa2ea121623a0072256cd56e88ba1d1e60a90cd85a51f0869fa5d70623bdd6e9`. After writing the record I
  called `check_source_qa(REPO_ROOT, <this record>, <its SHA>)` as a function, with no other
  side effect. The result is in the hand-over notes, since it cannot be written here without
  changing the hash.
- Exit codes: `main` returns 0 only when result files were written, and 2 for `INVALID`
  (Step 0 or stop report).

## Proposals (advisory; none is required before execution)

| # | Proposal |
| --- | --- |
| P1 | Operational, no code change: capture the single run's stdout and stderr to a log outside the repository (e.g. the coordinator's scratchpad), with the exit code. A crash on a residual raise is then documented for the Owner. |
| P2 | For any future successor scorer, not this run: wrap the post-Step-0 segment so that any unexpected exception after the classifier loads is recorded as an `INVALID` stop report. Doing it now would change the module SHA and need another delta QA, which this record does not recommend. |
| P3 | Result QA should treat `fusion_r1_stop_report.json` as the run's `INVALID` record and as an output outside the contract §8 table, written only on R4 paths. |
| P4 | A later append-only note should correct addendum 1's module diffstat from "+220/−26" to "+194/−26". This is cosmetic. |

## Commands run

| Command | Result |
| --- | --- |
| `graft check .` (start and end) | `graph check: OK — the wiring graph is in sync with the code` |
| `git status --short \| head -60`; `git log --oneline -3` | 13 ` M` Owner files plus `??`; HEAD `17db663` |
| `shasum -a 256` on the prefix copies, the 3 reviewed files, the addendum, the original record and the 4 spec documents (start and end) | all match the brief; unchanged at end |
| `diff -u <prefix> <post-fix>` for module and tests; compare with the fix session's diffs; `git diff --no-index --numstat` | identical bodies; module +194/−26, tests +368/−0 |
| Scratch `delta_qa_checks.py`, run with `uv run python` from `detector/`, outside the repo. It does an AST identity check (functions and constants), `manifest(REPO_ROOT, {})` (new and pre-fix), `_source_file` refusals, the data guard, `recheck_before_write` on the real checkout plus a stale-hash refusal, `precheck_g5_support` on real GT, a 4,000-trial `parse_probs_csv` old-vs-new and `softmax_violations` agreement check, and an old-vs-new crop/classify equivalence with the pinned crop function and a synthetic linear net on synthetic PNGs (CPU). No classifier load, no real crop classified | exit 0; results in D1–D5 |
| `latency_preflight(REPO_ROOT)` called as a function (no inference) | registry `ba5ab04f…`, torch 2.14.1 / ultralytics 8.4.172, `versions_match_sahi_r1 = true` |
| `(cd detector && uv run pytest -q tests/test_classifier_fusion_r1.py)` | 56 dots, exit 0; `-v` summary `56 passed in 5.00s` |
| `(cd detector && uv run ruff check m1 tests)` | `All checks passed!`, exit 0 |
| `uv run ruff check src tests` | `All checks passed!`, exit 0 |
| `uv lock --check` (root) | `Resolved 201 packages`, exit 0 |
| `(cd detector && uv lock --check)` | `Resolved 66 packages`, exit 0 |
| `(cd detector && uv run python -m m1.classifier_fusion_r1 step0)` | exit 0; `passed=true`; TP 547, FP 150, hits 457, yolo 7/33/42/48/40 = 66/18/12/55/14, mAP50 `0.8520835680058519`, mAP50-95 `0.6088678434901063`; `fusion_metric_computed=false`, `classifier_loaded=false`; nothing written |
| `ls <pilot run dir> \| grep -i fusion` | no `classifier_fusion_r1` directory (before and after) |

No source file was changed by this review, so no Graft rebuild was needed.

## Flags

`sealed_test_accessed=false`, `training_authorized=false`, `run_invoked=false`,
`latency_measured=false`, `classifier_loaded=false`, `classifier_forward_run_on_real_crops=false`,
`fusion_metric_computed=false`, `app_enable_authorized=false`, `threshold_lock_written=false`,
`d05_changed=false`, `reviewed_files_edited=false`, `existing_files_edited=false`,
`commit_or_push=false`.
