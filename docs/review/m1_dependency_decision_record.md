# M1 detector dependency owner decision

Status: `OWNER_APPROVED_SEPARATE_DETECTOR_PROJECT_DEPENDENCIES`
Decision date: `2026-10-18` (`Asia/Ho_Chi_Minh`)

The owner approved PyTorch and Ultralytics with exact pins in the separate `detector/` uv project.
This isolates the detector's NumPy/OpenCV requirements from the root TensorFlow/E0 environment.

Approved files and hashes:

| File | SHA-256 |
| --- | --- |
| `detector/pyproject.toml` | `80a60ba75ecf68a33006a9dbb8d32eacb75b7a7dbe87dd952b7b9f9f9ab1fa7e` |
| `detector/uv.lock` | `5d56642af267bdff63f7d2a627ccf97a8f04cbf848a673a5d65988a471baaec5` |

Current exact direct pins are Torch `2.14.1`, TorchVision `0.29.1` and Ultralytics `8.4.172`.
The root environment is not replaced by this decision. This record authorizes the dependency
layout; it does not authorize a pretrained-weight download, sealed-test access, deployment or
publication of model weights.
