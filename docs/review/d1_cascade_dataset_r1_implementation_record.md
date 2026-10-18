# D1 cascade detector dataset R1 implementation record

Status: `QA_FAIL_0_CRITICAL_1_HIGH_0_MEDIUM_0_LOW`
Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

## Purpose and boundary

R1 prepares only the one-class detector dataset for the Owner-approved cascade comparison. It is a
new successor package and does not change the QA-pinned M1 54-class exporter or its outputs. It
does not implement or train the 54-class crop classifier, run YOLO, select a threshold or access
the sealed test.

## Implementation

- New builder: `scripts/build_d1_cascade_detector_dataset.py`.
- New tests: `tests/test_d1_cascade_detector_dataset.py`.
- New committed manifest:
  `docs/review/generated/d1_cascade_detector_manifest.json`.
- New local ignored output: `data/processed/d1_cascade_yolo/`.
- New package verifier entry: `d1-cascade` in `scripts/run_parallel_checks.py`.
- Draft-only evaluation addendum:
  `docs/review/d1_cascade_gate_addendum_proposal.md`.

The builder pins the M1 manifest, M1 class map and Owner dual-baseline decision. It reuses the M1
split and label derivation, preserves every normalized coordinate string and rewrites only the
class token to `0`. The CLI exposes only `manifest`, `verify`, `export` and `verify-export`; there
is no test export command.

## Measured local output

- Train: `3712` frames (`1912` raw + `1800` WP35), `12621` boxes.
- Validation: `376` raw frames, `560` boxes.
- Image symlinks: `4088`.
- Regular files: `4089` (`4088` labels plus `data.yaml`).
- Classes: exactly one, `0: traffic_sign`.
- Test output paths: absent; `test_included=false`.
- Manifest SHA-256:
  `d6ca36a4c21cbadb922df897625ce80dc9d6fa3d5770b3c6cb84ddff78e10fd2`.

The exporter is idempotent only when every existing byte and symlink target is exact. It refuses
to overwrite differing labels, images, output-directory symlinks or file symlinks. The verifier
checks the exact root, exact `train`/`val` split directories, image and label rosters, source
hashes, symlink targets, label bytes and generated YAML.

## Validation performed by PM

- Targeted Ruff: PASS.
- `tests/test_d1_cascade_detector_dataset.py`: 11/11 PASS.
- Manifest verifier: PASS.
- Full local export: PASS (`8177` artifacts written).
- Full local export verifier: PASS.
- Negative tests reject malformed labels, out-of-range classes, non-finite/out-of-range
  coordinates, extra output files, a forbidden `images/test` split, output-directory symlinks and
  tampered labels.

This is PM evidence, not an independent QA verdict. R1 must receive independent QA before it is
used by a Colab runner or described as an accepted baseline package.

## Independent QA verdict

R1 failed independent QA because the real CLI resolved `--out` before the function-level symlink
guard. An output-root symlink therefore wrote all `8177` artifacts into its external target and
both `export` and `verify-export` returned success. R1 is retained as FAIL evidence; R2 supersedes
it and must be reviewed independently.
