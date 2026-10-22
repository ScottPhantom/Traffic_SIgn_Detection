from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COLAB_ROOT = REPO_ROOT / "detector/colab"
DETECTOR_ROOT = REPO_ROOT / "detector"
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

r5 = importlib.import_module("run_d1_l4_capacity_r5")
verifier = importlib.import_module("verify_d1_l4_capacity_r5")


@pytest.mark.parametrize("value", (0, 1, 0.0, 1.0, "false", "true", None))
def test_governance_booleans_are_exact(value: object) -> None:
    with pytest.raises(RuntimeError, match="exact boolean"):
        verifier._require_boolean(
            {"not_model_quality_evidence": value},
            "not_model_quality_evidence",
            True,
            "report",
        )


def test_expected_boolean_value_is_enforced() -> None:
    with pytest.raises(RuntimeError, match="exact boolean False"):
        verifier._require_boolean(
            {"sealed_test_accessed": True},
            "sealed_test_accessed",
            False,
            "report",
        )


def test_r5_source_roster_is_append_only() -> None:
    assert set(r5.r4.SOURCE_PATHS).issubset(r5.SOURCE_PATHS)
    assert r5.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r5.py",
        "detector/colab/verify_d1_l4_capacity_r5.py",
    )
