# M1-Colab-R2 QA remediation report

Status: `PM_READY_FOR_INDEPENDENT_RE_REVIEW`
Prepared: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Supersedes implementation package M1-Colab-R1; preserves its FAIL verdict

## Independent QA verdict being remediated

M1-Colab-R1 received `FAIL — 0 Critical, 1 High, 3 Medium, 0 Low`. QA did not create a PASS
record. The four reproduced findings were:

1. a malformed/failed execution, invalid SQLite database and incomplete run contract could still
   be packaged with a hard-coded `SUCCEEDED` outcome;
2. public `--skip-sync` could bypass `uv sync --frozen` and still reach packaging;
3. CUDA/GPU/driver placeholder values such as `UNKNOWN` passed environment validation;
4. an existing bundle-manifest sidecar could be overwritten.

R2 addresses every finding without changing D-05, opening the sealed test, uploading data or
training a model.

## R2 changes

### H1 — evidence-derived result packaging

`detector/colab/run_d1_colab.py` now validates before packaging:

- exact `colab_execution.json` schema, successful terminal state, non-empty start/end timestamps,
  `sealed_test_accessed=false`, null error, exact ordered required steps, run/repository bindings,
  train/val stem hashes, bundle SHA-256 and training parameters/command;
- the existing M1 `inspect_run_weights()` contract for run identity, both weight hashes, governed
  data, D-05 settings, exact environment schema and clean source checkout;
- CUDA backend for Colab result packages;
- non-empty required artifacts and a `results.csv` with at least one completed epoch;
- SQLite integrity, exact `logs` columns, logger identity, ordered workflow/training/terminal
  events, and subprocess output between training start/end;
- matching lifecycle events in `colab_train.log`.

The result manifest now derives terminal outcome and sealed-test status from validated execution
evidence and binds the run attestation. `verify_result_archive()` independently rejects unknown,
duplicate, linked, missing, extra, size-drifted or hash-drifted archive members and outcome drift.
`detector/colab/verify_d1_result.py` exposes that verifier as a standalone CLI.

### M1 — frozen sync cannot be bypassed

The production `--skip-sync` option was removed. Every workflow now executes
`uv sync --frozen`, and the packager requires the exact ordered
`detector_lock_synchronized` step. A missing or reordered step fails closed.

### M2 — exact CUDA identity

`validate_environment_record()` now rejects the placeholders `UNKNOWN`, `N/A`, `NONE`, `NULL`
and `UNAVAILABLE` for CUDA version, GPU name and NVIDIA driver. If `nvidia-smi` cannot provide a
driver on a claimed CUDA run, the run cannot become a validated result package. Apple M1 Pro MPS
latency evidence continues to use null CUDA/driver fields and remains valid.

### M3 — no sidecar/partial overwrite

The bundle builder preflights the archive, sidecar, archive partial and sidecar partial paths and
refuses if any already exists. It uses exclusive creation for new partials. Result packaging uses
the same fail-closed policy. The approved pretrained download also refuses an existing partial
instead of deleting it.

## Added regression coverage

The R2 tests now cover:

- the original QA counterexample (`FAILED`, `sealed_test_accessed=true`, invalid DB and bad run
  evidence) and confirm no result archive is created;
- absence of the `--skip-sync` option and rejection of a missing sync step;
- rejection of `UNKNOWN` NVIDIA evidence;
- preservation/refusal for existing bundle and result sidecars;
- SQLite corruption;
- positive evidence-derived packaging plus post-package hash/roster verification;
- tampered result-manifest outcome;
- the previous train/val-only archive attacks and sealed-test exclusions.

Local R2 pre-handoff checks:

- Colab-specific root tests: `19 passed`;
- detector suite: `54 passed`;
- relevant root/detector Ruff: pass;
- standalone result-verifier help path and notebook JSON: pass.

The full required gates and independent adversarial re-review remain mandatory before R2 can be
called PASS. No source checkpoint, upload or Colab smoke may be performed until that verdict.
