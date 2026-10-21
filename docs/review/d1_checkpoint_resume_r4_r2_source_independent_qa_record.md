# D1 checkpoint/resume R4-R2 runtime-evidence source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

Predecessor records remain immutable:

- `d1_checkpoint_resume_r4_source_independent_qa_record.md`;
- `d1_checkpoint_resume_r4_r1_source_independent_qa_record.md`.

## Verdict

**FAIL / NO-GO for source release, the R4 live two-runtime smoke, and the 100-epoch pilot.**

R4-R2 repairs the three explicitly remaining R4-R1 behaviors at the ordinary-file happy-path
level: archived execution JSON is parsed with duplicate-key/non-finite rejection; same-runtime,
bad-boot-ID, malformed-prior-JSONL and run-binding failures produce a durable schema-v2 failed
execution record and append-only failed attempt; and the live verifier re-hashes the current
`latest.json`, checkpoint manifest and five recovery artifacts before accepting the claimed
checkpoint binding.

Independent adversarial testing nevertheless found that the new checkpoint verifier does not
apply the pinned checkpoint store's component-wise no-symlink and full semantic validation. It
accepted recovery artifacts reached through symlinked ancestor directories, including a symlinked
`recovery/` root and a symlinked `weights/` directory. It also accepted a checkpoint manifest whose
`run` value was an object rather than a governed run identity. Therefore the current recovery state
can differ materially from the claimed verified checkpoint while `verify_current_checkpoint`
returns success. The R4-R2 source is not safe to pin or run on Colab.

This QA did not run Colab, train a model, upload data, access the sealed test, commit, push or modify
any predecessor record.

## Repaired prior findings

### R1 — Exact archive/live attempt equality and aware chronology: PASS

- `validate_runtime_evidence` requires exactly two terminal attempts in fresh/resume order,
  distinct runtime digests, identical run/checkpoint bindings, and an aware, non-overlapping
  chronology.
- `verify_live_state` compares both the validation summary and the complete ordered archived
  attempt list with the live JSONL attempt list.
- Independently valid but different archive/live digest pairs are rejected.

### R2 — Strict archived execution JSON: PASS

`verify_r4_result_archive` now passes the archived `colab_execution.json` bytes through
`strict_json_bytes`. Duplicate keys and `NaN` are rejected. The parser is recursive, so this also
protects nested `execution_attempts` and `runtime_identity` objects.

### R3 — Durable preflight failure recording: PASS for the required ordinary-path cases

Direct adversarial executions confirmed a nonzero return plus a durable schema-v2
`colab_execution.json` with `status=FAILED` and an appended failed JSONL record for:

- malformed Linux boot ID;
- mismatched fresh/resume run binding;
- malformed prior attempt JSONL.

The declared unit test separately confirms the same-runtime refusal is durably recorded. These
records preserve `sealed_test_accessed=false` and do not overwrite the prior fresh record.

### R4 — Current-pointer and artifact rebinding: PARTIAL

The new verifier strict-parses the direct `latest.json` and checkpoint manifest files, checks the
pointer/manifest hash and binding relationships, enforces the five-file roster, and re-hashes all
five payload files. Direct byte tampering is rejected. The ancestor-symlink and manifest-semantics
bypasses below prevent this item from passing as a complete repair.

## Blocking findings

### B1 — Ancestor symlinks bypass current-checkpoint verification

`verify_current_checkpoint` checks `is_symlink()` only on the final `latest.json`, snapshot,
manifest and payload paths. It does not perform a lexical component-by-component `lstat()` check
and does not call the pinned `CheckpointStore.load_latest()` / safe-directory validation.

Two independent reproductions were accepted:

1. `state/recovery` was a directory symlink to an external recovery tree. The direct
   `latest.json`, snapshot and artifacts appeared as ordinary paths through that ancestor and the
   verifier returned the manifest.
2. `snapshots/epoch-0002/weights` was a directory symlink to an external directory containing
   hash-matching `best.pt` and `last.pt`. Both payload paths reported `is_file=true` and
   `is_symlink=false`, and the verifier accepted them.

This violates the repository's writable/readback defense rule and the predecessor requirement to
verify the current recovery pointer through the pinned checkpoint-store safety boundary.

Required repair: reuse the pinned checkpoint-store verifier with the exact recovered binding
object, or apply its component-wise no-symlink checks to `state_dir`, `recovery`, `snapshots`, the
generation directory, `weights`, and every file before and after hashing. Add direct tests for a
symlinked recovery root, snapshots root, generation ancestor and weights ancestor, not only a
symlink at the final file path.

### B2 — Checkpoint manifest run identity is not validated

The custom verifier validates the top-level key set but never validates `manifest["run"]`. An
adversarial manifest with `run={"not":"string"}`, a recomputed manifest hash and otherwise valid
artifacts was accepted. The pinned checkpoint store requires a string matching its governed run
pattern.

Required repair: validate the complete checkpoint manifest semantics at least as strictly as
`CheckpointStore._verify_generation`: exact run pattern, exact integer epoch type/range, exact
binding object/hash and canonical generation, in addition to the existing roster and hashes. Add
type-confusion and unsafe-run regression tests.

### B3 — Required preflight failure regression coverage is incomplete

The implementation behavior for malformed boot ID, malformed prior JSONL and run-binding mismatch
was confirmed only by this QA's ad-hoc adversarial executions. The committed candidate test suite
contains a durable-failure regression only for same-runtime resume. The R4-R1 repair requirement
explicitly requested direct tests for all four cases.

Required repair: add permanent tests for malformed/missing boot ID, malformed/duplicate/non-finite
prior JSONL and mismatched run binding, asserting the exact preserved prior record, the terminal
failed record, fsynced artifact readability, `sealed_test_accessed=false`, and absence of R1/training
delegation.

## Positive properties independently confirmed

- The successor remains append-only and imports the pinned R3/R1 runner rather than modifying it.
- Runtime identity retains only the declared schema and SHA-256 digest, not raw boot ID, account,
  hostname, URL, token or cookie data.
- Different valid archive/live runtime identities fail closed.
- Missing, malformed, equal and reordered runtime evidence fails closed.
- Timestamps must be timezone-aware and fresh/resume intervals cannot overlap or reverse.
- Direct recovery artifact byte tampering fails closed.
- The notebook is unexecuted, defaults to `MODE = "fresh"`, uses the new R4 label and remains
  blocked by `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Source and notebook contain no `export-test` or `--final-eval`; successful evidence requires
  `sealed_test_accessed=false`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 + R4-R2 root tests | PASS, **30/30** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52** |
| `git diff --check` | PASS |
| Strict duplicate/non-finite archive JSON | PASS |
| Required ordinary-path preflight failures | PASS by tests plus independent reproductions |
| Recovery-root ancestor symlink | **FAIL: accepted** |
| Weights-directory ancestor symlink | **FAIL: accepted** |
| Non-string checkpoint run identity | **FAIL: accepted** |

Mechanical green checks do not override the demonstrated checkpoint acceptance bypasses.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` |
| `detector/colab/d1_train_checkpoint_r2.ipynb` | `a0e3ea9ea7b8026515d3c3b8f52552fc58ab72678a67c84f2104648bc7df7b87` |
| `tests/test_d1_checkpoint_runtime_evidence_r4.py` | `3d373d0f51848ec73e3d6bdeda0f65e99614c9a54e27973542d4baf6b7406211` |
| `docs/review/d1_checkpoint_resume_r4_implementation_record.md` | `1cbd06acf26ed5d9d2c114f2e0912264b1c5d3809c5f4fcede1c6ab247a30a49` |
| Pinned predecessor runner | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| Pinned predecessor notebook | `546e60d9e980b64ef3a0c1fb535ad0cb23e6c2444c91fd358253797762eb9ccc` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| Exact archive/live attempts | PASS |
| Aware full chronology | PASS |
| Strict archived execution JSON | PASS |
| Durable ordinary-path preflight failure evidence | PASS |
| Current pointer/direct-file hash rebinding | PASS |
| Component-wise recovery path safety | **FAIL** |
| Complete checkpoint manifest semantics | **FAIL** |
| Required permanent negative-path tests | **FAIL** |
| R4-R2 source release | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit an append-only R4-R3 repair to a new independent source QA. Only a source QA PASS may
authorize commit/push and the live two-runtime smoke. A later independent artifact QA must still
PASS before any 100-epoch pilot GO decision.
