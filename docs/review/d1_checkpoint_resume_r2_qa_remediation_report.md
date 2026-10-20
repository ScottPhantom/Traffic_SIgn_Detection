# D1 checkpoint/resume R2 QA remediation report

Status: `PM_REMEDIATED_AWAITING_INDEPENDENT_QA_R2`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Base: immutable R1 FAIL record
`docs/review/d1_checkpoint_resume_r1_independent_qa_record.md`.

Boundary: `LOCAL_REPAIR_ONLY_NO_COLAB_NO_TRAINING_NO_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Finding closure

### H-1 — incomplete generation collision

Checkpoint copies now use attempt-unique hidden staging directories. The canonical
`epoch-NNNN` directory is created only by atomic rename after the staged snapshot verifies. An
invalid legacy canonical directory is moved into `recovery/quarantine/` before retry, preserving
evidence without blocking the resumed epoch. The regression now interrupts epoch 2, restores
epoch 1 into a new local runtime and successfully checkpoints epoch 2.

### H-2 — results-root symlink

`resumable_train` preserves the lexical path, checks every existing component with `lstat`,
requires exact equality with the governed `contract.RESULTS_DIR`, then repeats safe-directory
checks before creating or restoring a run. External symlink targets are rejected before writes.

### H-3 — state child symlinks

The successor runner checks every writable log/state child. Text logging and JSONL append use
`os.open(..., O_NOFOLLOW)`; SQLite is pre-created/opened with `O_NOFOLLOW` before the existing
schema handler is attached. Execution temp paths and existing result outputs reject symlinks,
including broken links. Regression attacks cover all five writable top-level state children.

### H-4 — early stopping

Only an explicit `--stop-after-epoch` may produce `PAUSED_FOR_RESUME`. A normal return before the
maximum epoch is finalized as `COMPLETED_EARLY_STOPPED`, writes a `TRAINED` run contract and is
eligible for normal packaging.

### M-1 — resume continuity

The callback retains the verified previous epoch. Its first resume callback must equal
`completed_epoch + 1`; every subsequent callback must be contiguous. A replay or gap raises before
the snapshot pointer advances.

### L-1 — notebook Ruff

The notebook was formatted without execution. It remains valid JSON with null execution counts
and empty outputs; standalone notebook Ruff now passes.

## Current release boundary

`CODE_COMMIT` remains `PENDING_AFTER_QA`. The notebook is deliberately non-runnable on Colab until
R2 independent QA passes and the Owner authorizes commit/push. No predecessor pin was modified.
