# D1 checkpoint/resume R4 runtime-evidence source independent QA record

Status: `INDEPENDENT_QA_FAIL`

Date: 2026-10-21 (`Asia/Ho_Chi_Minh`)

Reviewer: `Codex independent QA source-review session`

Boundary: `READ_ONLY_SOURCE_QA_NO_TRAINING_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_SEALED_TEST`

## Verdict

**FAIL / NO-GO for the R4 live smoke and NO-GO for the 100-epoch pilot.**

The append-only successor correctly derives a privacy-preserving digest from the scoped tag and
Linux boot ID, rejects equal/missing/malformed digests in the direct evidence validator, embeds
two attempts in `colab_execution.json`, keeps the notebook unexecuted and fail-closed on an
unreleased commit pin, and contains no sealed-test command. The positive and declared adversarial
unit tests pass.

Independent adversarial review nevertheless found acceptance bypasses in the cross-artifact and
chronology checks. In particular, the live verifier can accept different runtime identities in the
live JSONL and the result archive. This contradicts the implementation record's claim that the
live evidence is compared with the archived copy and prevents source release.

This QA did not run Colab, train a model, upload data, access the sealed test, or authorize either
the live smoke or the 100-epoch pilot.

## Blocking findings

### B1 — Archive/live runtime identities are not compared

`validate_runtime_evidence` returns a reduced summary containing only an attempt count, a Boolean
`distinct_runtime_digests`, the run/checkpoint bindings, and the sealed-test flag. It omits both
actual runtime digests and the ordered attempt records. `verify_live_state` independently validates
the live JSONL and archived execution record, then compares only those reduced summaries.

An adversarial reproduction used valid but different digest pairs for the two sources:

- live JSONL: digest pair `11…11` / `22…22`;
- archived execution: digest pair `33…33` / `44…44`;
- identical run/checkpoint bindings and valid fresh/resume statuses.

Both summaries were equal, and `verify_live_state` returned
`D1_R4_LIVE_STATE_VERIFIED`. Therefore a copied, substituted or stale archive can disagree with the
live runtime evidence without detection.

Required repair: compare the complete canonical ordered attempts, or include their canonical
SHA-256 and both runtime digests in the returned evidence and require exact equality. Add an
end-to-end verifier test in which both independently valid sources have different digest pairs.

### B2 — Reordered or impossible chronology can pass

Attempt timestamps are checked only as non-empty strings. The sole ordering test is lexical
`fresh.started_at < resume.started_at`; neither timestamp syntax nor UTC parsing is enforced, and
finished times are not ordered.

The validator accepted this deliberately invalid evidence as `D1_RUNTIME_EVIDENCE_VERIFIED`:

- fresh: `started_at="a"`, `finished_at="z"`;
- resume: `started_at="b"`, `finished_at="a"`.

Thus the resume may appear to finish before it starts and to begin before the fresh leg finishes.
The current reversed-list unit test does not exercise this bypass.

Required repair: parse the exact UTC timestamp form emitted by the runner, reject naïve/non-UTC or
malformed values, and enforce
`fresh.started_at <= fresh.finished_at < resume.started_at <= resume.finished_at`. Add malformed,
offset-equivalent, overlap and reversed-finish tests.

### B3 — Archived execution JSON is not parsed strictly

`read_attempts` rejects duplicate keys and non-finite constants, but
`verify_r4_result_archive` reads the archived `colab_execution.json` with plain `json.loads`.
Duplicate JSON keys therefore use last-key-wins semantics, and `NaN`/`Infinity` are accepted by the
Python decoder. This creates schema ambiguity in the artifact that carries the runtime evidence.

Required repair: use the same duplicate-key/non-finite-constant rejection for archived JSON bytes
as for repository `strict_json`, and add archive-level duplicate-key and non-finite-value tests.

### B4 — Wrapper preflight failures are not durably recorded

Runtime identity derivation, bundle hashing, prior-attempt parsing, equal-runtime rejection and
run-binding comparison execute before the wrapper delegates to the R1 runner's guarded lifecycle.
Exceptions at those points escape directly and do not append a terminal failure attempt or write a
durable failure execution record/log. The most important expected negative path—attempting resume
on the same runtime—therefore leaves only transient notebook stderr.

Required repair: add an append-only, fail-safe preflight failure record that cannot overwrite a
valid prior attempt, or a separate durable preflight audit file with strict schema and fsync. Test
same-runtime, malformed boot ID, malformed prior JSONL and run-binding mismatch failure paths.

### B5 — Claimed checkpoint binding is not rechecked by the live verifier

`verify_live_state` validates the checkpoint-binding strings stored in the two attempts but does
not read `recovery/latest.json` and require its current verified binding to equal that evidence.
Consequently, the current recovery pointer may disagree with both the live and archived claims
without this R4 verifier detecting the mismatch.

Required repair: re-verify the current recovery pointer/checkpoint manifest using the pinned
checkpoint-store verifier and compare its binding to both attempts and the archived execution.
Add missing, linked, malformed and changed-latest-pointer tests.

## Positive properties independently confirmed

- R4 is append-only and loads the pinned R3/R1 successor rather than modifying it.
- The runtime identity payload contains only `{schema, digest}` and does not retain the raw boot ID,
  backend hostname, account token, cookie or Colab URL.
- The digest is deterministic for the same tag/boot ID and changes for a different boot ID.
- Resume preflight directly rejects the same digest and mismatched run binding.
- Direct validation rejects missing/malformed digests, wrong attempt order, changed run binding,
  changed checkpoint binding, and a mismatch between an execution record and attempts supplied to
  that same validation call.
- The successor notebook has no outputs or execution counts, defaults to `MODE = "fresh"`, uses a
  new R4 run label and is blocked by `CODE_COMMIT = "PENDING_AFTER_QA"`.
- Source and notebook contain neither `export-test` nor `--final-eval`; the successful evidence
  contract requires `sealed_test_accessed=false`.

## Mechanical validation

| Gate | Result |
| --- | --- |
| R3 + R4 root tests | PASS, **22/22** |
| Detector checkpoint-store tests | PASS, **5/5** |
| Root Ruff | PASS |
| Root lock check | PASS, **168 packages** |
| Detector Ruff | PASS |
| Detector lock check | PASS, **66 packages** |
| Repository verifier matrix | PASS, **52/52** (reported concurrently and independently by PM) |
| `git diff --check` | PASS |
| Adversarial archive/live digest-pair mismatch | **FAIL: accepted** |
| Adversarial invalid/reversed timestamp chronology | **FAIL: accepted** |

Mechanical green checks do not override the two demonstrated acceptance bypasses.

## Reviewed hashes

| Artifact | SHA-256 |
| --- | --- |
| `detector/colab/run_d1_colab_checkpoint_r2.py` | `ab5d1f155c5a9830c8e35857c5d501cbab2a927051e9f58b8fd1cb6d3d4f2a28` |
| `detector/colab/d1_train_checkpoint_r2.ipynb` | `a0e3ea9ea7b8026515d3c3b8f52552fc58ab72678a67c84f2104648bc7df7b87` |
| `tests/test_d1_checkpoint_runtime_evidence_r4.py` | `bf5d16499897f9b952f7071adbb5e40414a4812922b7266b74a966f3ac00f443` |
| `docs/review/d1_checkpoint_resume_r4_implementation_record.md` | `1cbd06acf26ed5d9d2c114f2e0912264b1c5d3809c5f4fcede1c6ab247a30a49` |
| Pinned predecessor runner | `e3193ad71e4376149d925958cc8c3d415e7ca912f7adfeae86973548db701336` |
| Pinned predecessor notebook | `546e60d9e980b64ef3a0c1fb535ad0cb23e6c2444c91fd358253797762eb9ccc` |

## Gate disposition

| Gate | QA disposition |
| --- | --- |
| Privacy-preserving runtime digest derivation | PASS |
| Same/missing/malformed digest rejection in direct validator | PASS |
| Exact archive/live runtime evidence equality | **FAIL** |
| Timestamp syntax and full chronology | **FAIL** |
| Strict archived JSON schema | **FAIL** |
| Durable expected-failure evidence | **FAIL** |
| Current checkpoint-to-evidence binding | **FAIL** |
| R4 source release | **NO-GO** |
| R4 live two-runtime smoke | **NO-GO** |
| 100-epoch pilot | **NO-GO** |

Submit an append-only repaired successor to a new independent source QA. Only after that source QA
passes may the code be pinned and the two-runtime live smoke begin. A later, separate QA must still
audit the retained live artifacts before any 100-epoch GO decision.
