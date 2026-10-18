# D1 cascade crop classifier R1 implementation record

Status: `D1_CASCADE_CLASSIFIER_R1_AWAITING_INDEPENDENT_QA`

Date: `2026-10-19` (`Asia/Ho_Chi_Minh`)

Boundary: `TRAIN_AND_VALIDATION_ONLY_NO_TRAINING_NO_TEST_ACCESS_NO_UPLOAD_NO_DOWNLOAD_NO_COMMIT_NO_PUSH`

## Scope and decision boundary

R1 implements the 54-output crop-classifier package needed by the Owner-approved comparison
baseline. It does not choose an architecture for the Owner, train a model, select a threshold,
approve the proposed cascade gates or make the cascade eligible for sealed-test evaluation.

The CLI exposes only `check`, `train`, `evaluate` and `latency`. `evaluate` is validation-only and
has no split argument. There is no test command, `--final-eval` flag or test-path input. The
package refuses a data roster containing `test.p` or any other unexpected entry. No sealed-test
artifact was read, created or logged during implementation or validation.

## Implementation

- `detector/d1_cascade_classifier/contract.py` validates the reviewed crop-manifest hash, exact
  train/validation roster, exact manifest and array schemas, NumPy dtypes/shapes/contiguity,
  array hashes, index hashes, class counts and the 54-row sign-name table. Pickles are loaded with
  a restricted unpickler that permits only the NumPy globals needed by the reviewed package.
- `detector/d1_cascade_classifier/model.py` exposes exactly two explicit candidates:
  `compact_cnn` and `vgg16_scratch`. Both have 54 outputs. The VGG constructor is called with
  `weights=None`; the package has no automatic architecture selection or download path.
- `detector/d1_cascade_classifier/data.py` applies fixed tensor conversion and normalization.
  There is no geometric augmentation and horizontal flipping is explicitly false.
- `detector/d1_cascade_classifier/cli.py` enforces seeds `20261018`, `20261019`, `20261020`,
  deterministic algorithms, zero loader workers, scratch initialization and a fixed results root.
  Common telemetry clients are placed in offline/disabled mode and Python socket connections are
  blocked while models run. New result paths fail closed on symlink components.
- Every training contract binds SHA-256 digests of the exact data contract, model contract,
  training config and environment record. Both checkpoints and the epoch history are hashed.
  Evaluation verifies those bindings and all artifacts before loading `weights_only=True`.
- Validation reports top-1 accuracy, macro-F1 over represented classes, balanced accuracy over
  represented classes, 54 per-class recall/support rows and 15-bin expected calibration error.
  The 35 validation-absent classes remain explicit and cannot contribute to selection evidence.
- Latency uses batch 1, 50 warm-ups and exactly 300 measured forward passes.

## Pinned inputs

| Input | SHA-256 |
| --- | --- |
| Crop manifest | `6526844b44670e6b933ade6b48271f0f122621f783672dbfa04a1d4119beb576` |
| Detector lock | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |
| Detector project config (unchanged) | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| Dual-baseline Owner decision | `39f26b0e29a2a60a5972ea07e6e0dcf04ce5e53f722a3c92b3a69b267934a0b2` |
| Cascade gate addendum proposal (not approved) | `56d100532278fc5a13d552c3a067821508d5b40f9a04704092ff88c8b371f403` |

## R1 source snapshot

| File | SHA-256 |
| --- | --- |
| `detector/d1_cascade_classifier/__init__.py` | `fda3d39a0603c715c111ce2eac8757932d27a0b45104a47b8802331d7336435b` |
| `detector/d1_cascade_classifier/contract.py` | `d17e51319104dad48e2cfd68342d8a1e12c1dce33c35d1a0b1aee5187663288f` |
| `detector/d1_cascade_classifier/data.py` | `e55fbaddea154131a0ef20f8d2653150b0f2c8eecdc8ff31dbcb16d6a463ed5d` |
| `detector/d1_cascade_classifier/model.py` | `fdcbc4156a4bef9b5eed56a8ebc58746408a14f6558cd4b3c38a4e49df47b77a` |
| `detector/d1_cascade_classifier/metrics.py` | `612259aa52bf8794db3c717b7b6f481532f9bccc572034709cfcefc66d316078` |
| `detector/d1_cascade_classifier/cli.py` | `45091eb2d1f01c9d05912ed347b90911fd16b16c82df6e8dc3fcc79f16dc0116` |
| `detector/tests/test_d1_cascade_classifier.py` | `f2cfe59af15381d0e386ca8df88d8265af098e2b976c71a6eeb5829fad00b4ee` |

## Verification performed

- Governed CLI check: PASS; 54 classes, train `12,621`, validation `560`, exact manifest hash,
  and `sealed_test_accessed=false`.
- New classifier suite: `16/16` PASS, including hostile pickle, schema/hash/roster mutations,
  sealed-test paths, unapproved seed/architecture, VGG `weights=None`, 54 outputs, metric
  reconciliation, offline controls, symlink output and tampered run bindings/artifacts.
- Complete detector suite: `70/70` PASS.
- Detector Ruff: PASS.
- `uv lock --check`: PASS, 66 packages; `detector/pyproject.toml` and `detector/uv.lock` unchanged.

## Remaining work and QA request

Independent QA must reproduce the snapshot hashes and challenge the data loader, test exclusion,
architecture/seed allowlists, scratch-only construction, offline boundary, model output shape,
run bindings, metrics and latency contract. Until a separate QA session issues PASS, this package
must not be used for a pilot. Even after package QA, the Owner must explicitly choose which
architecture(s) to run and later approve numeric cascade gates before any sealed-test access.
