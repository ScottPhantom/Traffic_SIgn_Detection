# D1 corrected-validation evaluator R3 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)  
Status: `AWAITING_INDEPENDENT_QA`  
Boundary: `NO_REAL_EVALUATION_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Purpose

R3 is an append-only successor to the independently failed R2 evaluator. R1 and R2, together
with their QA records, remain unchanged. R3 may be used for real validation only after an exact
independent QA PASS.

## Pinned predecessor evidence

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r2.py` | `010bcc60c6b314c05fca308f521d287c998079c74c7154b20ef37225f1a0f2d8` |
| `detector/tests/test_corrected_val_r2.py` | `ce08d8b3276a76e572ff970559347dec51db01c471f137f2b3ed421f94d99b9e` |
| `docs/review/d1_corrected_val_r2_independent_qa_record.md` | `19ca3e92d9631d3ab45c195d16321c107c3462482143a39ef8ba36608614e28f` |

R2 findings pinned here are two High findings (transient swap-back input consumption and unsafe
report cleanup) and one Medium finding (early descriptor leakage).

## R3 candidate under review

| Artifact | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r3.py` | `7d356ed0bead2dedefcbe008ba2718d0a0d4ff65f26d94b35af162face993a34` |
| `detector/tests/test_corrected_val_r3.py` | `fc4e02733a52e5634c7cc86300b9d69c8d9ee6968b5d16f767564cb82efcd02d` |

## Remediation design

1. The registered checkpoint is opened with the R2 no-follow/hash guard and retained until all
   work finishes.
2. Every validation image and label is opened first, copied through its open descriptor, and
   compared with the governed expected SHA-256 before any consumer runs.
3. The checkpoint, 376 images, 376 labels and generated validation-only YAML are copied into an
   exclusive `0700` temporary snapshot. Both Ultralytics consumers receive only snapshot paths.
   The public corrected-data paths are never consumer inputs after the snapshot is complete.
4. Snapshot metadata records 754 files and a canonical roster hash. The snapshot is destroyed on
   leaving the evaluation scope before report publication begins.
5. Report publication uses a random exclusive partial, descriptor-relative hard-link publication,
   retained directory bindings and exact-inode rollback. A path not created by the invocation is
   never removed.
6. Descriptor ownership begins immediately after the checkpoint open and every acquired
   descriptor is closed in `finally` paths.

## Mechanical evidence before QA

- Ruff on the exact R3 source and tests: PASS.
- Exact R3 tests: **8/8 PASS**.
- Real authority check: 376 validation frames, 39 corrected frames, no test payload and
  `sealed_test_accessed=false`.
- Private snapshot smoke on the real registered pilot binding: **754 records**, 376 validation
  frames, roster SHA-256
  `5101f1cca2bd9f14abfc3eecd1ae3110543701dcaf40a76094755af244e554dc`.
- The smoke did not invoke model inference and did not create a report.

## Independent QA request

Reproduce all R2 attacks against the exact R3 hashes, especially transient swap/restore of the
checkpoint, image link, label, data root and parent; verify that no consumer sees replacement
bytes. Attack snapshot construction at every open/copy/hash boundary. Exercise pre-existing and
late report regular/symlink/hardlink collisions, failures at write/fsync/link/unlink/stat/relation
validation, exact before/after directory rosters, and descriptor counts for success and every
failure point. Confirm validation-only routing and absence of sealed-test access.

An independent PASS authorizes only a real validation run on the already registered pilot
`best.pt`. It does not authorize training, Drive upload, commit/push or sealed-test access.
