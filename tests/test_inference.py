import numpy as np
from PIL import Image

from cpv301_autodrive.inference import preprocess_image
from cpv301_autodrive.labels import GTSRB_LABELS


def test_gtsrb_mapping_has_43_classes() -> None:
    assert len(GTSRB_LABELS) == 43
    assert GTSRB_LABELS[14] == "Stop"
    assert GTSRB_LABELS[17] == "No entry"


def test_preprocess_matches_training_contract() -> None:
    image = Image.new("RGB", (64, 48), color=(255, 128, 0))
    batch = preprocess_image(image)
    assert batch.shape == (1, 32, 32, 3)
    assert batch.dtype == np.float32
    assert 0.0 <= float(batch.min()) <= float(batch.max()) <= 1.0
