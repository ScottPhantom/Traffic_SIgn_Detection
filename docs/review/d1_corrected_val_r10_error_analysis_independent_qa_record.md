# D1 corrected-validation R10 error-analysis packet independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL_REMEDIATION_REQUIRED`  
Reviewer: `Codex fresh independent artifact-and-governance QA session`  
Boundary: `READ_ONLY_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST`

## Verdict

**FAIL — 0 Critical, 0 High, 1 Medium and 1 Low finding.**

Every numerical count, share, confusion cell, class-gate recall and training-label support claim in
the packet reproduces from the pinned R10 result and the current corrected train-label export. The
selector and matching-semantics explanations are also correct. The packet nevertheless cannot be
accepted as the decision authority because Track B states the wrong Owner-decision boundary and
then contradicts itself by acknowledging that the Owner already requested that baseline.

This FAIL does not reject the R10 result or its independent result-QA PASS. It requires an
append-only packet revision before the packet is used to authorize or route a successor experiment.
Validation-only planning may continue; inference, training, sealed-test access and a new experiment
remain unauthorized by this packet.

`test_included=false` and `sealed_test_accessed=false` in the R10 result. No test material was
opened during this review.

## Exact reviewed inputs

| Input | SHA-256 | Status in this review |
| --- | --- | --- |
| `docs/review/d1_corrected_val_r10_error_analysis_and_improvement_packet.md` | `2ce6d44458bedc4692edf38380748aa1652c6a5d0d7a80fa0b4dbf9c1d26feac` | immutable packet under QA |
| `results/experiments/D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2/eval_val_wp38_r1_r4_r10.json` | `b33e247038c237d059207f75ad8ff33e0b5d6d00e4380826cd35ae85aefa02d5` | authoritative corrected-validation result |
| `docs/review/d1_corrected_val_r10_result_independent_qa_record.md` | `9940b31c344e9e683d0bd3d6ddc25b8a31053bbeb83398801637be08df2d06a2` | pinned result-QA PASS |
| `docs/review/d1_dual_baseline_owner_decision_record.md` | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` | controlling Track B Owner decision |
| `docs/review/generated/m1_yolo_classes.csv` | `7cda296a95bd8512a1bb2e85109ce9a1574fb882e692b11d4d0ee6a1cb58d242` | YOLO-id to derived-class-key authority |

## Verified numerical evidence

### Operating point and selector

- The stored point is confidence `0.20`, NMS IoU `0.70`, 376 images, 560 GT boxes, 483
  class-agnostic true-positive matches, 214 unmatched-prediction false positives and 77 misses.
  Arithmetic reproduces recall `483/560 = 0.8625` and FP/image
  `214/376 = 0.5691489361702128`.
- `detector/m1/metrics.py::select_threshold` evaluates the default grid `0.05..0.95` in steps of
  `0.05`, retains points with class-agnostic recall at least `0.85`, then minimizes
  `(fp_per_image, -confidence)`. Corrected evaluation calls it with no custom grid. Because the
  selected minimum-FP eligible point still has FP/image `0.5691 > 0.30`, the packet's conclusion
  that the existing grid has no point satisfying both recall and FP/image is correct.

### Diagnostic background row

The confusion matrix is 55 by 55 (54 derived classes plus `BACKGROUND`). The 54 GT rows sum to 560;
the background row sums to 214. The packet's six reported background-row cells reproduce exactly:

| Predicted derived class | Count | Independently rounded share of 214 |
| --- | ---: | ---: |
| 10 | 53 | 24.8% |
| 12 | 44 | 20.6% |
| 23 | 35 | 16.4% |
| 30 | 19 | 8.9% |
| 46 | 13 | 6.1% |
| 39 | 12 | 5.6% |

The total is `176/214 = 0.8224299065`, correctly reported as 82.2%.

### Class confusion and gate evidence

- GT 7: support 111; diagnostic row has background 36, predicted 17 count 10, predicted 18 count
  2 and predicted 49 count 1. Class-aware gate evidence is 66/111 = `0.594594...`.
- GT 32: support 29; diagnostic row has predicted 7 count 6 and background 5. Class-aware gate
  evidence is 18/29 = `0.620689...`.
- GT 41: support 21; diagnostic row has predicted 39 count 6, predicted 40 count 2 and background
  2. Class-aware gate evidence is 12/21 = `0.571428...`.
- GT 46: support 104; diagnostic row has predicted 10 count 58, diagonal 42 and background 4.
  Class-aware gate evidence is 55/104 = `0.528846...`, so it narrowly passes the non-critical 0.50
  gate.
- GT 8: support 51; diagnostic row has predicted 12 count 6 and background 15.

The packet correctly distinguishes the score-ordered, class-agnostic diagnostic pairing in
`_greedy_pairs()` / `confusion_matrix()` from the separate class-aware matching used by
`operating_point()` and `gate_report()`. For example, class 7 has diagnostic diagonal 62 but
class-aware gate hits 66; class 46 has diagnostic diagonal 42 but class-aware gate hits 55. The
packet is correct that these values need not be equal.

### Train-label support

All 3,712 label files in
`data/processed/m1_yolo_wp38_r1_integration_r4/labels/train/` were parsed read-only against the
pinned YOLO class map. Their 12,621 boxes reproduce every packet claim:

| Derived class | Train-label boxes |
| --- | ---: |
| 7 | 228 |
| 32 | 138 |
| 41 | 610 |
| 10 | 1,431 |
| 46 | 427 |

These are current training-export label occurrences, including the governed WP35 train-only
augmentation, not independent-scene counts. The packet only claims label support and does not
misrepresent them as independent observations.

## Matching-semantics and evidence-boundary audit

- The R10 JSON contains the full aggregate confusion matrix and exactly 20 bounded stems in each
  error-sample category, but it does not contain every predicted box or a visual FP atlas. The
  packet correctly keeps visual causes as hypotheses and routes them to a new QA-reviewed
  validation-only package.
- D1-EA-R1 is explicitly prohibited from copying validation images, crops, predictions or
  pseudo-labels into train. Track A limits mining to the existing train split or separately
  approved new training scenes, retains `fliplr=0`, and permits only train-derived augmentation.
  No validation leakage is authorized.
- The package request contains no test input and requires `sealed_test_accessed=false`. Track B's
  future sealed-test eligibility is correctly left to a separate addendum. No test access is
  implied.
- The packet's opening boundary and closing recommendation correctly state that it authorizes no
  run and that a concrete 100-epoch run still needs a frozen contract, data delta, resume behavior,
  acceptance criteria, independent QA and explicit Owner authorization.

## Findings

### M1 — Track B misstates and internally contradicts the existing Owner-decision boundary

Packet lines 95-96 say the one-class detector plus 54-class crop classifier changes D-05 scope and
"needs an Owner decision plus classifier gates." Lines 102-103 then call it the comparison baseline
"already requested by the Owner."

The controlling append-only decision record, SHA-256
`39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2`, is more precise:

- the Owner already selected option C and authorized the one-class detector plus classifier as a
  comparison baseline;
- it may be built and validated on train/validation data;
- it does not inherit the 54-class D-05 gates; and
- its classifier taxonomy, acceptance metrics, threshold protocol and sealed-test eligibility
  require an explicit append-only addendum before final evaluation.

The packet's generic demand for a new architecture decision is therefore false, while its failure
to state the exact remaining addendum scope obscures the real governance boundary. The language is
safely conservative, but an accepted decision packet must not replace a verified Owner decision
with a contradictory summary.

**Required remediation:** issue an append-only R1 packet that pins the dual-baseline decision
record and states that Track B is already Owner-authorized for train/validation comparison. State
separately that (a) the classifier taxonomy/gates/threshold/sealed-test addendum remains required
before final evaluation and (b) this packet still does not authorize a concrete training run; the
frozen run contract and current explicit-run authorization gate remain in force.

### L1 — `483 class-agnostic detections` is imprecise metric terminology

Packet line 20 calls 483 "class-agnostic detections." The stored field is
`operating_point.true_positives`: 483 class-agnostic matched true positives. At the diagnostic
threshold there are 697 retained predictions in total (`483 TP + 214 FP`). The surrounding counts
make the intended arithmetic recoverable, so this does not invalidate any numerical conclusion,
but the wording can be misread as the total detection count.

**Required remediation:** say `483 class-agnostic true-positive matches`, and describe the
confusion-matrix background row as 214 unmatched-prediction FP. Keep visual-background root cause
as a hypothesis until D1-EA-R1 supplies the proposed atlas.

## Commands and observed results

Read-only checks included:

```text
graft check .
graft ask <selector, class-aware gate and class-agnostic confusion questions> --source .
graft skeleton detector/m1/metrics.py
shasum -a 256 <packet> <R10 JSON> <result-QA record> <dual-baseline decision>
jq <operating point, confusion matrix, gates and policy fields> <R10 JSON>
uv run python - <<'PY'  # matrix cells/shares, arithmetic, class-map and 3,712 train-label audit
PY
```

Observed results: Graft freshness `OK`; all task-supplied hashes matched; matrix shape and totals
were 55×55, 560 GT and 214 background-row FP; all packet counts and shares matched; all five
training-support counts matched; selector and dual-matcher claims matched source. No inference,
training, evaluation rerun, model loading, upload, commit, push or sealed-test access occurred.

## Bounded next state

| Action | QA disposition |
| --- | --- |
| Preserve the immutable input packet as the initial QA-fail record | **YES** |
| Accept its empirical error counts as reproduced evidence | **YES** |
| Treat the current packet as the successor experiment decision authority | **NO — FAIL** |
| Produce an append-only R1 with M1/L1 remediation | **YES** |
| Build D1-EA-R1 before choosing the training change | **YES, after the R1 packet passes QA** |
| Train or launch a smoke/100-epoch run from this packet | **NO-GO** |
| Run unchanged seeds `20261019` / `20261020` | **NO-GO** |
| Access sealed test | **NO-GO** |

