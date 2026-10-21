# D1 Pilot validation memory repair — independent QA record

Date: 2026-10-21 (Asia/Ho_Chi_Minh)  
QA mode: independent, source-only, fail-closed  
Verdict: **PASS**

## Scope and authorization boundary

This review covers only:

- `detector/m1/cli.py`;
- `detector/tests/test_m1.py`;
- `docs/review/d1_pilot_validation_memory_repair_implementation_record.md`.

QA did not modify PM source, evaluate real data, train or resume a model, access the sealed test,
write a model report, commit, or push. The only project change made by QA is this append-only record.

## Reviewed identities

| File | SHA-256 |
| --- | --- |
| `detector/m1/cli.py` | `3e0c13b3c47fb396429a0d06e16c6e6d98ca063d10d68d81a4c87af42b4cf967` |
| `detector/tests/test_m1.py` | `525ee768f841f3f3bbc379825a54bf2447c553d3e4382e983acc953814d29905` |
| implementation record | `50598e5446bc8276040247084934155a1bdc82e52b86c8780ed590d1e5b00ab6` |

The source diff is limited to importing iterator/sequence types, adding
`iter_image_predictions`, routing `load_frames` through it, and adding focused regressions.

## Root-cause verification and memory bound

PASS. Inspection of the pinned Ultralytics 8.4.172 loader confirms the implementation record's
root cause:

- a `list` or `tuple` source is passed through `autocast_list`, which opens/converts every list
  element before `LoadPilAndNumpy` retains the complete set in `self.im0`;
- a string image path uses `LoadImagesAndVideos` instead;
- `stream=True` controls result iteration but does not prevent the list-source conversion and
  retention that already happened.

The old `load_frames` supplied all 376 validation paths in one list. The repair supplies exactly one
string path to each `predict` invocation. Therefore no invocation can preload the full validation
image list, and at most one source image is available to that invocation's loader.

`load_frames` still accumulates compact `Frame` objects containing ground-truth and prediction
arrays for downstream metrics. Its total memory is therefore proportional to boxes/classes/scores,
not mathematically constant, but it no longer retains all full-resolution source pixels through the
Ultralytics list loader. The implementation record's more specific one-full-resolution-image claim
is accurate.

## Ordering and exact-one-result behavior

PASS. `load_frames` continues to sort image paths before inference. `iter_image_predictions` walks
that sequence serially and yields `(path, result)` in the same order. Each path receives its own
result iterator:

- zero results raises `RuntimeError` naming that path;
- exactly one result yields that path/result pair;
- a second result raises `RuntimeError` naming that path.

This is at least as fail-closed as the old strict `zip`, while eliminating any possibility that a
result from one source path is silently paired with another source path. An error aborts frame
construction before any evaluation report is written.

Focused tests cover ordered one-path calls and parameterized zero/multiple-result failures. QA also
executed an independent adversarial fake-model check covering three ordered paths and all prediction
arguments; it passed.

## Prediction-parameter and output-contract equivalence

PASS for the governed semantic/output contract. The old and new calls use the same:

- confidence `0.001`;
- governed NMS IoU argument;
- governed image size;
- governed device;
- `max_det=300`;
- `stream=True`;
- `verbose=False`.

The source value remains the same filesystem path represented as a string; only the number of paths
per invocation changes from all images to one. Ultralytics 8.4.172 has `rect=False` by default, so
both old list-source and new single-path calls use the same square letterbox mode rather than
silently changing rectangular preprocessing. Frame construction, label conversion, unknown boxes,
matching, threshold selection, bootstrap, report schema and metric code are unchanged.

The new helper preserves the number and ordering of returned `Frame` objects when the model obeys
the one-result-per-image contract. It does not and cannot promise bit-for-bit equal floating-point
predictions across different inference batch groupings; GPU kernels may have batch-dependent
rounding. This is not promoted as verified equivalence. The failed old path produced no governed
evaluation report, and any newly authorized validation run must be treated as the first complete
report from this repaired source and reviewed separately.

## Sealed-test and authorization controls

PASS. The repair does not change `_evaluation_preflight`, registry binding, threshold-lock binding,
test logging, split selection, data contract checks or report writing. The existing behavior remains:

- validation rejects all final-evaluation options;
- test requires `--final-eval`, a non-empty reason, committed threshold lock, exact locked
  confidence/NMS values and bootstrap;
- test access is logged before the test contract/data path is opened;
- train/validation `data.yaml` cannot reference the sealed test.

No sealed-test file, image, label, metric or access log was opened during this QA.

## Validation evidence

- detector Ruff (`m1`, `tests`): PASS;
- focused `tests/test_m1.py`: **57/57 PASS**;
- complete detector suite: **108/108 PASS** in 3.71 seconds;
- detector lock check: PASS, 66 packages resolved;
- independent all-parameter/order/zero/multiple fake-model attack: PASS;
- pinned Ultralytics loader/default-configuration inspection: PASS;
- Graft wiring graph: `OK` and in sync with source.

No real validation evaluation was run, so this QA does not claim a measured peak-memory reduction,
a successful MPS/CPU report, or model metrics. Those remain execution evidence to be collected only
after the repair is separately released and a validation-only run is authorized.

## Verdict and authorization boundary

**PASS.** The reviewed repair correctly removes the all-images list-source preload, preserves
ordered one-to-one frame production and all governed inference parameters, fails closed on zero or
multiple results, and leaves sealed-test controls unchanged.

This PASS approves only the source repair at the hashes above. It does not authorize commit or push,
real validation evaluation, threshold selection, latency measurement, another training seed,
sealed-test access, artifact mutation, deployment, publication or any model-quality claim.
