# D1 pilot validation memory repair — implementation record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
Status: `AWAITING_INDEPENDENT_QA`

## Observed failure

The governed seed `20261018` run was registered and validation evaluation was started with the
committed registry. Ultralytics completed its validation pass and measured:

- mAP50: approximately `0.829`;
- mAP50-95: approximately `0.589`;
- 376 images and 560 labelled instances.

The CLI then failed before writing `eval_val.json`. On MPS it reported
`Invalid buffer size: 18.36 GiB`. A CPU rerun completed the Ultralytics pass but its second
prediction pass terminated without producing the report. These partial console values are
diagnostic observations, not the governed pilot report.

## Root cause and repair

`m1.cli.load_frames` passed a Python list containing all 376 full-resolution validation paths to a
single `YOLO.predict(..., stream=True)` invocation. Ultralytics' list-source path can preload the
complete image list before yielding results, producing excessive memory pressure even though the
result iterator is streamed.

The append-only repair adds `iter_image_predictions`. It invokes `YOLO.predict` once per image path
with `stream=True`, yields exactly one `(path, result)` pair, and rejects zero or multiple results.
At most one full-resolution source image enters the Ultralytics loader at a time. Prediction
parameters remain unchanged: confidence `0.001`, governed NMS IoU, governed image size/device,
`max_det=300`, and quiet output.

No metric, matching, threshold-selection, bootstrap, data contract, model weight, registry,
training configuration, sealed-test control, or report schema was changed.

## Tests

Focused regressions prove:

- one `predict` call per ordered image path;
- `source` is a string path, never the complete list;
- streaming and `max_det=300` remain enabled;
- zero-result and multiple-result responses fail closed.

Observed local gates before QA:

- detector Ruff: PASS;
- focused `tests/test_m1.py`: PASS, 57 tests;
- complete detector pytest: PASS, 108 tests;
- detector lock check: PASS, 66 packages resolved.

## Authorization boundary

This repair authorizes no sealed-test access, new training, threshold lock, next seed, deployment,
commit, push, or model-quality claim. Validation evaluation may be rerun only after independent QA
PASS and a clean committed source revision.

