# D1 YOLO54 improvement R2 — single-change ablation contract (successor of R1)

Status: `CONTRACT_AND_TRAINER_SUCCESSOR_AWAITING_INDEPENDENT_QA` · Boundary:
`PREPARATION_ONLY_NO_TRAINING_NO_SMOKE_NO_SEALED_TEST` · Author: Claude Code, branch
`claude/centercam-yolo54-r1`, 2026-10-23.

Implementation: `detector/m1/yolo54_improvement_r2.py`; tests:
`detector/tests/test_yolo54_improvement_r2.py`.

## 0. Predecessor

R1 is `docs/review/d1_yolo54_improvement_r1_contract.md` and `detector/m1/yolo54_improvement_r1.py`,
committed as `b661b8c`. Its independent QA,
`docs/review/d1_yolo54_improvement_r1_independent_qa_record.md`, gave PASS with 0 Critical, 0 High,
2 Medium and 6 Low. None of the R1 files is edited. R1 never trained. R2 supersedes R1 for every
future run, and R1 must not be used to train.

## 1. Changes by R1 QA finding

| Finding | R2 change |
| --- | --- |
| **M1** `--fraction`, `--workers` and `--device` bypassed the pilot-equivalence guard | `execute` refuses any `imgsz`, `batch`, `seed`, `workers` or `fraction` different from the pilot (`PINNED_RUNTIME`: 1280 / 4 / 20261018 / **4** / **1.0**) before training starts. The CLI defaults equal the pilot. `fraction`, `workers` and `device` are also forbidden as ablation overrides. `device` stays a runtime knob: it selects the accelerator and is already recorded in the recovery binding (`device`), so a resume on a different device string is refused by the checkpoint store. |
| **M2** The A3 mechanism was mis-grounded | `best.pt` is already the fitness-best epoch 20, so late overfit cannot affect the evaluated model. A3 is restated as **learning rate near the peak**: at epoch 20 the pilot's linear schedule is still at ≈ 0.80 × lr0, while a 40-epoch cosine schedule is at ≈ 0.50 × lr0 (both with `lrf 0.01`, tested). Its success criterion is now an explicit **non-inferiority at ~40 % of the cost** test, and a pass is reported as a cost result, not an accuracy gain. |
| **L1** A4 implicitly changed `warmup_bias_lr` and momentum/beta1 | `warmup_bias_lr` joins the optimizer category, and A4 pins it at the pilot's effective **0.0**, where explicit SGD would otherwise use 0.1. The change from AdamW beta1 0.9 to SGD momentum 0.937 is disclosed as part of the optimizer change. |
| **L2** `plan` was not the exact settings | `plan` calls the real `resumable_train.train_arguments` with the pilot runtime values. Only `data`, `name` and `device` are listed in `runtime_placeholders`, because they are bound at train time. A test checks that the key set equals the real trainer's keys plus the overrides. |
| **L3** Evidence wording | A5 now says small size explains a **minority** of class-7 misses (19 of 45 are 11–17 px) and most class-41 misses. A6 labels its 17/36 dark/backlit figure as an **R10** basis that has not been recounted on R3. The evaluator successor recounts it. |
| **L4** No noise margin; conf point not stated | Every success criterion is labelled **screening** at **conf 0.20** (`success_kind`, `screening_conf`). Promotion additionally requires the group-bootstrap 95 % CI of the delta (see §4). |
| **L5** Test gaps | New tests cover: <ul><li>`workers` and `fraction` refusal, including through the CLI;</li><li>a real `CheckpointStore.load_latest` refusal of an A5 pointer under the A6 binding;</li><li>R1 and R2 bindings differing for identical overrides;</li><li>refusal of nested runs;</li><li>no `ultralytics`, `torch`, `cv2` or `PIL` import during `plan`.</li></ul> |
| **L6** Write scope | Corrected in §2. |
| Info: process-global patch, not reentrant | A nested `execute` in the same process is refused, and the patch is restored in `finally`. |
| Info: Ultralytics restores checkpoint args on resume | Unchanged and acceptable. The recovery binding refuses a resume whose settings differ, so the restored args equal the bound ones. |

## 2. Scope, ownership and write scope

The scope is unchanged from R1 §1. No training, smoke or inference is started. No Codex-owned file
is edited. The L4 queue is Cascade B0 → VGG16 E2 → YOLO54 smoke/resume → YOLO54 long training,
after QA PASS.

A future, Owner-authorised `train` call writes only to:

- the Drive checkpoint folder `M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1/<ablation>/`.
  This is the Owner-named root. R1 never wrote there, and the `ablation.package` field of the
  binding keeps R1 and R2 checkpoints apart;
- a **new** run directory `results/experiments/<governed run name>/` in the runtime's repository
  checkout, created by `m1.resumable_train`, which refuses an existing one. It is never the pilot run
  directory.

It never overwrites the pilot `best.pt`, the baseline predictions, the pinned validation results,
the thresholds or any manifest or QA record.

## 3. Baseline and ablations

The baseline and the evidence table are as in R1 §2: D1-VRE-R2 on the R3 labels, with 624 GT.

- mAP50 0.884, mAP50-95 0.626, AP-small 0.289.
- Recall @0.20 0.877, FP/image 0.399.
- Class recall: class 7 0.595, class 32 0.621, class 41 0.462.

The pilot's `args.yaml` gives: `optimizer auto` → AdamW, lr0 0.000172, `warmup_bias_lr 0.0`,
`hsv_v 0.4`, `multi_scale 0.0`, `cos_lr false`, `workers 4`, `fraction 1.0`.

| ID | Category | Change from pilot | Hypothesis | Screening criterion on R3 val, conf 0.20 | L4 |
| --- | --- | --- | --- | --- | ---: |
| A3_schedule_40e_cos | schedule | `epochs 40`, `cos_lr True` | Lower LR near the epoch-20 peak (≈ 0.5 vs 0.8 × lr0) reaches the same quality sooner | **Non-inferiority:** mAP50-95 ≥ 0.616 (pilot − 0.01), FP/img ≤ 0.419 (pilot + 0.02), recall ≥ 0.85 | 1.6 h |
| A4_optimizer_sgd | optimizer | `optimizer SGD`, `lr0 0.01`, `momentum 0.937`, `warmup_bias_lr 0.0` (pinned at the pilot value) | Explicit SGD generalises better than auto-AdamW | FP/img − 0.05 with recall ≥ 0.85, mAP50 within − 0.01 | 3.8 h |
| A5_multi_scale | multi_scale | `multi_scale 0.25` (~960–1600 px) | Small signs: AP-small 0.289, most class-41 misses, a minority of class-7 misses | AP-small + 0.03, recall of classes 7 and 41 each + 0.05 | 4.5 h, smoke first |
| A6_photometric_value | photometric | `hsv_v 0.4 → 0.6` | Dark/backlit class-7 misses (17/36 on **R10**; not recounted on R3) | Class-7 recall + 0.05, FP/img not + 0.03 | 3.8 h |

The rules enforced by `validate` and `execute`, and tested, are the R1 rules plus the following:

- `fraction`, `workers` and `device` are forbidden as overrides.
- `workers` and `fraction` must equal the pilot at `train` time.
- A nested run is refused.

The deferred items are as in R1 §3: imbalance sampling/loss, higher resolution, class-wise
thresholds and hard-negative mining.

## 4. Data, evaluation and promotion rules

**Data and evaluation.** As in R1 §4.

- Train only on the pilot's WP36-R1 train split, with the WP35 train-only enrichment.
- No validation or sealed-test pixels, crops, predictions or labels in training.
- The 13 classes without validation support never drive selection.
- Compare only through **one** evaluator: a registered successor of D1-VRE-R2 that accepts ablation
  weights. It is not built here, because the shared evaluators are Codex-locked.

**Screening versus promotion.**

- **Screening.** The criteria above are screening criteria only. Each has a single seed and a point
  estimate at conf 0.20.
- **Promotion.** An ablation can be proposed for promotion only if all three hold:
  1. it meets its screening criterion;
  2. the group-bootstrap 95 % CI of the delta against the pilot, computed by the same evaluator,
     excludes the wrong side. For A3, this means the lower bound of ΔmAP50-95 is above −0.01 and
     the upper bound of ΔFP/img is below +0.02. For A4–A6, the CI of the targeted delta excludes 0;
  3. every single-seed validation check passes.
- **Out of scope.** Three-seed runs need a separate contract. Seeds 20261019/20261020 stay NO-GO
  under the unchanged pilot configuration. D-05, the thresholds and the sealed test are untouched.
  No claim may be made from training metrics.

## 5. Next steps

1. Independent QA of this contract, the R2 module and its tests.
2. Once L4 is free, after Cascade B0 and VGG16 E2:
   - a 1-epoch fresh smoke plus a resume smoke per chosen ablation, after source/package QA;
   - then the long run.
3. Follow-up packages, not part of R2:
   - the Colab notebook and runner wiring, bundle pins and runtime digest;
   - the evaluator successor.
