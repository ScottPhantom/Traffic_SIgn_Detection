# D1 checkpoint/resume R4-R4 source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL / NO-GO for commit/push, notebook pinning, the live two-runtime smoke and the 100-epoch
pilot.**

R4-R4 correctly rejects boolean schema versions and boolean/non-positive artifact sizes on its
declared checkpoint-verification path. It also preserves durable failure evidence for malformed
JSON text, duplicate keys, non-finite constants, invalid UTF-8 and a direct `latest.json` symlink.
However, independent adversarial execution found that valid JSON with a non-object top level still
crashes the failure recorder before either durable artifact is written. It also found that a
symlinked `recovery/` ancestor is followed while collecting the failure checkpoint binding, and
that an unvalidated traversal value in `generation` is used to read a manifest outside the
recovery snapshots tree before the pinned predecessor rejects the value. These are residual schema
and path-boundary gaps in the exact area R4-R4 claims to close.

Mechanical green checks do not override these reproductions. This QA did not run Colab, train a
model, upload data, access the sealed test, commit, push or edit any predecessor source/QA record.

## Blocking findings

### B1 — Valid non-object pointer JSON still suppresses durable failure evidence

`durable_preflight_failure` calls the inherited `checkpoint_binding`, which immediately calls
`.get("binding_sha256")` without first requiring an object. The R4-R4 exception list does not catch
`AttributeError`. A `recovery/latest.json` containing any of `[]`, `"hello"` or `1` therefore
raises inside the failure recorder.

The direct production-entry reproduction used resume mode, a missing boot-ID file and
`latest.json` containing `[]`. The runner returned 1 and printed the original `FileNotFoundError`,
but neither `colab_execution.json` nor `execution_attempts.jsonl` existed afterward. Only the
recovery directory and invalid pointer remained. This is the same durability property that the
R4-R3 QA required R4-R4 to close, reached through a valid-JSON wrong-type pointer rather than
malformed JSON text.

Required repair: strict-parse the pointer inside the best-effort collector, require an exact object
schema before accessing it, and catch all expected schema/access exceptions around collection.
Pointer evidence that is absent, linked, malformed, non-object or semantically invalid must yield
`checkpoint_binding_sha256=null` while the original preflight error is durably recorded. Add
permanent production-entry regressions for object, list, string, number, boolean and null top-level
values, not only corrupt text.

### B2 — A symlinked recovery ancestor imports an external checkpoint binding

The recorder checks only `latest.is_symlink()`. With `state/recovery` as a directory symlink and an
ordinary external `latest.json`, `latest.is_file()` is true and `latest.is_symlink()` is false.
The inherited collector follows the ancestor and the failure record receives the external
64-character binding instead of `null`.

Independent reproduction created a regular state directory, symlinked its `recovery/` child to an
external directory, and placed a structurally sufficient pointer there. The resulting durable
record contained the external value `aaaa...aaaa` as `checkpoint_binding_sha256`. This contradicts
the prior QA requirement that a linked pointer be treated as unavailable and violates the
component-wise no-symlink boundary already enforced by the success verifier.

Required repair: component-check `state_dir`, `recovery` and `latest.json` lexically before any
failure-path read, or reuse a safe best-effort helper that returns `null` on every linked ancestor.
Add separate direct-pointer and recovery-ancestor symlink regressions through the production entry
point.

## Additional path-hardening finding

R4-R4 reads `recovery/snapshots/<generation>/checkpoint_manifest.json` before validating
`generation`. With an existing `snapshots/` directory and `generation="../../outside"`, the
independent attack reached and parsed `state/outside/checkpoint_manifest.json`; the later R4-R3
validation then rejected the generation, so this was not an acceptance bypass. Validate the exact
`epoch-[0-9]{4}` grammar before constructing or reading any generation-derived path. This should
be repaired with the blockers because it is an adjacent path-boundary regression introduced by
the R4-R4 pre-validation wrapper.

## Independently confirmed positive properties

- All four handed-off SHA-256 values matched the frozen candidate exactly before and after review.
- The inherited R4-R3, R4-R2 and checkpoint-store files matched their prior reviewed hashes.
- Latest/manifest boolean schema versions and boolean artifact sizes fail closed.
- Zero and negative artifact sizes fail closed through the declared typed checks.
- Duplicate-key, non-finite, corrupt-text and invalid-UTF-8 pointers leave a durable FAILED record
  with a null checkpoint binding.
- A direct `latest.json` symlink leaves a null checkpoint binding.
- The successor notebook is unexecuted, defaults to `MODE = "fresh"`, uses the isolated R4-R4
  label and remains blocked at `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Source and notebook contain no `export-test` or `--final-eval`; the success contract continues to
  require `sealed_test_accessed=false`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 + R4/R4-R3/R4-R4 targeted root tests | PASS, **44/44** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52**, supplied by the synchronized PM gate run |
| `git diff --check` | PASS |
| Boolean schema versions and sizes | PASS, rejected |
| Duplicate/non-finite/corrupt-text pointer durability | PASS |
| Valid non-object pointer durability | **FAIL, no durable records** |
| Recovery-ancestor symlink isolation | **FAIL, external binding imported** |
| Generation path validation before read | **FAIL, traversal path read attempted** |

Graft reported the current graph stale because the new R4-R4 runner/tests were not yet indexed.
Freshness-aware `graft ask` located the active successor flow; this read-only QA did not rebuild or
write `graft/` because its only authorized write is this append-only review record.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r4.py` | `25431f08a10b016a21b19a5c5c98c1d7419eee180bb7aeaf772b674f9b1cb27f` |
| `detector/colab/d1_train_checkpoint_r4.ipynb` | `1efdbc6e03426b062410df0da2c03970b0a45fdc924ef40dd2091916633c0941` |
| `tests/test_d1_checkpoint_runtime_evidence_r4_r4.py` | `a10e2c76df9ce4777f5c68459c04425184dbe7715149dbd59803ffa892c0260d` |
| `docs/review/d1_checkpoint_resume_r4_r4_implementation_record.md` | `e9c30c829238e750ef8a6582b155f89639b28473ce9ad0ad28ba2c3d2e291071` |
| Inherited `run_d1_colab_checkpoint_r3.py` | `1c2999cbaf4248b5df649a3a0e63e5b2c5d1d7ae697ae858ef06df19707dbe0c` |
| Inherited `run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| R4-R3 boolean/integer repair | PASS for declared checkpoint fields |
| Malformed-text pointer durability | PASS |
| Complete wrong-type pointer durability | **FAIL** |
| Failure-path component-wise path isolation | **FAIL** |
| R4-R4 commit/push and notebook pin | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit an append-only R4-R5 repair to a new independent source QA. Only a later source QA PASS may
authorize commit/push, notebook pinning and the live two-runtime smoke. A separate independent live-
artifact QA PASS remains mandatory before any 100-epoch pilot GO decision.
