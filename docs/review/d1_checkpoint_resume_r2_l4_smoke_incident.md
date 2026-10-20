# D1 checkpoint/resume R2 L4 smoke incident

Date: 2026-10-21 (Asia/Ho_Chi_Minh)

Status: `ABORTED_BEFORE_TRAINING_NO_CHECKPOINT_CREATED`

## Verified observations

- Notebook account: `tainguyentan0908@gmail.com`.
- Runtime: Colab L4 (Python 3), 52.96 GB RAM shown by Colab.
- Train/val bundle preflight passed from the eight verified Drive parts.
- Checked-out code commit: `891d3eeec39c60a1b203ce9adffae941034f7f5a`.
- The runner started in `fresh` mode with `epochs=2` and `--stop-after-epoch 1`.
- After about eight minutes, the runner process remained at about 100% CPU, no CUDA
  compute process was present, and `colab_train.log` contained only the workflow-start
  record. Training had not begun and no recovery checkpoint existed.
- The operator interrupted the cell. The notebook showed `KeyboardInterrupt`; the sealed
  test was not exported or accessed.

## Root cause

`extract_historical_bundle` opened a gzip tar archive and called `extractfile` twice for
each missing member: once for verification and again for extraction. The second call
seeked backward in the compressed stream. With 5,888 files this repeatedly reinflated the
archive and made pre-training verification impractically slow.

## R3 remediation

- Sort members by `offset_data` and process them in archive order.
- Read each payload member exactly once while hashing and writing it.
- Write new files to a sibling `.partial` path, verify size and SHA-256, then atomically
  replace the destination.
- Add a regression test that proves one `extractfile` call per payload member and checks
  that no partial file remains.
- Use a new append-only Drive run label `checkpoint_smoke_seed_20261018_r2`; preserve the
  aborted R1 state as evidence.

The 100-epoch pilot remains `NO-GO`. R3 must pass independent QA and the two-runtime L4
recovery drill before that gate can change.
