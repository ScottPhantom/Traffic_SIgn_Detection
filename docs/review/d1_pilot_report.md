# D1 YOLO11s pilot report — seed 20261018

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: `AWAITING_INDEPENDENT_QA`  
Interim decision: **NO-GO for seeds 20261019 and 20261020 with the unchanged pilot configuration**

## Scope and evidence boundary

This is a single-seed validation report for the 54-class YOLO11s D1 detector. It is not a D-05
final verdict, because D-05 requires exactly three seeds and one sealed-test evaluation. The sealed
test was not exported, opened, or evaluated. All reviewed training and evaluation evidence records
`sealed_test_accessed=false`.

The model accepts a full-scene image and emits bounding boxes plus one of the 54 governed classes
in a single detector. Any future vehicle behavior remains simulation only.

## Bound artifacts

| Artifact | SHA-256 |
| --- | --- |
| `best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `last.pt` | `75ada6ba44804252c65e6ec76660511e0cc6ea69ee164c766055033dac11ea25` |
| `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| run attestation | `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` |
| committed run registry | `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9` |
| `eval_val.json` | `e6fe9eb58e4d06e3815d94be477f5b450625042c25b08995c1217ffd26dc8895` |
| `latency_mps.json` | `54a4d268890013f90140529b3ea31c21462d38f38e8596e98ca7e7510a8af01a` |

The completed Colab package and its live R5 verification passed independent QA before the run was
registered. The memory-bounded validation repair also passed independent source QA before this
report was produced.

## Training result

- architecture: YOLO11s, 54 output classes;
- pretrained source: Owner-approved Ultralytics `yolo11s.pt`;
- seed: `20261018`;
- epochs: 100/100;
- image size: 1280;
- batch: 4;
- device: NVIDIA L4;
- horizontal flip: disabled (`fliplr=0.0`);
- terminal state: `SUCCEEDED`, `COMPLETED_FROM_FINAL_CHECKPOINT`;
- checkpoint: `epoch-0100`;
- retry history: 6 attempts, 4 failed resumes, 5 distinct runtime digests;
- Ultralytics accumulated training time at epoch 100: 14,786.4 seconds, approximately 4 h 6 min.

The accumulated training time is read from `results.csv`; it is not presented as total elapsed
wall time across Colab disconnects, Drive checkpoint copying, and operator recovery.

## Validation metrics

Validation contains 376 images and 560 labelled boxes. Metrics below are measured, not estimates.

| Metric | Measured | D-05 reference | Pilot result |
| --- | ---: | ---: | --- |
| mAP50 | 0.8292 | >= 0.60 | PASS |
| mAP50-95 | 0.5888 | >= 0.40 | PASS |
| AP-small | 0.2819 | no standalone gate | diagnostic only |
| class-agnostic recall | 0.8571 | >= 0.85 | PASS |
| false positives/image | 0.5505 | <= 0.30 | **FAIL** |
| M1 Pro MPS latency p95 | 47.30 ms | <= 100 ms | PASS |

AP-small uses 213 small-object boxes across 13 supported classes and the project's class-aware
101-point AP method over IoU 0.50:0.95.

### Validation-selected operating point

With NMS IoU fixed by the evaluation command at `0.70`, the selector chose
`confidence=0.15`: the confidence candidate satisfying class-agnostic recall >= 0.85 with the
smallest measured FP/image on its validation grid. This pilot invocation did not search NMS IoU;
therefore `0.70` is not claimed as a validation-selected NMS value. Joint confidence/NMS selection
remains a separate prerequisite before a final three-seed threshold lock can be created.

- true positives: 480/560;
- false positives: 207;
- precision: 0.6987;
- class-agnostic recall: 0.8571;
- FP/image: 0.5505;
- 95% group-bootstrap CI for recall: `[0.7513, 0.9615]`;
- 95% group-bootstrap CI for FP/image: `[0.2499, 1.0820]`.

This confidence value is pilot evidence only. It is not the final committed threshold lock, which
cannot be created until all three governed seed validation reports exist.

### Resolution breakdown

| Resolution | Images | GT boxes | TP | FP | Recall | FP/image |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 960x540 | 337 | 531 | 473 | 170 | 0.8908 | 0.5045 |
| 540x960 | 39 | 29 | 7 | 37 | 0.2414 | 0.9487 |

The vertical 540x960 subset is a confirmed blocker: recall is 0.2414 and FP/image is 0.9487. The
validation set contains no 1920x1080 sample, so behavior at that resolution remains unverified.

### Per-class recall and support at confidence 0.15

Only classes with validation support are listed. A class gate applies only when support is at
least 20 boxes.

| Class key | Support | Hits | Recall | Critical | Gate status |
| --- | ---: | ---: | ---: | --- | --- |
| 0 | 13 | 13 | 1.0000 | yes | low support |
| 2 | 5 | 5 | 1.0000 | yes | low support |
| 3 | 5 | 5 | 1.0000 | no | low support |
| 4 | 12 | 8 | 0.6667 | no | low support |
| 5 | 14 | 13 | 0.9286 | no | low support |
| 6 | 22 | 21 | 0.9545 | no | PASS |
| 7 | 111 | 71 | 0.6396 | yes | **FAIL** |
| 8 | 51 | 34 | 0.6667 | no | PASS |
| 10 | 21 | 21 | 1.0000 | no | PASS |
| 12 | 57 | 35 | 0.6140 | no | PASS |
| 13 | 17 | 17 | 1.0000 | yes | low support |
| 14 | 3 | 0 | 0.0000 | no | low support |
| 23 | 16 | 16 | 1.0000 | no | low support |
| 26 | 14 | 8 | 0.5714 | no | low support |
| 32 | 29 | 19 | 0.6552 | yes | **FAIL** |
| 34 | 37 | 31 | 0.8378 | no | PASS |
| 39 | 8 | 7 | 0.8750 | yes | low support |
| 41 | 21 | 12 | 0.5714 | yes | **FAIL** |
| 46 | 104 | 56 | 0.5385 | no | PASS |

The validation artifact reports no support for 35 class keys:
`1`, `9`, `11`, `15`, `16:2.0`, `16:2.2`, `16:2.5`, `17`, `18`, `19`, `20`, `21`, `22`,
`24`, `25`, `27`, `28`, `29`, `30`, `33`, `35`, `36`, `37`, `38`, `40`, `42`, `43:2.5`,
`43:2.7`, `44`, `45`, `47`, `48`, `49`, `50`, and `51`. These classes were not used to select
the model or claim a class gate. The 35 keys reconcile exactly with the governed coverage split:
13 classes have test support but no validation support, while the already documented 22
train-only classes have neither validation nor test support. This is an existing governance
limitation, not a newly discovered coverage discrepancy.

### Error evidence

The report identifies representative validation stems:

- missed sign: `0009`, `0022`, `0279`-`0296` (first 20 retained by the report);
- wrong class: `0002`, `0004`-`0007`, `0010`, `0012`-`0017`, `0019`-`0021`, `0023`-`0027`;
- false or wrong box: `0003`, `0004`, `0019`, `0024`, `0030`, `0041`, `0044`, `0046`-`0048`,
  `0053`, `0055`, `0056`, `0065`, `0068`, `0070`, `0071`, `0293`, `0313`, `0314`.

Ten annotated unknown boxes were available for the diagnostic unknown-overlap check; six were
recognized as a known class, a 0.60 false-recognition rate. This is not an OOD guarantee.

## Latency

Latency was measured on Apple M1 Pro/MPS at image size 1280, batch 1, confidence 0.15 and NMS IoU
0.70, using 50 warm-up iterations and 300 measured iterations:

- mean: 45.30 ms;
- p50: 44.45 ms;
- p95: 47.30 ms;
- maximum: 207.66 ms.

The p95 gate passes. The latency artifact records checkout commit
`0f5ddb174beba8678430cf2329d124fde6cfa2b8` and 54 dirty/untracked paths because the authoritative
user worktree contains unrelated changes plus the extracted run. The validation artifact does not
contain an execution-environment/source-checkout receipt or the candidate confidence-grid curve;
its bound model and artifact hashes are the available validation reproducibility boundary. This
limitation and the latency dirty-count must remain visible.

## Pilot decision

The single-seed pilot passes mAP, overall recall, and latency references, but fails the validation
FP/image reference and all three supported critical-class gates (`7`, `32`, `41`). It also performs
poorly on vertical images, and NMS IoU has not yet been selected on validation.

Therefore the unchanged configuration is **NO-GO** for starting seeds `20261019` and `20261020`.
Running two more expensive seeds would not resolve the demonstrated data/operating-point blockers
by itself.

Permitted next actions after independent QA of this report are limited to preparing an Owner
decision package with validation-only evidence. The package should choose between:

1. keep D-05 unchanged and remediate vertical-image/generalization, critical classes and false
   positives before retraining;
2. propose the already-scoped one-stage detector plus classifier cascade, subject to its separate
   Owner decision and QA gates;
3. propose a one-time D-05 gate adjustment using validation evidence only.

No option is approved by this report. The sealed test remains closed.

