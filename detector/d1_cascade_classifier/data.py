"""In-memory tensor datasets for the governed 32x32 crop package."""

from __future__ import annotations

import numpy as np
import torch
from torch.utils.data import Dataset


class CropDataset(Dataset[tuple[torch.Tensor, torch.Tensor]]):
    """No geometric augmentation: directional signs are never horizontally flipped."""

    def __init__(self, arrays: dict[str, np.ndarray]) -> None:
        self.features = arrays["features"]
        self.labels = arrays["labels"]

    def __len__(self) -> int:
        return int(self.labels.shape[0])

    def __getitem__(self, index: int) -> tuple[torch.Tensor, torch.Tensor]:
        image = torch.from_numpy(self.features[index].copy()).permute(2, 0, 1).float().div_(255.0)
        # Fixed normalization has no learned/test-derived state.
        image = image.sub_(0.5).div_(0.5)
        return image, torch.tensor(int(self.labels[index]), dtype=torch.long)
