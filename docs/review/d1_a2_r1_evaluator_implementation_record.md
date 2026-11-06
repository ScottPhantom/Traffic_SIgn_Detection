# D1-A2-R1 evaluator successors — implementation record

Status: `IMPLEMENTED_NOT_RUN_ON_A2_DATA_AWAITING_INDEPENDENT_SOURCE_QA`
Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Author: Claude Code (Opus 5.5), sub-agent of the coordinating session.
Contract: `docs/review/d1_a2_r1_run_contract.md` §4 (evaluator plan), §2, §5.

**Boundary.** This record covers source code and synthetic tests only.

- The code has **not** been run on real A2 data. The A2 result archive did not exist when it was
  written.
- No training, inference, download, upload or network access happened. No D-05 gate or threshold
  changed. The sealed test (`afa03d4b…`) was not opened, listed or scored.
- The files were staged under `<worktree>/tmp/a2_eval/` and are **not** in the Desktop checkout.
- The code **needs independent source QA before use.**

## 1. What was built

| Staged path → repo path | SHA-256 | Role |
| --- | --- | --- |
| `detector/colab/evaluate_d1_a2_r1_common_r1.py` | `c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317` | A2 common evaluator, successor of the A3 evaluator |
| `detector/m1/a2_pilot_paired_ci_r1.py` | `2dc6088ccc9efc92fc85543960c028a5b1aadb8d23c321ff241a04d1deaf0e1d` | A2 − pilot paired group bootstrap |
| `detector/tests/test_evaluate_d1_a2_r1_common_r1.py` | `cb41583457c7fe5975a79280cb1c60d3f1976aebbf4ae9adcb690a661af3ab5e` | 54 tests |
| `detector/tests/test_a2_pilot_paired_ci_r1.py` | `673cab0249f36a1da3ed37d73ba6902533bc77c3fd1e2d1c4a0877f331beb46a` | 23 tests |
| `docs/review/d1_a2_r1_evaluator_implementation_record.md` | (this file) | record |

`a2_pilot_paired_ci_r1.EVALUATOR_SHA256` pins the evaluator bytes above. If QA changes the
evaluator, update that constant. A test fails until the two agree.

## 2. Predecessors read (SHA-256 observed in the Desktop checkout, read-only)

| File | SHA-256 | Use |
| --- | --- | --- |
| `docs/review/d1_a2_r1_run_contract.md` | read | binding spec |
| `detector/colab/evaluate_d1_a3_r2_common_r1.py` | `5d8e49bfafc1343ff1cc3fd4064410914ab6e75c23a1108240b09c36dc3ecca6` (= contract) | imported; re-verified at run time |
| `detector/m1/a3_pilot_paired_ci_r1.py` | `7edb3824a0f69f385fcb07628d4a5720688ee55af5cc4421c7b118165c0bdea4` (= contract) | imported; re-verified by the CI |
| `detector/colab/run_d1_colab_a2_r1.py` | `a6bb6e684701b5a95bd03b71bac777693ec08f1ccb853c98edb2cefdcec2d6de` (= contract §5) | imported; re-verified at run time |
| `detector/m1/resumable_train_a2_r1.py` | `c3823eefb9777912fc76302a642427a64869c9097274fc4d5841966c07d42ace` (= contract §5) | `verify_owner_authorization`, `SPEC`; re-verified |
| `detector/colab/package_d1_a3_r2_result_r1.py` | `432d30fad9d3b7114373bda6de3727ffcb31db29b4228ce962ff94618986cc87` | read for the attestation pattern (not imported) |
| `detector/colab/run_d1_colab_checkpoint_r6.py` | `71a9f4a9f8efaa81f657dd414ab8a7d3354ae13a7fcd024e04b42ef2ccce8a35` | `verify_r4_result_archive` (via launcher) |
| `detector/colab/run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` | runtime evidence, `strict_json_bytes` |
| `detector/colab/run_d1_colab_checkpoint_r1.py` | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` | packager (read) |
| `detector/colab/run_d1_colab.py` | `6a508eebcb83915201569bc74913a3dd546b288caf2331a9b3e4bd7a567500bc` | `verify_result_archive` (base) |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` | common report/AP (via A3 evaluator) |
| `detector/m1/yolo54_improvement_r3.py` | `548144b107714d95427b1704700a2ff8cd879143d8f2366e931afecf6777a639` (= contract) | `FOCUS_KEYS`, `A2_REPEAT_KEYS` |
| `detector/m1/a2_repeat_list_r1.py` | `28fc4cedb438859f2edd6215a97eb00cb36f385344e19731155e1da971712619` (= contract) | `EXPECTED_YOLO_IDS` |
| `detector/m1/contract.py` | `901e7e372d9660cd79e6bfcab43684b1693f0a4aafad9f4c331fd8f04ba6bbbf` (= contract) | env validation, gates, hashes |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` | operating points, bootstrap |
| `detector/m1/resumable_train.py` | `0a963d4bc246613402283531b6280836606ac1f5b35b5d215b3959a1354aa6e7` (= contract) | outcome schema (read) |
| `detector/tests/test_a3_pilot_paired_ci_r1.py`, `test_run_d1_colab_a2_r1.py`, `test_package_d1_a3_r2_result_r1.py` | `194a8f55…`, `6a5745e1…` (= contract), `034d9dd6…` | test models |
| Pilot `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` | source of the governed export binding |
| A3 `comparison_a3_r1.json` | `98b8947e379e2dbf88066884ee4540bc669f8402d459b1891b071b53ee2c2c73` | pilot-side anchor for the CI |

## 3. Design

### 3.1 Evaluator (`evaluate_d1_a2_r1_common_r1.py`)

**Single change.** The pilot side is the A3 evaluator's own objects, reused by import:

- `a3eval.common`, `a3eval.verify_package`, `BUNDLE_SHA256 = 8e6ffe77…`;
- `a3eval.infer`, with `conf=0.001`, NMS IoU 0.70, `imgsz=1280` and the 376/624 roster check;
- `common.load_pinned_baseline` and `common.report`.

The module defines no inference, matching, AP or operating-point code of its own (tested). Only
the candidate side is new.

**Required CLI inputs:**

- `--archive` / `--archive-sha256`;
- `--manifest` / `--manifest-sha256`;
- `--owner-authorization-sha256`;
- `--expected-checkout`;
- `--state`, `--bundle` and `--output-dir`, as in A3.

**Run order (`run`).** Each step must pass before the next one runs.

1. Refuse an existing output directory.
2. Re-verify the predecessor SHA-256s: the A3 evaluator, the A2 launcher and the A2 trainer.
3. **Candidate pins.**
   - The SHA formats are checked first.
   - Then the manifest bytes, then the archive bytes, and the manifest must bind the archive. No
     other file is read before these pass.
4. **Inherited archive verifier.** `launcher.r6.verify_r4_result_archive` runs unchanged. It
   checks:
   - the R1 8-file roster, member sizes and hashes;
   - `terminal_outcome=SUCCEEDED`, `sealed_test_accessed=false` and the manifest `archive_name`;
   - the R4/R6 two-runtime evidence in the archived execution record: fresh pause and resume
     success, distinct runtime digests, the same bindings and `schema_version` 2.
   - The run name must also match `D1_yolo11s_wp33_afa03d4b_20261018_<ts>_a2_r1`.
5. **Run attestation, recomputed offline.**
   - `launcher.inspect_a2_run_weights` cannot be called directly here. It re-reads the
     Colab-absolute runtime files and needs the run directory to sit under the local
     `RESULTS_DIR`.
   - `verify_run_contract` therefore applies the same schema and invariants using the launcher's
     own `_exact_keys`, `A2_RUN_CONTRACT_KEYS`, `A2_DATA_KEYS`, `expected_train_args` and
     constants, plus `contract.validate_environment_record(require_clean=True)`.
   - It builds the same attestation dict and requires `canonical_sha256` to equal the manifest's
     `run_attestation_sha256`.
   - A test cross-checks this against the launcher's real `inspect_a2_run_weights` on a local
     mirror and gets identical dicts and SHA.
6. **Archived execution record.** It must show:
   - experiment and package `D1-A2-R1`, `SUCCEEDED`, `epochs=100`;
   - outcome `COMPLETED` or `COMPLETED_FROM_FINAL_CHECKPOINT` at epoch 100;
   - `COMPLETED_EARLY_STOPPED` is refused explicitly;
   - list SHA, roster, authorization equal to the run contract's, the checkout, seed, tag and
     state suffix.
7. **Training log.** `results.csv` must hold epochs 1..100 and end at 100. `args.yaml` must show
   `epochs: 100` and `patience: 0`.
8. **Owner authorization.** `resumable_train_a2_r1.verify_owner_authorization` runs on the local
   checkout. The record named in the run contract must exist, match its SHA-256, contain the
   authorization line and name the list and roster SHAs.
9. **Live state (A3 parity).** `<state>/colab_execution.json` must be SUCCEEDED, 100 epochs and
   sealed-false, with the same run, checkpoint and authorization bindings. The
   `recovery/latest.json` generation must be `epoch-0100` and its binding must equal the archived
   checkpoint binding.
10. **Bundle and inference.** Bundle verification and the evaluation scope come next. `best.pt` is
    extracted only if it matches the run contract's `best.pt` SHA. Then come inference, the
    baseline, the CSV and the JSON.

**Output.** `a2_predictions.csv` and `comparison_a2_r1.json`. The JSON keys are the A3 keys with
`a3_` renamed to `a2_`, plus candidate identity fields:

- `experiment`, `a2_run`;
- `a2_run_attestation_sha256`, `a2_run_contract_sha256`, `a2_train_list_sha256`;
- `a2_training_outcome`, `owner_authorization`, `checkout_commit`, `predecessor_sha256`.

The JSON always carries `sealed_test_accessed=false` and the archive and manifest SHAs.

### 3.2 Paired CI (`a2_pilot_paired_ci_r1.py`)

**Reused unchanged** from `m1.a3_pilot_paired_ci_r1`:

- `verify_pins`, which verifies the bundle, the pilot CSV `87884c53…`, the A3 anchors, the A3
  evaluator and the report;
- `gt_frames`, `with_predictions`, `class_names`, `frame_stats`;
- `resample_indices` (1000 rounds, seed 20261018, intact groups, identical draws for both
  models);
- `paired_block`, `per_group`, `_correct_matrices`, `ci95`, `canonical`.

`paired_block` output is relabelled `a3` → `a2`. The numbers are unchanged, which is tested
against the predecessor.

**New in this successor:**

- **A2 pins.** The CSV and JSON SHA-256 are required CLI inputs. The A2 evaluator SHA is pinned.
  The JSON must bind:
  - `package`, `experiment`, `split`, 376/624;
  - the CSV SHA, the bundle SHA and sealed-false.
  - Its `pilot_common_method` must equal the QA-passed A3 JSON's exactly, which is the pilot-side
    single-change check.
- **Derived-key mapping.** `FOCUS_KEYS` = R3 `("7","32","41","46")`. Criteria classes are R3
  `A2_REPEAT_KEYS` `("7","32","41")`. They are mapped through the bundle `classes.csv`, and the
  result must equal `EXPECTED_YOLO_IDS` `{7:7, 32:33, 41:42}`. An identity map is refused.
- **Point-estimate check before any CI.** For both models:
  - the operating points at 0.20 and at the validation-selected confidence (A2's read from its
    JSON, the pilot's required to be 0.20);
  - `select_threshold`;
  - the per-model `group_bootstrap`;
  - exact-class mAP50 and mAP50-95 within 1e-12.
  - Any mismatch aborts. A test proves no resample is drawn first.
- **Degenerate flags.** Each interval gets `zero_width_ci` and `ci_degenerate`. The latter also
  covers a class whose support sits in a single group, and an unsupported class. They are listed
  in `degenerate_ci_flags`, with the contract §4 caveat.
- **mAP.** A paired CI for both mAP50 and mAP50-95 (the predecessor had mAP50-95 only).
- **`r3_a2_criteria_fixed_020`.** A descriptive point readout of the R3 §5 criteria:
  - each class recall up by ≥ 0.05;
  - FP/image up by ≤ 0.03;
  - overall recall ≥ 0.85, read as the D-05 agnostic recall, i.e. the pilot's 0.8766.
  - It is labelled `..._NOT_ACCEPTANCE`.
- **Output.** `docs/review/generated/d1_a2_pilot_paired_ci_r1.json`, write-once, with a `verify`
  mode.

## 4. Commands run and results (verified current behavior)

All commands ran from the Desktop `detector/` directory. They used `--no-sync`,
`PYTHONDONTWRITEBYTECODE=1` and `-p no:cacheprovider`, so no cache or bytecode was written to the
checkout.

| Command | Result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. uv run --no-sync pytest -p no:cacheprovider -c $PWD/pyproject.toml --rootdir $PWD -o addopts="" -q <wt>/tmp/a2_eval/detector/tests tests/test_a3_pilot_paired_ci_r1.py tests/test_run_d1_colab_a2_r1.py` | **120 passed** in 125.9 s (77 new + 43 predecessor) |
| `... pytest --co ... <wt>/tmp/a2_eval/detector/tests` | 77 collected: 54 evaluator + 23 CI |
| `uv run --no-sync ruff check --no-cache --config $PWD/pyproject.toml <wt>/tmp/a2_eval/detector` | `All checks passed!` |
| `uv run --no-sync ruff format --check --no-cache --config $PWD/pyproject.toml <wt>/tmp/a2_eval/detector` | `4 files already formatted` |

`<wt>` = `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/.claude/worktrees/centercam-yolo54-r1`.

How the staged tests load the code:

- They load the staged modules by file path, from `Path(__file__).parents[1]`.
- They resolve the checkout's `detector/colab` through `m1.contract.DETECTOR_ROOT`.
- The same files therefore run unchanged once they are copied into the checkout.
- `test_predecessor_pins_match_the_checkout` and `test_evaluator_pin_equals_the_sibling_evaluator_source`
  passed against the real Desktop files.

The default repo gate (`uv run ruff check src tests && uv run pytest -q && uv lock --check`) and
`graft build/check` were **not** run. The files are not in the checkout yet. Run them after
placement.

### 4.1 Refusal paths covered (evaluator, `test_candidate_refusals` + named tests)

- **Wrong hash:**
  - archive SHA, manifest SHA, malformed SHA;
  - a manifest that does not bind the archive;
  - a tampered member, a renamed archive;
  - a wrong attestation SHA;
  - an archived `best.pt` not equal to the run contract's;
  - `extract_best` with a foreign `best.pt` SHA.
- **Experiment ≠ D1-A2-R1:** in the run contract and in the execution record.
- **Status ≠ SUCCEEDED:**
  - archived execution `FAILED`, refused by the R4/R6 evidence check;
  - live execution `FAILED`;
  - a missing two-runtime attempt.
- **Not 100 epochs:**
  - execution `epochs=40`, outcome `completed_epoch=99`;
  - `train_args.epochs=40`, `results.csv` with 99 epochs;
  - `args.yaml` with patience 30, `train_args.patience=30`;
  - live `epoch-0040`.
- **Early-stopped:** outcome `COMPLETED_EARLY_STOPPED`.
- **`git_dirty_files != 0`:** refused.
- **List SHA ≠ `90d735d6…`:**
  - in the run contract, including the 339-variant hash `c953d458…`;
  - in the execution record.
- **Authorization SHA missing or wrong:**
  - CLI argument absent or other;
  - run-contract `owner_authorization.sha256` missing;
  - execution `owner_authorization` null;
  - local record missing or tampered.
- **`sealed_test_accessed != false`:** in the manifest, the run contract and the execution record.
- **Also refused:**
  - wrong checkout, wrong GPU (not L4), changed D-05 gates, other export binding;
  - an extra run-contract key, pilot `data`, a non-A2 run name;
  - a live binding mismatch, an existing output directory.
  - A refusal happens before any bundle or model access (tested).

**CI refusals and properties:**

- CSV/JSON SHA mismatch or malformed;
- sealed-true, other package, other experiment;
- CSV-binding or bundle mismatch;
- a changed pilot side, a changed evaluator source;
- an identity class map;
- a point-estimate mismatch before any CI;
- determinism: the same seed gives byte-identical output, another seed differs;
- identical draws for both models;
- degenerate flags;
- mAP equal to `common.average_precision`.

## 5. Morning run (after QA and placement into the checkout)

Read these values from the A2 run, not from this file:

- `<ARCHIVE>` = `<state>/<RUN>_result.tar.gz`. Do **not** rename it, because the manifest binds
  `archive_name`.
- `<MANIFEST>` = `<ARCHIVE>.manifest.json`.
- `<ARCHIVE_SHA>` / `<MANIFEST_SHA>`, from `shasum -a 256` on the downloaded files. Cross-check
  them against Codex's Colab record.
- `<AUTH_SHA>` = the `--owner-authorization-sha256` used to launch A2. The record itself must be
  present in the Desktop checkout at its `docs/review/` path.
- `<CHECKOUT>` = the `--expected-checkout` used to launch A2. It equals `checkout_commit` in
  `colab_execution.json`.
- `<STATE>` = the local copy of the Drive folder `M1_D1_Colab/runs/d1_a2_seed_20261018_r1`. Only
  `colab_execution.json` and `recovery/latest.json` are read from it.

```bash
cd detector
uv run python colab/evaluate_d1_a2_r1_common_r1.py \
  --bundle ../tmp/yolo11n_n1_extract_r1 \
  --state "<STATE>" \
  --archive "<ARCHIVE>" --archive-sha256 <ARCHIVE_SHA> \
  --manifest "<MANIFEST>" --manifest-sha256 <MANIFEST_SHA> \
  --owner-authorization-sha256 <AUTH_SHA> \
  --expected-checkout <CHECKOUT> \
  --output-dir ../results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1 \
  --device mps
shasum -a 256 ../results/experiments/d1_a2_seed_20261018_r1/evaluation_common_r1/{a2_predictions.csv,comparison_a2_r1.json}
uv run python -m m1.a2_pilot_paired_ci_r1 write --a2-csv-sha256 <CSV_SHA> --a2-json-sha256 <JSON_SHA>
uv run python -m m1.a2_pilot_paired_ci_r1 verify --a2-csv-sha256 <CSV_SHA> --a2-json-sha256 <JSON_SHA>
```

The A3 evaluator was run with `PYTHONPATH=.` semantics; add `PYTHONPATH=.` if `m1` does not
resolve. The CI run takes about 1000 × 2 `ap_per_class` calls, like the predecessor.

## 6. Unresolved points and risks for the morning run

1. **Attestation format** (proposal, partly unverified). The offline attestation copies the
   launcher shim formula exactly, and the test checks it against the launcher function. The real
   packager path has never produced an A2 archive. Contract §12 lists "packaging shim on a real
   Colab result" as unknown. If the real archive's attestation differs, the evaluator refuses
   rather than accepts.
2. **Pinned predecessors.** The run fails closed if the committed A2 launcher, the trainer or the
   A3 evaluator differ from the contract SHAs above, for example after QA edits. The fix would be
   to re-pin after review.
3. **Local Owner authorization record.** The record must be present at the same bytes in the
   Desktop checkout. A record that exists only on Colab causes a refusal.
4. **Live state.** `--state` is required, for A3 parity. If only the archive and manifest were
   downloaded, fetch `colab_execution.json` and `recovery/latest.json` too.
5. **Strictness choices** beyond `inspect_a2_run_weights`. Each of these refuses rather than
   accepts:
   - `gpu_name == "NVIDIA L4"`;
   - the governed export binding equal to the pilot's;
   - repeated counts 975/339/636;
   - the run-name pattern;
   - exactly two runtime attempts (inherited R4/R6 rule).
6. **Messages.** The reused `a3eval.infer` error messages say "A3". The behavior is unchanged;
   only the text is misleading.
7. **Evaluator pin in the CI.** If the evaluator is edited, update
   `a2_pilot_paired_ci_r1.EVALUATOR_SHA256`.

## 7. Claim classification

- **Verified current behavior:**
  - the refusal paths and properties in §4.1, by 77 synthetic tests;
  - offline attestation equal to `inspect_a2_run_weights` on a synthetic mirror;
  - `verify_training_log` accepting the real pilot `results.csv` and `args.yaml` shape;
  - ruff check and format clean.
- **Verified artifact:** the predecessor SHA-256s in §2, which match the contract where it states
  them, and the staged file SHA-256s in §1.
- **Proposal:**
  - the morning commands in §5;
  - the output locations;
  - reading "overall recall" as agnostic recall;
  - the criteria readout format.
- **Unknown:**
  - the behavior on the real A2 archive;
  - whether Codex's run meets every invariant (§6);
  - A2's metrics;
  - the CI runtime on real data.
