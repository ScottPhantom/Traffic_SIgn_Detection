# D1 corrected-validation evaluator R5 independent QA record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `INDEPENDENT_QA_FAIL`  
Reviewer: `Codex fresh independent source-QA session`  
Boundary: `READ_ONLY_NO_ADVERSARIAL_EXECUTION_NO_REAL_EVALUATION_NO_INFERENCE_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Verdict

**FAIL — 0 Critical, 1 High, 0 Medium and 0 Low findings.**

R5 closes the R4 cleanup and post-publication close-error findings, but its report candidate remains
addressed by the mutable pathname `report.partial`. The evaluator verifies bytes, inode identity and
link count through the retained descriptor, then publishes the object found at that pathname with
`renameatx_np(..., RENAME_EXCL)`. A same-user concurrent actor can replace the candidate directory
entry after the last descriptor check and before the rename. The exclusive rename protects only the
destination from replacement; it does not bind the source directory entry to the verified descriptor.

R5 therefore remains **NO-GO** for real corrected-validation inference. Preserve R1–R5 and their QA
records; repair this issue only in an append-only successor and submit the successor's exact bytes to
fresh independent QA.

`sealed_test_accessed=false` throughout this review.

## Exact reviewed inputs

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r5.py` | `8d726cbdb31b610ca406e65d3231123d2099a8762cbdf300699dc188a17b1e40` |
| `detector/tests/test_corrected_val_r5.py` | `9e8cce57d7a9ef4c42fc11aa016e4a692dbcb433e2ed9e59d8dd543086e4fde5` |
| `docs/review/d1_corrected_val_r5_qa_remediation_report.md` | `a8cac472e75843323a8c2a959c12058bdd59689e9f42eed4f1a26f0eb3f2c03d` |
| `docs/review/d1_corrected_val_r4_independent_qa_record.md` | `ff6b3bc258500198b7b782beb21755b8cba6799c140c27a1c50fa0c1ea368021` |

All four hashes matched the requested pins before review. No reviewed implementation, test,
remediation or predecessor-QA file was modified. This append-only record is the only QA-authored
repository artifact.

## Review performed

- `PROJECT_MEMORY.md`, the R5 remediation record and the pinned R4 FAIL record were read before the
  source review.
- `graft check .` reported the wiring graph synchronized. A freshness-aware Graft query identified
  `_safe_write_report()` as the report-publication path.
- Source reasoning traced the retained descriptor checks at lines 387–400 and the later pathname
  rename at lines 402–407 of `detector/m1/corrected_val_r5.py`.
- The supplied exact-suite observation is **10/10 PASS**. This QA did not rerun the suite and, per
  the review boundary, did not execute a new adversarial reproduction.
- No model inference, corrected-validation evaluation, training, upload, download, commit, push or
  sealed-test operation was performed.

Green mechanical tests do not establish the missing atomic binding between the verified descriptor
and the pathname consumed by the rename.

## Verified retained properties

- R5 creates a private `0700` staging directory and requires it to be on the run filesystem.
- The candidate descriptor is opened with `O_EXCL` and `O_NOFOLLOW`, and the initially opened object
  must be a regular single-link file.
- Candidate bytes are written, fsynced and rehashed through that descriptor.
- Final-name collisions are rejected atomically by `RENAME_EXCL`; an existing final regular file,
  symlink or hardlink is not overwritten.
- The report-publication path contains no pathname deletion. Descriptor-close errors after a
  successful publication do not reverse the returned success.
- The parser remains validation-only and the report payload declares `test_included=false` and
  `sealed_test_accessed=false`.

These properties are useful but do not close the source-path race described below.

## Finding

### QA-D1-CORR-VAL-R5-001 — High — the published source pathname is not bound to the verified descriptor

`_safe_write_report()` opens `report.partial` and stores the original `fstat()` result at lines
387–390. It writes and fsyncs the candidate, verifies the descriptor hash at lines 395–398, and
checks that a second `fstat(temp_fd)` still identifies the originally opened inode at lines 399–400.
It then validates directory relations and calls `_rename_exclusive(staging_fd, "report.partial",
root_fd, REPORT_NAME)` at lines 401–407.

The final syscall resolves `report.partial` from the staging-directory namespace at rename time. It
does not rename `temp_fd`. Between the last descriptor check and that lookup, a same-user concurrent
actor can:

1. move or unlink the verified `report.partial` entry while the evaluator still holds `temp_fd`;
2. install a different regular file, hardlink or symlink at the same candidate name; and
3. let `RENAME_EXCL` publish that replacement under the final report name.

The evaluator then sets `final_published=True` and returns without opening or stating the final name,
without proving that it references `owned`, without checking `st_nlink == 1`, and without hashing the
published inode. Consequently the final report's bytes, file type, inode and link count can differ
from the object whose bytes were verified.

The random temporary-directory name and mode `0700` reduce accidental interference, but they do not
form an isolation boundary against another process running as the same operating-system user.
`RENAME_EXCL` guarantees destination non-replacement only; it provides no compare-and-rename
condition for the source inode.

The current R5 tests cover destination insertion immediately before rename and correctly prove that
an Owner destination is not overwritten. They do not replace the **source** candidate after its last
descriptor check. Descriptor-copy tests similarly protect evaluator inputs, not the report
publication source name. The observed 10/10 PASS therefore does not exercise this finding.

Impact: an evaluation command can return success while publishing bytes or a link topology that is
not bound to the computed report payload. Because this file is intended to carry model-evaluation
evidence and subsequent gate decisions, loss of publication integrity is a High-severity blocker.

Required append-only repair:

- Do not authorize a later pathname publication from an earlier descriptor observation; an
  additional pre-rename `stat()` alone would retain the same race.
- Prefer reserving the final name directly with `O_CREAT | O_EXCL | O_NOFOLLOW` and mode `000`, then
  write, fsync and hash through the retained descriptor.
- Before making the report readable, verify through the run-directory descriptor that the final
  name still references the retained inode, is regular and has exactly one link. Make a descriptor
  permission transition the publication event, then fsync and verify the inode/hash again.
- On failure, do not unlink a pathname based on an earlier inode observation. Leave any owned final
  reservation unreadable for explicit recovery if conditional deletion cannot be guaranteed.

This repair description is a requirement for a successor, not a review or approval of any existing
R6 implementation.

## Authorization boundary

| Action | QA disposition |
| --- | --- |
| Preserve R5 and this immutable FAIL record | **YES** |
| Implement an append-only successor | **YES** |
| Run R5 on the registered pilot `best.pt` | **NO-GO** |
| Run any real corrected-validation inference | **NO-GO** |
| Train or retrain | **NO-GO** |
| Access, export or upload sealed test | **NO-GO** |
| Treat the observed 10/10 test result as QA PASS | **NO** |
| Commit/push for operational use | **NO-GO** |

Only a fresh independent QA PASS on an append-only successor may authorize the Owner workflow to
run corrected validation on the existing registered pilot. Such a PASS would still not authorize
training, sealed-test access, final evaluation, model acceptance, deployment or publication.
