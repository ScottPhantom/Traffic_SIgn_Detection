# M1-WP38-R1 downstream integration R3 QA remediation report

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_TRAINING_NO_EVALUATION_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Scope

Initial, R1 and R2 packages and their QA `FAIL` records remain immutable. R3 preserves R2's
directory-descriptor write defense and addresses only R2 findings M-1-R2 and L-1-R2.

## M-1-R2 remediation: strict completion marker

`EXPORT_COMPLETE.json` now has one exact schema and exact values. Extra/missing fields, wrong
package/status, boolean substitution, changed governance flags, missing count keys or any count
other than `train=1912`, `train_wp35=1800`, `val=376` fail verification. Type checks use exact
Python integers so booleans cannot pass as counts. Full dataset roster/hash replay remains required
after the marker passes.

## L-1-R2 remediation: descriptor stack cleanup

The R3 tree builder records each descriptor immediately after opening it. If any later directory
creation/open fails, every recorded descriptor is closed in reverse order before the exception is
re-raised. An injected mid-tree failure confirms `/dev/fd` returns to the pre-call descriptor set.

## Current readback

- Materialized R3 output: 3,712 train and 376 val images.
- Exactly 39 corrected validation PNGs, stems `1319..1357`.
- Test directories/files absent; sealed-test access log absent.
- Strict completion marker and full export verification: `valid=true`.
- Graft synchronized: 3,422 wiring nodes.

## Exact review hashes

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py` | `729277d443fffd4fa21d3a793f7f5b0b18744bf703cf9ecf9088a0c6bcfb5226` |
| `docs/review/generated/m1_yolo_wp38_r1_integration_r3_manifest.json` | `734b082d49e607de97e61a8a7db7203993fe7645b552be8c99e5cc2aed31be9e` |
| `tests/test_m1_wp38_r1_integration_r3.py` | `ca813cad25cf8a79726b3d37edd80c9a479e708b0500620baab89d478ce8085b` |
| R2 independent QA `FAIL` record | `b37c7bf34e6160b496dd28cd56993e7a786689ac7733968513aac09c0464f7eb` |

## QA gate

Independent QA must attack every marker field/type/count, reproduce the partial-tree descriptor
failure, regress R2 path-swap attacks, verify the exact train/val-only roster and authenticated
Dataset Graph, and issue `PASS` or `FAIL`. A `PASS` permits work on a separate clean-commit bundle
successor and corrected-validation evaluation, but not training, upload, commit/push or sealed-test
access.
