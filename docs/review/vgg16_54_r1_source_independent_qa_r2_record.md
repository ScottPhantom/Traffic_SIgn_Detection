# VGG16-54 R1 — independent source QA R2

Verdict: **PASS**

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `SOURCE_QA_ONLY_NO_GPU_RUN_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Reviewed snapshot

- Source manifest SHA-256:
  `552750165f253fff37cd0740ac6bf0559ad05862e54033027d6a479089ec85f6`.
- Source manifest roster: `22` files, all bytes matched.
- VGG configuration SHA-256:
  `b5275ca6635859f3eb2ae5d98e480da18f748667a96f92a36d1e2145b197c15a`.
- Runner SHA-256:
  `4d6092d1c10e3ae4aca95ab422fd3e9c980bf438a666b91bd6f9f3855cdafaec`.
- Efficient checkpoint store SHA-256:
  `c79c85ccc95376c8922955e16be131dda74ae7b0b4eda65d787d47da1cfab160`.
- VGG tests SHA-256:
  `6d8e62fc8628dce16a1519313a36799fcc49db8d790f6f300195146b90ec2bb3`.
- Checkpoint-store tests SHA-256:
  `40c24b9b943538740036225623deb5651b6528f0d96a8058f9de3a0aa924c754`.
- Isolated D1-VRE-R2 test SHA-256:
  `3157d001cdd458d9537caf77cce6fd395052da29d6c6a7f4a65d29f33560adaf`.

## R1 blocker closure

### H-1 — telemetry now fails closed before restore

The R1 attack was reproduced by changing `checkpoint_io_seconds` to `-1` in
`checkpoint_io.jsonl`. On this R2 snapshot, `restore_latest(...)` raised
`RuntimeError: checkpoint I/O telemetry duration is invalid`, and the requested destination did
not exist afterward. No checkpoint byte was copied and no model/data/GPU path was entered.

Independent payload attacks changed model, optimizer, AMP scaler, Python/NumPy/Torch/CUDA RNG,
binding and latest-pointer data. All were rejected before a restore destination existed.

### G-1 — real-input test is isolated

`tests/test_val_reeval_r2.py::test_real_inputs_pass_check_without_model` passed while the real
D1-VRE-R2 output remained in place. The test uses an isolated `tmp/pytest_vre_r2/...` output path;
no existing evaluation artifact was deleted, renamed or overwritten. The complete detector test
suite then reached 100% with exit code 0.

## Required checks

- The VGG16 convolutional stack calls `vgg16(weights=None)`, uses global average pooling,
  dropout and a `Linear(512, 54)` crop head. The live model test returned 54 logits.
- Frozen configuration is max 100 epochs, minimum 30 epochs, patience 15, scratch weights,
  54 classes, no horizontal flip and `sealed_test_accessed=false`.
- Cascade B0 bundle readback: 3,712 train images / 12,621 train crops; 376 validation images /
  624 validation crops; 8,575 members; `test_included=false` and
  `sealed_test_accessed=false`.
- Owner/source-QA/smoke proofs rejected 12/12 wrong-hash, schema, `seal=true` and symlink attacks.
- Fresh smoke accepts only completed epoch 0; resume smoke accepts only completed epoch 1. Epoch
  2 or later is rejected before epoch 3 can run.
- Recovery retained exactly two generations. Checkpoint I/O telemetry remained separately timed.
- Supported-class macro-F1 is primary; lower validation loss wins ties.
- Early stopping did not trigger before epoch 30, triggered with a 15-epoch stale window,
  produced a valid early-stopped terminal package and preserved `best.pt` across a later
  non-improving epoch.
- Targeted Ruff passed; 26 targeted VGG/checkpoint tests passed; the isolated D1-VRE-R2 test
  passed; full detector pytest reached 100% with exit code 0; `uv lock --check` passed.
- Final `graft check .` returned `OK`; all 22 source-manifest hashes matched.

## Authorization

This PASS authorizes only creation of a launch notebook and a future L4 fresh-epoch-1 smoke after
the exact Owner approval, source-QA proof and hashes are pinned. It does not authorize resume
smoke, long training, result publication, upload, commit, push or sealed-test access. Resume smoke
requires the fresh epoch-1 artifact and a genuinely different runtime; long training requires
independent smoke-artifact QA PASS.

No training, upload, download, commit, push or sealed-test access occurred in this review.
