"""Approved scratch-only classifier architectures."""

from __future__ import annotations

import torch
from torch import nn

from .contract import CLASSES, validate_architecture


class CompactCNN(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1, bias=False),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1, bias=False),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.AdaptiveAvgPool2d(1),
        )
        self.classifier = nn.Sequential(nn.Flatten(), nn.Dropout(0.2), nn.Linear(128, CLASSES))

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        return self.classifier(self.features(inputs))


def build_model(architecture: str) -> nn.Module:
    """Construct exactly one approved model; all choices use random initialization."""
    validate_architecture(architecture)
    if architecture == "compact_cnn":
        model: nn.Module = CompactCNN()
    else:
        from torchvision.models import vgg16

        model = vgg16(weights=None, num_classes=CLASSES)
    output = model(torch.zeros(1, 3, 32, 32))
    if tuple(output.shape) != (1, CLASSES):
        raise RuntimeError(f"classifier output shape differs: {tuple(output.shape)}")
    return model
