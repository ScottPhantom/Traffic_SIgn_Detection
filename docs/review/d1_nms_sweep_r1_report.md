# D1 NMS IoU × confidence sweep R1 — pilot YOLO11s-54

Date: 2026-11-06. Status: validation diagnostic, independent source and result QA **PASS**. Decision under the predeclared rule: **`KEEP_0_70`**. This does not lock NMS or confidence for a final model.

## Scope and reproduction

The existing pilot `best.pt` was inferred locally on the pinned R3 validation set of 376 images, 624 annotated boxes and nine D-02 groups. Every configuration used the same Ultralytics preprocessing, image size 1280 and input confidence 0.001. Only NMS IoU and `agnostic_nms` changed. MPS completed the run; CPU fallback was not needed. The source package and 11 CSVs are pinned by SHA-256 in [the machine-readable result](generated/d1_nms_sweep_r1.json); CSVs remain Git-ignored under `results/experiments/d1_nms_sweep_r1/`.

The required 0.70/class-aware equivalence gate passed before the other ten inferences: at confidence 0.20, **547/624** signs localized, **150** FP, **457/624** correct-class hits, mAP50 **0.8521**, mAP50-95 **0.6089**. The pinned pilot prediction CSV reproduced these scores. Every one of 220 confidence cells and 11 mAP pairs, all nine leave-one-group-out folds and the paired bootstrap were independently recalculated in [result QA](d1_nms_sweep_r1_result_independent_qa_record.md). `sealed_test_accessed=false`; `thresholds_locked=false`.

## Scores at each configuration's selected confidence

All eleven configurations select confidence **0.20** on the complete validation roster under D-05's recall ≥0.85 and fewest FP/image rule. mAP is computed over each configuration's full post-NMS candidate set, independent of the selected confidence.

| NMS | IoU | Localized TP | FP | FP/image | Correct-class hits | mAP50 | mAP50-95 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Per-class | 0.45 | 547 | 135 | 0.3590 | 457 | 0.8543 | 0.6095 |
| Per-class | 0.50 | 547 | 138 | 0.3670 | 457 | 0.8539 | 0.6093 |
| Per-class | 0.55 | 547 | 140 | 0.3723 | 457 | 0.8537 | 0.6094 |
| Per-class | 0.60 | 547 | 143 | 0.3803 | 457 | 0.8535 | 0.6095 |
| Per-class | 0.65 | 547 | 146 | 0.3883 | 457 | 0.8529 | 0.6093 |
| **Per-class, current** | **0.70** | **547** | **150** | **0.3989** | **457** | **0.8521** | **0.6089** |
| Per-class | 0.75 | 547 | 155 | 0.4122 | 457 | 0.8516 | 0.6085 |
| Per-class | 0.80 | 547 | 161 | 0.4282 | 457 | 0.8509 | 0.6082 |
| Across classes | 0.80 | 547 | 109 | 0.2899 | 433 | 0.7562 | 0.5385 |
| Across classes | 0.85 | 547 | 124 | 0.3298 | 434 | 0.7568 | 0.5393 |
| Across classes | 0.90 | 547 | 166 | 0.4415 | 435 | 0.7587 | 0.5418 |

Recall that ignores class is 547/624 = **0.8766** for all selected points in this run. The across-class 0.80 setting is the numerical minimum of FP/image, but it removes **24 correct-class detections** relative to 0.70 and lowers mAP50-95 by **0.0704**. The paired nine-group, 1,000-draw CI for the change in FP/image is **[-0.1640, -0.0588]**; for the change in mAP50-95 it is **[-0.1533, -0.0354]**. All 9/9 cross-validation folds select across-class 0.80, yet the mAP CI is wholly below zero, violating the predeclared requirement that class-aware AP must not show a clear decrease. Thus **`KEEP_0_70`**.

The per-class IoU **0.45** result is a secondary diagnostic: 15 fewer FP at the same 457 correct-class hits and a similar mAP50-95. The predeclared global selection and CI only tested the overall winner against 0.70. There is no paired uncertainty or independent hold-out evidence here to promote 0.45 into an app policy. A follow-up record can test it explicitly if the Owner wants that direction.

## Figures

- [Recall and FP/image by NMS IoU](figures/d1_nms_sweep_r1_lines.svg) uses the selected confidence per per-class IoU and shows across-class variants separately.
- [FP/image heatmap](figures/d1_nms_sweep_r1_heatmap.svg) covers all 220 cells; dark borders mark cells meeting recall ≥0.85.

## Limits and next action

These are retrospective scores from **one pilot checkpoint and validation only**. The nine groups are not an external test set; the resulting policy can overfit validation. FP reduction alone is insufficient when signs are assigned the wrong class. This study does not change the model weights, Dynamic Threshold app policy, D-05 gates or sealed-test status. If a new NMS setting is proposed for the final candidate, it needs a separate prospective locking record and Owner approval before any final sealed evaluation. No training or sealed-test evaluation was performed.
