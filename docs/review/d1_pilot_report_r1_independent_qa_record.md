# D1 YOLO11s pilot quality report R1 — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, read-only remediation audit, fail-closed  
Verdict: **PASS**

## Scope and preserved history

This append-only R1 review covers the remediated `docs/review/d1_pilot_report.md` and the same
immutable validation, latency, registered-run and source evidence reviewed in
`docs/review/d1_pilot_report_independent_qa_record.md`.

The earlier record remains authoritative for report SHA-256
`53470f8cf33e899205f9405671c47b58ec435bc189891b40425b61deb3930c3f` and its **FAIL** verdict. It
was not edited or replaced. This R1 record reviews only the current report SHA-256:

`62a33ea315466b84248dac4c3f826187aab7e8771565ac5e49cecf4f3bf9196d`

QA did not train or resume a model, run evaluation or latency measurement, open/export/read the
sealed test, change a threshold or gate, modify any report/run artifact, commit, push, upload, or
authorize another seed. The only project change made by QA in this remediation pass is this
append-only record.

## Immutable evidence identities

| Artifact | SHA-256 / identity |
| --- | --- |
| `eval_val.json` | `e6fe9eb58e4d06e3815d94be477f5b450625042c25b08995c1217ffd26dc8895` |
| `latency_mps.json` | `54a4d268890013f90140529b3ea31c21462d38f38e8596e98ca7e7510a8af01a` |
| `best.pt` | `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633` |
| `last.pt` | `75ada6ba44804252c65e6ec76660511e0cc6ea69ee164c766055033dac11ea25` |
| `run_contract.json` | `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88` |
| committed run registry | `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9` |
| canonical run attestation | `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` |
| recorded source commit | `0f5ddb174beba8678430cf2329d124fde6cfa2b8` |
| prior append-only FAIL record | `1bd0f59ecb504d78f3807fac56de74ac6639dff014d890f7d58f9d1d18892ce8` |

The artifact hashes did not change during remediation. The production registered-weight binder
continues to accept the run and reproduces the exact seed, weight, contract, registry and canonical
attestation identities above.

## Closure of prior findings

### QA-D1-PILOT-REPORT-001 — CLOSED

PASS. The report still lists the exact 35 zero-support validation keys, but now reconciles them with
the approved data design:

- 13 test-bearing classes with no validation support;
- 22 already documented train-only classes with neither validation nor test support.

The two sets are disjoint, their union equals the artifact's 35-key `unverified_classes` roster,
and there are no extra or missing keys. The report now explicitly says that this is an existing
governance limitation, not a newly discovered coverage discrepancy. It no longer uses the expected
35-class absence as a new NO-GO reason.

The remaining statement that these classes were not used to select the model or claim a class gate
is bounded to class-specific selection evidence: zero-support keys contribute no GT support,
per-class AP or class gate. The global class-agnostic FP/image metric still counts every unmatched
detection irrespective of predicted class, as the reviewed metric code requires.

### QA-D1-PILOT-REPORT-002 — CLOSED

PASS. The report now states all four required facts without overclaim:

- NMS IoU `0.70` was fixed by the evaluation command;
- the selector searched only its confidence grid and chose `0.15` conditional on that NMS value;
- NMS `0.70` is not claimed as validation-selected;
- joint confidence/NMS selection remains a prerequisite before a final three-seed threshold lock.

This matches source commit `0f5ddb1`: `select_threshold` searches confidence values 0.05 through
0.95 at increments of 0.05, while `cmd_evaluate` supplies one caller-selected NMS value. The pilot
decision is correctly scoped as NO-GO for the unchanged fixed-NMS configuration, not as a completed
D-05 threshold lock.

### Validation execution-source limitation — CLOSED by explicit disclosure

PASS. The latency paragraph now attributes commit `0f5ddb1` and the 54 dirty/untracked paths only
to the latency artifact, which actually contains those fields. It explicitly states that
`eval_val.json` contains neither an execution-environment/source-checkout receipt nor the candidate
confidence-grid curve, and identifies the bound model/artifact hashes as the available validation
reproducibility boundary.

That wording correctly limits the claim. QA verified the confidence-selection algorithm and the
selected output's internal arithmetic, but did not independently recompute the minimizer from raw
predictions because the curve is not retained.

## Revalidated measurements and decision boundary

All unchanged measurements remain consistent with the immutable JSON artifacts:

- 376 validation images, 560 GT boxes, 480 class-agnostic TP and 207 FP;
- confidence 0.15, recall `0.8571`, precision `0.6987`, FP/image `0.5505`;
- mAP50 `0.8292`, mAP50-95 `0.5888`, AP-small `0.2819` over 213 boxes/13 classes;
- group-bootstrap intervals `[0.7513, 0.9615]` for recall and `[0.2499, 1.0820]` for FP/image;
- portrait row: 39 images, 29 GT, 7 TP, 37 FP, recall `0.2414`, FP/image `0.9487`;
- exactly three supported critical classes, all failing: 7, 32 and 41;
- UNKNOWN diagnostic: 6 recognized-as-known of 10, rate 0.60;
- Apple M1 Pro/MPS latency at 1280, batch 1, 50 warm-up and 300 measured iterations: p95
  `47.30` ms at confidence 0.15 and fixed NMS IoU 0.70.

The single-seed report does not claim a D-05 final verdict. Its interim NO-GO remains supported by
independent validation failures even after the coverage wording correction: FP/image exceeds 0.30,
all three supported critical-class references fail, portrait behavior is poor, and NMS has not been
selected on validation. It does not lower a gate, create a threshold lock or approve a corrective
option.

## Sealed-test and validation checks

- exact current report hash: PASS;
- immutable eval/latency/run hashes: PASS;
- production registered-weight binding: PASS;
- 13+22 coverage partition: PASS;
- fixed-NMS/confidence-selection wording: PASS;
- execution-source/candidate-curve limitation: PASS;
- numeric, per-class, resolution, bootstrap, error-sample and latency consistency: PASS;
- single-seed/no-final-verdict and simulation-only boundaries: PASS;
- Graft freshness: `OK`, wiring graph in sync;
- sealed test: not accessed by QA; no governed access-log entry, exported test directory or test
  metric was observed in the reviewed scope.

No model test suite was run because this task prohibited evaluation/test activity and changed no
source code. QA used strict JSON parsing, SHA-256 checks, source inspection, production read-only
binding, arithmetic recomputation and governed-document comparison.

## Verdict and authorization boundary

**PASS.** The current report at SHA-256
`62a33ea315466b84248dac4c3f826187aab7e8771565ac5e49cecf4f3bf9196d` accurately reports the
reviewed single-seed validation and M1 Pro latency evidence, closes both prior reporting blockers,
keeps the validation provenance limitation explicit, preserves the sealed-test boundary and does
not overstate a final verdict.

This PASS approves only the pilot report at the exact hash above. It does not authorize seeds
`20261019` or `20261020`, a threshold lock, a D-05 gate change, sealed-test access, training,
evaluation, deployment, publication, commit or push. The accepted interim state remains **NO-GO
for the unchanged pilot configuration**; next action is limited to an Owner decision package using
validation-only evidence.
