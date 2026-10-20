# D1 checkpoint/resume R1 implementation record

Status: `PM_IMPLEMENTED_AWAITING_INDEPENDENT_QA`

Date: 2026-10-20 (`Asia/Ho_Chi_Minh`)

Boundary: `LOCAL_IMPLEMENTATION_ONLY_NO_COLAB_NO_TRAINING_NO_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Implemented

- `detector/m1/checkpoint_store.py`: atomic, hashed, two-generation Drive recovery store.
- `detector/m1/resumable_train.py`: governed fresh/pause/resume/finalize training entrypoint.
- `detector/colab/run_d1_colab_checkpoint_r1.py`: successor Colab orchestration, append-only
  attempt log and compatible eight-artifact result package.
- `detector/colab/d1_train_checkpoint_r1.ipynb`: fail-closed two-runtime recovery drill.
- `docs/d1_colab_checkpoint_r1_operator_guide.md`: Owner instructions and acceptance evidence.
- Targeted detector and root regression tests for interruption, restoration, binding mismatch,
  symlinks, fresh/resume command separation and sealed-test exclusion.

The pinned primary notebook, runner, CLI and verifier remain byte-unchanged. The successor accepts
the immutable historical data bundle only after independently deriving the current governed
train/val roster and comparing every binding except the historical source Git commit. Both the
bundle's source commit and the clean successor code commit are recorded separately.

## Recovery semantics

The smoke target is two epochs so a real optimizer resume can be demonstrated. The first runtime
is intentionally stopped after exactly one completed epoch. After the runtime is destroyed, the
second runtime must restore `last.pt` plus optimizer/scheduler/scaler state and complete epoch 2.
This is a recovery drill, not a model-quality experiment and not authorization for the 100-epoch
pilot.

## Fail-closed release state

The notebook contains `CODE_COMMIT = 'PENDING_AFTER_QA'` and asserts that it is a 40-character Git
SHA. Therefore it cannot execute on Colab until independent QA passes and the Owner explicitly
authorizes the reviewed commit/push. After that commit exists, a notebook-only successor must pin
the reviewed SHA before upload or execution.

## Required QA scope

Independent QA must review source and execute the real CLIs with synthetic artifacts. At minimum:

- fresh epoch-1 pause followed by local result deletion and resume to epoch 2;
- config, pointer, manifest, checkpoint and symlink attacks;
- historical bundle source-commit/current-code-commit separation;
- result-package roster and standalone verifier compatibility;
- notebook fail-closed placeholder, exact Drive route, unexecuted cells and test exclusion;
- no mutation of pinned predecessor files.

No Colab cell, GPU training, Drive write, sealed-test access, commit, push or upload occurred in
this implementation package.
