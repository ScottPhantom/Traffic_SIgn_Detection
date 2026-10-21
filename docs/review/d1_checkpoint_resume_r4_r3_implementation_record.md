# D1 checkpoint/resume R4-R3 implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Boundary: `APPEND_ONLY_TRAIN_VAL_ONLY_NO_LIVE_TRAINING_NO_SEALED_TEST`

R4-R3 preserves the hash-reviewed R4-R2 runner, notebook and QA records. It adds a successor runner
and notebook to close the R4-R2 checkpoint-verifier findings.

## Changes

- `run_d1_colab_checkpoint_r3.py` checks every existing path component without resolving through
  symlinks, including `state/recovery`, `snapshots/<generation>` and `weights/`.
- The latest pointer and checkpoint manifest are duplicate-key/non-finite strict JSON. The runner
  validates the run name, integer epoch range and generation relationship before delegating full
  roster/hash/size/binding verification to the pinned `CheckpointStore` implementation.
- `d1_train_checkpoint_r3.ipynb` uses a new Drive run label and remains unexecuted/fail-closed at
  `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Permanent tests cover recovery and weights ancestor symlinks, non-string run identity, missing or
  malformed boot ID, malformed prior JSONL and run-binding mismatch. All preflight failure cases
  must leave a durable FAILED execution record and appended attempt.

## Gate

R4-R3 source must receive a new independent QA PASS before commit/push or notebook pinning. A PASS
would authorize only a new two-runtime/two-epoch L4 smoke. The 100-epoch pilot remains **NO-GO**
until the live artifacts receive a separate independent QA PASS.
