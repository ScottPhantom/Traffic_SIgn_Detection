# D1 YOLO11s pilot quality report — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, read-only evidence audit, fail-closed  
Verdict: **FAIL**

## Scope and authorization boundary

This review covers only:

- `docs/review/d1_pilot_report.md`;
- the registered seed-20261018 run, its `best.pt`, `last.pt`, `run_contract.json` and committed run
  registry;
- the existing validation artifact `eval_val.json`;
- the existing Apple M1 Pro/MPS artifact `latency_mps.json`;
- the evaluation/metric source at commit `0f5ddb174beba8678430cf2329d124fde6cfa2b8`;
- the binding D-05 and dataset-coverage records needed to interpret the report.

QA did not train or resume a model, run model evaluation or latency measurement, open/export/read
the sealed test, change a threshold, modify a run artifact or report, commit, push, upload, or
authorize another seed. The only project file created by QA is this append-only record.

## Reviewed identities

| Artifact | SHA-256 / identity |
| --- | --- |
| pilot report | `53470f8cf33e899205f9405671c47b58ec435bc189891b40425b61deb3930c3f` |
| `eval_val.json` | `e6fe9eb58e4d06e3815d94be477f5b450625042c25b08995c1217ffd26dc8895` |
| `latency_mps.json` | `54a4d268890013f90140529b3ea31c21462d38f38e8596e98ca7e7510a8af01a` |
| `best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `last.pt` | `75ada6ba44804252c65e6ec76660511e0cc6ea69ee164c766055033dac11ea25` |
| `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| committed run registry | `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9` |
| canonical run attestation | `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` |
| `results.csv` | `b515c4407ecfec7e1448efac438ca7e9bc8abbed7ce992e10eee02efcc81394e` |
| D-05 decision record | `c81f37ed0236c019644914445776632dbe0fbcef0f7d5b964fb5c6d635555702` |
| recorded source commit | `0f5ddb174beba8678430cf2329d124fde6cfa2b8` |

The production `bind_run_weights` path accepted the registered `best.pt` and reproduced the exact
seed, weight, contract, registry and attestation identities above. The current detector metric,
contract and CLI sources are unchanged from the recorded source commit; later repository commits do
not change those three files.

## Correctly reproduced report evidence

### Model/run binding and training summary

PASS. The contract binds D1, YOLO11s, seed `20261018`, 100 epochs, image size 1280, batch 4,
pretrained mode, deterministic mode, `fliplr=0.0`, NVIDIA L4 and a clean training checkout. It binds
only the two reviewed weights. `results.csv` has 100 epoch rows; its epoch-100 accumulated time is
`14786.4` seconds, so the report's approximately 4 h 6 min statement is accurate and correctly does
not claim total wall time across interrupted Colab attempts.

The previously authenticated live-artifact record establishes `epoch-0100`, terminal
`SUCCEEDED`, outcome `COMPLETED_FROM_FINAL_CHECKPOINT`, six attempts, four failed resumes, five
distinct runtime digests and `sealed_test_accessed=false`. This report audit did not re-run or
mutate that workflow.

### Validation numbers and arithmetic

PASS. Independent JSON/matrix arithmetic reproduced:

- 376 images and 560 labelled boxes;
- mAP50 `0.8292039144342593`, mAP50-95 `0.5888191737174719` and AP-small
  `0.2818783965999705` over 213 boxes in 13 classes;
- confidence `0.15`, 480 class-agnostic TP, 207 FP, recall `480/560 = 0.8571428571`, precision
  `480/(480+207) = 0.6986899563`, and FP/image `207/376 = 0.5505319149`;
- group-bootstrap intervals `[0.7513175676, 0.9614731635]` for recall and
  `[0.2499426606, 1.0820063384]` for FP/image; both contain their point estimates;
- the per-class AP50 roster is exactly the 19 supported validation classes and its mean equals the
  recorded mAP50 within floating-point precision;
- the confusion-matrix support, matched detections and background-row FP totals equal the operating
  point exactly.

The source performs 1,000 deterministic resamples of complete D-02 groups with seed `20261018`.
The interval schema and values are present and internally valid. Because the report does not retain
the individual bootstrap draws, QA verified source semantics and output consistency rather than
recomputing the interval from raw predictions.

### Resolution, class gates and error samples

PASS for the reported measurements. The two resolution rows sum exactly to the overall counts:

- `960x540`: 337 images, 531 GT, 473 TP and 170 FP;
- `540x960`: 39 images, 29 GT, 7 TP and 37 FP.

There is no `1920x1080` row, so the report correctly marks that resolution unverified. The portrait
recall `7/29 = 0.2413793103` and FP/image `37/39 = 0.9487179487` substantiate the stated portrait
blocker.

Exactly three critical classes meet the 20-box support rule and all three fail: class 7 has
`71/111 = 0.6396`, class 32 has `19/29 = 0.6552`, and class 41 has `12/21 = 0.5714`. All six gated
non-critical classes pass the 0.50 reference. The ten low-support rows, their hits/support, and all
three 20-stem error-sample lists match the artifact exactly. UNKNOWN diagnostic support is 10,
recognized-as-known is 6, and the reported 0.60 rate is correct; the report appropriately does not
promote it to an OOD guarantee.

### Latency and dirty-worktree limitation

PASS. The latency artifact records Apple M1 Pro, MPS, image size 1280, batch 1, confidence 0.15,
NMS IoU 0.70, 50 warm-up iterations and 300 measured iterations. Mean `45.3018` ms, p50 `44.4451`
ms, p95 `47.3005` ms and maximum `207.6626` ms match the report. The p95 result is below the D-05
100 ms reference. The same artifact records commit `0f5ddb174beba8678430cf2329d124fde6cfa2b8`
and 54 dirty/untracked paths, and the report keeps that limitation visible.

## Blocking findings

### QA-D1-PILOT-REPORT-001 — Medium — the 35-class absence is real but not newly or unexpectedly exposed

The artifact does contain exactly 35 zero-support validation class keys, and the report reproduces
their list correctly. However, those 35 keys partition exactly into two already governed sets:

- the 13 test-bearing classes with no validation support: `9`, `11`, `17`, `18`, `19`, `20`, `22`,
  `25`, `28`, `30`, `40`, `45`, `50`;
- the 22 already documented no-test/train-only classes: `1`, `15`, `16:2.0`, `16:2.2`, `16:2.5`,
  `21`, `24`, `27`, `29`, `33`, `35`, `36`, `37`, `38`, `42`, `43:2.5`, `43:2.7`, `44`, `47`,
  `48`, `49`, `51`.

There is no extra or missing key. `PROJECT_MEMORY.md` and the governed dataset card already state
that 35 classes have no valid crops; D-05 separately calls out the 13 classes that have test but no
val because they must not drive selection/tuning. Therefore the report's claims that this is
"broader-than-expected" and that the pilot "exposes" the coverage are inaccurate. Using that
expected partition as a newly discovered NO-GO reason is not evidence-bounded.

The blanket sentence that all 35 classes "were not used to select the model" is also too broad.
They contribute no GT support, per-class AP or class-gate evidence, which is the defensible claim.
The aggregate class-agnostic FP total still contains 29 unmatched predictions whose predicted keys
belong to six of the 35 absent classes (`17`, `18`, `19`, `30`, `40`, `42`). Counting those
detections as global FP is reasonable, but the report must distinguish that aggregate detector
metric from class-specific selection evidence.

Required remediation: state the exact 13+22 governed partition, describe the absence as expected,
remove it as a newly discovered blocker, and narrowly state what class-specific evidence did not
contribute. This correction does not erase the separately measured FP, critical-class or portrait
failures.

### QA-D1-PILOT-REPORT-002 — Medium — confidence was selected at a fixed NMS, but the report obscures the untuned NMS requirement

At commit `0f5ddb1`, `select_threshold` evaluates only the confidence grid 0.05 through 0.95 in
0.05 increments. `cmd_evaluate` passes one caller-supplied NMS value into inference; it does not
search an NMS grid. Thus the artifact shows that confidence 0.15 was selected under a fixed NMS IoU
of 0.70. It does not show that NMS 0.70 itself was selected on validation.

D-05 Q4 requires both confidence and NMS thresholds to be chosen on validation. The report says
"the governed selector chose confidence=0.15 with NMS IoU=0.70" without disclosing that NMS was
fixed, and then discusses the operating point as if threshold selection were complete. That wording
can incorrectly imply that the D-05 confidence-and-NMS selection requirement has been satisfied.

Required remediation: say explicitly that confidence 0.15 is the best point on the governed
confidence grid **conditional on fixed NMS IoU 0.70**, mark NMS tuning/justification as outstanding,
and do not create a final threshold lock until the full three-seed val protocol satisfies D-05. No
rerun is needed merely to preserve the current conclusion as "NO-GO for this unchanged fixed-NMS
configuration"; a future compliant threshold-selection package must address NMS before final lock.

## Evidence limitation requiring explicit wording

`latency_mps.json` contains the commit and dirty-file environment record. `eval_val.json` does not
contain an environment block, execution receipt, source commit, candidate confidence curve or raw
prediction digest. Its selected point is internally consistent with the reviewed source's schema
and selection semantics, and its filesystem timestamp follows commit `0f5ddb1`, but those facts are
not a cryptographic execution-source binding and cannot independently prove that 0.15 minimized
FP/image over every candidate.

Accordingly, the sentence "the recorded evaluation checkout is commit `0f5ddb1...`" must be
narrowed to say that the **latency artifact** records that checkout. The report should disclose that
the validation artifact does not record its execution environment/candidate curve. A future report
format should retain the candidate curve and source/environment binding; this QA does not authorize
rerunning validation solely to add them.

## Sealed-test and final-verdict boundary

PASS. Both model-quality artifacts are explicitly `split=val` or use validation images. Their
weight, contract, registry and seed bindings agree. No final threshold lock is present. The governed
sealed-test access log is absent and no exported test directory or test metric was found in the
reviewed scope. The authenticated training package evidence says `sealed_test_accessed=false`.

The report correctly states that one validation seed cannot produce the D-05 final verdict and does
not claim one. Its central interim **NO-GO for the unchanged pilot configuration** remains supported
even after removing the incorrect coverage rationale: FP/image fails (`0.5505 > 0.30`), all three
supported critical-class references fail, and portrait performance is poor. This is validation-only
evidence and is not a sealed-test verdict or safety claim.

## Validation summary

- Graft freshness: `OK`, graph in sync;
- exact report/eval/latency hashes: PASS;
- production registered-weight binding and canonical attestation: PASS;
- operating-point, confusion, per-class, resolution and UNKNOWN arithmetic: PASS;
- group-bootstrap source semantics and interval schema: PASS;
- latency parameters/statistics/environment record: PASS;
- 35-class roster count: PASS; governance interpretation in report: **FAIL**;
- confidence selector at fixed NMS: PASS; claim implying complete confidence+NMS selection:
  **FAIL**;
- single-seed/no-final-verdict and core NO-GO boundaries: PASS;
- sealed test: not accessed by QA; no access artifact observed.

No model test suite was run because this task expressly prohibited evaluation/test activity and
made no source-code change. Verification used only strict JSON parsing, hashes, source inspection,
production read-only binding, arithmetic recomputation and governed-document comparison.

## Verdict and authorization boundary

**FAIL.** The measurements and the core NO-GO conclusion are substantially correct, but the report
mischaracterizes already governed 35-class validation coverage and obscures that NMS 0.70 was fixed
rather than selected. It also attributes the recorded source environment too broadly to validation
when only the latency artifact carries that binding.

This FAIL does not invalidate the registered weights or the measured val/latency artifacts. It
blocks approval of `docs/review/d1_pilot_report.md` at the reviewed hash until an append-only R1
report corrects the findings and receives independent QA. It authorizes no report edit by QA, no
next-seed training, no threshold lock, no D-05 gate change, no sealed-test access, no deployment,
no commit and no push.
