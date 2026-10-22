# D1-VLA-R1 — validation label-completeness audit

Status: `D1_VLA_R1_AWAITING_INDEPENDENT_QA`
Boundary: `VALIDATION_LABEL_AUDIT_PROPOSAL_ONLY_NO_RELABEL_NO_GATE_CHANGE_NO_TRAINING_NO_SEALED_TEST`

Audits the D1-EA-R1 background false positives (manifest `d87f090e…`) at conf 0.20.
Proposal only: it does not relabel validation, change any gate or the R10 result, or
authorize training. Validation remains diagnosis-only; the sealed test stays closed.

## Strata of the 214 background false positives

| Stratum | Count |
| --- | ---: |
| `INSIDE_LABELLED_BOX` | 10 |
| `NO_LABEL_NEARBY_IOU_LT_0_1` | 138 |
| `OVERLAPS_LABELLED_IOU_GE_0_5` | 66 |

Only `NO_LABEL_NEARBY_IOU_LT_0_1` candidates can be missing labels; the others are H1 duplicates or H3
box-extent issues and are not reviewed here.

## Visual-review decisions (138 candidates)

| Decision | Count |
| --- | ---: |
| `NOT_A_SIGN` | 7 |
| `OUT_OF_TAXONOMY_LABELLED_UNKNOWN` | 4 |
| `OUT_OF_TAXONOMY_UNLABELLED` | 9 |
| `UNCLEAR` | 2 |
| `UNLABELLED_IN_TAXONOMY` | 116 |

112 unique in-taxonomy unlabelled signs after merging 4 same-sign duplicates.

| Proposed class | Confidence | Unique boxes |
| --- | --- | ---: |
| 10 | MEDIUM | 44 |
| 23 | MEDIUM | 29 |
| 12 | HIGH | 7 |
| 0 | LOW | 6 |
| 39 | MEDIUM | 5 |
| 23 | HIGH | 4 |
| 41 | MEDIUM | 4 |
| 10 | HIGH | 2 |
| 14 | MEDIUM | 2 |
| 2 | HIGH | 2 |
| 2 | LOW | 2 |
| 39 | HIGH | 2 |
| 12 | MEDIUM | 1 |
| 3 | HIGH | 1 |
| 41 | HIGH | 1 |

`docs/review/generated/d1_vla_r1_proposed_val_labels.csv` lists the 104 HIGH/MEDIUM boxes as YOLO-normalized proposals.

## Diagnostic what-if (not a result, not a gate)

| Ground truth | Added boxes | FP | FP/image | Agnostic recall | Precision |
| --- | ---: | ---: | ---: | ---: | ---: |
| R10 labels | 0 | 214 | 0.569 | 0.8625 | 0.6930 |
| + HIGH/MEDIUM proposals | 104 | 110 | 0.293 | 0.8840 | 0.8422 |
| + all proposals incl. LOW | 112 | 102 | 0.271 | 0.8854 | 0.8537 |

Recall changes because added labels are new ground truth that the model must also match.
These numbers show how much of FP/image is label incompleteness. They must not replace R10
or be used for gating until the owner approves a derived validation relabel and it passes QA.

## Limits

- Only signs the model detected are audited; unlabelled signs the model missed are not found.
- Proposed boxes are the model's boxes, not hand-drawn; a relabel must redraw them.
- Classes 10/23/39/41 on the 1208–1229 and 1342–1357 poles are read partly by consistency
  with sharper frames of the same pole (MEDIUM); the 3.5t truck disc needs its QCVN variant.
- Review pages: `docs/review/assets/d1_vla_r1/` (git-ignored, DATASET01 pixels).
