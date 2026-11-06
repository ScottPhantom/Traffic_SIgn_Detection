# D1 two-seed provisional threshold R1 — validation R3

Status: `PROVISIONAL_TWO_SEED_NOT_A_LOCK`. Date: 2026-11-06 (Asia/Ho_Chi_Minh).
This is a validation-only description of the YOLO11s-54 pilot configuration at
seeds 20261018 and 20261019. The governed R3 roster has 376 images, 624 ground
truth boxes and nine D-02 groups. `sealed_test_accessed=false`;
`thresholds_locked=false`.

## Direct answer

The **provisional two-seed setting is confidence 0.19, class-aware NMS IoU
0.70**. At that setting, mean class-agnostic recall is **0.85497** and mean
false positives per image is **0.38032**. Seed 20261018 reaches recall 0.88942
and FP/image 0.41223; seed 20261019 reaches recall 0.82051 and FP/image
0.34840. Thus the mean clears the 0.85 recall marker, but seed 19 alone does
not, and the selected setting does not clear the 0.30 FP/image marker.

There **is** an unrestricted grid cell that reaches both mean markers:
confidence 0.19, across-class NMS IoU 0.80 gives mean recall 0.85497 and
FP/image 0.24734. It is **not adopted**: the paired mAP50–95 difference versus
class-aware 0.70 has 95% interval **[-0.13119, -0.03448]**, wholly below zero.
The frozen change rule requires the mAP interval not to lie wholly below zero.
Its FP/image interval is [-0.20055, -0.08253] and the nine leave-one-group-out
folds vote 9/9 for that NMS configuration, but all three conditions must hold.

The previous one-seed pilot diagnostic used confidence 0.20, class-aware NMS
0.70: recall 0.87660, FP/image 0.39894. Its **two-seed** mean at the same
setting is recall 0.84455, FP/image 0.36835, so it no longer reaches the
mean-recall eligibility marker. The provisional 0.19 setting is selected under
the prespecified finer grid; this contrast is seed variation and a changed
selection population, not evidence that the weights or pipeline improved.

## Frozen selection and evidence

| Setting | Seed 18 recall / FP/image | Seed 19 recall / FP/image | Two-seed mean recall / FP/image | Decision |
| --- | ---: | ---: | ---: | --- |
| 0.20, class-aware 0.70 | 0.87660 / 0.39894 | 0.81250 / 0.33777 | 0.84455 / 0.36835 | Mean recall below 0.85 |
| 0.19, class-aware 0.70 | 0.88942 / 0.41223 | 0.82051 / 0.34840 | **0.85497 / 0.38032** | Provisional two-seed setting |
| 0.19, across-class 0.80 | 0.88942 / 0.29521 | 0.82051 / 0.19947 | 0.85497 / 0.24734 | Rejected by paired mAP CI |

The confidence grid is 0.05–0.95 in 0.05 steps, union 0.15–0.30 in 0.01
steps (31 unique values). Eight class-aware and three across-class NMS
configurations yield 341 two-seed cells. Each cell averages the two seed
recalls and FP/image arithmetically; it does not report a standard deviation
from only two training seeds. Exact-class mAP50–95 comes from each full
post-NMS candidate pool before confidence filtering. The selected class-aware
0.70 mean mAP50–95 is 0.56486. The unrestricted across-class 0.80 cell's
mean is 0.50486, a difference of -0.06000.

The 0.70 seed-19 inference reproduced the QA-passed common validation anchor
at confidence 0.20: 507 localized GT hits, 127 false positives, 379
correct-class hits, mAP50 0.73087 and mAP50–95 0.52086. Only after that
gate passed did the other ten NMS settings run. The seed-18 predictions were
read unchanged from the 11 QA-pinned CSVs of D1 NMS sweep R1. The seed-19
best weight was extracted from its QA-passed result archive with SHA-256
`046cfea22e6daf45342063b58cd9082aa4b0b0528a3a6d9af7ac23bbac015bce`.
The new 11 prediction CSVs are local and Git-ignored under
`results/experiments/d1_two_seed_provisional_threshold_r1/`; their SHA-256
values and all input bindings are in
`docs/review/generated/d1_two_seed_provisional_threshold_r1.json`.

The paired intervals used 1,000 draws of intact D-02 groups at seed
20261018, sharing each draw across both training seeds and both NMS
configurations, then averaging the two seeds before subtraction. The
leave-one-group-out check selected on eight groups and evaluated the held-out
group. Those intervals quantify roster/group variation for these two trained
weights; they do not establish performance across future training seeds or
new driving scenes.

## Boundary and next gate

This result is **2/3 of the planned seeds**, an in-sample validation diagnostic
for the report and deck. It is not `LOCKED_ON_VAL`, does not call the legacy
lock writer, does not change D-05 or the app, and cannot authorize the sealed
test. The frozen three-seed R3 contract remains in force. Seed 20261020 and
its independent run/evaluation QA, plus the separately QA-passed successor
lock writer/reader, are still required before any final lock. Independent
result QA for this provisional package is recorded separately.
