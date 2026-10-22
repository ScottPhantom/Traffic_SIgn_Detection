# D1 corrected-validation evaluator R2 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-QA session`  
Boundary: `READ_ONLY_NO_REAL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 2 High, 1 Medium and 0 Low findings.**

R2 correctly rejects persistent weight changes and regular/symlink/hardlink occupation of the
final report name. It also preserves the R1 validation-only parser, R4 authority, registered pilot
binding, CCW90 transformation and metric flow. It does not close R1 H-1 against transient
swap-and-restore attacks, leaks descriptors on failures before its `try/finally`, and can delete an
owner-created partial or leave report artifacts after publication failures.

The corrected-validation evaluator remains **NO-GO**. Preserve R1, its FAIL record, R2 and this
FAIL record; implement an append-only R3 and submit its exact bytes to fresh independent QA.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r2.py` | `010bcc60c6b314c05fca308f521d287c998079c74c7154b20ef37225f1a0f2d8` |
| `detector/tests/test_corrected_val_r2.py` | `ce08d8b3276a76e572ff970559347dec51db01c471f137f2b3ed421f94d99b9e` |
| R1 independent QA FAIL record | `cda54add52e2cd2c672446f92e8cb1380a1bd30110c7fb86e33011146f2248ab` |
| `docs/review/d1_corrected_val_r2_qa_remediation_report.md` | `f4935e5890e4f47960c39fb8d7572946076b8819b940edb4ba761bfd5e12d489` |
| pinned R1 evaluator | `0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5` |
| pinned R4 integration exporter | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

All requested hashes matched before and after review. No reviewed source was modified.

## Verified nominal properties

- Real R4 authority/materialised verification passed: 376 validation frames, exactly 39 corrected
  frames, train/validation-only data, `test_included=false` and `sealed_test_accessed=false`.
- The real registered pilot `best.pt` remains bound to seed `20261018`, weight SHA-256
  `5d5815a96218759e93cd9bc51261ed55778da5397dfe7fe25c1f78908b10b633`, run-contract SHA-256
  `9f8fc94c471addcd540b9efded730e1dcfb0ce9da820b820343ecc44d0810b88`, attestation SHA-256
  `7fa5df339676adaae220e1963916b2e48e2525455713d500db5d76343e2fc9fc` and registry SHA-256
  `ba5ab04fd6e28e849a6b1aaf345bb5e284eb2a7aa1ee9c7cee0714209ed2b0c9`.
- Parser choices remain exactly `check` and `evaluate`; there is no train/test/final-eval route.
- R2 hash-pins and delegates to the exact reviewed R1 evaluator, so metric construction and the
  bounded one-image-at-a-time prediction flow are unchanged.
- The governed UNKNOWN boxes on corrected stems `1319..1328` retain the R1 normalized CCW90
  transform `x'=y, y'=1-x, w'=h, h'=w` before pixel conversion.
- Final-name occupation by pre-existing and late-created regular files, symlinks and hardlinks was
  independently rejected with `FileExistsError`; external owner bytes were unchanged and the R2
  partial was absent after those six attacks.
- Nominal publication produced exactly one regular, single-link final report and no partial.

## Findings

### QA-D1-CORR-VAL-R2-001 — High — transient swap-back defeats the claimed use-time binding

R2 retains descriptors and compares complete pre/post fingerprints, but both Ultralytics and the
R1 frame loader still consume public pathname strings. A retained descriptor proves what stayed
open; it does not force the consumer to read from that descriptor. Pre/post equality cannot detect
an object that is replaced, consumed and restored with its original inode before the post-check.

Fresh local mock attacks independently performed that exact sequence for all requested surfaces:

| Surface replaced during mocked evaluation | Bytes consumed by mock | R2 outcome |
| --- | --- | --- |
| registered `best.pt` | `EVIL-WEIGHT` | report published; `use_time_binding_verified=true` |
| validation image symlink | `EVIL-IMAGE` | report published; `use_time_binding_verified=true` |
| validation label | `EVIL-LABEL` | report published; `use_time_binding_verified=true` |
| corrected-data root | `EVIL-ROOT` | report published; `use_time_binding_verified=true` |
| corrected-data parent | `EVIL-PARENT` | report published; `use_time_binding_verified=true` |

Each attack renamed the governed object aside without changing its inode, installed and consumed a
replacement at the public pathname, removed the replacement, and renamed the original object back
before post-verification. The final fingerprint, retained descriptor and public relation checks all
matched, demonstrating that H-1 remains open.

Required repair:

- build evaluator-owned private, exclusive, no-follow snapshots from already-opened verified
  descriptors and make both YOLO instances and the frame loader consume only those snapshot paths;
- bind the snapshot hashes/roster into the report and destroy the private snapshot after use;
- retain all five swap-back tests and require failure before report publication.

### QA-D1-CORR-VAL-R2-002 — High — report failure cleanup deletes owner paths or leaves artifacts

`_safe_write_report()` unconditionally unlinks the partial name on failure while `linked` is false,
even when `O_EXCL` failed because that partial existed before the call. Independent tests showed
that pre-existing partial regular, symlink and hardlink directory entries were all deleted. R2 did
not create those entries and therefore has no authority to remove them.

The opposite failure also occurs after `os.link()` sets `linked=true`:

- an injected failure removing the partial left both final and partial, linked to the same inode
  with link count 2;
- an injected final relation-validation failure left the final report present even though
  `_safe_write_report()` raised.

Thus a failed invocation can destroy an owner path or leave a report that appears successful and
blocks a clean retry.

Required repair:

- track explicit ownership separately from publication state; unlink a partial only if this
  invocation successfully created that exact inode;
- on every failure after publication, remove only the exact final inode created by this invocation
  through the retained directory descriptor, without touching a replacement object;
- add pre-existing partial regular/symlink/hardlink tests, injected unlink/fsync/link/stat/relation
  failures, final replacement races and exact before/after directory-roster assertions.

### QA-D1-CORR-VAL-R2-003 — Medium — early guard failures leak retained descriptors

The cleanup `try/finally` begins only after opening the data-directory chain, weight guard and full
input fingerprint. If `_open_weight_guard()` or `_input_fingerprint()` raises, no cleanup path owns
the descriptors already opened.

Independent reproduction opened the corrected-data path chain, then supplied a symlink as the
registered weight. The guard correctly raised `registered best.pt is not a single-link regular
file`, but `/dev/fd` increased from 4 to 9: five descriptors leaked.

Required repair:

- establish descriptor ownership and the outer `try/finally` immediately after the first
  successful open;
- close every acquired descriptor in reverse order on failures at each acquisition/fingerprint
  step, without masking the primary exception;
- add exact `/dev/fd` equality tests for all injected failure points and successful completion.

## Mechanical evidence

```text
graft check .
graft ask "Trace corrected_val_r2 end-to-end..." --source .
cd detector && uv run ruff check m1/corrected_val_r2.py tests/test_corrected_val_r2.py
cd detector && uv run pytest -q tests/test_corrected_val_r2.py
cd detector && uv run ruff check m1 tests && uv run pytest -q && uv lock --check
uv lock --check
```

Observed results:

- exact R2 tests: **6/6 PASS**;
- full detector suite: **119/119 PASS**;
- Ruff and root/detector locks: **PASS**;
- Graft graph: synchronized after the freshness-aware query;
- exact sealed-test access log: absent before and after QA.

The nominal tests do not cover swap-and-restore consumers, pre-existing partial ownership,
post-publication cleanup failures or early acquisition leaks.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R2 and this FAIL record | **YES** |
| Implement append-only evaluator R3 | **YES** |
| Run R2 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train/retrain | **NO-GO** |
| Access/export/upload sealed test | **NO-GO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run validation on the existing registered `best.pt`. It would not authorize training or any
sealed-test action.
