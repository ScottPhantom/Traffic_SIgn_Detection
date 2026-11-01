from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from cpv301_autodrive.labels import GTSRB_LABELS

IMAGE_SIZE = (32, 32)


@dataclass(frozen=True)
class Prediction:
    class_id: int
    label: str
    confidence: float
    accepted: bool


def preprocess_image(image: Image.Image) -> np.ndarray:
    """Match the training notebook: RGB 32x32 and pixel values divided by 255."""

    rgb = image.convert("RGB").resize(IMAGE_SIZE, Image.Resampling.BILINEAR)
    array = np.asarray(rgb, dtype=np.float32) / np.float32(255.0)
    return np.expand_dims(array, axis=0)


class ModelService:
    """Lazy TensorFlow loader so health checks do not load the model into memory."""

    def __init__(self, model_path: Path, confidence_threshold: float = 0.50) -> None:
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self._model: Any | None = None

    @property
    def loaded(self) -> bool:
        return self._model is not None

    def load(self) -> Any:
        if self._model is None:
            if not self.model_path.is_file():
                raise FileNotFoundError(f"Model not found: {self.model_path}")
            from tensorflow import keras

            self._model = keras.models.load_model(self.model_path, compile=False)
        return self._model

    def predict(self, image: Image.Image) -> Prediction:
        probabilities = np.asarray(self.load().predict(preprocess_image(image), verbose=0))[0]
        if probabilities.shape != (len(GTSRB_LABELS),):
            raise ValueError(
                f"Expected {len(GTSRB_LABELS)} output classes, got {probabilities.shape}"
            )
        class_id = int(np.argmax(probabilities))
        confidence = float(probabilities[class_id])
        return Prediction(
            class_id=class_id,
            label=GTSRB_LABELS[class_id],
            confidence=confidence,
            accepted=confidence >= self.confidence_threshold,
        )
