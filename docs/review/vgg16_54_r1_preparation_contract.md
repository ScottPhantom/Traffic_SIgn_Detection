# VGG16-54 R1 — preparation and execution contract

Status: `IMPLEMENTED_SOURCE_CANDIDATE_AWAITING_OWNER_CONFIG_APPROVAL_AND_INDEPENDENT_QA`

Date: `2026-10-24` (`Asia/Ho_Chi_Minh`)

Boundary: `PREPARATION_ONLY_NO_GPU_RUN_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Objective

Prepare the first VGG16-family 54-class crop classifier that can replace the CompactCNN stage in
the already measured one-class-YOLO cascade. The existing one-class detector remains unchanged;
this package trains only the classifier and therefore reuses the detector foundation without
claiming that YOLO weights can be transferred into VGG16.

This R1 candidate is **not** the roadmap E2 ImageNet-transfer experiment. It uses
`weights=None`, performs no download and is named `vgg16_crop54_scratch`. A later transfer-learning
successor requires explicit Owner authorization to download/pin official ImageNet VGG16 weights.

## Verified inputs reused

- Cascade B0 bundle archive SHA-256:
  `5a5a9afbf06b9bc2f55546f5a49738ed9ca9ac6f96a78931f78669e71dab4806`.
- Bundle manifest SHA-256:
  `bae147b6f7c6f80ac973923df4b60fd31b6587221fe75eaa2d9ed4b93ee6a51b`.
- Training: `12,621` 32×32 RGB crops across all 54 classes.
- Validation: `624` R3 ground-truth crops from 376 corrected frames. This is the same validation
  crop material used for Cascade B0, so the new classifier can be compared with CompactCNN under
  the same protocol.
- Sealed test is absent from the bundle and inaccessible from the runner.

## Proposed configuration — not yet Owner-approved

| Field | Proposal |
| --- | --- |
| Architecture | VGG16 convolutional feature stack + global average pooling + dropout + 54-way linear head |
| Initialization | scratch (`weights=None`) |
| Input | RGB `32×32` governed crops |
| Seed | `20261018` |
| Epochs | maximum `100`; never stop before epoch 30; early-stop after 15 consecutive epochs without a better validation selection score |
| Batch / workers | `256` / `2` |
| Optimizer | AdamW, lr `1e-4`, weight decay `1e-4` |
| AMP | enabled on CUDA L4 |
| Augmentation | no horizontal flip; no geometric transform |
| Selection | supported-class macro-F1, then lower validation loss |
| Test | unavailable; `sealed_test_accessed=false` |

The 100-epoch value is a ceiling, not a claim that later epochs must be better. The runner always
keeps `best.pt` by validation supported-class macro-F1 (validation loss is the tie-break) and may
stop after the original 30-epoch baseline window when 15 epochs pass without improvement. This
gives scratch VGG16 more optimization time while bounding overfitting and wasted L4 time.

The smaller crop-specific head keeps the VGG16 feature stack while avoiding the roughly 100M
parameters in the original 4096-unit ImageNet fully connected head. This is a proposal for a
resource-appropriate baseline, not a claim of improved accuracy before measurement.

## Recovery and evidence

- New isolated Drive state:
  `M1_D1_Colab/runs/vgg16_54_seed_20261018_r1`.
- `EfficientCheckpointStore` keeps two verified recovery generations and a chained
  `checkpoint_io.jsonl` ledger.
- Each recovery payload contains model, optimizer, AMP scaler, Python/NumPy/Torch/CUDA RNG,
  selection state and history.
- Text log, SQLite log, `colab_execution.json`, archive and result manifest preserve
  `sealed_test_accessed=false`.
- GPU train/validation time and checkpoint I/O time are recorded separately.
- Resume verifies the complete chained checkpoint-I/O ledger before copying or loading any
  recovery bytes, so a tampered ledger fails before GPU training.

## Mandatory gates before long training

1. Owner approves the exact proposed JSON configuration (or requests an R2 configuration).
2. Independent source QA passes both this package and `checkpoint_store_r2`.
3. A launch notebook is generated with a pushed immutable commit and exact proof/hash anchors.
4. Fresh L4 smoke completes epoch 1 and creates a verified Drive checkpoint.
5. A genuinely different L4 runtime resumes at epoch 2 without restarting.
6. Independent artifact QA issues PASS for the two-runtime smoke.
7. Only then may the runner resume toward the 100-epoch ceiling, subject to the locked early-stop
   rule.

The active D1-A3-R2 YOLO54 run is not modified or interrupted. No validation comparison may be
published until the VGG16 result is complete and receives independent result QA.

For the two-runtime smoke, the resume command fails closed unless the restored checkpoint reports
exactly `completed_epoch=1`; it may not accept epoch 2 or later and silently cross the governed
smoke boundary.
