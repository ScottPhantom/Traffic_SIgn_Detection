# YOLO11n dual-track R1 — independent source QA

Date: 2026-10-25 (`Asia/Ho_Chi_Minh`)  
Scope: pre-commit N54/N1 source only  
Verdict: **PASS**

## Boundary

This was a read-only independent QA review. It did not edit source, train a model, upload data,
commit, push or access the sealed test. This verdict authorizes only progression to the later
immutable commit/notebook and L4 smoke gates after the Owner grants the corresponding authority.
It does not authorize a long training run.

## Frozen authority and shared weight

- Owner record SHA-256:
  `b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c`.
- Frozen run contract SHA-256:
  `60a0e2fb16565a19ba99957d01f3160ca4872659361951ce3d0d8316e69247f3`.
- Official out-of-Git `yolo11n.pt` SHA-256:
  `0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1`.
- Observed weight size: `5,613,764` bytes.
- Independent load readback: Ultralytics `DetectionModel`, task `detect`, 80 COCO source names.
- Git boundary: `models/pretrained/yolo11n.pt` is ignored and untracked.

## Source bindings

### N54

| File | SHA-256 |
| --- | --- |
| `detector/m1/resumable_train_n54_r1.py` | `d5fa857c285c0eb3139d0346714db5d77c02633ad0183e446b244bd824790391` |
| `detector/tests/test_resumable_train_n54_r1.py` | `d6b5b2b45a8d07f00a803c2de73e77925e61ef5fafe3874117ee135431443b22` |
| `detector/colab/run_yolo11n_n54_r1.py` | `b5d188d5a5e19292c9f9ede92688aadc8ed5100ff06ee088278dd940cd0603d8` |
| `detector/tests/test_yolo11n_n54_r1.py` | `042214b8941db2d14ed3ea5bbc52c8ea8019c85692617539826cba88739e9f11` |

### N1 successor and inherited bundle runtime

| File | SHA-256 |
| --- | --- |
| `detector/colab/build_yolo11n_n1_bundle_r1.py` | `a7a8d9cd8520ddd0656c2fe582f239404b4f71b566f5bae9eccd8fd6daa20529` |
| `detector/colab/run_yolo11n_n1_r1.py` | `b60e829104f644248912acddf4397fe07ff647e709feefef6dd0443c393e5753` |
| `detector/tests/test_yolo11n_n1_r1.py` | `74c423c78ad29586bb331c5ac2a765dc9ecbae6acc6028b8565fb0da195b951b` |
| `detector/pyproject.toml` | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| `detector/d1_cascade_classifier/__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| `detector/d1_cascade_classifier/model.py` | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| `detector/d1_cascade_classifier/data.py` | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| `detector/d1_cascade_classifier/contract.py` | `e847db9ae322fe3a7ba11e8e77743ec32440027f5d29222f2c937d746a9cfc94` |
| `detector/d1_cascade_classifier/metrics.py` | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| `detector/m1/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `detector/m1/metrics.py` | `d24570f85795e3bc5a2e754ace80a8081c510ff4a78833f2ab5316953a017f9f` |
| `detector/m1/checkpoint_store.py` | `e1f8f00c036d6407d327164d907f3641427864cc35cf817336209ae5da76891c` |
| `detector/colab/build_cascade_b0_bundle_r1.py` | `9b5b73b1a64449655963e13f437f15814ef879d17fff3a521a209e7414851afe` |
| `detector/colab/run_cascade_b0_r1.py` | `0ece03891ebe0f8c318efd7a062fdb8d799d4cf9cc357b0cf8840b4103ad876a` |
| `detector/colab/extract_cascade_b0_r1.py` | `f67663f42f8904e63f892c0ae5e861b1954c2fe9c12292cc0b607c0e3d64f068` |
| `detector/colab/evaluate_cascade_b0_r1.py` | `8bedb4c199f39eafbef240b614511ef8c40a5c7c4794772b0c6691a0df416b42` |
| `docs/review/cascade_b0_execution_contract_r1.md` | `e19871af64a169fd5560c1414914a5915a70d43e981ce3d340df6d4429a660e7` |
| `docs/review/yolo11n_dual_track_r1_owner_decision_record.md` | `b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c` |
| `docs/review/yolo11n_dual_track_r1_run_contract.md` | `60a0e2fb16565a19ba99957d01f3160ca4872659361951ce3d0d8316e69247f3` |

## Independent checks and findings

The final re-QA verified:

1. both N54 and N1 are frozen to seed `20261018`, image size 1280, batch/workers 4/4 and exactly
   100 epochs, with no fallback to YOLO11s;
2. N54 accepts only fresh epoch 1, a distinct-runtime resume to epoch 2 and a third-runtime long
   resume to epoch 100; state path, checkout, bundle, model, source QA and smoke proof are bound;
3. N54 rejects non-L4 hardware before training, accepts recovery from an epoch-100 final
   checkpoint, and uses readback plus atomic publication for retryable result packaging;
4. N1 remaps every detector class to `traffic_sign` without changing box coordinates, exposes no
   classifier-training stage, and reuses the existing CompactCNN/VGG16-54 artifacts;
5. N1 long execution requires `MODE=resume`; its smoke proof binds the normalized state path and a
   fully verified epoch-2 checkpoint manifest;
6. the N1 bundle roster contains only train/validation data and regular files, replaces the old
   YOLO11s member with the exact YOLO11n weight, and records both test/seal flags false;
7. no source route exposes `export-test`, `--final-eval` or a sealed-test split.

Two earlier QA rounds found and caused remediation of long-fresh replay, stale 40-epoch wording,
missing N54 orchestration, state-proof replay, non-L4 execution, terminal packaging recovery,
epoch-1 proof acceptance and failed-long retry. The final adversarial replay/retry cases passed.

## Validation readback

- Targeted Ruff: PASS.
- Targeted YOLO11n suite: `39 passed`.
- Inherited Cascade suite relevant to N1: `34 passed`.
- Actual N1 builder roster/remap audit: PASS.
- Graft graph: current/OK.
- Official weight hash/size/load/Git-ignore: PASS.
- `sealed_test_accessed=false`.

## Remaining gates

1. Owner authorization for a scoped immutable commit and push.
2. Append-only notebook generation pinned to that commit and this QA record hash.
3. Private train/validation-only bundle upload/readback where needed.
4. Fresh L4 epoch 1, distinct-runtime resume epoch 2 and independent smoke-artifact QA for each
   track.
5. Only after the matching smoke PASS: long resume to epoch 100, terminal artifact QA,
   validation-only common-method comparison and measured latency.

The sealed test remains closed throughout these gates.
