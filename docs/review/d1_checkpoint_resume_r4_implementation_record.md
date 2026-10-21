# D1 checkpoint/resume R4 runtime-evidence implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Boundary: `TRAIN_VAL_ONLY_NO_LIVE_TRAINING_NO_SEALED_TEST`

## Purpose

R3 proved checkpoint creation and true epoch-2 resume, but independent QA could not prove from
retained artifacts that the two legs ran on distinct Colab runtimes. R4 is an append-only successor;
it does not modify the R3 runner, notebook, reports, checkpoints or result package.

## Implementation

- `detector/colab/run_d1_colab_checkpoint_r2.py` derives a privacy-preserving SHA-256 identity from
  a scoped training tag and Linux `/proc/sys/kernel/random/boot_id`. It persists only the schema and
  digest, never the raw boot ID, backend hostname, Colab URL, account token or cookie.
- Each append-only `execution_attempts.jsonl` record binds the runtime digest, the common training
  run binding and the checkpoint binding. The resume leg fails before training unless exactly one
  valid fresh `PAUSED_FOR_RESUME` record exists, the run binding matches, and the runtime digest is
  different.
- `colab_execution.json` schema version 2 embeds the ordered attempt evidence and binds its terminal
  runtime, run and checkpoint values. The result archive retains this execution record while keeping
  the previously reviewed eight-file roster.
- `verify_live_state` requires exactly two attempts in fresh/resume order, different valid runtime
  digests, identical run/checkpoint bindings, `SUCCEEDED`, and
  `sealed_test_accessed=false`. It also compares the live JSONL evidence with the copy bound into the
  verified result archive.
- `detector/colab/d1_train_checkpoint_r2.ipynb` is an unexecuted successor using a new R4 run label.
  Its code commit is deliberately `PENDING_AFTER_QA`; it cannot run until QA PASS, commit/push, and
  an exact commit pin.

## Fail-closed tests

`tests/test_d1_checkpoint_runtime_evidence_r4.py` covers:

- deterministic but privacy-preserving digest derivation;
- valid two-runtime evidence;
- equal, missing and malformed runtime digests;
- reordered attempts;
- altered run and checkpoint bindings;
- disagreement between external JSONL and packaged execution evidence;
- end-to-end fresh/resume persistence through the successor wrapper;
- an unexecuted, train/val-only, sealed-test-free notebook.

## Current gate

This implementation does not authorize a live smoke or the 100-epoch pilot. Required order:

1. independent QA of R4 source, tests and notebook;
2. commit and push the QA-passed implementation;
3. replace only `CODE_COMMIT = "PENDING_AFTER_QA"` with that exact clean commit, then commit/push the
   notebook pin;
4. run a new fresh leg on L4 under `checkpoint_smoke_seed_20261018_r4`;
5. disconnect/delete that runtime, allocate a new L4, change only `MODE` to `resume`, and Run all;
6. submit the retained Drive evidence and result package to a new independent QA session.

The 100-epoch pilot remains **NO-GO** until the final live-smoke QA returns PASS.
