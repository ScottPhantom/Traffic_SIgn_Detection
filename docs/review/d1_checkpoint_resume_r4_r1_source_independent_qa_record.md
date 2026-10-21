# D1 checkpoint/resume R4-R1 runtime-evidence source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

Predecessor verdict: `d1_checkpoint_resume_r4_source_independent_qa_record.md` remains immutable.

## Verdict

**FAIL / NO-GO for source release, the R4 live smoke, and the 100-epoch pilot.**

R4-R1 correctly repairs the two demonstrated acceptance bypasses from the first review:

1. `verify_live_state` now compares the complete ordered archived `execution_attempts` list with
   the live JSONL attempts, so independently valid but different digest pairs fail closed.
2. Attempt timestamps are parsed as timezone-aware datetimes and must satisfy
   `fresh_start < fresh_finish <= resume_start < resume_finish`.

The new regression tests cover different archived digest pairs, malformed/naïve timestamps and
overlapping chronology, and all pass. However, three additional source/package gates identified in
the predecessor QA remain unchanged: archived execution JSON still has ambiguous parsing, critical
preflight rejection paths are not durably recorded, and the live verifier does not bind its claimed
checkpoint hash to the current recovery pointer. The package therefore remains unfit to pin or run
on Colab.

## Repaired findings

### R1 — Exact archive/live runtime attempt equality: PASS

`verify_r4_result_archive` returns the archived ordered attempts. `verify_live_state` now requires
that list to equal the live JSONL list, in addition to comparing the validation summary. A targeted
regression supplies two valid evidence sets with identical summaries but different runtime digest
pairs and confirms rejection.

### R2 — Parsed full chronology: PASS

All four attempt timestamps are parsed with `datetime.fromisoformat`, naïve timestamps are rejected,
and the complete fresh/resume interval ordering is enforced. Malformed, naïve and overlapping
fixtures fail closed. The earlier strings `a/z/b/a` are no longer accepted.

## Remaining blocking findings

### B1 — Archived execution JSON remains non-strict

`verify_r4_result_archive` still parses the archived `colab_execution.json` with plain
`json.loads(handle.read())`. Unlike `read_attempts` and repository `strict_json`, this permits
duplicate object keys with last-key-wins semantics and accepts Python's non-finite JSON constants.
The file carrying the archived runtime evidence therefore has an ambiguous schema.

Required repair: parse archive bytes with duplicate-key and non-finite-constant rejection. Add
archive-level tests for duplicate `execution_attempts`, `runtime_identity`, `schema_version`, `NaN`
and `Infinity` values.

### B2 — Critical R4 preflight failures remain non-durable

Boot-ID reading/validation, bundle hashing, prior-attempt parsing, same-runtime rejection and
run-binding comparison all execute before delegation to the R1 guarded lifecycle. Exceptions from
these checks escape without a terminal append-only failure record or durable preflight log. In
particular, the expected same-runtime refusal leaves no persistent record explaining why recovery
did not proceed.

Required repair: record these rejections in a separate append-only/fsynced preflight audit artifact,
without overwriting the valid fresh attempt. Add direct tests for same runtime, malformed/missing
boot ID, malformed prior JSONL and run-binding mismatch.

### B3 — Current checkpoint pointer is not rebound during live verification

`verify_live_state` compares stored checkpoint-binding strings between the two attempt sources, but
never calls `checkpoint_binding(state_dir)` or the pinned checkpoint-store verifier. A changed,
missing, linked or malformed `recovery/latest.json` can therefore disagree with the live and
archived evidence while the R4 live verifier still accepts the stored claim.

Required repair: verify `recovery/latest.json` and its referenced checkpoint manifest/files through
the pinned recovery verifier, then require its binding to equal both attempts and the archived
execution. Add changed/missing/linked/malformed pointer and checkpoint-manifest tests.

## Positive properties retained

- Append-only successor relationship to the pinned predecessor remains intact.
- Runtime evidence retains only the declared schema and SHA-256 digest, not the raw boot ID or
  browser/account/runtime secrets.
- Equal, missing and malformed runtime digests fail in direct validation.
- Fresh/resume status order and equal run/checkpoint claims are enforced.
- Archive/live runtime digest substitution now fails closed.
- Malformed, naïve, reversed and overlapping attempt chronology now fails closed.
- Notebook remains unexecuted, defaults to fresh mode and is blocked by
  `CODE_COMMIT = "PENDING_AFTER_QA"`.
- No sealed-test command is present and successful evidence requires
  `sealed_test_accessed=false`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R4-R1 + R3 root tests | PASS, **26/26** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52**, verified in the same QA workflow before R4-R1 |
| `git diff --check` | PASS |
| Different valid archive/live digest pairs | PASS: rejected |
| Malformed/naïve/overlapping timestamps | PASS: rejected |
| Duplicate/non-finite archived execution JSON | **FAIL: parser remains permissive** |
| Durable same-runtime/preflight refusal evidence | **FAIL: absent** |
| Current recovery pointer/checkpoint rebinding | **FAIL: absent** |

Mechanical tests do not cover or override the remaining package-verification gaps.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r2.py` | `399114f11beb3816d05dfa689524fb3bce7f131f1d6438b4ef34a106ca0044a0` |
| `detector/colab/d1_train_checkpoint_r2.ipynb` | `a0e3ea9ea7b8026515d3c3b8f52552fc58ab72678a67c84f2104648bc7df7b87` |
| `tests/test_d1_checkpoint_runtime_evidence_r4.py` | `30573b512931939c90af372cdc9ecc901a08931f56bd31397a90d823a9023892` |
| `docs/review/d1_checkpoint_resume_r4_implementation_record.md` | `1cbd06acf26ed5d9d2c114f2e0912264b1c5d3809c5f4fcede1c6ab247a30a49` |
| Pinned predecessor runner | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| Pinned predecessor notebook | `546e60d9e980b64ef3a0c1fb535ad0cb23e6c2444c91fd358253797762eb9ccc` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| Exact archive/live attempt equality | PASS |
| Timestamp syntax and full chronology | PASS |
| Strict archived execution JSON | **FAIL** |
| Durable preflight failure evidence | **FAIL** |
| Current checkpoint-to-evidence binding | **FAIL** |
| R4-R1 source release | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit another append-only repair for independent source QA. Only a source PASS may authorize pinning
and the two-runtime live smoke; a separate artifact QA must then PASS before the 100-epoch pilot.
