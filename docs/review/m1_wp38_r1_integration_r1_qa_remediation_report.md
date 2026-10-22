# M1-WP38-R1 downstream integration R1 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Scope

This append-only successor preserves the initial integration and its independent `FAIL` record.
It addresses only findings H-1 and M-1 from that review. It does not authorize training,
evaluation, an official Colab archive, Drive upload, commit/push or sealed-test access.

## H-1 remediation: writable-path safety

`scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py` replaces the predecessor's writable
flow with these fail-closed rules:

- the output must be new;
- every existing output-parent component is walked lexically and checked with `lstat()`;
- symlinks, regular files and special files in directory positions are rejected;
- all output directories are created inside a private sibling staging tree;
- labels and `data.yaml` use exclusive, no-follow regular-file creation and require link count 1;
- image symlinks are created only at new leaves inside the private tree;
- the complete tree is promoted atomically with `os.replace()`;
- a failed build removes only its unique staging tree and never touches an existing output.

Attack tests cover a linked parent, output root, `images`, `labels`, split directory and final
leaf. Each attack is rejected before victim mutation. Existing regular output is also preserved.

## M-1 remediation: authenticated Dataset Graph authorities

`src/cpv301_autodrive/dataset01_view_r1.py` is the current application wrapper. Before rendering
an authority badge it verifies exact SHA-256 pins for WP36-R1 split/manifest/QA, the D02 registry,
and WP38-R1 manifest/QA. It then validates:

- exact CSV schemas and unique/exhaustive 3,215-stem rosters;
- split counts 1,912 train, 376 val, 903 test and 24 listed quarantined frames, while raw 0248
  remains absent from the governed split and is displayed as quarantined;
- exact split-list hashes and sealed-test hash `afa03d4b...`;
- exact 39 corrected stems `1319..1357`;
- validation-only membership and group `D02-C0034`;
- `sealed_test_accessed=false` and `training_authorized=false`.

Forged WP38 stem, WP36 split, duplicate WP36 row and wrong D02 group attacks are rejected before
the predecessor graph builder runs.

## Materialised candidate readback

- Output: `data/processed/m1_yolo_wp38_r1_integration_r1/` (ignored local artifact).
- Train images: 3,712 = 1,912 real + 1,800 WP35.
- Validation images: 376, including exactly 39 corrected PNG derivatives.
- Test directories/files: absent.
- Export verification: `valid=true`.
- Sealed-test access log: absent.

## Exact review hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py` | `29839def04afa2ba8915195a8362f3e65fcde1fc22700bac242dc804e7461fa1` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r1_manifest.json` | `6fbc33e8cd168a203d798e8abfee077f8f34450e8e9b66c03f9812d675e75675` |
| `src/cpv301_autodrive/dataset01_view_r1.py` | `6763c8d7fd22004773bbac84067f39d0b85c88df5c049759de9250bf433431dc` |
| `tests/test_m1_wp38_r1_integration_r1.py` | `187ed5d34f83e75c86d74502dbda0e6a46f480f64735eaff64c98667672dea71` |
| `tests/test_dataset01_view_r1.py` | `b8f32ae5bf6dce31c37af64ce4552bc32d0022106022a793757da1020964bff4` |
| Initial independent QA `FAIL` record | `3f676588350e089c72457b3159ddb434122642671258c7d0f46dbc605feae338` |

## Required independent QA decision

QA must reproduce the linked-output and forged-authority attacks, verify the train/val-only
materialisation and sealed-test boundary, and issue `PASS` or `FAIL`. Only a `PASS` permits work on
the clean-commit Colab bundle successor and corrected-validation evaluation. It still does not
authorize a new 100-epoch run or sealed-test access.
