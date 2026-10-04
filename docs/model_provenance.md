# Model provenance and evidence boundary

## Artifact

- File: `models/VGG16_model.h5`
- Drive ID: `18lQG_A4TkDgI27Qh9OLlTT-uVL8xrIlo`
- SHA-256: `745cf3f6e9f5edfe32954866d93f07d9504f6bc2d4f3667c8b8f99f1c924b565`
- Saved by the Drive notebook with TensorFlow 2.20.0 / Keras 3 on Python 3.13.
- Verified locally with TensorFlow 2.20.0 / Keras 3 on Python 3.12.

## Observed model contract

- Input: `(None, 32, 32, 3)` RGB image tensor.
- Preprocessing used by the notebook: cast to float and divide pixels by 255.
- Output: `(None, 43)` Softmax scores for the GTSRB label mapping.

The Drive filename calls the artifact `VGG16_model.h5`. The notebook code builds a smaller Sequential CNN with 32-filter and 64-filter convolution blocks, Batch Normalization, Max Pooling, a 512-unit Dense layer and a 43-unit Softmax head. It is VGG-inspired, not the canonical 16-layer `keras.applications.VGG16` architecture.

## Training log readback

`artifacts/DB_logger.db` contains 40 rows. The final rows report:

- Epoch 9: train accuracy `0.9572`, validation accuracy `0.8574`, validation loss `0.5339`.
- Epoch 10: train accuracy `0.9844`, validation accuracy `0.8560`, validation loss `0.5363`.
- Final log message: training ended successfully on 2026-09-18.

The notebook output also contains an `input ran out of data` warning on alternating epochs because of the generator/`steps_per_epoch` configuration. These logged values should therefore be treated as training-run evidence, not a complete independent evaluation.

## Local smoke test

The local runtime loaded the HDF5 file with `compile=False` and predicted the first GTSRB test image:

- True class from `Test.csv`: `16`.
- Predicted class: `16`.
- Confidence: approximately `0.9999999`.

This single sample proves model loading and inference wiring only. The current artifacts do not contain a full held-out test evaluation report, so they do not establish test accuracy, test macro-F1, calibration quality, or open-set/OOD performance.

## Full local GTSRB test evaluation — 2026-10-03

The downloaded model was evaluated on all 12,630 samples in `data/processed/test.p`
using the notebook preprocessing contract (`float32 / 255`). The reproducible outputs are
under `results/evaluation/gtsrb_test_baseline/`.

- Accuracy: `0.8682`
- Macro-F1: `0.7921`
- Weighted-F1: `0.8705`
- Balanced accuracy: `0.7949`
- Wrong predictions: `1,665`
- Wrong predictions with confidence at least `0.90`: `324`

The largest directional failures include 117 `Keep right -> Keep left` errors and 86
`Turn right ahead -> Turn left ahead` errors. The training notebook configured
`horizontal_flip=True`, which changes the meaning of directional traffic signs while leaving
the original label unchanged. This is a concrete training defect, not just a deployment issue.

These metrics show that the model is not completely wrong on its source-domain closed-set
benchmark. They do not support deployment in Vietnam: no Vietnamese traffic-sign set,
full-scene detector, unknown/non-sign evaluation, temporal evaluation, or safety validation is
present. See `docs/initial_model_assessment.md` for the go/no-go assessment.
