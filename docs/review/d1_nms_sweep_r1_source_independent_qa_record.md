# D1 NMS sweep R1 — independent source QA

Reviewed: 2026-11-06 (Asia/Ho_Chi_Minh), by a Codex agent separate from the author and execution agent. Scope is authorization, contract, source, tests and pinned-input preflight. No model inference was run in this review.

Verdict: PASS

## Reviewed byte bindings (SHA-256)

| File | SHA-256 |
| --- | --- |
| `docs/review/d1_nms_sweep_r1_owner_authorization_2026-11-06.md` | `83cd0b57e6320bee3858447239666a688aea78b6e24d6cf7d985d0255a71a487` |
| `docs/review/d1_nms_sweep_r1_contract.md` | `754979728d665918a341ff7b26308f7465b049a5e0462f75c16151e52b000d9a` |
| `detector/m1/nms_sweep_r1.py` | `0a114a495337bef898bddcbfa3711556f2d740f028d7150ca91a9029a7e4311e` |
| `detector/tests/test_nms_sweep_r1.py` | `dba2cc86274eef61395e6ca1e371b76697f84546c8daa6b6e22d49d72b4fbd56` |

## Checks

- The Owner quotation is recorded and bounded to one local pilot diagnostic. The source fixes the pilot checkpoint and validation R3 bundle paths; `check_pins()` verifies 11 files and `verify_package`/`verify_evaluation_scope` enforce a train/val-only package. Read-only preflight returned `11 pins verified`; no sealed-test member was opened. `sealed_test_accessed=false`.
- Inference reads the sorted validation images and label54 files, as the pinned common evaluator does, and changes only Ultralytics `iou` and `agnostic_nms` while retaining `conf=0.001`, `imgsz=1280`, default `max_det`, RGB conversion, clipping and the same common AP scorer.
- The 11 distinct configurations and 20 confidence values produce 220 specified cells. Each cell contains localization recall, exact-class recall, precision, TP, FP, FP/image and the 7/32/41 focus recalls with YOLO IDs 7/33/42. Selection requires recall ≥0.85 and uses FP/image, mAP50-95 and distance-to-0.70 ties in contract order.
- `baseline_gate` checks the required conf-0.20 counts and both AP values against the pinned CSV before creating the output directory or running the ten alternatives. A mismatch raises and stops.
- Paired CI code uses the pre-existing 9-group 1,000-draw resampler with seed 20261018; the same draw indices are used on both predictions. Leave-one-group-out computes selection using the other eight groups and scores the held-out group. The candidate decision requires the three contract conditions, including adjacent-IoU votes with the same NMS mode. No threshold is locked or application rule changed.
- `PYTHONPATH=. uv run --no-sync pytest -q tests/test_nms_sweep_r1.py`: 5 passed. Ruff on the two new Python files: all checks passed. `graft check .`: graph in sync after a freshness-aware query.

## Limits for execution and result QA

This PASS permits only the pinned local validation run. It does not establish baseline reproduction, performance gain or result integrity. The runner's CPU fallback, if needed, must be invoked and documented by the execution agent. Result QA must independently verify all eleven CSV hashes, 220 cells, baseline gate, bootstrap and cross-validation outputs, and the sealed-test flag before a report or commit.
