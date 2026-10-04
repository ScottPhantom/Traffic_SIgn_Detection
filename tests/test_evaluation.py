import numpy as np
import pytest

from cpv301_autodrive.evaluation import expected_calibration_error


def test_expected_calibration_error_for_one_shared_bin() -> None:
    y_true = np.array([0, 1])
    y_pred = np.array([0, 0])
    confidence = np.array([0.8, 0.8])
    assert expected_calibration_error(y_true, y_pred, confidence) == pytest.approx(0.3)
