# D1 corrected-validation evaluator R9 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS`  
Reviewer: `Codex fresh independent source-and-adversarial QA session`  
Boundary: `NO_MODEL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

R9 closes the exact R8 binding gap. It independently serializes the evaluator's intended payload,
requires the predecessor-issued binding's SHA-256, byte count, content URI and R9 locator to match
those canonical bytes, reopens through R8's strict descriptor-bound authority, and requires both
the consumed bytes and parsed document to equal the intended payload before returning the binding.

The exact R8 failure was independently replayed: a predecessor published and self-bound a
different canonical, sealed-safe metric document between publication and R9 acceptance. R9
rejected it with `corrected-validation published binding differs from intended payload`. Existing
R9 attacks also reject same-semantic noncanonical bytes, post-binding descriptor content changes
and authority-field tampering.

This PASS authorizes only the bounded next workflow: corrected-validation evaluation of the
already registered pilot checkpoint using the exact R9 bytes. It does not authorize training,
sealed-test access, final evaluation, model acceptance, deployment or publication.

`sealed_test_accessed=false` throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r9.py` | `008a8d335ce2a05a886c69ca2fc3e54d5265338138ec75786d11317206009fa2` |
| `detector/tests/test_corrected_val_r9.py` | `7d57209a63538f2713296ecfbd82e325b3531f27f98997d1e195440f9e9b3a34` |
| `docs/review/d1_corrected_val_r9_qa_remediation_report.md` | `85f977903ebd5fe770c4ed941b02068d6297f56697bb664f3b20b8b674195f0c` |
| `docs/review/d1_corrected_val_r8_independent_qa_record.md` | `a616a232690f607bb528308b428d55c9c1595c82461078a74cc6327a1a7c3684` |

All four hashes matched the requested immutable inputs before and after review. No reviewed
source, test, remediation or predecessor-QA file was modified. This append-only record is the only
QA-authored repository artifact.

## Review performed

- Read `AGENTS.md`, `PROJECT_MEMORY.md`, the R9 remediation report and pinned R8 independent FAIL
  record.
- Used Graft before source review to trace intended canonical bytes, predecessor binding,
  descriptor-bound consumption and evaluate reconstruction; the closing `graft check .` reported
  the wiring graph in sync.
- Reviewed pin enforcement, canonical serialization, strict intended authority, raw-byte and
  document equality, delegated R8 binding validation, locator use, evaluate reconstruction,
  parser scope and sealed-test guards.
- Independently replayed the R8 pre-binding substitution with a different canonical metric
  document whose `test_included` and `sealed_test_accessed` values remained false. R9 failed closed
  before accepting the binding.
- Ran the exact R9 suite: **11/11 PASS**.
- Ran R6-R9 regressions excluding only their duplicate sealed-safe authority checks:
  **42/42 PASS**.
- Ran the R4 integration-authority suite: **11/11 PASS**.
- Ran the full detector suite: **192/192 PASS**.
- Ran `ruff check m1 tests`: PASS.
- Ran `uv lock --check` in `detector/`: PASS.
- No model weights were loaded. No image inference, corrected-validation evaluation, training,
  upload, download, commit, push or sealed-test operation was performed.

## Verified authority contract

- `verify_pins()` anchors the exact R8 implementation, R8 tests, R8 remediation report and R8
  independent FAIL record before R9 public operations run.
- `_canonical_bytes()` uses sorted, indented, UTF-8 JSON with `ensure_ascii=false`,
  `allow_nan=false` and exactly one trailing newline, matching the pinned publication contract.
- `_safe_write_report()` computes intended bytes and SHA-256 before delegating publication. It
  requires the returned binding's byte count, content URI, locator and digest to equal that
  independent authority.
- The binding is then passed to R8's `_open_bound_report()`, which performs the complete strict
  schema, device/inode, regular-file, single-link, mode-`0400`, size, digest, locator, relation and
  sealed-safe checks while reading through one retained descriptor.
- R9 additionally requires descriptor-consumed bytes to equal the intended canonical bytes and the
  parsed document to equal the intended payload. Self-consistent binding of another document and
  semantically equal noncanonical serialization both fail.
- A locator/descriptor content replacement after binding fails under R8's bound hash and identity
  checks. Tampering with the binding's digest, content URI, byte count or locator fails before
  acceptance.
- `consume_report()` temporarily binds R8 to the R9 report name and delegates to R8's strict
  reopen-and-verify consumer. The locator alone is never treated as report evidence.
- `evaluate()` captures the intended-payload-authenticated binding, requires inherited report
  authority to equal its content URI, consumes again through the strict binding, and reconstructs
  status, mAP values, operating point and gate result only from that consumed document. It does
  not trust inherited metric fields.
- The CLI remains validation-only (`check` and `evaluate`). The authority check returned
  `val_frames=376`, `corrected_frames=39`, `test_included=false` and
  `sealed_test_accessed=false`.

## Exact R8-failure replay

The bounded replay supplied R9 with an intended report containing `map50=0.8`. The fake pinned
predecessor behavior for the attack interval wrote and self-bound another canonical document with
`map50=0.01`, while keeping both sealed-safe flags false. R9 independently recomputed the intended
hash and rejected the predecessor binding:

```text
{
  "error": "corrected-validation published binding differs from intended payload",
  "rejected": true,
  "sealed_test_accessed": false
}
```

The replay used only synthetic JSON in an automatically removed temporary directory. It did not
exercise model inference or any dataset split.

## Findings

No findings.

The exact and full suites are mechanical evidence for the reviewed contracts; they do not claim
Vietnamese-domain model quality, D-05 passage, final-test performance, deployment safety or
generalization.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R1-R8 and their immutable FAIL records | **YES** |
| Preserve R9 and this immutable PASS record | **YES** |
| Run exact R9 on the registered pilot `best.pt` for corrected validation only | **YES — bounded to validation** |
| Select/report corrected-validation metrics after artifact verification | **YES — subject to the existing D-05 workflow** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Final model acceptance, deployment or safety claim | **NO-GO** |
| Commit/push | **NOT AUTHORIZED BY THIS QA** |

Any operational run must preserve the exact reviewed R9 source and pinned inputs, retain the
generated binding/report artifacts, confirm `sealed_test_accessed=false`, and report observed
metrics separately from this source-QA decision.
