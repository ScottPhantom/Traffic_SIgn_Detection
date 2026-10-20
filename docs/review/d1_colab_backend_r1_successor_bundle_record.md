# D1 Colab backend R1 successor bundle record

Status: `LOCAL_SUCCESSOR_BUNDLE_READY_AWAITING_INDEPENDENT_QA_AND_PRIVATE_UPLOAD`

Recorded: `2026-10-20`

Boundary: `TRAIN_VAL_ONLY_NO_UPLOAD_NO_COLAB_RERUN_NO_TRAINING_NO_SEALED_TEST_ACCESS`

## Purpose

The first real D1 smoke failed before epoch one because the locked detector environment rejected
the inherited Colab Matplotlib inline backend. Backend R1 was independently QA-approved and
committed as `ffc2b448f06c45dae597de5b565cab64c0377573`. This new bundle pins that repaired commit and
uses a new filename so the failed run and its original bundle remain immutable evidence.

## Verified local artifacts

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `tmp/m1_colab_train_val_backend_r1.tar.gz` | `766226800` | `7ea344cb1e2c166786d0552f215993969efec9b5f06a9bf49310d4390243d641` |
| `tmp/m1_colab_train_val_backend_r1.tar.gz.manifest.json` | `1499866` | `7e0dc5b0144faa5f0be407224eaf8070dd51199fa8a1d2f164b248fd6a06d5b2` |

The builder and its official verifier report:

- `status=VERIFIED` and `test_included=false`;
- exactly `5888` payload files;
- `1912` raw train images, `376` raw validation images, `1800` WP35 train images and `1800`
  WP35 train labels;
- embedded repository commit `ffc2b448f06c45dae597de5b565cab64c0377573`;
- train stem-list SHA-256 `6ac767509def899071f6d6dc0da1e98e62a2a19eb0e62292970e8273b4c99372`;
- validation stem-list SHA-256 `ae3f3509319fbb301012e9fbeb7431caacfcd4035c9d2f9167f24e3ed2b8f593`.

Build and verification commands:

```text
uv run python scripts/build_m1_colab_bundle.py build --repo-root . --archive tmp/m1_colab_train_val_backend_r1.tar.gz
uv run python scripts/build_m1_colab_bundle.py verify --repo-root . --archive tmp/m1_colab_train_val_backend_r1.tar.gz
```

## Successor notebook controls

`detector/colab/d1_train.ipynb` now uses:

- archive `m1_colab_train_val_backend_r1.tar.gz` and its exact sidecar;
- fresh state directory `runs/smoke_seed_20261018_backend_r1`;
- built-in mounted-byte size and SHA-256 checks for both files before opening the archive manifest;
- the unchanged one-epoch T4-compatible smoke configuration and governed runner.

The notebook is unexecuted and contains no test-export or final-evaluation command. The original
failed state directory `runs/smoke_seed_20261018` must not be deleted or reused.

## Remaining authorization boundary

No Drive object has been created or overwritten by this package step. After independent QA passes,
the Owner must explicitly authorize uploading these exact two new files to the existing private
Drive folder. A Colab rerun is not a verified result until the new persisted execution record,
SQLite/text logs and result archive are read back.
