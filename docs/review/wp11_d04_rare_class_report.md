# M0-WP11 D-04 rare-class decision-support report

Status: `M0_WP11_AWAITING_QA_D04_DECISION_SUPPORT_ONLY`  
Boundary: `D04_DECISION_SUPPORT_ONLY_NO_OWNER_APPROVAL_NO_SEMANTIC_MERGE_NO_RAW_MUTATION_NO_SPLIT_NO_TRAINING`

## Decision boundary

This package uses the current D-04 scope `box_count < 50`, which contains exactly 20 classes. It is
different from the WP8 analysis flag `image_count < 100` (29 classes). Neither rule authorizes a
semantic merge. All owner decisions remain `PENDING`; D-03 remains `PENDING`; Gate 0 remains
`BLOCKED`; `training_authorized=false`.

Raw train/test counts are descriptive source metadata only. They are not independent evaluation
evidence. Effective independent support is `UNKNOWN_PENDING_D02` because physical-sign/scene group
truth and a group-aware split do not yet exist. Adjacent or proxy sequences are not group truth.

## Recommendation rule

- `box_count <= 20`: `COLLECT_MORE` and quarantine the class from model-comparison claims pending
  independent-group data.
- `21 <= box_count < 50`: `OWNER_REVIEW_REQUIRED` before any model-comparison inclusion.
- Outside D-04 scope: `KEEP_NATIVE_PENDING_D03`.
- No automatic merge, relabel, split, training or taxonomy approval is permitted.

Across all 52 rows: 5 `COLLECT_MORE`, 15
`OWNER_REVIEW_REQUIRED`, and 32 `KEEP_NATIVE_PENDING_D03`.

## D-04 decision-focused subset

| Class | Code | Images | Boxes | Eligible images | Eligible boxes | Recommendation | Owner |
| ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| 1 | W.205c | 22 | 22 | 22 | 22 | OWNER_REVIEW_REQUIRED | PENDING |
| 4 | W.205a | 33 | 33 | 33 | 33 | OWNER_REVIEW_REQUIRED | PENDING |
| 9 | R.303 | 43 | 43 | 43 | 43 | OWNER_REVIEW_REQUIRED | PENDING |
| 11 | I.409 | 26 | 26 | 26 | 26 | OWNER_REVIEW_REQUIRED | PENDING |
| 15 | W.203c | 29 | 29 | 29 | 29 | OWNER_REVIEW_REQUIRED | PENDING |
| 19 | P.124d | 29 | 29 | 29 | 29 | OWNER_REVIEW_REQUIRED | PENDING |
| 21 | W.203b | 11 | 11 | 11 | 11 | COLLECT_MORE | PENDING |
| 25 | S.505a*Xe máy | 25 | 25 | 25 | 25 | OWNER_REVIEW_REQUIRED | PENDING |
| 27 | W.225 | 36 | 36 | 36 | 36 | OWNER_REVIEW_REQUIRED | PENDING |
| 28 | S.505a*Xe tải và công | 27 | 27 | 27 | 27 | OWNER_REVIEW_REQUIRED | PENDING |
| 29 | P.104 | 45 | 45 | 45 | 45 | OWNER_REVIEW_REQUIRED | PENDING |
| 31 | Camera | 38 | 38 | 38 | 38 | OWNER_REVIEW_REQUIRED | PENDING |
| 33 | W.202b | 19 | 19 | 19 | 19 | COLLECT_MORE | PENDING |
| 37 | W.205b | 47 | 47 | 47 | 47 | OWNER_REVIEW_REQUIRED | PENDING |
| 42 | R.301e | 21 | 21 | 21 | 21 | OWNER_REVIEW_REQUIRED | PENDING |
| 43 | W.239b* | 27 | 27 | 27 | 27 | OWNER_REVIEW_REQUIRED | PENDING |
| 44 | W.233 | 3 | 3 | 3 | 3 | COLLECT_MORE | PENDING |
| 47 | P.124b1 | 16 | 16 | 16 | 16 | COLLECT_MORE | PENDING |
| 48 | W.210 | 41 | 41 | 41 | 41 | OWNER_REVIEW_REQUIRED | PENDING |
| 51 | W.246c | 5 | 5 | 5 | 5 | COLLECT_MORE | PENDING |

## Extreme-support evidence

- Class 44: 3 complete instances rendered in `docs/review/assets/wp11/d04_extreme_atlas/class_044.png`.
- Class 51: 5 complete instances rendered in `docs/review/assets/wp11/d04_extreme_atlas/class_051.png`.

Class 44 (`W.233`) has exactly 3 images/3 boxes; class 51 (`W.246c`) has exactly 5 images/5 boxes.
Every available instance is hash-bound, its exact label line and pixel bbox are recorded, and every
instance was rendered in the two-page atlas. Because D-02 is unresolved, these counts do not imply
3 or 5 independent physical signs.

## G0.4 quarantine effect

The WP10 registry excludes entire stem `0248` from split/training eligibility. Class 49 changes from
120 images/221 boxes to 119 eligible images/219 eligible boxes. The WP9 derived clip is not counted
as a training sample. Class 49 and its taxonomy remain present and `UNAPPROVED`; only sample 0248 is
quarantined. No other class count changes.

## Owner action

Review the 20 D-04 rows independently. `COLLECT_MORE` and `OWNER_REVIEW_REQUIRED` are PM proposals,
not approvals. D-04 remains `PENDING_OWNER_DECISION`; WP11 must pass QA before presentation to the
owner. This package does not approve D-04, D-03, D-02, a final split, training, or experiments.
