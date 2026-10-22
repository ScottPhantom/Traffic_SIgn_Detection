# M1 Colab WP38-R1 R4 bundle R1 implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `NO_ARCHIVE_BUILT_NO_UPLOAD_NO_COMMIT_NO_PUSH_NO_TRAINING_NO_SEALED_TEST`

## Purpose

The original WP38-R1 bundle candidate predates downstream integration QA and is retained unchanged.
This append-only R1 successor reuses its deterministic archive machinery and exact 5,927-file
train/validation roster, but binds the bundle contract to the accepted integration R4 exporter,
manifest and independent QA PASS record.

## Contract

- Package: `M1-COLAB-WP38-R1-R4-TRAIN-VAL-BUNDLE`.
- Schema: 2.
- Files: 5,927 regular source files.
- Counts: 1,912 raw train images; 337 raw validation images; 39 corrected validation PNGs; 39
  corrected validation labels; 1,800 WP35 train images; 1,800 WP35 train labels.
- Allowed splits: train and validation only.
- Test stem hash may be recorded as the governance seal, but no test image or label is present.
- `test_included=false`, `sealed_test_accessed=false`, `training_authorized=false`.
- The archive builder refuses a dirty checkout and refuses to overwrite archive, sidecar or partial
  output paths.

## Current result

The contract verifier returns `valid=true` with 5,927 records. Targeted tests pass 5/5, including
exact roster/count checks, R4 QA bindings, test exclusion and the dirty-checkout refusal. No archive
has been built because the current checkout contains uncommitted project work. Nothing has been
uploaded to Drive.

## Exact QA inputs

| File | SHA-256 |
| --- | --- |
| `scripts/build_m1_colab_bundle_wp38_r1_r1.py` | `64cfa2d3f52db838f38e113d08c71c25418ce885e89b95322d9880263b7969d9` |
| `tests/test_m1_colab_bundle_wp38_r1_r1.py` | `575ca94c3555880c51b253a1a5a0244d2ca5a8b7a110c2f73afa26123b2d3e92` |
| Integration R4 QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |

## Gate

Independent QA must verify the exact hashes, schema, roster, metadata binding, sealed-test
exclusion, unsafe archive/member rejection inherited from the predecessor, output no-overwrite
policy and clean-commit gate. A QA PASS makes the source ready for an Owner-authorized commit,
archive build and private Drive upload. It does not itself authorize any of those external writes,
training, model acceptance or sealed-test access.
