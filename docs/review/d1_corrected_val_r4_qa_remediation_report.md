# D1 corrected-validation evaluator R4 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `AWAITING_INDEPENDENT_QA`  
Boundary: `NO_REAL_EVALUATION_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Purpose

R4 is the append-only successor to R3. R3 remains immutable `INDEPENDENT_QA_FAIL` because its
descriptor-relative report rollback used a non-atomic `stat` followed by `unlink`, allowing a
replacement Owner file to be deleted. R4 preserves the R3 private-snapshot input design and
replaces report publication.

## Pinned predecessor evidence

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r3.py` | `7d356ed0bead2dedefcbe008ba2718d0a0d4ff65f26d94b35af162face993a34` |
| `detector/tests/test_corrected_val_r3.py` | `fc4e02733a52e5634c7cc86300b9d69c8d9ee6968b5d16f767564cb82efcd02d` |
| `docs/review/d1_corrected_val_r3_independent_qa_record.md` | `d8624a2beaf998d051e55952acab1407895e43a6980f61527089633e038e7b93` |

## R4 candidate under review

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r4.py` | `5d3f69b8fa6e150acfc9fbf7d9ca1b9aa8e0af1c43538c175125e3dbe3a88e18` |
| `detector/tests/test_corrected_val_r4.py` | `50614fe194e4218f537f096ed1ad69dad530e143cf94ab107f044c5974c99e4a` |

## R4 publication design

1. The report is fully serialized, written, fsynced, rehashed and checked against retained
   directory relations under a random exclusive partial name.
2. macOS `renameatx_np(..., RENAME_EXCL)` then moves the verified partial to the fixed report name
   in one atomic no-replace operation. A destination that appears before the syscall makes the
   call fail with `EEXIST`; it is never overwritten or deleted.
3. The atomic rename is the final mutating publication operation. R4 never runs `stat` then
   `unlink` against the final report name and never rolls the final name back by pathname.
4. Descriptor closes after successful publication are non-authoritative cleanup and cannot turn
   an already atomically published report into a reported failure.
5. The R3 private snapshot is still destroyed before report publication starts. Model inference
   consumes only the 754-entry verified private snapshot, never public data/checkpoint paths.

## Mechanical evidence before QA

- Ruff on exact R4 source/tests: PASS.
- Targeted non-authority tests: **8/8 PASS**.
- Nominal publication produces exactly one final file and performs zero post-publication unlinks.
- Injected final replacement immediately before the atomic rename returns `EEXIST`; the unique
  Owner bytes remain at the report name and no evaluator partial remains.
- Pre-existing final symlink remains unchanged; relation failure before publication rolls back the
  evaluator-owned random partial.
- No model inference, training, upload, commit/push or sealed-test access occurred.

## Independent QA request

Re-run the complete R3 QA matrix on these exact hashes. In particular, interpose a final
regular/symlink/hardlink immediately before `renameatx_np`, attempt replacement concurrently with
the syscall, inject all pre-publication failures, and prove there is no syscall after successful
publication that can generate a false failure or delete/overwrite another inode. Reconfirm the
private-snapshot swap-back defenses, descriptor equality, real R4 data authority, registered
pilot binding, validation-only parser, full detector gates and absent sealed-test log.

Only an independent PASS may authorize local corrected-validation inference on the already
registered pilot `best.pt`. It does not authorize training, Drive upload, commit/push or sealed-test
access.
