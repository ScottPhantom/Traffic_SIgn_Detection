"""Conservative scene-discontinuity signal for a review-only video demo."""

from __future__ import annotations

import cv2
import numpy as np

SCENE_CUT_SCORE_MIN = 0.30
THUMBNAIL_SIZE = (64, 36)


def scene_thumbnail(frame_bgr: np.ndarray) -> np.ndarray:
    """Reduce a decoded BGR frame to a small grayscale image for comparison."""
    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
        raise ValueError("Scene-cut input must be a BGR frame")
    small = cv2.resize(frame_bgr, THUMBNAIL_SIZE, interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)


def scene_change_score(previous: np.ndarray, current: np.ndarray) -> float:
    """Return normalized mean absolute pixel change, without an accuracy claim."""
    if previous.shape != THUMBNAIL_SIZE[::-1] or current.shape != previous.shape:
        raise ValueError("Scene-cut thumbnails differ from the fixed shape")
    return float(np.abs(current.astype(np.int16) - previous.astype(np.int16)).mean() / 255)
