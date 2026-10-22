# D1 corrected-validation evaluator R10 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_PASS`  
Reviewer: `Codex fresh independent source-and-adversarial QA session`  
Boundary: `NO_MODEL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**PASS — 0 Critical, 0 High, 0 Medium and 0 Low findings.**

R10 closes the live R9 compatibility defect without weakening the intended-payload authority. It
still requires the R8-issued binding and descriptor-consumed raw bytes to match independently
computed canonical intended bytes exactly. Its redundant document comparison now compares the
consumed JSON object with `json.loads(canonical_intended_bytes)`, so valid JSON normalization of
tuples to lists and numeric object keys to strings no longer creates a false failure.

A realistic synthetic payload containing tuple values and numeric resolution keys reproduced the
old R9 failure and passed R10 with byte-exact canonical authority. The exact R8 substitution attack
using a different canonical, sealed-safe document with `map50=0.01` still failed closed. R10 also
rejects semantically equal noncanonical bytes and post-binding descriptor replacement, delegates
strict use-time consumption, and reconstructs public metrics only from the consumed normalized
intended report.

This PASS authorizes only a new corrected-validation attempt on the already registered pilot using
the exact R10 bytes. The failed R9 command and its preview metrics remain unaccepted evidence. This
PASS does not authorize training, sealed-test access, final evaluation, model acceptance,
deployment or publication.

`sealed_test_accessed=false` throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r10.py` | `5897e951244a5e8761bda7202779fe30acb0d5da085686d49c96a04f69e5dfd3` |
| `detector/tests/test_corrected_val_r10.py` | `efdc73df79758457f26f02a4a32a573e52283ef40e60d4486ac0d9cccf3d1dc3` |
| `docs/review/d1_corrected_val_r10_qa_remediation_report.md` | `eccdfef3c55b4c048ca80ddd07e57bc141faaad0dfd5ec478d5917116a7344af` |
| `detector/m1/corrected_val_r9.py` | `008a8d335ce2a05a886c69ca2fc3e54d5265338138ec75786d11317206009fa2` |
| `detector/tests/test_corrected_val_r9.py` | `7d57209a63538f2713296ecfbd82e325b3531f27f98997d1e195440f9e9b3a34` |
| `docs/review/d1_corrected_val_r9_qa_remediation_report.md` | `85f977903ebd5fe770c4ed941b02068d6297f56697bb664f3b20b8b674195f0c` |
| `docs/review/d1_corrected_val_r9_independent_qa_record.md` | `22b487b9504e622c2850902f6512b4ea4a641aabbca239bfd3c97b52ea26878e` |
| `docs/review/d1_corrected_val_r9_live_execution_failure_record.md` | `35c9e218c5783c674a339eb7679ee8534ed13b534d386281b95fb4126b052193` |

All eight hashes matched the exact R10 scope and its pinned R9 evidence before and after review. No
reviewed source, test, remediation or predecessor record was modified. This append-only record is
the only QA-authored repository artifact.

## Review performed

- Read `AGENTS.md`, `PROJECT_MEMORY.md`, the R10 remediation report, the R9 independent PASS record
  and the pinned R9 live-execution failure record.
- Used Graft before source review to trace JSON normalization, canonical bytes, predecessor
  binding, descriptor-bound consumption and evaluate reconstruction; the closing `graft check .`
  reported the wiring graph in sync.
- Reviewed pin enforcement, canonical serialization, JSON-space comparison, strict R8 binding
  delegation, raw-byte equality, locator consumption, metric reconstruction, parser scope and
  sealed-test guards.
- Reproduced a realistic intended payload containing tuples and numeric object keys. Confirmed
  canonical raw bytes matched exactly, R10 accepted, JSON normalization produced lists and string
  keys, and R9's old direct object comparison failed.
- Replayed the R8 pre-binding substitution with a different canonical document containing
  `map50=0.01` and both sealed-safe flags false. R10 failed closed before accepting the binding.
- Ran the exact R10 suite: **7/7 PASS**.
- Ran R8-R10 regressions excluding only duplicate sealed-safe authority checks: **32/32 PASS**.
- Ran the R4 integration-authority suite: **11/11 PASS**.
- Ran the full detector suite: **199/199 PASS**.
- Ran `ruff check m1 tests`: PASS.
- Ran `uv lock --check` in `detector/`: PASS.
- No model weights were loaded. No image inference, corrected-validation evaluation, training,
  upload, download, commit, push or sealed-test operation was performed.

## Live R9 failure and R10 normalization replay

The pinned live record shows R9 completed validation inference over 376 images and 560 instances,
then failed closed because it compared a parsed JSON document with the pre-serialization Python
object. The preserved R9 report is not accepted corrected-validation evidence.

The independent replay used this intended shape:

```text
resolution_breakdown = {
  540: ("landscape", 39),
  960: ("portrait", 337),
}
```

Observed result:

```text
canonical_raw_bytes_match=true
normalized_document_matches=true
normalized_keys=["540", "960"]
normalized_value_is_list=true
pre_serialization_object_differs=true
r9_failed_old_object_comparison="corrected-validation consumed document differs from intended payload"
r10_accepted=true
sealed_test_accessed=false
```

This proves the precise distinction required by the live failure: raw published bytes remain
byte-exact, while the secondary semantic comparison is performed in JSON-normalized space.

## Verified R10 authority contract

- `verify_pins()` anchors the exact R9 implementation, tests, remediation, independent PASS and
  live-execution failure record before R10 public operations run.
- `_canonical_bytes()` retains sorted, indented, UTF-8 JSON with `ensure_ascii=false`,
  `allow_nan=false` and exactly one trailing newline.
- `_safe_write_report()` computes intended bytes, digest and normalized intended document before
  publication. The returned byte count, content URI, locator and digest must match the independent
  authority exactly.
- R8's strict `_open_bound_report()` then enforces binding schema, device/inode, regular-file,
  single-link, mode-`0400`, size, digest, locator, directory relations and sealed-safe fields while
  reading through one retained descriptor.
- Descriptor-consumed bytes must equal the intended canonical bytes. The parsed document must
  equal `json.loads(intended_bytes)`, not the pre-serialization Python object.
- A tuple/list or numeric/string-key normalization is accepted only when the canonical raw bytes
  still match exactly. A compact or otherwise noncanonical serialization of the same JSON object
  fails the binding hash/size authority.
- A different canonical report substituted before binding fails the independent intended digest.
  A descriptor content replacement after binding fails R8's bound hash check.
- `consume_report()` delegates through R9 to R8's strict reopen-and-verify consumer under the R10
  report name. The locator alone is never accepted as evidence.
- `evaluate()` captures the normalized intended-payload binding, requires inherited report
  authority to equal its content URI, consumes again through the strict binding, and reconstructs
  status, mAP values, operating point and gate result only from that consumed document. It does
  not trust inherited metric fields.
- The CLI remains validation-only (`check` and `evaluate`). The authority check returned
  `val_frames=376`, `corrected_frames=39`, `test_included=false` and
  `sealed_test_accessed=false`.

## R8 substitution replay

The independent replay published and self-bound a different canonical report with
`map50=0.01`, while retaining `test_included=false` and `sealed_test_accessed=false`. R10 rejected
it before returning a binding:

```text
{
  "error": "corrected-validation published binding differs from intended payload",
  "rejected": true,
  "sealed_test_accessed": false,
  "substitute_map50": 0.01
}
```

Both bounded replays used synthetic JSON in automatically removed temporary directories. They did
not exercise model inference or any dataset split.

## Findings

No findings.

The exact and full suites are mechanical evidence for the reviewed contracts. This source QA does
not accept the failed R9 metrics, does not establish D-05 passage, and does not claim final-test
performance, Vietnamese-domain generalization, deployment safety or production readiness.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R1-R9 and their immutable records | **YES** |
| Preserve R10 and this immutable PASS record | **YES** |
| Retry corrected validation with exact R10 on the registered pilot `best.pt` | **YES — bounded to validation** |
| Accept the failed R9 preview metrics | **NO** |
| Report R10 metrics after a successful artifact-verified run | **YES — subject to the existing D-05 workflow** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Final model acceptance, deployment or safety claim | **NO-GO** |
| Commit/push | **NOT AUTHORIZED BY THIS QA** |

Any operational retry must preserve the exact reviewed R10 source and pinned inputs, retain the
generated binding/report artifacts, confirm `sealed_test_accessed=false`, and report observed R10
metrics separately from this source-QA decision.
