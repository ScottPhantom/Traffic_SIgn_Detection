# D1 corrected-validation evaluator R2 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `VALIDATION_ONLY_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Scope

Evaluator R1 and its QA `FAIL` record remain immutable. R2 addresses H-1 and H-2 from that record:
long-running inference could reopen pathnames after preflight, and report output could follow a
symlink introduced after the no-overwrite check.

## H-1 use-time binding

R2 retains a no-follow descriptor for the registered `best.pt` and no-follow descriptors for the
complete corrected-data path chain throughout inference. It computes a full pre-run fingerprint of
`data.yaml`, all 376 image links and their regular targets, and all 376 labels, including inodes,
targets and content hashes. Before any report is written it:

1. reruns the full descriptor-bound R4 materialised verifier;
2. rebinds `best.pt` through the committed run registry;
3. recomputes the complete input fingerprint;
4. verifies the retained weight descriptor, public weight pathname and retained data-directory
   relationships still identify the same objects.

The R1 report write is intercepted in memory. Any changed binding aborts before a result file is
created. The accepted report records the input fingerprint, weight inode/hash and equal pre/post
authority state.

## H-2 report publication

R2 writes a same-directory partial with `O_CREAT|O_EXCL|O_NOFOLLOW` relative to a retained run
directory descriptor. It publishes with descriptor-relative `link()`, which atomically fails if any
regular file, symlink or hardlink already occupies the final name, then removes the partial. It
never opens the final report pathname for writing. The final inode/link count and complete run
directory chain are revalidated before return.

## Current evidence

- Weight replacement after opening: rejected.
- Pre-existing report symlink: rejected; external owner bytes unchanged.
- Report symlink created at publication: rejected; external owner bytes unchanged; partial removed.
- Authentic report: exact regular single-link file.
- Targeted R2 tests: 6/6 PASS.
- R4 authority check: PASS; 376 validation frames, 39 corrected frames, no test.
- No real model evaluation has run; sealed-test access log remains absent.

## Exact QA inputs

| File | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r2.py` | `010bcc60c6b314c05fca308f521d287c998079c74c7154b20ef37225f1a0f2d8` |
| `detector/tests/test_corrected_val_r2.py` | `ce08d8b3276a76e572ff970559347dec51db01c471f137f2b3ed421f94d99b9e` |
| Evaluator R1 independent QA FAIL record | `cda54add52e2cd2c672446f92e8cb1380a1bd30110c7fb86e33011146f2248ab` |

## Gate

Independent QA must reproduce weight/data identity changes during a mocked long evaluation,
pre-existing and late report substitutions, descriptor cleanup, R4 authority, metric parity and
the validation-only surface. Only a QA PASS permits running R2 against the registered pilot
`best.pt`; it does not authorize new training or sealed-test access.
