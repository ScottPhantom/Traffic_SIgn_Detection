# D1 single-seed 100-epoch pilot R1 implementation record

Date: 2026-10-21  
Status: `IMPLEMENTED_LOCALLY_QA_PENDING_NO_LIVE_PILOT`  
Scope: train/val only; sealed test remains closed

## Authorization and predecessor

The live R4-R6 two-runtime L4 recovery drill and its independent artifact QA both PASSed. The
artifact QA record authorizes the D1 single-seed 100-epoch pilot only. It does not authorize sealed
test access, final evaluation, model acceptance or deployment.

Pilot R1 reuses the QA-passed runner at implementation commit
`47c86d17430808ceeee6e1a1a553cf6fef88e5ed`; no pinned runner is modified.

## Added artifacts

- `detector/colab/d1_train_pilot_r1.ipynb`: unexecuted Colab notebook.
- `scripts/build_d1_pilot_notebook.py`: deterministic builder derived from the pinned R6 smoke
  notebook.
- `tests/test_d1_pilot_colab.py`: notebook/configuration/sealed-boundary checks.

The pilot configuration is fixed to seed `20261018`, 100 epochs, image size 1280, batch 4, device
0 and run label `pilot_seed_20261018_r1`. Batch 4 is the configuration exercised by the accepted
L4 recovery smoke.

## Recovery sequence

1. `MODE="fresh"` uses a new Drive state and intentionally stops after epoch 1.
2. The operator disconnects that runtime, connects a new L4 runtime, changes only
   `MODE="fresh"` to `MODE="resume"`, and runs all cells.
3. Resume restores the Drive checkpoint and trains toward epoch 100. The R6 callback mirrors every
   model-save checkpoint to Drive.
4. A hard runtime disappearance before a terminal attempt is appended may be retried with
   `MODE="resume"` on another L4. A recorded `FAILED` attempt is fail-closed and requires review;
   its Drive state must not be deleted or overwritten.
5. Success requires `SUCCEEDED`, `epoch-0100`, a verified result archive, two distinct retained
   runtime digests and `sealed_test_accessed=false`.

The notebook contains neither `export-test` nor `--final-eval` and never refers to the processed
test directory.

## Local verification before independent QA

- Notebook builder completed.
- Ruff passed for the builder and tests.
- Pilot notebook tests plus R4-R6 strict runtime-evidence tests passed: 11/11.

No Colab pilot, upload, validation evaluation or sealed-test operation was performed by this
implementation package. Independent source QA is mandatory before commit/push and live use.
