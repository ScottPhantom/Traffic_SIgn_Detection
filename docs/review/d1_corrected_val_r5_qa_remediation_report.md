# D1 corrected-validation evaluator R5 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `AWAITING_INDEPENDENT_QA`  
Boundary: `NO_REAL_EVALUATION_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Purpose

R5 is the append-only successor to R4. R4 remains immutable `INDEPENDENT_QA_FAIL` because its
pre-publication cleanup could delete an Owner replacement and an injected descriptor-close failure
after atomic publication could make the caller observe failure while the final report existed.

## Pinned predecessor evidence

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r4.py` | `5d3f69b8fa6e150acfc9fbf7d9ca1b9aa8e0af1c43538c175125e3dbe3a88e18` |
| `detector/tests/test_corrected_val_r4.py` | `50614fe194e4218f537f096ed1ad69dad530e143cf94ab107f044c5974c99e4a` |
| `docs/review/d1_corrected_val_r4_independent_qa_record.md` | `ff6b3bc258500198b7b782beb21755b8cba6799c140c27a1c50fa0c1ea368021` |

## R5 candidate under review

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r5.py` | `8d726cbdb31b610ca406e65d3231123d2099a8762cbdf300699dc188a17b1e40` |
| `detector/tests/test_corrected_val_r5.py` | `9e8cce57d7a9ef4c42fc11aa016e4a692dbcb433e2ed9e59d8dd543086e4fde5` |

## R5 remediation policy

1. A `0700` staging directory is allocated under the operating-system temporary root, outside the
   repository and run directory, and checked to be on the same filesystem as the run directory.
2. The report candidate is written, fsynced and rehashed through retained descriptors inside that
   staging directory. The run directory sees no partial name.
3. `renameatx_np(..., RENAME_EXCL)` atomically moves the candidate to the fixed report name as the
   final mutating publication syscall. It cannot replace an existing regular file, symlink or
   hardlink.
4. R5 performs no pathname deletion at all. On any pre-publication failure it deliberately leaves
   the private temporary evidence for the operating system's temporary-file lifecycle rather than
   risk deleting an Owner replacement. The repository and run-directory roster remain unchanged.
5. After successful publication, all descriptor-close errors are collected but cannot reverse the
   successful outcome. No fallible mutating syscall follows publication.
6. The QA-passed parts of R3/R4 remain: both model consumers read only the 754-entry verified
   private input snapshot, which is destroyed before report publication.

## Mechanical evidence before QA

- Ruff on exact R5 source/tests: PASS.
- Targeted non-authority tests: **9/9 PASS**.
- A pre-existing run-directory partial with a similar name is preserved unchanged.
- Injected pre-publication relation failure leaves the run directory empty and preserves only the
  evaluator candidate in its private OS-temp staging directory; no unlink is called.
- Final replacement immediately before atomic rename fails with `EEXIST`; Owner bytes remain.
- Injected temporary-fd close failure after successful publication is absorbed; the call returns
  success with one final report and continues closing retained descriptors.
- No model inference, training, upload, commit/push or sealed-test access occurred.

## Independent QA request

Re-run the complete R4 matrix on these exact hashes. Verify that no `unlink`/`remove`/`rmtree`
exists in the report publication path, all pre-publication failures leave the run directory exact,
concurrent/final replacements cannot be overwritten or deleted, and close/rmdir failures after
publication cannot produce false failure. Reconfirm snapshot attacks, descriptor accounting, real
R4 data authority, registered pilot binding, validation-only parser, full detector gates and
absent sealed-test log. Treat private OS-temp residue as the explicit fail-safe policy; confirm it
contains only evaluator-owned candidate bytes and no governed input or model data.

Only an independent PASS may authorize local corrected-validation inference on the already
registered pilot `best.pt`. It does not authorize training, Drive upload, commit/push or sealed-test
access.
