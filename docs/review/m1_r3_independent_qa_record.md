# M1-R3 independent QA record

Status: `QA_FAIL_M1_R3_FINAL_REPORT_CROSS_FIELD_BLOCKERS_REPAIR_REQUIRED`
Reviewer: `Codex independent QA session (did not author M1-R3 and did not act as PM)`
Reviewed at: `2026-10-19T00:02:00+07:00`
Boundary: `QA_OF_M1_R3_PACKAGE_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `eae9146e471fff261d674a4ec9653ee073301b37`

This append-only record re-reviews only the M1-R3 package described by
`docs/review/m1_r3_qa_remediation_report.md`. It preserves the initial, R1 and R2 independent QA
records byte-for-byte. It changes no M1 source, test, manifest, model, dataset, Owner record,
project memory or roadmap file.

## Verdict

- **M1-R3: FAIL.** 0 Critical, 2 High, 0 Medium, 0 Low.
- All twelve delegated input and package hashes match the reviewed bytes. Every requested
  mechanical gate passes.
- R3 closes the R2 primitive domain/type/schema gap: 240/240 independent negative mutations were
  rejected, the valid unbounded-above FP/latency cases were not falsely rejected, exponent
  overflow failed closed, and invalid inputs failed before aggregate output creation.
- R3 does not close the complete H-4 trust boundary. A report can still contradict its confusion
  matrix and per-class AP evidence while emitting final PASS. A latency report can also benchmark
  a different image size from final evaluation; confidence/NMS/threshold lock are absent from the
  latency artifact entirely. Both attacks retained three real temporary-Git registry anchors and
  one clean committed threshold lock, yet `cmd_aggregate` returned `all_gates_passed=true`.
- **Do not start the pilot, open the sealed test, or issue a D-05 verdict from M1-R3.** PM must
  repair both cross-field bindings and request a successor independent review.
- This verdict does not revoke Gate 0 or the Owner's D-05 decisions. It says only that the M1-R3
  executable final-verdict layer remains capable of accepting internally contradictory evidence.

## Pin and package readback

- R2 independent QA input SHA-256:
  `0e776459cc9397d3940198db8fe22716c2de707e20e91b8b5b1c5fb3b0816b07`.
- R3 remediation report SHA-256:
  `a8557836440b5b2af8d715503e88cc581a0badbded3b92035dc469336152642e`.
- Every R3 source/artifact pin matches the current byte:
  - detector CLI `c27e3289...`, tests `7006f07f...`, contract `cdf2ccba...`, metrics
    `5be05038...`;
  - YOLO builder `3b52c63f...`, crop builder `1f1bfac3...`;
  - root YOLO tests `8ccc91ec...`, crop tests `a5e64bc1...`;
  - M1 manifest `8a8df5f2...`, crop manifest `6526844b...`.
- The reviewed branch is `DEV/Rroject_Pineline`; HEAD and `origin/DEV/Rroject_Pineline` are both
  `eae9146e471fff261d674a4ec9653ee073301b37`.

## Executable gates

- Detector Ruff: PASS.
- Detector `uv lock --check`: PASS, 66 packages resolved.
- Entire detector test suite: **43/43 PASS**.
- `YOLO_OFFLINE=true uv run python -m m1.cli check`: PASS. It reported Apple M1 Pro, `arm64`,
  MPS available, detector lock `5d56642a...`, export manifest `8a8df5f2...` and test seal
  `afa03d4b...`.
- Root targeted Ruff: PASS.
- Root `uv lock --check`: PASS, 168 packages resolved.
- Root M1/crop tests: **16/16 PASS** (9 YOLO-export and 7 crop tests).
- Package verifiers: **51/51 PASS** in 89.7 seconds wall time.
- `git diff --check`: PASS.
- Final `graft check .`: PASS, 2,222 nodes and 5,641 edges. Graft map/ask/skeleton/caller queries
  saved 749,409 source tokens during this review, approximately USD 0.40 at the session rate.
- Per the delegated scope, no full historical root `pytest` run was performed.

## Independent attack matrix

### Positive paths and false-reject check

- A temporary real Git repository held three complete run contracts, three distinct arbitrary
  synthetic checkpoint pairs, a clean committed three-entry run registry, three validation-report
  hashes and one clean committed threshold lock. Three complete test reports and three Apple M1
  Pro-shaped latency reports aggregated to PASS without calling the sealed-test logger.
- A second synthetic smoke went through the actual `cmd_evaluate` report-construction path with a
  mocked YOLO result and twenty synthetic `Frame` objects. Its generated test report passed the R3
  validator. The real logger was replaced and no repository or sealed-test file was accessed.
- A third smoke went through the actual `cmd_latency` report-construction path with mocked model,
  timer and MPS synchronization. Its generated latency report passed the R3 validator.
- Valid `FP/image > 1`, per-resolution `FP/image > 1`, FP bootstrap bounds above one and latency
  above one were accepted when their dependent flags remained consistent. These are deliberately
  unbounded above, so R3 did not introduce those false rejections.

### Domain, type and exact-schema attacks

The independent in-memory matrix rejected **240/240** expected-negative cases. It covered:

- negative, greater-than-one, non-finite, boolean, string, list and null mutations across all
  rate-valued fields consumed by aggregation or report gates;
- negative, non-finite, boolean, string, list and null mutations of FP/image and FP bootstrap
  values while retaining their valid unbounded-above domain;
- negative, float and boolean mutations of seeds, image sizes, image counts, AP-small counts,
  UNKNOWN counts, confusion cells, class supports and latency counts;
- missing keys, extra keys and wrong containers at the test-report top level and in weight,
  threshold-lock, operating-point, AP-small, resolution-row, UNKNOWN, confusion, error-sample,
  bootstrap, gate, single-seed-check and class-gate objects;
- equivalent latency top-level/environment schema attacks;
- confusion wrong shape/negative cells, class/AP roster mismatch, support mismatch, UNKNOWN
  count/rate mismatch, reversed bootstrap bounds, `mAP50-95 > mAP50`, inconsistent latency
  ordering and an incorrect latency `passed` flag; and
- mismatched critical/gated/passed flags, unverified/low-support rosters, individual single-seed
  checks and the single-seed summary flag.

A literal JSON `1e999` parsed as a non-finite float and was rejected. A three-seed class/unverified
roster mismatch was rejected before the aggregate output path was created. A `map50=2` report was
also rejected before output creation.

### Short R2 regression recheck

- Duplicate-key/NaN strict parsing tests passed, and an isolated four-candidate threshold lock was
  rejected before the test-access callback.
- A complete self-issued checkpoint contract was rejected before a committed registry existed;
  the exact clean committed registry positive path passed.
- Coherent WP35 source/export label tampering remained rejected.
- The crop missing/extra roster regression remained rejected.
- One checkpoint relabelled as three seeds remained rejected.

## H-4A — FAIL, High: primary metrics and gates are not bound to confusion/AP evidence

`_validate_test_report` validates confusion dimensions and uses ground-truth row totals for class
support/rosters, but it never recomputes the operating-point recall, precision or FP count from the
matrix. It also never reconciles global `map50` with the `per_class_ap50` values. The single-seed
and final checks are recomputed only from the separate reported metric fields, so contradictory
evidence can remain schema-valid.

Two minimal three-seed counterexamples kept every identity, lock, schema and numeric-domain check:

1. Each confusion matrix moved all twenty class-0 ground truths from the class-0 diagonal into the
   BACKGROUND column, meaning all twenty signs were missed. The operating point and class gate
   still claimed recall `1.0` and PASS. Validation and aggregation accepted the reports and emitted
   `all_gates_passed=true`.
2. Each report retained `map50=0.8` while setting the only supported class's AP50 to `0.0`.
   Validation and aggregation again emitted final PASS.

The validator also accepted AP-small `value=1.0` with `classes=0` and `support=0`. AP-small is
report-only under D-05, but this independently disproves the claimed complete cross-field evidence
validation.

### Required repair

1. Recompute class-agnostic hits, misses and false predictions from the confusion matrix; reconcile
   operating-point recall and precision exactly, and reconcile FP/image using the validated image
   count. Bind per-resolution FP totals to the same overall evidence.
2. Reconcile `map50` with the supported `per_class_ap50` aggregate using a documented numerical
   tolerance matching Ultralytics output.
3. For per-class recall, either add validated hit counts generated by the same class-aware matcher
   or otherwise bind each gate row to reproducible primary counts; do not trust a standalone
   reported recall value.
4. Require AP-small zero classes/support to imply value zero, and require positive class/support
   evidence for a non-zero AP-small value.
5. Add complete-report regression attacks for each contradiction and prove failure before output.

## H-5 — FAIL, High: latency evidence is not bound to the final evaluation configuration

The latency validator requires a positive `imgsz`, but aggregation does not require it to equal the
test report's `imgsz` or even to be identical across seeds. More importantly, `cmd_latency` uses a
caller-supplied confidence, but the latency JSON does not record confidence, NMS IoU or a threshold
lock at all. Aggregation can therefore authenticate the weight and Apple M1 Pro shape while being
unable to prove that the timed preprocessing/inference/NMS configuration is the selected final
configuration.

The independent real-Git fixture kept all test reports at `imgsz=1280`, changed all three otherwise
valid latency reports to `imgsz=32`, and retained p95 `40 ms`. All validators accepted the reports
and aggregation emitted `all_gates_passed=true`. This can game the only D-05 latency gate with a
different workload while preserving the approved weight identity.

### Required repair

1. Bind every latency report to the same clean committed threshold lock/candidate as its test
   report and record the exact confidence and NMS IoU used by prediction.
2. Require latency `imgsz`, confidence and NMS to equal the corresponding final test-evaluation
   configuration for the same seed/weight; require the three latency reports to use one consistent
   image size.
3. Add mixed-size, smaller-size, unrecorded/changed confidence and changed-NMS attacks. Each must
   fail before aggregate output creation.

## Evidence boundary and final state

- No model training, real prediction, real latency benchmark, checkpoint creation, upload,
  download, deployment, commit, push or publication occurred.
- No raw sealed-test image, label, export or metric was opened. All registry, lock, report,
  evaluator, latency and aggregate work used temporary synthetic files, mock objects and temporary
  Git repositories.
- The detector test directories/YAML, crop `test.p`, sealed-test access log, real run registry and
  real threshold lock were absent before handoff. No QA process remained running.
- User/PM source and generated artifacts were not edited. Only this independent QA record was
  added.
- Passing the repaired executable controls in a successor review would still establish research/
  simulation evidence only, not Vietnamese deployment accuracy or driving-safety validation.
