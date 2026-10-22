# D1 corrected-validation evaluator R7 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-and-test QA session`  
Boundary: `NO_NEW_ADVERSARIAL_SIMULATION_NO_MODEL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R7 implements the stated post-publication round trip: it freshly opens the run-directory chain,
opens the report through retained-directory and lexical authorities, requires the same regular
single-link mode-`0400` inode, hashes both descriptors against the canonical payload, revalidates
relations, and rechecks the final entry under the retained directory descriptor. Those checks
correctly reject an ancestor swap that exists before the round trip begins.

They do not, however, establish the stable namespace boundary required by the pinned R6 FAIL
record. The last relation validation is another point-in-time check, and the last final-entry check
uses only the retained `root_fd`. A same-user mutation after that validation/check and before the
lexical `Path` is consumed can still make the returned path name another object. R7 therefore
remains **NO-GO** for real corrected-validation inference.

No new adversarial simulation was performed in this review, as explicitly required. The finding
is based on source reasoning against the pinned R6 requirement. `sealed_test_accessed=false`
throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r7.py` | `3ec7a92fc49817af71273575f36df3471bc3d28276f3dc11f37ccd7f40a9ac29` |
| `detector/tests/test_corrected_val_r7.py` | `2e8962702e60e60f644945334dedef5950375618211731836bd083a5f17f7290` |
| `docs/review/d1_corrected_val_r7_qa_remediation_report.md` | `8fd4faf0fe9a066c79ec497f130d45667104f190563f942b953011b4b1ffdfcf` |
| `docs/review/d1_corrected_val_r6_independent_qa_record.md` | `10605012f01234c7a1ac6bb7a4c72b61e0045daec6fb0d7780948e567f8d296b` |

All four hashes matched the requested pins before and after review. No reviewed source, test,
remediation or predecessor-QA file was modified. This append-only record is the only QA-authored
repository artifact.

## Review performed and evidence limits

- Read `PROJECT_MEMORY.md`, the R7 remediation record and the pinned R6 independent QA record.
- Used a freshness-aware Graft query before source review. The query refreshed the graph for R7;
  the closing `graft check .` reported the wiring graph in sync.
- Traced `_safe_write_report()`, `_verify_public_round_trip()`, the inherited R6 publication path,
  exact-byte construction, both descriptor opens, inode/mode/link checks, both hashes, relation
  validation, final-entry binding, close behavior and parser boundary.
- Ran `ruff` on the exact R7 source and test: PASS.
- Ran the exact R7 suite: **6/6 PASS**.
- Ran the R6 publication regressions excluding the duplicate authority check: **11/11 PASS**.
- Ran `uv lock --check` in `detector/`: PASS.
- The supplied statement that the full detector suite passed before R7 existed is historical PM
  evidence, not an independent R7 full-suite result. This QA did not rerun that suite.
- This QA did not perform a new adversarial simulation, model inference, corrected-validation
  evaluation, training, upload, download, commit, push or sealed-test operation.

## Verified R7 properties

- R7 pins the exact R6 implementation, tests, remediation and independent FAIL record before its
  public entry points may run.
- `_safe_write_report()` temporarily changes the predecessor report name, delegates publication to
  R6, restores the predecessor name even if R6 fails, and only then invokes the fresh round trip.
- `_verify_public_round_trip()` freshly obtains retained directory authority and validates its
  relations before opening the report.
- It opens the report once relative to retained `root_fd` and once through
  `run_dir / REPORT_NAME`, using read-only and `O_NOFOLLOW` flags.
- Both opened objects must be regular, have exactly one link, have mode `0400`, identify the same
  device/inode pair and independently hash to the exact canonical JSON payload.
- Relations are validated again after both hashes, and the current final entry under retained
  `root_fd` must still identify the retained report inode.
- Existing tests cover exact successful publication, an ancestor swap immediately after R6
  publication, a public final-name symlink, predecessor-name restoration on failure, the
  validation-only parser and sealed-safe authority data.
- The CLI remains validation-only (`check` and `evaluate`). The authority check returned
  `val_frames=376`, `corrected_frames=39`, `test_included=false` and
  `sealed_test_accessed=false`.

These are material improvements over R6, but they do not close the pinned requirement that a
returned lexical path have a stable authority through downstream consumption.

## Finding

### QA-D1-CORR-VAL-R7-001 — High — the returned lexical path still has no stable namespace authority

`_verify_public_round_trip()` opens the retained-directory and lexical report descriptors at lines
86-98 of `detector/m1/corrected_val_r7.py`. It proves their file type, link count, mode, identity
and canonical hashes at lines 99-110. It then validates ancestor relations at line 111 and checks
the final entry relative to retained `root_fd` at lines 112-114.

That final entry check is not a fresh lexical lookup. It says that `REPORT_NAME` still identifies
the retained inode **inside the directory held open by `root_fd`**. If the public `run_dir`
relation changes after line 111, line 112 still succeeds against the detached retained directory.
After line 114, any ancestor or final entry may also change before `_safe_write_report()` returns
the predecessor's lexical `output` at lines 124-133. No descriptor or stable directory authority
is transferred to the consumer.

The pinned R6 QA record explicitly required either one descriptor-bound authority for publication
and consumption or a trusted/stable namespace boundary, and warned that finite point-in-time
ancestor checks do not make a same-user-mutable path durable. R7 adds more point-in-time checks but
implements neither required boundary.

The R7 ancestor-swap test at lines 68-89 of `detector/tests/test_corrected_val_r7.py` changes the
directory immediately after predecessor publication and before `_verify_public_round_trip()`
opens it. That is correctly rejected. The test does not cover a relation change after the second
validation at line 111 or after the final retained-entry check. Its 6/6 PASS is therefore
consistent with this static finding.

Impact: a command can finish its integrity checks while the returned path subsequently resolves to
different bytes, inode identity or permissions. Downstream review and gate logic are still asked
to trust a mutable name rather than the verified descriptor-bound object. Because the report is
model-evaluation evidence, this remains a High-severity authorization blocker.

Required append-only repair:

- Do not treat a finite final relation check as durable proof for a lexical `Path` in a namespace
  writable by the same-user threat actor.
- Make publication and immediate downstream consumption use one descriptor-bound authority, or
  place the report behind a demonstrably stable namespace boundary before returning a path.
- Add a normal deterministic regression for relation change at the final validation/return
  boundary without weakening R6's collision preservation, exact-byte/hash, single-link,
  mode-`0400`, failure quarantine and sealed-safe behavior.
- Preserve R7's dual-open/hash round trip as defense in depth.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R7 and this immutable FAIL record | **YES** |
| Implement an append-only successor | **YES** |
| Run R7 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Treat 6/6 exact tests as QA PASS | **NO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run corrected validation on the existing registered pilot. Such a PASS would still not authorize
training, sealed-test access, final evaluation, model acceptance, deployment or publication.
