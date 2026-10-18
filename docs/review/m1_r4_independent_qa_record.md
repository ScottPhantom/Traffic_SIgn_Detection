# M1-R4 independent QA record

Status: `QA_PASS_M1_R4_H4A_H5_CLOSED`
Reviewer: `Codex independent QA session (did not author M1-R4 and did not act as PM)`
Reviewed at: `2026-10-19T00:12:12+07:00`
Boundary: `QA_OF_M1_R4_PACKAGE_ONLY_SYNTHETIC_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `eae9146e471fff261d674a4ec9653ee073301b37`

This append-only record re-reviews only the M1-R4 package described by
`docs/review/m1_r4_qa_remediation_report.md`. It preserves every earlier independent QA record
byte-for-byte. It changes no M1 source, test, manifest, model, dataset, Owner record, project
memory or roadmap file.

## Verdict

- **M1-R4: PASS.** 0 Critical, 0 High, 0 Medium, 0 Low.
- **H-4A: CLOSED.** Primary integer counts, operating-point ratios, resolution totals, confusion
  evidence, class-aware hit/support/recall rows, the supported-class AP50 mean and AP-small
  zero/non-zero state are cross-validated. The independent contradiction attacks failed closed.
- **H-5: CLOSED.** Final latency evidence is bound to the clean committed threshold lock and to
  the same per-seed weight, confidence, NMS IoU and image size as test evaluation. The independent
  lock/configuration substitution attacks failed closed.
- All twelve delegated input and package hashes match the reviewed bytes. Every requested
  mechanical gate passes.
- A real temporary Git fixture with three synthetic run contracts, three distinct weight pairs, a
  clean committed run registry, validation-report hashes and committed primary/alternate
  threshold locks produced a valid three-seed final aggregate with
  `all_gates_passed=true`. Actual `cmd_evaluate` and `cmd_latency` report construction ran behind
  model/data/logger mocks; every generated report passed the real validators.
- The focused independent matrix completed **30 accepted-positive checks** and **24 expected
  rejections**. Every expected-negative aggregate case failed before its output path existed.
- No open R4 finding remains within the delegated scope. This PASS removes the independent-QA
  blocker identified by R3; it is not authorization to train, start a pilot, use Colab, upload,
  open the sealed test, commit or push. Those remain separate Owner/PM decisions.
- This verdict establishes executable research/simulation controls only. It does not establish
  Vietnamese deployment accuracy, open-set/OOD safety or driving-safety validation.

## Pin and package readback

- R3 independent QA input SHA-256:
  `6da1eb65ca5f28794d67e9ac518994f79d49e099546e151ce657802ed4a7b6d9`.
- R4 remediation report SHA-256:
  `86312e3515059bbd7552213f331dcc732dbe8fa22b1c71e5dae688fae299d6bf`.
- Every R4 source/artifact pin matches the current byte:
  - detector CLI `fa776f4e...`, metrics `d24570f8...`, tests `97c5c97b...`, contract
    `cdf2ccba...`;
  - YOLO builder `3b52c63f...`, crop builder `1f1bfac3...`;
  - root YOLO tests `8ccc91ec...`, crop tests `a5e64bc1...`;
  - M1 manifest `8a8df5f2...`, crop manifest `6526844b...`.
- The reviewed branch is `DEV/Rroject_Pineline`; HEAD and
  `origin/DEV/Rroject_Pineline` are both
  `eae9146e471fff261d674a4ec9653ee073301b37`.

## Executable gate matrix

| Gate | Result | Readback |
| --- | --- | --- |
| Detector Ruff | PASS | `All checks passed!` |
| Detector lock | PASS | 66 packages resolved; lock unchanged |
| Entire detector suite | PASS | **53/53** |
| Detector CLI contract check | PASS | Apple M1 Pro, `arm64`, MPS available, detector lock `5d56642a...`, export manifest `8a8df5f2...`, test seal `afa03d4b...` |
| Root targeted Ruff | PASS | M1/crop builders and tests clean |
| Root lock | PASS | 168 packages resolved; lock unchanged |
| Root M1/crop suite | PASS | **16/16** |
| Package verifiers | PASS | **51/51** in 90.2 seconds wall time |
| Git whitespace check | PASS | `git diff --check` produced no error |
| Graft freshness | PASS | 2,226 nodes and 5,654 edges |

Graft map/ask/skeleton/caller queries were used before source inspection and saved 740,809 source
tokens during this review, approximately USD 0.40 at the session rate. Per the delegated scope,
the full historical root pytest suite was not run.

## Independent synthetic fixture and CLI smoke

The independent fixture used a newly initialized temporary Git repository, not the project
repository. It contained:

- three approved synthetic seeds, three complete run contracts and three distinct `best.pt` /
  `last.pt` byte pairs;
- a three-entry run registry tracked, committed and clean in that repository;
- three validation-report hashes plus two tracked, committed and clean threshold locks: a primary
  lock at confidence `0.5` / NMS `0.7`, and an alternate lock at confidence `0.4` / NMS `0.7`;
- forty synthetic ground-truth boxes across two synthetic classes and matching predictions; and
- Apple M1 Pro-shaped latency environment metadata without running a real model or benchmark.

The real `bind_run_weights` and `bind_threshold_lock` functions accepted all three registry and
primary-lock bindings. For each seed, the actual `cmd_evaluate` path constructed a complete test
report from mocked YOLO output and synthetic `Frame` evidence; the actual `cmd_latency` path
constructed a complete report from a mocked model and synchronization. The real test/latency
validators accepted all six reports.

The latency mock recorded 1,050 prediction calls: 50 warm-ups plus 300 measured calls for each of
three seeds. Every call received confidence `0.5` and `iou=0.7`. The three latency reports recorded
the full lock, confidence and NMS binding. Final aggregation accepted the three test plus three
latency reports, returned `all_gates_passed=true`, and recorded the exact committed primary-lock
hash.

The real sealed-test logger was replaced before entering `cmd_evaluate`; only an in-memory callback
captured the three expected calls. No project access log or sealed-test artifact was read or
written.

## Independent attack matrix

| ID | Attack or control | Expected | Observed |
| --- | --- | --- | --- |
| H4A-01 | Move all class-0 confusion hits to BACKGROUND while recall remains PASS | Reject | PASS: rejected |
| H4A-02 | Change global TP count without changing dependent metrics/evidence | Reject | PASS: rejected |
| H4A-03 | Change a resolution recall ratio without changing its counts | Reject | PASS: rejected |
| H4A-04 | Change a resolution image count so totals no longer reconcile globally | Reject | PASS: rejected |
| H4A-05 | Set mAP50 mean difference to `9e-7` | Accept | PASS: accepted |
| H4A-06 | Set mAP50 mean difference to `1.1e-6` | Reject | PASS: rejected |
| H4A-07 | Independently corrupt class hits, support, then recall | Reject all | PASS: 3/3 rejected |
| H4A-08 | AP-small `(classes,support,value)` of `(0,0,1)`, `(0,1,0)`, `(1,0,0)` | Reject all | PASS: 3/3 rejected |
| H4A-09 | AP-small value zero with positive class/support evidence | Accept | PASS: accepted |
| H4A-10 | Invalid operating-point ratio passed to final aggregation | Reject before output | PASS: rejected; no output existed |
| H5-01 | Remove the latency threshold-lock binding | Reject | PASS: rejected |
| H5-02 | Tamper the embedded latency lock hash | Reject | PASS: rejected |
| H5-03 | Dirty the real committed lock file, then reference it | Reject | PASS: rejected |
| H5-04 | Reference a missing lock artifact | Reject | PASS: rejected |
| H5-05 | Change latency confidence from its committed candidate | Reject | PASS: rejected |
| H5-06 | Change latency NMS IoU from its committed candidate | Reject | PASS: rejected |
| H5-07 | Use latency image size 32 against test image size 1280 | Reject before output | PASS: rejected; no output existed |
| H5-08 | Mix test image sizes across the three seeds | Reject before output | PASS: rejected; no output existed |
| H5-09 | Keep the same seed/weight but bind latency to the clean alternate lock/config | Reject before output | PASS: alternate report validated alone, aggregate rejected it; no output existed |
| NF-01 | Use self-consistent `FP/image=2.0` and two false positives | Accept report domain; gate may fail | PASS: accepted without false rejection |
| NF-02 | Use self-consistent latency values above one millisecond | Accept report domain | PASS: accepted without false rejection |
| NF-03 | Let class-aware hits differ from the confusion diagonal while all primary counts remain self-consistent | Accept | PASS: accepted without false rejection |
| R2-01 | Complete structurally valid self-issued run omitted from committed registry | Reject binding | PASS: structure accepted, registry binding rejected |
| R3-01 | Reuse one test report as three seeds | Reject before output | PASS: rejected; no output existed |
| R3-02 | Add an unknown top-level report field | Reject exact schema | PASS: rejected |

## H-4A closure assessment

The validator now has two independent paths to the global primary counts:

1. the integer operating-point and per-resolution counts, whose reported ratios must be reproduced
   within `1e-6` and whose resolution totals must equal the global row; and
2. the confusion matrix, whose GT rows, non-background matches and background-row predictions must
   exactly equal global ground truth, true positives and false positives.

Per-class gate rows are tied to integer class-aware hits and confusion-row support, and their recall
and flags are recomputed. The supported-class AP50 mean is tied to global mAP50 at the documented
`1e-6` tolerance. AP-small zero/non-zero evidence now fails closed for each contradictory state
requested by R3. The positive tolerance boundary and the class-aware/confusion divergence control
also show that the repair is not over-constrained.

**Assessment: H-4A closed with no residual severity.**

## H-5 closure assessment

The latency producer validates a provided committed lock before model construction, passes both
confidence and NMS IoU to prediction, and records the full lock binding plus those exact values.
The final latency validator requires that binding. Aggregation then checks one test image size, one
latency image size and exact per-seed equality of weight hash, complete threshold lock, image size,
confidence and NMS IoU.

The smaller-size, mixed-size, missing/dirty/tampered-lock, changed-threshold and alternate-clean-lock
attacks all failed before aggregate output. The actual mocked prediction call trace independently
confirmed that `cmd_latency` propagated NMS and confidence rather than merely serializing them.

**Assessment: H-5 closed with no residual severity.**

## Evidence boundary and final state

- No model training, real model prediction, real latency benchmark, checkpoint creation, upload,
  download, deployment, commit, push or publication occurred.
- No raw sealed-test image, label, export or metric was opened. All registry, lock, report,
  evaluator, latency and aggregate work used temporary synthetic files, frames, mock objects and a
  temporary Git repository.
- No real run registry, real threshold lock, `data_test.yaml`, crop `test.p` or sealed-test access
  log was present or created in the project checkout. No QA process remained running.
- Pre-existing user/PM source and generated-artifact changes were preserved. Only this independent
  QA record was added.
- PM may use this PASS as the successor independent-QA result for the R4 gate. Any pilot, training,
  external transfer or sealed-test action still requires its own explicit authorization and the
  repository's governed workflow.
