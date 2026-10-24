"""Append-only VGG16 crop-classifier successor for the 54-class cascade."""

from .model import ARCHITECTURE, CLASSES, VGG16Crop54, build_model

__all__ = ["ARCHITECTURE", "CLASSES", "VGG16Crop54", "build_model"]
