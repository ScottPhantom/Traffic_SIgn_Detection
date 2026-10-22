# D1 corrected-validation evaluator R8 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-and-adversarial QA session`  
Boundary: `NO_MODEL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R8 correctly changes the public API from a mutable `Path` to a strict `ReportBinding`. Its
consumer reopens the locator under retained directory authority, validates the schema and bound
file identity, and consumes JSON through the same verified descriptor. Replacement of the locator
**after** binding fails closed, and `evaluate()` reconstructs metrics from the consumed report
rather than inherited metric fields.

The binding step does not prove that the file it binds contains the payload passed to
`_safe_write_report()`. R8 delegates publication to R7, discards R7's returned value, then binds
whatever regular single-link mode-`0400` file currently occupies `REPORT_NAME`. A replacement in
that interval receives a new, internally valid content URI and identity binding; subsequent
consumption correctly verifies the replacement against that self-issued binding and returns its
metrics. This is a content-integrity failure, so R8 remains **NO-GO** for real
corrected-validation inference.

`sealed_test_accessed=false` throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r8.py` | `8240f42a82e6ce9712e3e130413d986ed5c8cb83d6bd1de821b40713b6e2dc13` |
| `detector/tests/test_corrected_val_r8.py` | `e2b999364d763a8a9f20dc57b80adac7c0e524021f24eebcffc67e931b6294bc` |
| `docs/review/d1_corrected_val_r8_qa_remediation_report.md` | `d09abc164d7edbd8f9ae337107ff3e50e9a0c95e2701f56c8209fe1498294c3b` |
| `docs/review/d1_corrected_val_r7_independent_qa_record.md` | `b14e70ea8cd3dade7a4f2f5528c59435204f2f3e3a7e38ee4ff3cd70d9950b3c` |

All four hashes matched the requested immutable inputs before and after review. No reviewed
source, test, remediation or predecessor-QA file was modified. This append-only record is the only
QA-authored repository artifact.

## Review performed

- Read `PROJECT_MEMORY.md`, the R8 remediation report and the pinned R7 independent FAIL record.
- Used Graft before source review to trace `ReportBinding`, `_safe_write_report()`,
  `_bind_report()`, `consume_report()` and `evaluate()`; the closing `graft check .` reported the
  wiring graph in sync.
- Reviewed the exact binding schema, content URI, hash, size, device/inode, mode, link count,
  regular-file flag, locator policy, sealed-test guards and parser boundary.
- Ran `ruff` on all detector `m1` source and tests: PASS.
- Ran the exact R8 suite: **17/17 PASS**.
- Ran the R6/R7 publication regressions excluding duplicate authority checks: **16/16 PASS**.
- Ran the R4 integration-authority suite: **11/11 PASS**.
- Ran the detector suite excluding eight duplicate `authority_check_stays_sealed_safe` tests:
  **174/174 PASS**. The exact R8 suite separately ran R8's authority check.
- Ran `uv lock --check` in `detector/`: PASS.
- Ran one bounded temporary-directory reproduction of the binding interval. It used synthetic JSON
  and a fake predecessor only; it did not load model weights, perform image inference, train,
  access sealed-test data or leave a repository artifact.

Green mechanical tests do not authenticate the newly bound bytes as the payload that the caller
asked R8 to publish.

## Verified R8 properties

- `ReportBinding` is frozen and serializes exactly the declared 12-field schema.
- `_validate_binding()` requires exact keys and exact Python types; rejects Boolean values in
  integer fields; enforces a lowercase 64-hex digest, `sha256:<digest>` content URI, positive byte
  count/inode, exact report locator, `REOPEN_AND_VERIFY_BEFORE_USE`, mode `0400`, link count one,
  a regular-file assertion and `sealed_test_accessed=false`.
- `_bind_report()` opens the report relative to a retained run-directory descriptor, reads and
  hashes through that descriptor, verifies regular/single-link/mode properties, rechecks the final
  entry and validates directory relations.
- `consume_report()` treats the pathname only as a locator. It validates the supplied binding,
  opens with `O_NOFOLLOW` relative to retained authority, requires matching device/inode/mode/link
  count, verifies exact byte count and SHA-256, checks the final entry and relations, parses the
  same descriptor bytes, and rejects reports whose `test_included` or `sealed_test_accessed` value
  is not exactly false.
- A locator regular-file replacement or symlink after binding fails closed and does not modify the
  Owner replacement.
- `evaluate()` captures the binding, checks inherited report authority equals the content URI,
  calls `consume_report()`, and returns status, metrics, operating point and gate result from the
  consumed document rather than inherited metric fields.
- The CLI remains validation-only (`check` and `evaluate`). The authority check returned
  `val_frames=376`, `corrected_frames=39`, `test_included=false` and
  `sealed_test_accessed=false`.

These properties close R7's error of treating a returned lexical path as evidence. They do not
authenticate the content selected when R8 first creates its binding.

## Finding

### QA-D1-CORR-VAL-R8-001 — High — the binding can authenticate a substituted pre-binding report

`_safe_write_report()` delegates to R7 at lines 243-250 of
`detector/m1/corrected_val_r8.py`. It ignores the predecessor return and calls
`_bind_report(run_dir)` at line 251. `_bind_report()` opens the current `REPORT_NAME`, reads its
bytes and constructs a fresh digest, content URI, size and filesystem identity from that object at
lines 201-229. It validates only the binding's internal schema and the current locator/relations at
lines 230-235.

Neither `_safe_write_report()` nor `_bind_report()` computes the canonical bytes of the `payload`
argument or requires the newly opened descriptor's hash/size to match that expected payload. R7's
post-publication checks happen before R8 starts `_bind_report()`, so the same-user mutable-namespace
threat established by the pinned R7 FAIL record can replace the final entry in this interval.

Once R8 issues a binding for the replacement, `_open_bound_report()` at lines 158-193 behaves
exactly as designed: it proves the replacement matches the self-consistent binding, parses its
JSON, and accepts it when `test_included=false` and `sealed_test_accessed=false`. The inherited
authority check at lines 298-303 is not independent authentication because R7 receives R8's
`ReportBinding`; `str(binding)` is the same newly issued content URI.

The bounded reproduction wrote the intended payload, replaced it before `_bind_report()` with a
different regular single-link mode-`0400` JSON document that retained both sealed-safe flags, then
called the real R8 binder and consumer. Observed result:

```text
binding_matches_intended=false
binding_policy=REOPEN_AND_VERIFY_BEFORE_USE
consumed_map50=0.01
sealed_test_accessed=false
test_included=false
```

R8 returned and consumed the substituted metric document without error. This did not require a
hash collision: the evaluator itself minted a correct new SHA-256 binding for the wrong bytes.

The current tests replace or symlink the locator only **after** `_safe_write_report()` has already
returned a binding. Those attacks correctly fail. The writer-success test does not replace the
entry between predecessor completion and `_bind_report()`, and the evaluate test mocks both the
writer and consumer. Exact 17/17 PASS is therefore consistent with this finding.

Impact: corrected-validation metrics and gate fields can be substituted before binding and then
presented as fully descriptor-verified evidence. Because R8's stated purpose is to authorize
model-evaluation evidence, this is a High-severity blocker.

Required append-only repair:

- Pass the intended payload, or its independently computed canonical bytes/hash and size, into the
  binding step and require the opened descriptor to match that authority before issuing a
  `ReportBinding`.
- Keep consumption descriptor-bound and retain the strict schema, identity, mode, link-count,
  locator-policy and sealed-safe checks.
- Add a regression that replaces `REPORT_NAME` after predecessor publication but before binding;
  the successor must fail closed rather than mint a binding for the replacement.
- Ensure `evaluate()` continues to reconstruct every public metric and gate result only from the
  descriptor-consumed, intended-payload-authenticated report.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R8 and this immutable FAIL record | **YES** |
| Implement an append-only successor | **YES** |
| Run R8 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Treat 17/17 exact tests as QA PASS | **NO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run corrected validation on the existing registered pilot. Such a PASS would still not authorize
training, sealed-test access, final evaluation, model acceptance, deployment or publication.
