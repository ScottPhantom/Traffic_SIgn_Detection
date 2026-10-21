# D1 checkpoint/resume R4-R3 source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL / NO-GO for commit/push, notebook pinning, the live two-runtime smoke and the 100-epoch
pilot.**

R4-R3 closes the three R4-R2 findings that motivated it: component-wise ancestor-symlink checks
now cover the recovery tree, the strict manifest read validates the run/epoch/generation
relationship, and the pinned `CheckpointStore` re-verifies the pointer, manifest, five-file roster,
hashes and binding. The permanent negative-path tests also cover the previously missing boot-ID,
malformed-prior-JSONL and run-binding failure cases.

Independent adversarial testing nevertheless found two fail-closed gaps. First, JSON booleans are
accepted as integer schema versions and artifact sizes. Second, a malformed existing recovery
pointer can prevent the preflight failure recorder itself from writing either durable failure
artifact. Both contradict the successor's declared strict-schema and durable-failure boundaries.
Mechanical green gates do not override these reproductions.

This QA did not run Colab, train a model, upload data, access the sealed test, commit, push or edit
any predecessor implementation/QA record.

## Blocking findings

### B1 — Boolean-to-integer type confusion passes checkpoint schemas

`verify_current_checkpoint` compares `latest["schema_version"] != 1`, then delegates the manifest
to `CheckpointStore`, whose equivalent schema comparison and file-size comparison also use normal
Python equality. Because `bool` is a subclass of `int`, all of the following independently passed
verification after hashes/pointers were consistently rebuilt:

- `latest.json` with `"schema_version": true`;
- `checkpoint_manifest.json` with `"schema_version": true`;
- all five file records with `"size": true` when each fixture artifact was exactly one byte.

Duplicate keys, non-finite values, pointer/manifest hash tampering and binding tampering were
correctly rejected; this finding is specifically a schema-type confusion. A checkpoint verifier
must not certify a JSON boolean as schema version 1 or byte size 1.

Required repair: before delegating to the pinned store, require
`type(latest["schema_version"]) is int`, `type(manifest["schema_version"]) is int`, and exact typed
file-record semantics (`path` string in the governed roster, positive non-boolean integer `size`,
lowercase SHA-256 string). Add permanent regressions for boolean schema versions and boolean/zero/
negative sizes.

### B2 — A malformed recovery pointer suppresses durable preflight failure evidence

`record_preflight_failure` tries to derive `checkpoint_binding` whenever
`recovery/latest.json` exists. If that existing pointer is malformed, this read raises inside the
failure recorder. The caller catches and discards that second exception, then returns failure
without writing `colab_execution.json` or appending `execution_attempts.jsonl`.

Direct reproduction used resume mode with an ordinary state directory, an existing
`recovery/latest.json` containing `{malformed}`, and a missing boot-ID file. The runner returned 1
and printed the original `FileNotFoundError`, but both durable failure artifacts were absent. The
only retained files were the malformed pointer and its parent directory.

This is broader than the covered malformed-prior-JSONL case and violates the implementation
record's statement that all preflight failures leave a durable FAILED execution record and
attempt. A corrupt or partially written recovery pointer is precisely a failure mode for which
durable evidence is required.

Required repair: make checkpoint-binding collection best-effort inside the failure recorder. A
malformed/missing/linked pointer should yield a null checkpoint binding plus a durable description,
not abort failure recording. Preserve the original preflight error, always attempt the atomic
execution write and append-only attempt independently, and add regressions for malformed,
duplicate-key, non-finite, wrong-type and linked recovery pointers.

## Independently confirmed positive properties

- All four handed-off SHA-256 values matched the frozen candidate exactly.
- Recovery-root, snapshots-root, generation and weights-directory symlink ancestors fail closed.
- Duplicate-key and non-finite latest/manifest JSON fail closed.
- Pointer-to-manifest hash changes and pointer binding changes fail closed.
- A non-string checkpoint run identity fails closed.
- The pinned store verifies the exact generation, five-file roster, hashes and binding on the
  ordinary typed happy path.
- Missing/malformed boot ID, malformed prior JSONL and run-binding mismatch return nonzero and are
  durably recorded for the fixtures covered by the candidate tests.
- The notebook is unexecuted, defaults to `MODE = "fresh"`, uses a new R4-R3 run label and remains
  fail-closed at `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Source/notebook contain no `export-test` or `--final-eval`; the successful evidence contract
  requires `sealed_test_accessed=false`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 + R4/R4-R3 root tests | PASS, **39/39** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| `git diff --check` | PASS |
| Graft freshness | PASS, **2676/2676 nodes in sync** |
| Recovery/snapshots/generation/weights ancestor symlinks | PASS, rejected |
| Duplicate/non-finite pointer and manifest JSON | PASS, rejected |
| Pointer/manifest hash and binding tampering | PASS, rejected |
| Boolean schema version and file size | **FAIL, accepted** |
| Malformed-pointer preflight failure durability | **FAIL, no durable records** |

The PM handoff also reported the repository verifier matrix at 52/52. This QA's own duplicate run
was interrupted after the blocking findings were already reproduced, so the matrix is not used as
independent support for the verdict.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r3.py` | `1c2999cbaf4248b5df649a3a0e63e5b2c5d1d7ae697ae858ef06df19707dbe0c` |
| `detector/colab/d1_train_checkpoint_r3.ipynb` | `8a6e7de015490aed1c9d0edf8c130ab2a67e708bd939233f8ff739240f7689f1` |
| `tests/test_d1_checkpoint_runtime_evidence_r4_r3.py` | `40e261ff80484f01ef1c168cc47a7eecdfe61537df9dcc92b0aee5e73edad14a` |
| `docs/review/d1_checkpoint_resume_r4_r3_implementation_record.md` | `d4d7ef0f82598537fb1a1934bd22fef71ff49e5dd00d7313d530fe0606b72183` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| R4-R2 ancestor-symlink repair | PASS |
| R4-R2 run/epoch/generation repair | PASS |
| R4-R2 permanent failure regressions | PASS for declared fixtures |
| Strict typed pointer/manifest/file-record schema | **FAIL** |
| Durable failure under malformed recovery state | **FAIL** |
| R4-R3 commit/push and notebook pin | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit an append-only R4-R4 repair to a new independent source QA. Only a later source QA PASS may
authorize commit/push, notebook pinning and the live two-runtime smoke. A separate independent live-
artifact QA PASS is still required before any 100-epoch pilot GO decision.
