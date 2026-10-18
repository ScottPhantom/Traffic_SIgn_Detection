# M1-R2 independent QA record

Status: `QA_FAIL_M1_R2_FINAL_REPORT_DOMAIN_BLOCKER_REPAIR_REQUIRED`
Reviewer: `Codex independent QA session (did not author M1-R2 and did not act as PM)`
Reviewed at: `2026-10-18T23:50:39+07:00`
Boundary: `QA_OF_M1_R2_PACKAGE_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `eae9146e471fff261d674a4ec9653ee073301b37`

This append-only record re-reviews the M1-R2 package described by
`docs/review/m1_r2_qa_remediation_report.md`. It preserves the initial and R1 independent FAIL
records byte-for-byte. It changes no M1 source, test, manifest, model, dataset, Owner record,
project memory or roadmap file.

## Verdict

- **M1-R2: FAIL.** 0 Critical, 1 High, 0 Medium, 0 Low.
- All ten R2 file pins match the reviewed bytes. The requested mechanical gates pass, and the
  prescribed attacks confirm that R2 closes the five concrete R1 bypasses.
- One new final-report integrity blocker remains. `cmd_aggregate` accepts finite but physically
  impossible metric values without range or semantic validation. An isolated three-run fixture
  with a real clean committed registry and threshold lock used `mAP=2`, recall `=2`,
  `FP/image=-1` and `latency_p95_ms=-5`; aggregation accepted all three reports and emitted
  `all_gates_passed=true`.
- **Do not start the pilot, open the sealed test, or use M1-R2 to issue a D-05 PASS.** PM must
  validate the complete numeric/report domain, add adversarial regression coverage, and request a
  successor independent review.
- This verdict does not revoke Gate 0 or the Owner's D-05 decisions. It says only that the M1-R2
  final aggregation boundary can still turn invalid report evidence into a final PASS.

## Pin and package readback

- R2 remediation report SHA-256:
  `8fbf4ee7cfcc681bd3b743b94853a3344aa3627d7ad10c06256e51ea039c4ab3`.
- R1 independent QA input SHA-256:
  `feaad72c4dfdf237e97c7d40c65a15e796bf889a50210cab2b9bad067c0faa84`.
- Every hash in the remediation report's **Bound R2 files** table matches the current byte:
  - YOLO builder `3b52c63f...`, crop builder `1f1bfac3...`;
  - detector contract `cdf2ccba...`, CLI `37b88579...`, metrics `5be05038...`;
  - detector tests `7adaa700...`, root tests `8ccc91ec...` and `a5e64bc1...`;
  - M1 manifest `8a8df5f2...`, crop manifest `6526844b...`.
- The reviewed branch is `DEV/Rroject_Pineline`; HEAD and `origin/DEV/Rroject_Pineline` are both
  `eae9146e471fff261d674a4ec9653ee073301b37`.

## Executable gates

- Root targeted Ruff: PASS.
- Root `uv lock --check`: PASS, 168 packages resolved.
- Root M1/crop tests: **16/16 PASS** (9 YOLO-export and 7 crop tests).
- Package verifiers: **51/51 PASS** in 90.1 seconds wall time.
- Detector Ruff: PASS.
- Detector `uv lock --check`: PASS, 66 packages resolved.
- Detector tests: **14/14 PASS**.
- `m1.cli check`: PASS. It reported the expected export manifest `8a8df5f2...`, test seal
  `afa03d4b...`, detector lock `5d56642a...`, Apple M1 Pro, `arm64` and MPS available.
- `git diff --check`: PASS.
- Final `graft check .`: PASS, 2,206 nodes and 5,597 edges. Graft map/ask/skeleton calls saved
  700,341 source tokens during this review; Graft remained an orientation and blast-radius aid,
  not evidence of semantic correctness.
- Per the delegated scope, no full historical root `pytest` run was performed.

## R2 remediation re-review

### C-1 — PASS for the prescribed threshold-lock attacks

An isolated no-data preflight fixture rejected all of the following before sealed-test logging:

- duplicate JSON keys, `NaN` and Infinity;
- boolean, negative and greater-than-one confidence values;
- four candidates and duplicate seed/weight candidates;
- stale export hash, wrong test seal and `sealed_test_seen=true`;
- wrong run-contract and run-attestation bindings;
- missing and byte-tampered validation reports.

The exact three-candidate positive fixture bound successfully. The log callback remained uncalled
for every invalid case. No test contract, image, label, model or prediction path was used.

### H-1 — PASS for coherent WP35 source/export label tampering

The targeted regression passed independently. In a temporary source/export fixture, changing the
WP35 source label and the corresponding exported label together was rejected because the source
label no longer matched the lineage SHA-256.

### H-2 — PASS for the prescribed checkpoint/registry attacks

In a temporary real Git repository, QA built a complete self-consistent `run_contract.json` next
to arbitrary `best.pt` and `last.pt` bytes. The weight was rejected with no registry, with an
untracked registry, with a staged-but-uncommitted registry, with a dirty registry, and with a clean
committed registry whose attestation was tampered. The same checkpoint bound successfully only
after its exact canonical attestation was present in a clean committed registry.

### H-3 — PASS for the prescribed crop-package attacks

A positive synthetic package with the exact five-file roster verified. Independent variants then
rejected a missing `train.p`, a byte-tampered `valid_index.csv`, a symlinked `signnames.csv`, and an
extra `unexpected.bin` roster member.

### M-1 — PARTIAL: identity and completeness controls pass; numeric domain fails

The isolated three-run happy path used three distinct registered weights, a clean committed
threshold lock with three live validation-report hashes, three complete synthetic test reports and
three Apple-M1-Pro-shaped latency reports. It aggregated successfully without calling the
sealed-test access logger.

The following negative cases were correctly rejected:

- one checkpoint relabelled as all three seeds;
- duplicate run directory and duplicate run attestation;
- missing and fake threshold locks;
- missing resolution, confusion, error-sample, UNKNOWN, AP-small and class-gate evidence;
- null bootstrap evidence; and
- fake Apple hardware identity.

## H-4 — FAIL, High: invalid numeric evidence can produce a final D-05 PASS

`_validate_test_report` checks field presence and a few container shapes, but it does not validate
the types, finiteness, ranges or cross-field consistency of the metric values. Likewise,
`_validate_latency_report` authenticates the claimed platform shape but does not require a finite,
non-negative `p95_ms`. `cmd_aggregate` then averages those unvalidated values and compares them
directly with the D-05 gates.

The independent counterexample retained all R2 identity controls: three distinct run hashes,
directories and attestations; a clean committed registry; one clean committed threshold lock;
correct per-seed lock candidates; complete Q6-shaped objects; and matching Apple M1 Pro latency
bindings. QA changed only the report numbers to finite but impossible values:

```text
map50 = 2.0
map50_95 = 2.0
ap_small.value = 2.0
operating_point.agnostic_recall = 2.0
operating_point.fp_per_image = -1.0
per-class recall = 2.0
latency p95_ms = -5.0
```

The command returned `all_gates_passed=true`. This is High because the only final-verdict layer can
promote invalid evidence to PASS even though run and threshold identities are genuine.

### Required repair

1. Enforce exact nested schemas and reject unknown as well as missing fields for test and latency
   reports.
2. Recursively reject booleans where numbers are required, non-finite values, and values outside
   their physical domains: AP/mAP/precision/recall/rates in `[0,1]`, counts/supports as non-negative
   integers, FP/image and latency as finite non-negative numbers, and valid confidence/NMS values.
3. Cross-check per-seed gate rows against the primary report metrics and recompute every aggregate
   gate only from validated inputs.
4. Add regression attacks for negative, greater-than-one, exponent-overflow/non-finite and
   type-confused values at every field consumed by `_mean_std` or a class/global gate.
5. Re-run the isolated positive registry/lock/report fixture and prove the invalid variants fail
   before any aggregate file is written.

## Evidence boundary and final state

- No model training, prediction, latency benchmark, checkpoint creation, upload, download,
  deployment, commit, push or publication occurred.
- No raw sealed-test image, label, export or metric was opened. All threshold, registry, report and
  aggregate attacks used temporary synthetic files and temporary Git repositories.
- The detector test directories/YAML, crop `test.p`, sealed-test access log, real run registry and
  real threshold lock were absent before handoff. No QA process remained running.
- User/PM source and generated artifacts were not edited. Only this independent QA record was
  added.
- Even after repair, DATASET01 group truth remains AI-inferred, validation is small/shifted,
  22 classes have no sealed-test evidence, and low-light/night performance remains unknown. A
  passing experiment would be research/simulation evidence, not driving-safety validation.
