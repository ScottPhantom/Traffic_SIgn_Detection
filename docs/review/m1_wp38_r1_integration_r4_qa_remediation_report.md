# M1-WP38-R1 downstream integration R4 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Scope

The initial, R1, R2 and R3 packages and their QA `FAIL` records remain immutable. R4 addresses
only R3 finding H-1-R3: verification was not bound to the marker, output-root and parent inodes
that had actually been checked or created.

## H-1-R3 remediation

R4 opens every existing component of the absolute output path with `O_NOFOLLOW`, retains the
complete descriptor chain, and records every parent/name/child relationship. The verifier opens
`EXPORT_COMPLETE.json` relative to the retained root descriptor, reads its bytes from that exact
descriptor, requires a single-link regular file, and revalidates the marker inode both before and
after the full semantic replay.

The train/validation tree is no longer accepted through a second path-based verifier. R4 opens
`images`, `labels`, `train` and `val` relative to retained descriptors; requires exact directory
rosters; validates every image symlink target and governed source hash; reads every label and
`data.yaml` from bound no-follow regular-file descriptors; and revalidates all retained directory
bindings before return. Test directories are excluded by the exact root/split rosters.

During materialisation, R4 captures the device/inode of the root created by the writer. Final
verification must open that same public root inode. A pre-existing valid replacement tree can no
longer receive `verified=true` for work written into a detached original tree.

## Attack regression

- Same-byte regular-file, symlink and hardlink marker replacement during semantic replay: rejected.
- Complete output-root replacement during semantic replay: rejected.
- Output-parent replacement during semantic replay: rejected.
- Valid public tree with an identity different from the materialiser-created root: rejected.
- Existing output destination: rejected; export remains new-output-only.
- No `export-test` or `--final-eval` command exists.

## Current materialised candidate

- Output: `data/processed/m1_yolo_wp38_r1_integration_r4/`.
- Train: 3,712 image symlinks and 3,712 regular labels (1,912 governed real images plus 1,800
  WP35 train-only images).
- Validation: 376 image symlinks and 376 regular labels.
- Corrected validation: exactly 39 governed WP38-R1 derivatives, stems `1319..1357`.
- Test directories/files: absent.
- Completion marker: exact R4 schema and counts.
- Materialiser and independent replay before QA: `valid=true` / `verified=true`.
- `sealed_test_accessed=false`; sealed-test access log absent.

## Exact review hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py` | `0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json` | `6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602` |
| `tests/test_m1_wp38_r1_integration_r4.py` | `98edd4001d288053de9c405728daf71871472c6f0fdd4871b4731146fc1979cf` |
| R3 independent QA `FAIL` record | `2e5820573e8efcac03b176fdf79717ef74604c81700e98ac5d046b2b8825fc17` |

## Local validation before independent QA

- R4 test module: PASS, including full materialisation and descriptor-bound replay.
- R4 export: `verified=true`, exact counts above.
- Ruff on the R4 exporter, tests and verifier registry: PASS.
- Sealed test was not enumerated, exported, opened or evaluated.

## QA gate

Independent QA must reproduce the R3 regular/symlink/hardlink marker swaps, root and parent swaps,
and the active writer-parent replacement attack against the exact hashes above. It must also
verify the exact train/validation/correction roster, descriptor cleanup, authenticated Dataset
Graph authorities, no-test boundary and sealed-test log absence. Only a fresh QA `PASS` may permit
a separate clean-commit bundle successor and corrected-validation evaluation. It does not
authorize training, Drive upload, commit/push or sealed-test access.
