# D1 L4 capacity successor R3 — independent QA record

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)  
Status: **INDEPENDENT_QA_FAIL — APPEND-ONLY SUCCESSOR REQUIRED**  
Reviewer: `Codex independent source-QA session`  
Boundary: `SOURCE_AND_SYNTHETIC_ATTACK_QA_NO_COLAB_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL: 0 Critical, 0 High, 1 Medium, 0 Low.**

R3 closes both exact R2 findings at their original attack surfaces. Effective-batch replay now
allows a full sequence or one final partial batch while rejecting a partial-only sequence, any
non-final partial, and multiple partials. Execution JSONL rejects integer/boolean equality
confusion for every field, duplicate/non-finite JSON, extra fields and invalid chronology. The R3
wrapper also survives a direct predecessor-validator bypass probe, and the seven-file source roster
is applied during independent anchor replay.

One nested type/value gap remains. R3 checks the result-side attempt identity types but not the
plan/telemetry attempt identities, so plan `repeat: true` remains equal to integer repetition `1`
in the inherited semantic replay. It also checks that telemetry `schema_version` is an integer but
does not require the value to equal `1`; integer version `2` passes. These two manifestations were
accepted together by the real R3 type-hardening function and then by the inherited plan/attempt
semantic replay. R3 remains NO-GO and must be superseded append-only.

## Frozen bytes reviewed

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_l4_capacity_r3.py` | `ab31982fdb14a56727c89b020e04bcc15822b4051e7608dae60e41d96f20d768` |
| `detector/colab/verify_d1_l4_capacity_r3.py` | `663227f9b5666296792ee14a96d2c8e304b885df0a8071e3be282e3da1481281` |
| `tests/test_d1_l4_capacity_r3.py` | `90b810c6d7c3f1bf1b68d93c8c03b19d0145db7a4c23c6116a26dab2124f7641` |
| `docs/review/d1_l4_capacity_r3_qa_remediation_report.md` | `747f38281ed385c09d385512a4e47e2a9aa3b4dee4741bb8eb423abd20162656` |

The R1 and R2 independent QA records remain byte-identical at SHA-256
`37ce181cee90df4c020fc81a3558825226201b8368e6220903c4b1721b3398dd` and
`94c9c2a00fd3f5c6865fbfc463c7c9b1d6f392c79e474cd06f0d4945a2ff4dce`. Their historical FAIL
verdicts were not modified. Existing PM changes and unrelated untracked artifacts were outside this
QA scope and were preserved.

## Finding

### M-1 — Nested plan/telemetry identity and schema values are not type/value strict

`verify_d1_l4_capacity_r3.py:35-84` applies exact types to top-level governance fields, result
identity fields, result OOM, and selected train arguments. It does not type-check the corresponding
`plan["roster"]` or `telemetry["attempt"]` identity fields. The inherited R1 verifier compares those
dictionaries with Python equality, under which boolean `true` equals integer `1`.

The same function requires telemetry `schema_version` to have type `int` at line 59, but unlike the
top-level artifacts at lines 53-54, it never requires that integer to equal version `1`. The
inherited attempt verifier checks only that the telemetry key exists, not its value.

An independent minimal artifact tree containing plan roster `repeat: true`, integer result
`repeat: 1`, and telemetry `schema_version: 2` produced:

```text
nested_plan_repeat_bool_and_telemetry_schema_2 ACCEPTED
r1_semantic_plan_replay_repeat_bool ACCEPTED {'attempt_id': 'b04_w04_r01', 'batch': 4, 'repeat': True, 'workers': 4}
r1_attempt_repeat_bool_telemetry_schema2 ACCEPTED 1
```

This does not demonstrate sealed-test access or a model-quality error, and all measured batch sizes
remain valid. It does demonstrate that the claimed type-strict evidence schema can verify a
non-canonical plan identity and unsupported telemetry schema version.

**Required successor repair:** validate exact types and expected values for every plan roster and
telemetry attempt identity before delegation; require telemetry `schema_version` to be exact integer
`1`; add full-chain attacks using boolean `repeat` on either side and integer schema versions other
than `1`.

## R1/R2 attack replay

| Attack class | Independent R3 result |
| --- | --- |
| Effective batch: one full step | Accepted as valid |
| Effective batch: one partial step only | Rejected because no full planned batch was observed |
| Effective batch: full plus one final partial | Accepted as valid |
| Effective batch: multiple/non-final partials | Rejected |
| Ultralytics effective trainer batch differs from plan | Rejected by inherited live R2 callback |
| Loader wait omitted from throughput | Rejected: injected timing preserved `compute=2`, loader gap `3`, total `5` seconds |
| Predecessor-validator delegation bypass | Rejected: replacing R2 effective-batch validator did not bypass the R3 sequence rule |
| Fake full package | A complete 24-attempt/56-file package with seven-source roster, fake Git/model/data, extra optimizer and invalid batch-16 evidence was rejected at the fake Git commit anchor |
| Missing R3 files from source roster | Rejected; five-file R2 roster was not accepted as R3 |
| Extra optimizer | Rejected by inherited exact train-argument roster |
| Generic failure relabelled OOM | Rejected; controlled CUDA OOM remained accepted |
| SQLite root/ancestor/file symlink and hard link | All rejected before an external write; external row count remained zero |
| Execution duplicate/non-finite/extra/chronology attacks | Rejected |
| Execution exact type matrix | Wrong-type schema, status, timestamp, plan/report hash and sealed marker values were all rejected |
| Nested plan/telemetry type-value attack | **Accepted — M-1** |

The R3 source-at-commit design extends the exact roster to seven files: the governed capacity
policy plus the R1, R2 and R3 runner/verifier pairs. A plan omitting the R3 pair is rejected, the
claimed repository must be the governed checkout, and each current source hash must match
`git show <commit>:<path>`. Since the candidate is intentionally uncommitted pending source QA, a
positive clean-commit R3 package cannot yet be produced; the current FAIL prevents that next gate.

## Preserved controls

- The fixed experiment remains 24 isolated attempts:
  `batch {4,8,12,16} × workers {4,8} × repeats {1,2,3}`.
- Eligibility still requires all three repetitions, throughput CV ≤ 5%, and peak VRAM ≤ 80%, which
  preserves at least 20% measured headroom.
- Selection remains non-cherry-pick and deterministic: within 95% of best median throughput, choose
  smaller batch, fewer workers, then lower VRAM.
- OOM evidence uses the closed R2 predicate; generic loader, bundle, hash and runtime errors stay
  `FAILED`.
- SQLite uses no-follow exclusive creation plus component, file-type, hard-link and inode checks on
  later opens.
- Static inspection found no `export-test`, `--final-eval`, Pilot R3 import, pilot notebook route or
  test-export path in R3 production source. The capacity work remains train/val-only and independent
  of the live Pilot R3.
- All observed governance markers remained `sealed_test_accessed=false`; the sealed test was not
  opened.

## Mechanical evidence

| Check | Result |
| --- | --- |
| Root R1-R3 targeted tests | PASS, `38 passed, 1 skipped`; skip is root env without Torch |
| Complete detector tests | PASS, `105 passed` |
| Scoped Ruff over reviewed R1-R3 source/tests | PASS |
| Root lock | PASS, `66 packages` |
| Detector lock | PASS, `66 packages` |
| `git diff --check` before record | PASS |
| Graft freshness/source trace | PASS, graph in sync |
| Effective-batch sequence matrix | PASS |
| Execution exact-type field matrix | PASS |
| Full fake 24-attempt package | Rejected at independent Git anchor |
| Nested plan/telemetry type-value probe | **ACCEPTED — Medium blocker** |

Green unit and mechanical checks cannot reverse the accepted negative test.

## Gate disposition

| Gate | Disposition |
| --- | --- |
| L4 capacity R3 source candidate | **FAIL** |
| Commit/push or notebook pin | **NO-GO** |
| Colab capacity execution | **NO-GO** |
| Capacity result/configuration selection | **NO-GO** |
| Owner final-config approval | **NO-GO pending append-only successor + independent QA PASS** |
| Current Pilot R3 | Unchanged; continue independently |
| Sealed-test access/final evaluation | **NO-GO / not accessed** |

