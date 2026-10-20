# D1 long-training checkpoint and recovery plan R1

Status: `R2_REMEDIATED_AWAITING_INDEPENDENT_QA_AND_L4_SMOKE`

Date: 2026-10-20 (`Asia/Ho_Chi_Minh`)

Boundary: `TRAIN_VAL_ONLY_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Decision

Do not start the 100-epoch D1 pilot with the current `run_d1_colab.py`. Its text and SQLite logs
are durable on Drive, but the live `best.pt` and `last.pt` remain on Colab's ephemeral disk until
the run finishes. A runtime reset can therefore lose all model progress.

The long run may start only after the successor path below passes an independent QA session. The
existing runner, notebook and their pinned hashes remain unchanged.

## Recovery design

The successor must train on `/content` for performance and attach
`m1.checkpoint_store.make_ultralytics_callback(...)` to Ultralytics `on_model_save`. After each
completed epoch, the callback must:

1. copy `last.pt`, `best.pt`, `results.csv`, `args.yaml` and `run_contract.json` into a new Drive
   generation;
2. write each file through a temporary file, `fsync`, compute SHA-256 and compare source/copy;
3. write and verify `checkpoint_manifest.json`;
4. update `latest.json` only after the whole generation is valid;
5. retain the current and immediately previous complete generations.

An interrupted copy is forensic evidence only. It is never resumable because `latest.json` still
points to the previous complete generation.

## Binding that must be identical on resume

The recovery binding must include at least:

- Git commit and detector lock SHA-256;
- approved pretrained-weight SHA-256;
- M1 export manifest SHA-256 and train/val stem hashes;
- seed, total epochs, image size, batch, workers, fraction and patience;
- `fliplr=0` and the D-05/test-seal binding already emitted by the M1 contract.

Changing any bound value creates a new experiment and a new Drive state directory. It must not
resume an earlier optimizer state.

## Resume protocol after Colab interruption

1. Reconnect a fresh GPU runtime. Do not delete or edit the previous Drive state.
2. Rerun mount, mounted-byte preflight, bundle reconstruction, exact checkout, frozen dependency
   sync, model hash verification and `m1.cli check`.
3. Read `latest.json`, independently re-hash its manifest and all five artifacts, then verify the
   requested binding.
4. Restore the verified snapshot to a new empty local run directory under `/content`.
5. Resume from restored `weights/last.pt` with Ultralytics optimizer/scheduler/scaler state. The
   first resumed epoch must equal `completed_epoch + 1`.
6. Append a new execution-attempt record and continue mirroring every completed epoch.
7. After normal completion, use the existing eight-artifact result packager and standalone
   verifier. Recovery snapshots are not accepted-model evidence by themselves.

If the latest generation fails verification, stop. Falling back to the previous retained
generation is allowed only through an explicit, logged recovery command that verifies it fully;
never edit `latest.json` by hand.

## QA attacks required before long training

Independent QA must run in a separate session and demonstrate:

- simulated interruption during each artifact copy leaves the old snapshot selected;
- tampered `last.pt`, `best.pt`, manifest, pointer and config binding are rejected;
- symlinked store/artifact paths and path traversal are rejected;
- two-generation retention never deletes the active or rollback generation;
- a fake resumed training starts exactly at the next epoch and retains optimizer state;
- real one-epoch smoke on Colab produces a Drive snapshot, a normal result archive and consistent
  SQLite/text/execution evidence;
- no test payload, `export-test` or sealed-test access appears anywhere in the path.

## Go/no-go sequence

| Gate | Required evidence | Current state |
| --- | --- | --- |
| C1 | Crash-safe store implementation and local interruption tests | R2 repaired; QA pending |
| C2 | Successor train CLI/runner/notebook integrates callback and resume | R2 repaired; QA pending |
| C3 | Independent QA of C1-C2, including adversarial tests | R1 FAIL; R2 pending |
| C4 | One-epoch L4 smoke, Drive checkpoint readback and result verifier PASS | NOT RUN |
| C5 | Owner reviews smoke and authorizes the 100-epoch pilot | NOT REQUESTED |

Current verdict: **NO-GO for long training**. This is deliberate; it prevents a costly pilot from
starting before resume is executable and independently verified.

## Local evidence produced in this package

- `detector/m1/checkpoint_store.py`: crash-safe store and Ultralytics callback adapter.
- `detector/tests/test_checkpoint_store.py`: interruption, tamper, binding, retention, symlink and
  callback regression coverage.
- Command: `cd detector && uv run ruff check m1/checkpoint_store.py
  tests/test_checkpoint_store.py && uv run pytest tests/test_checkpoint_store.py -q`.
- Observed result: Ruff PASS; pytest **5/5 PASS**.

No Colab cell or training command ran. No Drive object, dataset, checkpoint, test seal, commit or
remote branch was changed.
