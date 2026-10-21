# D1 checkpoint/resume R4-R5 source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL / NO-GO for commit/push, notebook pinning, the live two-runtime smoke and the 100-epoch
pilot.**

R4-R5 closes the three findings from R4-R4: valid non-object `latest.json` values now leave durable
failure evidence, a linked `recovery/` ancestor cannot inject an external checkpoint binding into
that evidence, and the generation grammar is checked before any generation-derived snapshot path
is constructed. The inherited checkpoint path, manifest and artifact checks also remain fail
closed in the reviewed candidate.

Independent adversarial execution nevertheless found one remaining type-confusion acceptance
bypass in the runtime-evidence verifier. A JSON floating-point `schema_version` value of `2.0` is
accepted as schema version integer `2`. This is the same strict-schema class that previously
blocked R4-R3 for `true == 1`, now present in the terminal execution evidence that is copied into
the result archive and compared with live state. Mechanical green checks do not override the
demonstrated acceptance.

This review did not run Colab, train a model, upload data, access the sealed test, commit, push or
modify predecessor implementation/QA records.

## Repaired inherited findings

### R1 — Durable valid non-object pointer failures: PASS

Production-entry regressions cover list, string and integer top-level pointer values. Each returns
nonzero and writes both a terminal `colab_execution.json` with `status=FAILED` and one append-only
failed attempt. The checkpoint binding is `null` and `sealed_test_accessed=false`.

The implementation performs the object check before calling the pinned R4 verifier, while the
best-effort failure collector treats all pointer-read/schema exceptions as an unavailable binding.

### R2 — Recovery-symlink binding injection: PASS

The failure collector applies component-wise lexical no-symlink checks to `state`, `recovery` and
`latest.json` before reading a binding. A direct production-entry regression confirms that a
linked recovery ancestor yields `checkpoint_binding_sha256=null` and does not modify or import the
external pointer value.

### R3 — Generation validation before path use: PASS

`verify_current_checkpoint` requires exact `epoch-[0-9]{4}` syntax before delegating to R4-R4.
The permanent regression replaces the delegate with a trap and confirms that a traversal-like
generation is rejected before the delegate or any snapshot lookup is reached.

## Blocking finding

### B1 — Floating-point execution schema version is accepted as integer version 2

`validate_runtime_evidence` currently checks:

```python
execution.get("schema_version") != 2
```

Python considers `2.0 == 2`, so strict JSON containing `"schema_version": 2.0` passes. The
independent reproduction supplied two otherwise valid, ordered, distinct-runtime attempts with
matching run/checkpoint bindings and an execution object whose only schema defect was the float.
The verifier returned `D1_RUNTIME_EVIDENCE_VERIFIED` instead of rejecting it.

This is reachable through both archive and live verification because both parsers correctly retain
JSON `2.0` as a Python float, and both paths call the same validator. If the live and archived
copies contain the same malformed value, their later equality check does not repair the schema
ambiguity.

Required repair: make the runtime execution schema version type-strict before value comparison,
for example `type(execution.get("schema_version")) is int` and exact value `2`. Add permanent
direct-validator plus archive/live regressions for `2.0`, `true`, `"2"` and `null`. Review the
remaining runtime-evidence scalar fields under the same JSON-type rule. Submit the append-only
successor as R4-R6; do not mutate R4-R5 or any prior QA record.

## Independently confirmed positive properties

- All four handed-off SHA-256 values matched the frozen candidate exactly before review.
- The inherited R4-R4, R4-R3 and R4-R2 candidates retained their reviewed hashes.
- Non-object/corrupt pointer failure durability, recovery-symlink isolation and generation-first
  validation pass through the production successor path.
- Boolean checkpoint schema versions, boolean/zero/negative checkpoint sizes, malformed run
  identities, ancestor symlinks, pointer/manifest hash changes and payload-byte tampering remain
  rejected by the inherited strict checkpoint verifier.
- Runtime evidence still requires exactly two attempts in fresh-pause/resume-success order,
  distinct SHA-256 runtime digests, equal run/checkpoint bindings, timezone-aware non-overlapping
  chronology, exact archived/live attempt equality and `sealed_test_accessed=false`.
- Result verification retains the canonical eight-file archive roster and byte hashes. Archived
  `colab_execution.json` and live JSONL parsing reject duplicate keys and non-finite values.
- The R5 notebook is unexecuted, defaults to `MODE = "fresh"`, uses an isolated R4-R5 label and is
  blocked at `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Source and notebook contain no `export-test` or `--final-eval` command.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 + all R4 through R4-R5 targeted root tests | PASS, **50/50** |
| Complete detector pytest | PASS, **93/93** |
| Root Ruff | PASS |
| Detector Ruff | PASS |
| Root lock | PASS, **168 packages** |
| Detector lock | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52**, independently rerun in 154.9 s wall time |
| `git diff --check` | PASS before this append-only record |
| R4-R4 three reported bypasses | PASS, rejected or durably recorded as required |
| Float `execution.schema_version = 2.0` | **FAIL: accepted as schema version 2** |

Graft initially reported the graph stale for the new R5 runner/tests. A freshness-aware `graft ask`
refreshed and located the active successor flow; it reported approximately 30,768 tokens saved.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r5.py` | `c1ebfe7e311aa4fb1ccad6738dc392b538083214fe89f79767408caef98acc48` |
| `detector/colab/d1_train_checkpoint_r5.ipynb` | `f9ae3b9080811f854f744c0751687c1e1a72a4d23bebc5ed62acfcbcf091ffbd` |
| `tests/test_d1_checkpoint_runtime_evidence_r4_r5.py` | `749cf19ec15f95cee84bb202ae09df6ba40fb47c3c68de5c0397308efe39a91e` |
| `docs/review/d1_checkpoint_resume_r4_r5_implementation_record.md` | `c77cbe0346981c2d7edfc8f75faf55bbd8617b34f5459608ce5be9d336fe85a5` |
| Inherited `run_d1_colab_checkpoint_r4.py` | `25431f08a10b016a21b19a5c5c98c1d7419eee180bb7aeaf772b674f9b1cb27f` |
| Inherited `run_d1_colab_checkpoint_r3.py` | `1c2999cbaf4248b5df649a3a0e63e5b2c5d1d7ae697ae858ef06df19707dbe0c` |
| Inherited `run_d1_colab_checkpoint_r2.py` | `8041540a1a8872c4c6fe893ab17d9c7facf09e344b31445102fc048273ff7112` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| R4-R4 non-object pointer durability repair | PASS |
| R4-R4 recovery-symlink isolation repair | PASS |
| R4-R4 generation-before-path repair | PASS |
| Strict runtime execution schema type | **FAIL** |
| R4-R5 commit/push and notebook pin | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit an append-only R4-R6 repair to a new independent source QA. Only a later source QA PASS may
authorize commit/push, notebook pinning and the live two-runtime smoke. A separate independent live-
artifact QA PASS remains mandatory before any 100-epoch pilot GO decision.
