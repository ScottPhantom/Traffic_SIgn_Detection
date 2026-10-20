# D1 Colab smoke backend failure — 2026-10-20

Status: `OBSERVED_FAILED_BEFORE_FIRST_EPOCH`

Boundary: `TRAIN_VAL_ONLY_NO_SEALED_TEST_ACCESS`

## Observed run

- Notebook source commit: `1842a1b77e6448a54fec486937f4c0f0e6ff19f5`.
- Drive state directory: `runs/smoke_seed_20261018` (preserved; do not reuse or delete).
- Runtime observed in Colab: Python 3 GPU runtime with NVIDIA T4; detector environment Python
  `3.12.3`.
- Configuration: seed `20261018`, one epoch, image size `1280`, batch `8`, device `0`.
- Started: `2026-10-20T03:22:10+00:00`; finished: `2026-10-20T03:24:22+00:00`.
- Terminal status: `FAILED`; `sealed_test_accessed=false`.

The persisted execution record completed these steps in order:

1. `bundle_verified_and_extracted`;
2. `train_val_export_regenerated`;
3. `detector_lock_synchronized`;
4. `approved_pretrained_weight_verified`;
5. `m1_cli_check_passed`.

`training_completed` is absent. No result archive or accepted checkpoint is claimed.

## Root cause evidence

The persisted `colab_train.log` records the first training subprocess failing before epoch one:

```text
contract check failed: Dataset '/content/Traffic_Sign_Detector/data/processed/m1_yolo/data.yaml' error
Key backend: 'module://matplotlib_inline.backend_inline' is not a valid value for backend
```

The notebook kernel supplied the inline Matplotlib backend to the separately locked detector
subprocess. That environment does not provide the notebook-only backend. This is not CUDA OOM,
bundle corruption, split mismatch, pretrained-weight mismatch or sealed-test access.

## R1 remediation

Both governed Colab runners now construct a subprocess environment that overwrites any inherited
backend with `MPLBACKEND=Agg` while retaining the telemetry-disable flags. Regression tests begin
with the exact observed inline-backend value and require the helper to return `Agg`.

The cascade runner's byte pin for the primary runner must be updated to the repaired primary-runner
SHA-256. A successor train/val bundle and a new run label are required before another smoke. The
failed state directory remains immutable evidence.

This record does not approve a rerun, upload, new bundle, training result or sealed-test access.
