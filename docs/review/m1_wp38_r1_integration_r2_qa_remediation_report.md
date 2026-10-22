# M1-WP38-R1 downstream integration R2 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Scope and preserved history

The initial integration and R1 remain immutable evidence with independent QA `FAIL` records. R2
addresses only R1 finding H-1-R1 (staging-path TOCTOU). The authenticated Dataset Graph wrapper
from R1 is reused byte-for-byte because independent QA confirmed M-1 closed.

## H-1-R1 remediation

R2 removes pathname-based staging writes. It creates a new output directory, opens it with
`O_DIRECTORY|O_NOFOLLOW`, pins its device/inode identity, and performs every descendant operation
relative to retained directory descriptors:

- `mkdir(..., dir_fd=...)` for every directory;
- `open(..., O_EXCL|O_NOFOLLOW, dir_fd=...)` for labels, YAML and completion marker;
- `symlink(..., dir_fd=...)` for image links;
- device/inode comparison after every directory create/open;
- root identity checks before and after the final completion marker;
- `EXPORT_COMPLETE.json` is written last and is mandatory for verification.

Therefore replacing the output pathname with a symlink after the directory is opened does not
redirect any write. A deterministic attack renames the open directory, replaces the old path
with `output -> victim`, creates directories and writes through the retained descriptors, and
proves the byte lands in the detached original inode while the victim remains unchanged. The
identity check then fails closed. A hardlinked final leaf is rejected by exclusive creation.

An interrupted output has no completion marker, is not trusted by verification, and is never
silently reused because future exports require a new output path.

## Current readback

- Local output: `data/processed/m1_yolo_wp38_r1_integration_r2/`.
- Train: 3,712 images (1,912 real + 1,800 WP35).
- Validation: 376 images, exactly 39 corrected PNG derivatives.
- Test directories/files: absent.
- `EXPORT_COMPLETE.json`: present and reports `test_included=false`,
  `sealed_test_accessed=false`.
- Export verification: `valid=true`.
- Sealed-test access log: absent.
- Graft: rebuilt and synchronized, 3,396/3,396 wiring nodes.

## Exact review hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py` | `a26f1ee3a778086cef35fcd56df7df508dbdaee58d23ba34decba49de264ae4c` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r2_manifest.json` | `7538697ba4fcdf59d86f62b7ce867ee0c609042a1d25922d2ff959607bc6f9de` |
| `tests/test_m1_wp38_r1_integration_r2.py` | `77064cae59d61b3ce80735a6d9f04c7bd95cb8b3b76f06a525e452cc38087748` |
| authenticated graph wrapper (unchanged) | `6763c8d7fd22004773bbac84067f39d0b85c88df5c049759de9250bf433431dc` |
| R1 independent QA `FAIL` record | `245ceb491886a79c121595f65b751f85fbc3a18f4d26461f0afeedc14cfc0b8d` |

## Required independent QA decision

QA must reproduce the pathname-swap race after output open, verify all writes remain anchored to
the original inode, attack child-directory/leaf creation, verify incomplete output rejection,
reconfirm the graph authorities and train/val-only contract, and issue `PASS` or `FAIL`. Only a
`PASS` permits a separate clean-commit bundle successor and corrected-validation evaluation. It
does not authorize new training, Drive upload, commit/push or sealed-test access.
