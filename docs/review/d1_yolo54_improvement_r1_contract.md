# D1 YOLO54 improvement R1 — single-change ablation contract

Status: `CONTRACT_AND_TRAINER_SUCCESSOR_AWAITING_INDEPENDENT_QA` · Boundary:
`PREPARATION_ONLY_NO_TRAINING_NO_SMOKE_NO_SEALED_TEST` · Author: Claude Code, branch
`claude/centercam-yolo54-r1`, 2026-10-23.

Implementation: `detector/m1/yolo54_improvement_r1.py`; tests:
`detector/tests/test_yolo54_improvement_r1.py`.

## 1. Scope and ownership

The Owner/Codex split of 2026-10-23 makes Claude responsible for preparing a YOLO54 improvement
successor. Codex owns Cascade B0, VGG16 E2, the shared evaluators, canonical status docs and the L4
runtime. This package therefore:

- starts **no** training, smoke or inference. The L4 queue is Cascade B0 → VGG16 E2 → YOLO54 smoke
  → YOLO54 long training;
- edits no Codex-owned file. It wraps `m1.resumable_train` without modifying it;
- writes only to a new Drive run root
  `M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1/<ablation>/`;
- never overwrites the pilot `best.pt`, the baseline predictions, the pinned validation results,
  the thresholds or any QA record.

## 2. Baseline and evidence

The baseline is the registered pilot
`D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2`: YOLO11s COCO
pretrained `85a76fe8…`, 54 classes, 1280 px, batch 4, 100 epochs, patience 0, seed 20261018,
`fliplr=0`. It was trained with the pilot's M1 export and Colab bundle.

Current validation reference: D1-VRE-R2 on the owner-accepted R3 labels (624 GT), result QA PASS
`95db91cb…`.

| Metric | Value | D-05 reference |
| --- | --- | --- |
| mAP50 | 0.884 | |
| mAP50-95 | 0.626 | |
| AP-small | 0.289 | |
| Recall @0.20 | 0.877 | |
| FP/image | **0.399** | ≤ 0.30 |
| Class 7 recall | **0.595** | ≥ 0.70 |
| Class 32 recall | **0.621** | ≥ 0.70 |
| Class 41 recall | **0.462** | ≥ 0.70 |

Evidence each hypothesis draws on:

- val mAP50-95 peaks at epoch 20 and then declines;
- 19 of 45 class-7 misses are 11–17 px;
- 17 of 36 R10 class-7 misses are dark or backlit;
- the class-41 misses are small, distant signs, with speed values misread as 39/40.

## 3. Ablations (one category each)

| ID | Category | Change from pilot | Hypothesis | Success on R3 val | L4 estimate |
| --- | --- | --- | --- | --- | ---: |
| A3_schedule_40e_cos | schedule | `epochs 40`, `cos_lr True` | late overfit after epoch 20 | mAP50-95 ≥ 0.626 and FP/img ≤ 0.399 at recall ≥ 0.85 | 1.6 h |
| A4_optimizer_sgd | optimizer | `optimizer SGD`, `lr0 0.01`, `momentum 0.937` (the pilot's `auto` resolved to AdamW, lr0 0.000172) | explicit SGD recipe generalises better than the auto AdamW | FP/img −0.05 with recall ≥ 0.85, mAP50 within −0.01 | 3.8 h |
| A5_multi_scale | multi_scale | `multi_scale 0.25` (a float in Ultralytics 8.4: ~960–1600 px; `True` would mean up to 2560 px) | small signs (AP-small 0.289) | AP-small +0.03, recall of classes 7 and 41 each +0.05 | 4.5 h, smoke first for memory |
| A6_photometric_value | photometric | `hsv_v 0.4 → 0.6` | dark/backlit class-7 misses | class-7 recall +0.05, FP/img not +0.03 | 3.8 h |

Rules enforced by `validate` and `execute`, and tested:

- **Single category.** Each ablation's keys must all belong to one whitelisted category. Mixing
  categories is refused, so every effect stays attributable.
- **Forbidden keys.** These can never be set: `data`, `split`, `val`, `classes`, `single_cls`,
  `fliplr`, `flipud`, `imgsz`, `batch`, `seed`, `resume`, `project`, `name`, `pretrained` and
  `fraction`. `fliplr=0` is re-applied last, whatever the ablation sets.
- **Pilot values.** imgsz 1280, batch 4 and seed 20261018 must equal the pilot. Epochs may only be
  reduced (≤ 100). Patience stays 0.
- **Recovery binding.** The overrides and the ablation key enter the checkpoint recovery binding, so
  a checkpoint cannot be resumed under a different ablation. The checkpoint directory must be the
  ablation's own folder.
- **Dry run.** `python -m m1.yolo54_improvement_r1 plan <ID>` prints the exact settings without
  importing Ultralytics or reading data.

Not proposed in R1, because each needs its own data contract or QA:

- **Imbalance sampling or loss** for classes 7/32/41: train-only repeat-factor lists need a new data
  delta and its own export verification.
- **Higher resolution**: needs a new L4 capacity check.
- **Class-wise thresholds**: a validation post-processing contract, which also needs the Owner's
  reading of D-05 Q4.
- **Hard-negative mining**: needs a review of train-label completeness first.

## 4. Data and evaluation rules

- **Training data.** Only the pilot's WP36-R1 train split, with WP35 train-only enrichment. No
  validation or sealed-test pixels, crops, predictions or labels may be used for training,
  augmentation or mining. The 13 classes without validation support never drive selection.
- **Checkpoint selection.** Each run keeps Ultralytics' `best.pt` on the same export as the
  pilot, so that the only difference is the ablation.
- **Final comparison.**
  - It runs on the R3 labels (624 GT), using the **same** evaluator protocol as D1-VRE-R2: MPS,
    1280 px, NMS 0.70, IoU 0.5, conf 0.20 plus the D-05 Q4 candidate, and the group bootstrap.
  - D1-VRE-R2 pins the pilot weights, so a new **evaluator successor** that accepts registered
    ablation weights is required. That evaluator is not built here, because the shared
    evaluators are Codex-locked during Cascade readiness.
  - Never compare models through two different evaluators.
- **No train-metric claims.** No improvement may be claimed from training metrics.
- **No other changes.** D-05, the thresholds and the sealed test are untouched.

## 5. Promotion and next steps

1. Independent QA of this contract, the trainer successor and its tests.
2. Once L4 is free, after Cascade B0 and VGG16 E2:
   - a 1-epoch fresh smoke plus a resume smoke per chosen ablation, on its own Drive folder and
     runtime digest, with source/package QA first;
   - then the long run.
3. The Colab notebook and runner wiring, bundle pins and runtime-digest retry history follow the
   QA-passed pilot runner pattern. They are a follow-up package, not part of R1.
4. An ablation is promoted to the next pilot only if it meets its success criterion **and** every
   single-seed validation check. Three-seed runs need a separate contract. Seeds
   20261019/20261020 stay NO-GO with the unchanged pilot configuration.
