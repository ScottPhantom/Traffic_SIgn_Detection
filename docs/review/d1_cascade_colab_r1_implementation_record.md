# D1 cascade Colab R1 implementation record

Status: `PM_READY_AWAITING_INDEPENDENT_QA`
Prepared: `2026-10-19` (`Asia/Ho_Chi_Minh`)
Boundary: `ONE_CLASS_DETECTOR_TRAIN_VAL_ONLY_NO_TRAINING_NO_TEST_ACCESS`
Base checkpoint: `150777a49d010096fbe246a61a9589f2a27b9e00`

## Purpose and authority

This successor package prepares the Colab training path for the one-class detector in the
Owner-approved detector-plus-classifier comparison baseline. It uses the independently reviewed
D1 cascade train/validation dataset and the already approved private M1 train/validation bundle.
It does not approve the cascade gate proposal, implement classifier evaluation, open the sealed
test, or change the primary 54-class M1 runner.

The package intentionally reuses the exact private upload rather than creating or uploading a
second copy:

- archive SHA-256:
  `eb5226e36cf619e271132794c97fd633f7528d72e25463356eb165f36f43e191`;
- source commit recorded inside that archive:
  `1842a1b77e6448a54fec486937f4c0f0e6ff19f5`;
- 5,888 regular payload files, train/validation only, with no test member;
- current M1 export-manifest SHA-256:
  `8a8df5f242829277fb86cfd55490dd4284e42a6c09f7ace6a509e42feb179d71`.

The successor verifier permits that one historical clean source commit only. It still reconstructs
the current governed file roster and validates every member path, split, kind, size and SHA-256.

## New files

| File | Role | SHA-256 |
| --- | --- | --- |
| `detector/colab/run_d1_cascade_colab.py` | Outer Colab workflow, internal one-class training command and result packager | `fe77a05c3a4aa2ed685d3fd75bc8e9026400a0e137a10bd056cb9c492e3b8f7c` |
| `detector/colab/d1_cascade_train.ipynb` | Private-Drive L4 launcher; one-epoch smoke by default | `a4b9871ccc7f7eaa48d2eceec4adc0192f5ae1d25f03f625608744408ce41d93` |
| `tests/test_d1_cascade_colab.py` | Contract, boundary, training-invariant and result-package regressions | `0f81beda9e6ffc553075cee9b4ad82bd7bf8b052c2a76a8bb687d78ea4f087da` |

No existing M1 runner, M1 bundle builder, dependency file, project memory or roadmap file was
edited by this package.

## Fail-closed controls

- The exact approved bundle archive SHA-256 and historical source commit are pinned. Every archive
  record is reconciled against the current governed train/validation roster and every payload is
  hashed before extraction. Missing, extra, linked, unsafe, wrong-split or changed members fail.
- The QA-approved cascade builder and manifest are pinned by SHA-256. The materialized dataset is
  regenerated and fully verified before training: one class, only `train` and `val`, and no
  `test:` entry in `data.yaml`.
- The exact detector lock and the Owner-approved local `yolo11s.pt` SHA-256 are required. The only
  optional download is the same official weight path already approved by the Owner, followed by
  byte verification.
- Seeds are restricted to `20261018`, `20261019` and `20261020`; training forces
  `deterministic=true`, `pretrained=true`, `fliplr=0.0`, and `plots=false`.
- Environment variables disable external experiment tracking, and the internal detector runtime
  also disables Ultralytics integrations. Training refuses a non-CUDA runtime.
- The internal run contract binds model, seed, full training arguments, one-class data manifest,
  split hashes, approved upload, detector environment, weights and `sealed_test_accessed=false`.
- Console output, `colab_train.log`, VGG16-compatible `DB_logger.db` and atomic
  `colab_execution.json` retain the complete lifecycle. The result package is emitted only after
  a successful terminal state and contains exactly eight required artifacts.
- The public command surface is `run`; the internal command is `_train`. Neither command has a
  test export, evaluation, threshold-selection or final-evaluation option.

## PM verification

Measured locally from the current shared worktree:

- cascade Colab targeted tests: **9/9 PASS**;
- root Ruff for the new test: PASS;
- root lock check: PASS, 168 packages resolved and lock unchanged;
- detector Ruff for `m1`, `tests` and the new runner: PASS;
- complete detector test suite: **70/70 PASS**;
- detector lock check: PASS, 66 packages resolved and lock unchanged;
- notebook JSON parse: PASS; all code-cell outputs are empty and metadata requests an L4 GPU;
- real approved private archive verification: PASS; SHA-256 matched, all 5,888 payload members
  re-hashed, allowed splits were exactly `train`/`val`, `test_included=false`, and the embedded
  source commit was the pinned `1842a1b...`;
- `git diff --check`: PASS.

The targeted suite executes the real local one-class dataset verifier, proves that only the three
fixed seeds parse, runs a fake Ultralytics training lifecycle through the real internal command,
checks `fliplr=0`, deterministic/pretrained flags and telemetry shutdown, validates exact weight
bindings, packages the canonical eight-file result, detects archive tampering, and rejects an
incomplete execution record. No actual model was trained.

## Independent QA request

QA should independently review the old-upload/new-runner boundary, especially the deliberate
historical bundle-commit exception; verify the exact archive SHA and full member roster when the
private bundle is available; exercise the real public CLI with a synthetic or copied safe bundle;
check that result validation cannot accept reordered/missing lifecycle steps, altered training
arguments, non-CUDA metadata, unsafe archive members or nonzero horizontal flip; and confirm that
no test route exists.

No upload, download, Colab execution, model training, validation evaluation, test export, sealed
test read, commit or push occurred while preparing this R1 record.
