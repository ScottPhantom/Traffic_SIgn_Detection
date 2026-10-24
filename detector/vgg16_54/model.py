"""VGG16 feature stack with a compact 54-class crop head.

This is intentionally distinct from the historical ``VGG16_model.h5`` and from
torchvision's very large ImageNet classification head.  The convolutional
stack is VGG16; the head is adapted to the governed 32x32 traffic-sign crops.
No network access or pretrained-weight download occurs here.
"""

from __future__ import annotations

import torch
from torch import nn

ARCHITECTURE = "vgg16_crop54_scratch"
CLASSES = 54
INPUT_SHAPE = (3, 32, 32)


class VGG16Crop54(nn.Module):
    """VGG16 convolutional features plus global pooling and a 54-way head."""

    def __init__(self, *, dropout: float = 0.3) -> None:
        super().__init__()
        if not 0.0 <= dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        from torchvision.models import vgg16

        # weights=None is an audited invariant: this R1 package never downloads weights.
        base = vgg16(weights=None)
        self.features = base.features
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Dropout(dropout),
            nn.Linear(512, CLASSES),
        )

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.avgpool(self.features(inputs)))


def build_model() -> VGG16Crop54:
    """Build the scratch-only R1 candidate and verify its public output contract."""
    model = VGG16Crop54()
    with torch.inference_mode():
        output = model(torch.zeros(1, *INPUT_SHAPE))
    if tuple(output.shape) != (1, CLASSES):
        raise RuntimeError(f"VGG16 crop-classifier output differs: {tuple(output.shape)}")
    return model
