# YOLO11n dual-track R1 — frozen source/run contract

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Status: `SOURCE_CANDIDATE_REMEDIATED_AWAITING_INDEPENDENT_RE_QA`  
Boundary: `NO_COMMIT_NO_PUSH_NO_UPLOAD_NO_COLAB_NO_TRAINING_NO_SEALED_TEST`

## Authority

The Owner decision is recorded in
`docs/review/yolo11n_dual_track_r1_owner_decision_record.md`, SHA-256
`b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c`.
It authorizes downloading the official `yolo11n.pt` outside Git, freezing the two 100-epoch
configurations below, implementing append-only successors and submitting those sources to an
independent QA session. It does not authorize commit, push, upload, Colab execution or training.

## Shared immutable input

- File: `models/pretrained/yolo11n.pt` (Git-ignored).
- Source: `https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo11n.pt`.
- SHA-256: `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Bytes: `5,613,764`.
- Load readback: Ultralytics `DetectionModel`, task `detect`, 80 COCO source names.

Every future local or Colab use must verify the exact byte hash before constructing a model. The
file remains outside Git. No fallback to a YAML scratch model or `yolo11s.pt` is permitted under
this contract.

## N54 — direct 54-class detector

Frozen values:

| Field | Value |
| --- | --- |
| package / experiment | `YOLO11N-N54-R1` |
| model | official `yolo11n.pt` with the shared hash above |
| classes | `54`, supplied by the governed D1 data YAML |
| seed / epochs | `20261018` / `100` exactly |
| image / batch / workers | `1280` / `4` / `4` |
| fraction / patience | `1.0` / `30` |
| schedule | `cos_lr=True` |
| deterministic / plots | `True` / `False` |
| horizontal flip | `0.0` through the inherited D1 forbidden overrides |
| data | exact approved D1-A3 train/validation-only bundle; no test payload |
| state suffix | `M1_D1_Colab/runs/yolo11n_n54_seed_20261018_r1` |

The append-only training core refuses configuration drift, model-name/hash drift, early stopping
on a terminal run, non-CUDA device selection and invalid smoke boundaries. The only smoke
boundaries are fresh to epoch 1 and resume to epoch 2. The later long resume must reach epoch 100.

N54 source pins submitted to QA:

| File | SHA-256 |
| --- | --- |
| `detector/m1/resumable_train_n54_r1.py` | `d5fa857c285c0eb3139d0346714db5d77c02633ad0183e446b244bd824790391` |
| `detector/tests/test_resumable_train_n54_r1.py` | `d6b5b2b45a8d07f00a803c2de73e77925e61ef5fafe3874117ee135431443b22` |
| `detector/colab/run_yolo11n_n54_r1.py` | `b5d188d5a5e19292c9f9ede92688aadc8ed5100ff06ee088278dd940cd0603d8` |
| `detector/tests/test_yolo11n_n54_r1.py` | `042214b8941db2d14ed3ea5bbc52c8ea8019c85692617539826cba88739e9f11` |

The Colab launcher source now enforces a caller-supplied full immutable checkout, the unique state
suffix, exact data-bundle/model/source-QA hashes, three distinct runtime identities, an epoch-2
smoke-QA proof, SQLite/text logs and result archive readback. The launcher rejects any sequence
other than fresh epoch 1, resume epoch 2 and long resume to epoch 100, requires an exact NVIDIA L4,
and supports retry from a final epoch-100 checkpoint after a packaging interruption. The actual
checkout value and notebook cannot be pinned until the Owner separately authorizes a commit and
push. Source QA in this package does not authorize execution.

## N1 — one-class proposal detector

Frozen values:

| Field | Value |
| --- | --- |
| package / experiment | `YOLO11N-N1-R1` |
| detector | official `yolo11n.pt`, one class `traffic_sign` |
| seed / detector epochs | `20261018` / `100` exactly |
| image / batch / workers | `1280` / `4` / `4` |
| optimizer | `AdamW`, `lr0=0.000172`, matching Cascade B0 |
| patience / deterministic / AMP | `0` / `True` / `True` |
| horizontal / vertical flip | `0.0` / `0.0` |
| NMS IoU | `0.70` |
| data | exact Cascade B0 train/validation roster and boxes, remapped to class 0 |
| classifiers | reuse existing QA-passed CompactCNN and VGG16-54 artifacts; no classifier retrain |
| state suffix | `M1_D1_Colab/runs/yolo11n_n1_seed_20261018_r1` |

The bundle builder copies only train/validation data and regular files, replaces the legacy
`models/yolo11s.pt` member with the exact `models/yolo11n.pt` bytes, and records
`test_included=false` and `sealed_test_accessed=false`. The runner exposes only `check` and
`detector` stages. It requires a hash-bound independent source-QA PASS before detector execution;
a terminal long run additionally requires `MODE=resume` and an independent fresh-1/resume-2
smoke proof bound to the exact state path and epoch-2 checkpoint pointer.

N1 source pins submitted to QA:

| File | SHA-256 |
| --- | --- |
| `detector/colab/build_yolo11n_n1_bundle_r1.py` | `a7a8d9cd8520ddd0656c2fe582f239404b4f71b566f5bae9eccd8fd6daa20529` |
| `detector/colab/run_yolo11n_n1_r1.py` | `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753` |
| `detector/tests/test_yolo11n_n1_r1.py` | `74c423c78ad29586bb331c5ac2a765dc9ecbae6acc6028b8565fb0da195b951b` |

## Independent source-QA acceptance criteria

QA is read-only and must independently verify:

1. every source pin above and the Owner-decision hash;
2. official weight filename, byte size, hash, local load and Git-ignore boundary;
3. exact 100-epoch freezes and no implicit switch back to YOLO11s;
4. N54 fresh epoch 1, resumed epoch 2 and terminal epoch 100 semantics with test doubles;
5. N1 one-class remapping, box preservation through the inherited audited builder, classifier
   non-retraining, state isolation and source/smoke QA gates;
6. no test member in either data route and no sealed-test export/evaluation CLI route;
7. targeted Ruff/Pytest plus adversarial hash, path, state and configuration-drift cases.

A QA PASS means only that this pre-commit source candidate satisfies this contract. The next gate
is an Owner-authorized immutable commit/push, followed by append-only notebook/launcher pinning,
bundle verification, fresh/resume L4 smoke and separate artifact QA. The sealed test stays closed.
