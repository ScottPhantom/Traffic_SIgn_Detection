# M0-WP6 — Frozen E0 compute/runtime and evaluation-readiness preflight

Status: `WP6_AWAITING_QA_READ_ONLY_PREFLIGHT`  
Boundary: `FROZEN_E0_LOCAL_PREFLIGHT_ONLY_NO_D05_APPROVAL_NO_CALIBRATION_NO_OOD_CLAIM_NO_VIETNAM_VALIDATION_NO_TRAINING`

WP6 proves only that the frozen local E0 control can be inventoried and benchmarked reproducibly on this host. It does not approve D-05, calibrate UNKNOWN/OOD, validate Vietnam, open Gate 0 or authorize training.

## Observed local host and runtime

- OS: macOS 27.0.1 (26A434), arm64.
- CPU: Apple M1 Pro; physical/logical cores: 10/10.
- Reliably observed memory: 17179869184 bytes.
- Hardware graphics/Metal: Apple M1 Pro (16 cores, spdisplays_metal4).
- Python: 3.12.13 at `.venv/bin/python3`; uv 0.11.14 (3fdfdc7d4 2026-05-12 aarch64-apple-darwin).
- TensorFlow/Keras: 2.20.0 / 3.15.1.
- TensorFlow-visible devices: `[{"name": "/device:CPU:0", "type": "CPU"}]`.
- Execution backend used: `TENSORFLOW_CPU_ONLY`. Hardware Metal exists, but TensorFlow exposes no GPU and `tensorflow-metal` is not installed.

No serial number, hardware UUID, provisioning identifier, username or display serial is recorded.

## Frozen E0 and local GTSRB artifacts

- Model: `models/VGG16_model.h5`, SHA-256 `745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565`.
- Architecture: SMALL_VGG_INSPIRED_SEQUENTIAL_CNN_NOT_CANONICAL_KERAS_VGG16; 2188107 parameters; input [None, 32, 32, 3]; output [None, 43].
- Train: 34799 samples, 43 classes, SHA-256 `5c319e00df7f45a18761e65dfd47341779c310798a71ea3f371659cc4a63da44`.
- Valid: 4410 samples, 43 classes, SHA-256 `7d92b991f95cf3bfcc6e35b88bad506b89e562992c1eb6c1034462a9604b6948`.
- Test: 12630 samples, 43 classes, SHA-256 `60b6450ffdb227042eb32f28d15fe77f98ad24dd550cc85eb445b8c0e502e470`.
- All three pickles have exact keys `features/labels/coords/sizes`, uint8 32x32x3 features and class IDs 0..42.
- Model/test/evaluation hashes reconcile with the frozen E0 manifest and retained Drive provenance.

`valid.p` is same-source GTSRB data used during model development. It may support a later diagnostic/calibration design, but it is not an independent Vietnamese holdout and cannot validate Vietnamese-domain performance.

## Reproducible batch-1 latency

Candidate measurement command (never updates the official package or trust anchor):

```bash
uv run python scripts/audit_e0_compute_readiness.py build --repo-root .
```

Official package verification command:

```bash
uv run python scripts/audit_e0_compute_readiness.py verify --repo-root .
```

- Split: `gtsrb_test`; deterministic seed 20261010.
- Backend: `TENSORFLOW_CPU_ONLY`; batch size 1.
- Warm-up: 20 iterations.
- Measured: 300 iterations in 3 repeats of 100.
- Timing: `time.perf_counter_ns around preprocess_image plus keras model.predict`.
- Included: preprocessing (`preprocess_image`) and `keras model.predict`; excluded: pickle/model loading, PIL construction, sample selection and serialization.
- p50: 21.739 ms; p95: 25.099 ms; mean: 22.439 ms; population std: 5.325 ms.
- Repeat means: [21.834, 23.530, 21.951] ms; repeat-mean CV: 0.034468.
- Clean-build benchmark attestation: `docs/review/generated/wp6_e0_compute_attestation.json`; verifier compares its runtime,
  exact observation digest, statistics and prediction trace with the evidence before accepting.
- Independent source anchor: `5102dc7493cd32f0f958430b3d0dd25b0e288ba10052b81ee17236b4acfb3c56`. A new measurement remains an
  unpinned candidate until a maintainer reviews it, changes this source constant and explicitly
  runs `promote-pinned`; no build command can rewrite or auto-promote the anchor.

This is an observed local diagnostic, not a D-05 pass/fail result. D-05 is still unapproved/inactive.

## Calibration/OOD readiness

Readiness classification: `TECHNICALLY_READY_FOR_LATER_DIAGNOSTIC_DESIGN_WITH_UNRESOLVED_GOVERNANCE_AND_OOD_INPUTS`.

- No approved D-05 bundle, latency gate, seed budget or reviewer decision
- No provenance-approved unknown-sign OOD set
- No provenance-approved non-sign/background OOD set for classifier rejection
- No difficult-image OOD groups for blur, night, rain, occlusion or full-scene inputs
- No independent Vietnamese validation/holdout with approved taxonomy and grouping
- No locked group-aware Vietnam train/validation/test manifests
- No frozen probability-export/calibration fitting protocol or threshold-selection protocol
- Current confidence_threshold=0.50 is a demo value and raw Softmax is not an UNKNOWN guarantee

No temperature, UNKNOWN threshold or OOD metric was fitted or selected. The existing `0.50` threshold remains a demo value.

## Governance state

- D-01…D-05 and G0.4: `PENDING`.
- Gate 0: `BLOCKED`.
- `training_authorized=false`.
- Experiment acceptance template: `UNAPPROVED / INACTIVE`.
- No training, split mutation, model overwrite or model promotion occurred.
