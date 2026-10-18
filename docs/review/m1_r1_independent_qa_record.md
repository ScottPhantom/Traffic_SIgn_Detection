# M1-R1 independent QA record

Status: `QA_FAIL_M1_R1_BLOCKERS_REMAIN_REPAIR_REQUIRED`
Reviewer: `Codex independent QA session (did not author M1-R1 and did not act as PM)`
Reviewed at: `2026-10-18T23:39:01+07:00`
Boundary: `QA_OF_M1_R1_PACKAGE_ONLY_NO_TRAINING_NO_SEALED_TEST_ACCESS_NO_UPLOAD_NO_COMMIT_NO_PUSH`
Reviewed checkpoint: `eae9146e471fff261d674a4ec9653ee073301b37`

This append-only record re-reviews the M1-R1 package described by
`docs/review/m1_r1_qa_remediation_report.md`. It preserves the initial independent FAIL record
byte-for-byte (SHA-256 `8c98a5d4d61f2be46c57ed9ea6a953f889896a5c26fb57a7315b2cc79966d169`)
and changes no M1-R1 source, test, manifest, model, dataset, owner record, project memory or
roadmap file.

## Verdict

- **M1-R1: FAIL.** 1 Critical, 3 High, 0 Medium, 1 Low.
- All remediation-report file pins match the reviewed bytes, and every requested mechanical gate
  passes. Several ordinary tamper cases are now correctly rejected.
- The five original findings are not all closed. Independent adversarial tests reproduced four
  trust-boundary bypasses: a malformed committed threshold lock can reach sealed-test logging;
  coherent WP35 source/export label tampering passes the materialised contract; an arbitrary
  checkpoint plus a self-authored run contract is trusted; and one seed can be triplicated into an
  aggregate that reports final PASS. The crop package also still accepts an unexpected extra file.
- **Do not start the pilot, create a final threshold lock, run sealed-test evaluation or promote a
  D-05 candidate from M1-R1.** PM must issue a successor repair and request another independent QA
  review.
- This QA verdict does not revoke Gate 0 or the Owner's D-05 decisions. It says only that the
  executable M1-R1 enforcement layer does not yet implement those decisions fail-closed.

## Pin and package readback

- Remediation report SHA-256:
  `6a7b399db31d010cb0769bddbab799fb77d3b496569d3ddcfc25fe4c58c756bf`.
- Every hash in its **Bound R1 files** table matches the current byte:
  - YOLO builder `fe1946cf...`, crop builder `80f4a5e6...`;
  - detector contract `3647de5a...`, metrics `5be05038...`, CLI `e9d818fe...`;
  - detector tests `a1adc524...`, root tests `189afb98...` and `5048cc07...`;
  - M1 manifest `8a8df5f2...`, crop manifest `6526844b...`.
- Approved local `models/pretrained/yolo11s.pt` still has SHA-256
  `85a76fe86dd8afe384648546b56a7a78580c7cb7b404fc595f97969322d502d5`, is ignored by
  `/models/pretrained/`, and is not Git-tracked.
- The sealed-test detector directory, `data_test.yaml`, crop `test.p` and sealed-test access log
  were absent before and after the review. QA did not open or export the sealed test.

## Executable gates

- Root Ruff over `src`, `tests` and both M1 builders: PASS.
- Root `uv lock --check`: PASS, 168 packages.
- Targeted root M1/crop tests: **15/15 PASS**.
- Package verifiers: **51/51 PASS** in 97.5 seconds wall time.
- Detector Ruff and `uv lock --check`: PASS, 66 packages.
- Detector tests: **11/11 PASS**.
- `YOLO_OFFLINE=true uv run python -m m1.cli check`: PASS; it reported commit `eae9146`, the
  expected detector lock, Torch `2.14.1`, Ultralytics `8.4.172`, MPS available, export manifest
  `8a8df5f2...` and test seal `afa03d4b...`.
- Full historical root tests: the serial repo-writing phase passed **126/126**. The parallel phase
  was stopped at the Owner's direction at about 85 percent after only the known stale WP26/WP27
  successor-absence failures had appeared. Exit `130` is the requested interruption, not an M1-R1
  result. No final full-suite count is claimed.
- Final `graft check .` after this record was added: PASS; the wiring graph remains in sync.

## Finding re-review

### C-1 — FAIL, Critical: malformed clean threshold locks can bypass the sealed-test preflight

#### Controls that now work

- Missing `--conf`, missing `--threshold-lock`, wrong finite confidence and wrong finite NMS IoU
  all stop inside `_evaluation_preflight` before test logging, test-contract access or model
  construction.
- An isolated real Git repository confirmed that untracked and dirty threshold locks are rejected
  as not committed and clean.
- `--bootstrap` is mandatory for a sealed-test report.

#### Remaining bypasses

`contract.bind_threshold_lock` checks only the set of candidate seeds. It does not require list
length three, unique candidate seeds or unique candidate weight hashes. A clean, Git-tracked lock
with four candidates, including a duplicate seed, was accepted.

The function also converts lock confidence/NMS values to floats without requiring finite,
in-range numbers. `_evaluation_preflight` compares them with:

```text
abs(argument - locked_value) > 1e-12
```

For a locked `NaN`, that comparison is false. A synthetic no-data attack supplied locked NaN
values with ordinary finite CLI values; preflight accepted them, wrote the access-log event and
reached the test-contract call. No real test data or model was used in this attack.

The binding also does not enforce the lock's recorded export-manifest hash or
`sealed_test_seen=false` state.

#### Required repair

1. Parse the lock with a strict JSON loader that rejects NaN/Infinity and duplicate keys.
2. Require exactly three candidates, exactly one per approved seed, three distinct weight hashes,
   finite confidence/NMS in `[0,1]`, and a schema with no unknown/missing fields.
3. Bind and verify the current export-manifest hash, test seal, `sealed_test_seen=false`, each val
   report hash, run-contract hash and candidate weight hash.
4. Compare only finite validated numbers, and add clean-committed attacks for duplicate candidate,
   duplicate weight, NaN/Infinity, stale export hash and already-seen test state. Every case must
   stop before access logging.

### H-1 — FAIL, High: coherent WP35 label tampering remains trusted

#### Controls that now work

On an isolated materialised train/val copy, the verifier rejected:

- changed `data.yaml`;
- a changed raw exported label;
- a changed WP35 exported label by itself;
- raw-image symlink redirection and changed raw-image bytes;
- changed WP35 image bytes;
- an extra label and a missing image.

#### Remaining bypass

`verify_materialised` derives the expected WP35 exported label from the current ignored
`data/processed/wp35_enrichment/labels/*.txt`, but does not compare that source label byte to the
`label_sha256` pinned in WP35 lineage. In a temporary WP35 source and export copy, QA changed the
first coordinate in `wp35_15_0000.txt` in both places. The materialised verifier returned
`valid=true` with no errors. The analogous image path is protected because image bytes are
compared with the lineage hash.

#### Required repair

Before deriving any expected WP35 YOLO label, verify both the WP35 source image and source label
against the lineage hashes. Reject on the source mismatch even if the exported label is changed
coherently. Add a regression attack that mutates the ignored source label and the materialised
label together.

### H-2 — FAIL, High: an arbitrary checkpoint can self-issue a trusted run contract

#### Controls that now work

- Arbitrary/non-approved training paths, a missing approved pretrained file and modified bytes at
  the approved path are rejected.
- A genuine weight changed after its recorded hash is rejected.
- The run weight must be named `best.pt` or `last.pt`, live under a `weights/` directory, have
  status `TRAINED` and use an approved seed.

#### Remaining bypass

`bind_run_weights` treats a neighbouring `run_contract.json` as its own trust root. QA created an
arbitrary `best.pt`, calculated its hash and wrote a minimal self-authored contract with
`status=TRAINED` and seed `20261018`. The binding accepted it. The test suite currently constructs
the same kind of self-authored contract as its positive case.

The binding does not require an approved-model entry, governed export/lock hashes, detector
environment, complete training arguments, a run directory under an approved results root, or an
independently pinned run attestation.

#### Required repair

Validate the complete run-contract schema and every M1 invariant, but do not use that mutable file
as the sole trust anchor. Add an append-only/committed run attestation or registry that pins the
run-contract hash, approved pretrained hash, export manifest, detector lock, seed and produced
weight hashes. Threshold-lock candidates must bind the run-contract/attestation hash as well as
the weight hash. Reject a self-consistent arbitrary checkpoint/contract pair in regression tests.

### H-3 — PARTIAL, Low: required crop files are protected, but the output roster is not exact

The verifier independently rejected missing, byte-modified and symlinked versions of each of:

- `train.p`, `valid.p`;
- `train_index.csv`, `valid_index.csv`;
- `signnames.csv`.

However, adding `unexpected.bin` to the materialised output still returned `valid=true`. This does
not alter the five consumed files, so it is Low, but it contradicts the initial required repair
and the R1 claim of an exact materialised package.

#### Required repair

Enforce an explicit output roster and reject extras. If sealed `test.p` and its index must later
coexist, define a separate post-final-evaluation roster/state rather than accepting arbitrary
files.

### M-1 — FAIL, High: one actual seed can be triplicated into a final PASS

#### Controls that now work

- Single-seed `gate_report` and `cmd_evaluate` cannot emit a final verdict.
- The aggregate rejects an absent/duplicate claimed seed, changed report weight hash, changed
  latency weight hash and inconsistent threshold-lock hash among the three test reports.
- Genuine `cmd_evaluate` report construction includes a named project AP-small method,
  precision/recall, per-class AP/recall/support, resolution breakdown, confusion matrix, error
  stems, UNKNOWN false recognition, group bootstrap and unverified/low-support class lists.

#### Remaining bypasses

`cmd_aggregate` does not compare a report's claimed seed with the seed returned by
`bind_run_weights`, does not require three distinct weights/run directories, and performs the same
omission for latency reports. QA supplied three test reports claiming the three approved seeds and
three matching latency reports, all bound to the same one-seed checkpoint. The aggregate returned
`all_gates_passed=true` and published the three-seed list.

The same accepted inputs used a fake threshold-lock hash that did not identify an actual clean,
tracked lock. The test reports omitted resolution, confusion, error samples, UNKNOWN and bootstrap
fields, yet aggregation still passed. A latency report whose environment explicitly did not
verify Apple M1 Pro was accepted because only `device == "mps"` is enforced.

#### Required repair

1. For every test and latency report, require `report.seed == bind_run_weights(...).seed`, then
   require three distinct approved seeds, weights, run directories and run attestations.
2. Resolve and validate one actual clean committed threshold-lock path/hash and require every test
   report to bind that artifact and its correct per-seed candidate.
3. Strictly validate the complete D-05 report schema and reject absent/null bootstrap, resolution,
   confusion, error, UNKNOWN, AP-small-method, unverified-class or support evidence.
4. Capture and validate a stable Apple M1 Pro hardware identity in latency reports; `device=mps`
   alone is insufficient.
5. Add a regression case that triplicates one checkpoint while relabelling report seeds; it must
   fail before writing an aggregate.

## Evidence boundary

- No model training, prediction, latency benchmark, checkpoint creation, upload, download,
  deployment, commit, push or publication occurred.
- No raw sealed-test image, label, export or metric was opened. All sealed-test-ordering attacks
  used mocks or isolated temporary Git repositories.
- All tamper attacks used temporary copies. User/PM source and generated artifacts were not edited.
- Passing unit tests and 51/51 verifiers establish only their exercised paths; the successful
  attacks above are direct counterexamples to an M1-R1 PASS.
- Even after repair, DATASET01 group truth remains AI-inferred, validation is small/shifted,
  22 classes have no sealed-test evidence, and low-light/night performance remains unknown.
