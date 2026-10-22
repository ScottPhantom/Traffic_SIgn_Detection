# D1 corrected-validation R10 error-analysis packet R1 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS`  
Reviewer: `Codex fresh independent artifact-and-governance QA session`  
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

R1 closes both findings from the immutable initial-packet QA FAIL. It states the prediction count
with the correct metric semantics and restores the exact existing Owner authority for Track B.
All retained empirical counts, shares, confusion cells, train-label supports, selector behavior and
matching-contract explanations reproduce from the pinned authorities.

This PASS accepts R1 as the decision packet for designing and implementing the next validation-only
D1-EA-R1 evidence-package builder and contract. It does not authorize model execution, a smoke
run, training, new seeds, sealed-test access, final evaluation, model acceptance or deployment;
the implementation must receive its own independent QA before a validation-only diagnostic run.

`test_included=false` and `sealed_test_accessed=false` in the R10 authority. No test material was
opened during this review.

## Exact reviewed inputs and pins

| Input | SHA-256 | Result |
| --- | --- | --- |
| `docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet_r1.md` | `9ec8dd0d9e2866ef098ca3afada624ea5562837531f9b077981c45940ed0f78f` | exact task input matched |
| initial packet | `2ce6d44458bedc4692edf38380748aa1652c6a5d0d7a80fa0b4dbf9c1d26feac` | R1 predecessor pin matched |
| initial packet QA FAIL record | `89ebb22aeb8b21f38e4fcea3d4ae49d40a188642cf3f56afb11d7ab917c5a984` | R1 predecessor-QA pin matched |
| `docs/review/d1_dual_baseline_owner_decision_record.md` | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` | R1 Owner-authority pin matched |
| R10 result JSON | `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5` | R1 empirical-authority pin matched |
| R10 result QA PASS record | `9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2` | R1 result-QA pin matched |

The initial packet remains byte-identical. R1 is a separate append-only successor and does not
rewrite any pinned predecessor evidence.

## Empirical reproduction

At confidence `0.20` and NMS IoU `0.70`, the R10 operating point has exactly:

```text
retained_predictions = 697 = 483 class-agnostic TP matches + 214 FP
unmatched_ground_truth = 560 - 483 = 77
images = 376
recall = 483 / 560 = 0.8625
FP/image = 214 / 376 = 0.5691489361702128
```

R1 therefore fixes the initial wording correctly: 483 is the class-agnostic matched-TP count, not
the total prediction count.

The 55×55 diagnostic confusion matrix has 560 events in its 54 GT rows and 214 entries in its
`BACKGROUND` row. R1's background-row class counts reproduce exactly: class 10 = 53, class 12 =
44, class 23 = 35, class 30 = 19, class 46 = 13 and class 39 = 12. Their total is 176, and
`176/214 = 82.24299065%`, correctly rounded to 82.2%.

The stated class evidence also reproduces:

- GT 7: support 111; diagnostic background 36, 7→17 = 10, 7→18 = 2, 7→49 = 1; class-aware gate
  hits 66 and recall `0.594594...`.
- GT 32: support 29; 32→7 = 6, diagnostic background 5; gate hits 18 and recall `0.620689...`.
- GT 41: support 21; 41→39 = 6, 41→40 = 2, diagnostic background 2; gate hits 12 and recall
  `0.571428...`.
- GT 46: support 104; 46→10 = 58, diagnostic diagonal 42, background 4; gate hits 55 and recall
  `0.528846...`, narrowly passing the non-critical 0.50 gate.
- GT 8: support 51; 8→12 = 6 and diagnostic background 15.

Read-only parsing of all 3,712 corrected-export train label files produced 12,621 boxes and exactly
the five stated supports: class 7 = 228, class 32 = 138, class 41 = 610, class 10 = 1,431 and class
46 = 427.

## Selector and matcher semantics

- `select_threshold()` evaluates the default grid `0.05..0.95` in increments of `0.05`, filters
  for class-agnostic recall at least `0.85`, then minimizes `(fp_per_image, -confidence)`. Corrected
  validation passes no custom grid. Since the selected eligible minimum is still FP/image 0.5691,
  R1 correctly says the existing grid has no point satisfying both current recall and FP gates.
- The aggregate confusion matrix uses score-ordered, class-agnostic greedy pairing. Per-class gate
  hits use a separate class-aware match. R1 correctly warns that diagnostic diagonal/miss counts
  need not equal `gates.classes[*].hits`.
- The result provides only aggregate confusion plus bounded stem samples, not all predicted boxes
  or a visual FP atlas. R1 correctly keeps visual causes hypothetical pending the proposed
  validation-only D1-EA-R1 package.

## Track B Owner authority and safety boundaries

R1 now matches the exact dual-baseline Owner record:

- the one-class traffic-sign detector plus crop classifier is already Owner-approved as a
  comparison baseline that may be built and validated on train/validation data;
- no new architecture approval is needed for that bounded comparison;
- it does not silently inherit the 54-class D-05 per-class gates; and
- before any final or sealed-test evaluation, a separate append-only Owner-approved addendum must
  define classifier taxonomy, acceptance gates, threshold protocol and sealed-test eligibility.

R1 also preserves the other required boundaries. D1-EA-R1 is diagnosis-only; validation images,
crops, predictions and pseudo-labels are prohibited from train. Track A mining is limited to the
training split or separately approved new training scenes, and augmentation remains train-derived
with `fliplr=0`. The packet explicitly authorizes neither smoke nor training nor new seeds nor test
access. A concrete run still needs an exact frozen data delta, experiment/recovery contract,
validation acceptance rules, independent QA and the existing run-authorization workflow.

## Commands and observed results

Read-only checks included:

```text
graft check .
graft ask <R10 selector and matcher semantics question> --source .
shasum -a 256 <R1 packet> <all five pinned predecessor/authority files>
jq <operating point, confusion matrix, gate and policy fields> <R10 JSON>
uv run python - <<'PY'  # predictions, misses, shares, cells and 3,712-file train-label audit
PY
```

Observed results: Graft freshness `OK`; all six exact hashes matched; prediction arithmetic,
matrix totals/cells, shares, gate values and five train supports matched; selector and matcher
semantics matched source; Track B language matched the Owner record; test and sealed flags remained
false. No model was loaded and no inference, evaluation rerun, smoke, training, upload, commit, push
or sealed-test access occurred.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Preserve initial packet and initial QA FAIL as immutable history | **YES** |
| Preserve R1 and this PASS record as current decision authority | **YES** |
| Design and implement the validation-only D1-EA-R1 builder/contract | **GO — no model execution** |
| Execute D1-EA-R1 validation inference | **NO-GO until the exact implementation passes independent QA** |
| Use validation pixels/crops/predictions for training | **NO-GO** |
| Launch smoke, pilot, unchanged seeds or any training from this PASS | **NO-GO** |
| Open or export sealed test | **NO-GO** |
| Prepare frozen Track A/B contracts after D1-EA-R1 visual QA | **YES — separately QA each contract** |

