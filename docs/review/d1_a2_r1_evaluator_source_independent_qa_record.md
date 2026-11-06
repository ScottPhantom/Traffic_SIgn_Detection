# D1-A2-R1 evaluator successors — independent source QA record

Date: 2026-11-05 (`Asia/Ho_Chi_Minh`)
Reviewer: Claude Code (Opus 5.5), independent source QA sub-agent. I did not write the code under
review.
Scope: the staged package under `<wt>/tmp/a2_eval/`, where
`<wt>` = `/Users/nguyentantai/Desktop/app/Traffic_Sign_Detector/.claude/worktrees/centercam-yolo54-r1`.
Spec: `docs/review/d1_a2_r1_run_contract.md` §2, §4, §5, §7, read from the Desktop checkout.

Verdict: PASS giới hạn — no Critical or High defect. The evaluator changes only the candidate side, its attestation rebuild is faithful, and every refusal path holds. Two Medium conditions apply to the morning run: M1 (the documented command needs `PYTHONPATH=.`) and M2 (only the standard two-attempt package is accepted).

**May the evaluator be used on the real A2 result tomorrow?** Yes, under all of these conditions:

1. The four staged source and test files are placed byte-identical into the Desktop checkout:
   - evaluator `c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317`;
   - CI `2dc6088ccc9efc92fc85543960c028a5b1aadb8d23c321ff241a04d1deaf0e1d`;
   - the two test files (§1).
2. The predecessors still hash as in §2. The default repo gate and `graft build . && graft check .`
   pass after placement.
3. The evaluator command carries `PYTHONPATH=.` (M1).
4. The A2 archive comes from the standard A2 launcher packaging path: fresh pause plus one
   successful resume, schema v2. A repair-packaged archive is refused by design and needs a new
   QA'd successor (M2).
5. The archive is not renamed. The local `--state` holds `colab_execution.json` and
   `recovery/latest.json`. The Owner authorization record exists in the Desktop checkout at the
   same bytes and path as on Colab.

This record authorizes no run, placement, commit or push.

## 1. Hashes verified

| Staged file | Claimed = observed SHA-256 |
| --- | --- |
| `detector/colab/evaluate_d1_a2_r1_common_r1.py` | `c08f5de603037aa3289dfc91d44bb2d67b3a29f7e94eba5f2967815fb0c08317` — match |
| `detector/m1/a2_pilot_paired_ci_r1.py` | `2dc6088ccc9efc92fc85543960c028a5b1aadb8d23c321ff241a04d1deaf0e1d` — match |
| `detector/tests/test_evaluate_d1_a2_r1_common_r1.py` | `cb41583457c7fe5975a79280cb1c60d3f1976aebbf4ae9adcb690a661af3ab5e` — match |
| `detector/tests/test_a2_pilot_paired_ci_r1.py` | `673cab0249f36a1da3ed37d73ba6902533bc77c3fd1e2d1c4a0877f331beb46a` — match |
| `docs/review/d1_a2_r1_evaluator_implementation_record.md` | `dab36b1fb1b25492456baddd752e220f2d583b4d7954a357254a5ba26465664a` — match |

## 2. Predecessors (Desktop checkout, read-only)

All of these match the implementation record §2 and, where it states them, the contract:

| File | Observed SHA-256 |
| --- | --- |
| `evaluate_d1_a3_r2_common_r1.py` | `5d8e49bf…ecca6` |
| `a3_pilot_paired_ci_r1.py` | `7edb3824…0bdea4` |
| `run_d1_colab_a2_r1.py` | `a6bb6e68…2d6de` |
| `resumable_train_a2_r1.py` | `c3823eef…42ace` |
| `a2_repeat_list_r1.py` | `28fc4ced…12619` |
| `yolo54_improvement_r3.py` | `548144b1…a639` |
| `contract.py` | `901e7e37…bbbf` |
| `run_d1_colab_checkpoint_r6.py` / `_r2.py` / `_r1.py` | `71a9f4a9…` / `8041540a…` / `e3193ad7…` |
| `run_d1_colab.py` | `6a508eeb…` |
| `evaluate_cascade_b0_r1.py` | `8bedb4c1…` |
| `metrics.py` | `d24570f8…` |
| `package_d1_a3_r2_result_r1.py` | `432d30fa…` |

The pilot `run_contract.json` hashes to `9f8fc94c…0b88`, which equals the contract.

## 3. Findings

### Critical / High

None.

### M1 (Medium) — the morning evaluator command does not run as written

**Evidence:**

- Implementation record lines 265–279 run `uv run python colab/evaluate_d1_a2_r1_common_r1.py …`
  from `detector/` without `PYTHONPATH`.
- `detector/pyproject.toml` sets `[tool.uv] package = false`, so `m1` is not installed.
- When a script runs, `sys.path[0]` is the script's directory (`colab/`). My probe
  `probe_import.py` gave `m1 resolvable: False` without `PYTHONPATH` and `True` with
  `PYTHONPATH=.`.
- The evaluator imports `from m1 import contract` (line 36). The A3 evaluator imports
  `from m1.metrics import Frame`.

**Effect:** the command fails closed with `ModuleNotFoundError`, which gives no wrong result.
Line 281 hedges with "add `PYTHONPATH=.` if `m1` does not resolve", but it will not resolve.

**Fix:** make it mandatory in §5:
`PYTHONPATH=. uv run --no-sync python colab/evaluate_d1_a2_r1_common_r1.py …`. Use `--no-sync`, or
`--frozen`, so `uv` does not re-lock. The CI commands use `python -m` from `detector/`, so they
resolve `m1` already.

### M2 (Medium, non-blocking) — only the standard two-attempt schema-v2 package is accepted

**Evidence:**

- The evaluator calls `launcher.r6.verify_r4_result_archive` (`evaluate…:144`).
- That function requires a `schema_version` that is exactly int 2 (`r6:30-37`) and exactly two
  attempts, fresh `PAUSED_FOR_RESUME` then resume `SUCCEEDED` (`run_d1_colab_checkpoint_r2.py:150-158`).
- Probe P1 shows that fresh + failed resume + resume is refused.

**This is not stricter than the launcher:**

- The launcher's own `r2.main` refuses any resume unless exactly one fresh attempt exists
  (`r2:417`).
- On Colab it swaps in the same verifier for the packager (`r2:503`, used at `r1:327`).
- An attempt is appended only on a clean pause, on success or on a caught exception
  (`r1:452/476/489`). A Colab disconnect that kills the process appends nothing, so a fresh resume
  on a new runtime still yields two attempts.
- `COMPLETED_FROM_FINAL_CHECKPOINT` is accepted (probe P2).

**What is refused:**

- A run with a caught resume failure. The launcher already refuses to continue such a run.
- A repair-packaged archive. The A3 precedent `package_d1_a3_r2_result_r1.py:7,359,364` emits
  schema 3 with a third "repair" attempt. If the A2 packaging shim fails on real Colab (contract §12
  marks this unknown), the A3-style salvage archive will be refused.

Implementation record §6.5 lists "exactly two runtime attempts" but does not name the repair-path
consequence.

**Fix:**

- State in the record that a repaired A2 archive needs an append-only evaluator successor with its
  own source QA, mirroring the repair packager's schema.
- Do not loosen this R1 evaluator.

### Low

- **L1 — not all transitive predecessors are pinned.** `verify_predecessors` (`evaluate…:106-116`)
  pins only the A3 evaluator, the A2 launcher and the A2 trainer. These are not pinned:
  - the launcher's r6/r5/r2/r1/`run_d1_colab` chain;
  - `m1/contract.py`, `m1/metrics.py`;
  - `evaluate_cascade_b0_r1.py`, `run_yolo11n_n1_r1.py`.

  The A3 evaluator pinned none of these either. Scoring drift is mitigated:
  - the CI requires the A2 JSON's pilot block to equal the QA-passed A3 JSON exactly
    (`a2_pilot_paired_ci_r1.py:118-119`);
  - it re-derives both models' points and mAP from the CSVs (`:291-332`).

  All the hashes I observed match §2. **Fix:** in any successor, add those SHA-256s to the
  `predecessor_sha256` output, or verify them. Until then, have the result QA record them.
- **L2 — `contract.data_yaml` is not compared** (`evaluate…:235-242`). This is the same gap as the
  launcher shim (A2 source QA advisory A2). **Fix:** require `run_data["data_yaml"]` to end in
  `/data/processed/m1_yolo/data.yaml`, or to equal the pilot's value.
- **L3 — Pyright `str | None` at `evaluate…:41` and `:109`.**
  - Cause: this is `ModuleType.__file__` typing. Pyright could not resolve the sibling import from
    the staged location (`evaluate…:33`, `reportMissingImports`).
  - Runtime risk: there is no None crash risk. `a3eval` is a file-backed module; if it were not
    found, line 33 would raise `ImportError` first. Both lines execute in the passing tests. Line 111
    (`a2t.__file__`) is not flagged.
  - Fix (optional): `assert a3eval.__file__ is not None`.
- **L4 — `results.csv` accepts a duplicated epoch row** (`evaluate…:340-342`, probe P4). This is
  permissive, not stricter. **Fix (optional):** require `epochs == list(range(1, 101))`.
- **L5 — CI `_maps` repeats `common.average_precision` without its empty-input guard**
  (`a2_pilot_paired_ci_r1.py:210-222`). Full-set equality within 1e-12 is enforced before any CI,
  and a resample with zero predictions cannot occur at `conf=0.001` on real data. **Fix
  (optional):** reuse the guard.
- **L6 (information) — the checks stricter than `inspect_a2_run_weights` are consistent.** Each
  one matches the contract and what the trainer writes:
  - **GPU.** `gpu_name == "NVIDIA L4"` (`:248-252`). The pilot record says exactly
    `"NVIDIA L4"`, and contract §1/§7 require L4.
  - **Export binding.** It must equal the pilot's (`:62-70,241`). This is byte-equal to the pilot
    `contract` block.
  - **Counts.** 975/339/636 (`:59,202`). `a2_repeat_list_r1.materialize_runtime` writes them from
    the pinned spec.
  - **Run-name pattern.** (`:58,146`) The real `m1.cli.run_name` output
    `D1_yolo11s_wp33_afa03d4b_20261018_<ts>_a2_r1` matches it (probe_runname). The pilot,
    `yolo11n` and other-seed names are refused.
  - **Only effect.** An A2 trained on a non-L4 GPU is refused, and that run would itself be a
    contract deviation.
- **L7 (cosmetic).** The reused `a3eval.infer` messages say "A3". This is already disclosed in
  §6.6.

## 4. Review questions

1. **Single change.** **Verified current behavior.**
   - These pilot-side objects are the predecessor's own: inference (`a3eval.infer`, conf 0.001,
     IoU 0.70, imgsz 1280), `verify_package`, `verify_evaluation_scope`, `load_pinned_baseline`,
     `report` and `BUNDLE_SHA256` (`evaluate…:50-51,476-487,504-505`).
   - Only `extract_best` is copied. It is candidate-side and identical to A3 except the
     parameterised name and hash.
   - The output keys are the A3 keys with `a3_`→`a2_`, plus identity fields (test-checked against
     the stored A3 JSON).
2. **Attestation rebuild.** It is faithful.
   - It uses the launcher's own `_exact_keys`, key sets, `expected_train_args` and constants.
   - The attestation has the same 11 keys, the same values and the same `canonical_sha256`.
     `run_contract_sha256` is computed from the archived bytes, which are the bytes the Colab
     packager hashed.
   - The author's cross-test against the real `inspect_a2_run_weights` gives an identical dict and
     SHA. I re-read both functions line by line.
   - Checks the evaluator cannot repeat offline are the runtime YAML/list existence and the weight
     files on disk. They are bound by the run-contract hash and the archive member hashes.
   - It could not accept anything the launcher would reject. It could reject a valid run only in
     the M2 repair case or the L6 non-L4 case.
3. **Refusal paths.** The tests cover each required path, and my probes confirmed them:
   - archive, manifest and authorization hashes;
   - experiment;
   - status;
   - epochs and early stop (archived and live);
   - `git_dirty_files`;
   - the list SHA, including the 339 variant `c953d458…`, plus 339-variant counts with the 975 SHA
     (probe P5);
   - the authorization SHA (CLI, record, execution, live, local record missing or tampered);
   - `sealed_test_accessed` (manifest, record, execution; integer 0 refused, P9).

   23 evaluator probes (P1–P23) gave 0 unexpected outcomes.
4. **Paired CI.**
   - **Class mapping.** Derived key→yolo id is translated through bundle `classes.csv` and checked
     against `EXPECTED_YOLO_IDS`. The real map is 7→7, 32→33, 41→42 (46→48). The real supports
     from the A3 JSON are 111/29/26, matching R3 §4, and the pilot agnostic recall is 0.87660. An
     identity map is refused (C1).
   - **Identical draws.** One `resample_indices` list (1000 rounds, seed 20261018, 9 intact
     groups) is used for both models after a frame-alignment check.
   - **Pilot side.** It must equal the A3 JSON exactly.
   - **Point estimates first.** `reproduce` runs before `resample_indices` (`:368-369`; test plus
     C4).
   - **Determinism.** Output is canonical, sorted, byte-compared in `verify` mode, and tested.
   - **Degenerate flags.** Zero-width, single-group and unsupported classes are flagged.
   - **Relabel.** It leaves no `a3` label behind (C3).
   - **Criteria readout.** It is labelled `…_NOT_ACCEPTANCE`. No threshold is selected or locked.
     The validation-selected block is labelled diagnostic.
   - **Boundaries.** No exact-boundary float issue exists: 0.05×111, 0.05×29, 0.05×26, 0.03×376
     and 0.85×624 are all non-integers.
5. **Pyright.** There is no real None crash risk (L3).
6. **Tests and lint.** See §5.
7. **Morning readiness.** It is not complete as written:
   - the command needs `PYTHONPATH=.` (M1);
   - placement steps (copy into `detector/colab`, `detector/m1`, `detector/tests`, `docs/review`)
     and the post-placement gate and Graft are only mentioned in §4, not in §5.

   The rest is correct:
   - the bundle path `../tmp/yolo11n_n1_extract_r1` equals `a3ci.BUNDLE`;
   - the output directory equals the CI's `A2_DIR`;
   - the CSV/JSON SHA hand-off is right;
   - the requirements on `--expected-checkout`, the local authorization record and the state
     files are right (§6.3–6.4).

## 5. Commands run (from the Desktop `detector/`; no bytecode/cache written; no git command)

| Command | Result |
| --- | --- |
| `shasum -a 256` on the 5 staged files and the predecessors | all match (§1–§2) |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. uv run --no-sync pytest -p no:cacheprovider -c <detector>/pyproject.toml --rootdir <detector> -o addopts="" -q <wt>/tmp/a2_eval/detector/tests tests/test_a3_pilot_paired_ci_r1.py tests/test_run_d1_colab_a2_r1.py` | **120 passed** in 124.98 s, no skips. The real-pilot `results.csv` test ran. |
| same with `--co` on the staged tests | 77 collected: 54 evaluator + 23 CI |
| `uv run --no-sync ruff check --no-cache --config <detector>/pyproject.toml <wt>/tmp/a2_eval/detector` | `All checks passed!` |
| `uv run --no-sync ruff format --check --no-cache …` | `4 files already formatted` |
| `pyright --pythonpath <detector>/.venv/bin/python <staged evaluator> <staged CI>` | 5 errors: 1 unresolved sibling import from the staged location (`:33`) and 4 = lines 41 and 109 × `__new__`/`__init__` (L3). 0 in the CI module. |
| `probes.py` (scratch) | P1–P23 and C1–C4: **0 unexpected** |
| `probe_runname.py` (scratch) | the real `run_name` format matches; 3 foreign names refused |
| `probe_import.py` (scratch) | `m1` unresolvable without `PYTHONPATH` (M1) |
| `probe_support.py` (scratch; A3 JSON + bundle `classes.csv`, train/val only) | supports 111/29/26 at yolo 7/33/42; class map 7→7, 32→33, 41→42 |

The scratch scripts are under
`/private/tmp/claude-501/-Users-nguyentantai-Desktop-app-Traffic-Sign-Detector/c0d7550b-5da5-44ff-bc50-750b12caaceb/scratchpad/qa_a2_eval/`.

**Not run:** the default repo gate and Graft build/check. The files are not placed yet. Run them
after placement.

## 6. Flags

- `sealed_test_accessed=false`. The sealed test (`afa03d4b…`) was never opened, listed or scored.
  The token was read only inside run names.
- No training, network, download, upload or inference happened, on real or other weights. No
  threshold or D-05 change was made.
- No file in the Desktop checkout was written, and no git command ran there. The staged files were
  not edited. This record is the only file written outside the scratchpad.

## 7. Claim classification

- **Verified current behavior:**
  - the single-change property;
  - attestation equivalence with the launcher;
  - the refusal paths;
  - the CI mapping, draws, ordering, determinism and flags;
  - the two-attempt rule being identical to the launcher's;
  - M1 (the `m1` import failure);
  - by tests (120 passed), probes and code reading.
- **Verified artifact:**
  - the staged and predecessor SHA-256s;
  - the pilot `run_contract.json` (`9f8fc94c…`) fields: `gpu_name`, `contract`, `train_args`,
    weight path shape;
  - the A3 JSON supports and pilot recall;
  - the bundle class map.
- **Proposal:** every fix in §3. The morning command corrected per M1.
- **Unknown:**
  - the behavior on the real A2 archive;
  - whether the A2 packaging shim succeeds on Colab (if not, M2 applies);
  - A2's metrics;
  - the CI runtime on real data.
