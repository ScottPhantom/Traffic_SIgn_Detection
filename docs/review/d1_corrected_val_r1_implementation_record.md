# D1 corrected-validation evaluator R1 implementation record

Date: 2026-10-22 (`Asia/Ho_Chi_Minh`)

Status: `AWAITING_INDEPENDENT_QA`

Boundary: `VALIDATION_ONLY_NO_TRAINING_NO_SEALED_TEST_NO_UPLOAD_NO_COMMIT_NO_PUSH`

## Purpose

The existing pilot validation report was produced against the original 39 portrait-encoded frames.
This append-only evaluator binds the registered pilot `best.pt` to the QA-passed R4 integration and
produces a distinct, non-overwriting report for the corrected validation set. It cannot train and
has no sealed-test command or split option.

## Governed behavior

- Pins the exact R4 integration exporter, manifest and independent QA PASS record.
- Replays the descriptor-bound R4 materialised verifier before model loading.
- Requires 376 validation frames, exactly 39 corrected frames and a train/validation-only YAML.
- Uses the existing committed run registry to bind `best.pt` and its original training contract.
- Runs Ultralytics validation and the project's bounded-memory per-image prediction flow at
  `imgsz=1280`, NMS IoU 0.70 by default.
- Selects the validation confidence that reaches class-agnostic recall 0.85 with minimum measured
  FP/image, matching the existing pilot method.
- Rotates the 10 governed unknown-box diagnostics on stems `1319..1328` with the same CCW90 mapping
  as the corrected frames: `x'=y`, `y'=1-x`, `w'=h`, `h'=w`.
- Writes only `eval_val_wp38_r1_r4.json` under the registered run and refuses overwrite/symlink.
- Always records `test_included=false` and `sealed_test_accessed=false`.

## Verification before QA

- Source Ruff: PASS.
- Targeted tests: 5/5 PASS.
- R4 data authority check: PASS; 376 validation frames, 39 corrected frames, no test.
- No model inference or evaluation has been run yet.
- Sealed-test access log remains absent.

## Exact QA inputs

| File | SHA-256 |
| --- | --- |
| `detector/m1/corrected_val_r1.py` | `0e56949d4a8e01b01a3de509f982ecbb4d0fd4ec1b44ef51975b47621289b8e5` |
| `detector/tests/test_corrected_val_r1.py` | `b05f314885877c72e4d57b84dbedd8e194f1f97dab7a93d35439ab7ff8d0c3a0` |
| Integration R4 QA PASS record | `27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591` |

## Gate

Independent QA must review the R4 binding, registered-weight binding, CCW90 box transform,
validation-only parser, report no-overwrite policy and metric parity with the existing evaluator.
Only a QA PASS permits running this evaluator on the already trained pilot `best.pt`. The result
remains validation evidence only and cannot authorize new training or sealed-test access by itself.
