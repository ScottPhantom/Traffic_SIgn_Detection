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

r4 = importlib.import_module("run_d1_l4_capacity_r4")
verifier = importlib.import_module("verify_d1_l4_capacity_r4")


@pytest.mark.parametrize(
    "patch",
    (
        {"attempt_id": 4},
        {"batch": True},
        {"workers": 4.0},
        {"repeat": True},
    ),
)
def test_attempt_identity_is_type_strict(patch: dict) -> None:
    record = {"attempt_id": "b04_w04_r01", "batch": 4, "workers": 4, "repeat": 1}
    record.update(patch)
    with pytest.raises(RuntimeError, match="exact type"):
        verifier._verify_attempt_identity(record, label="probe")


def test_attempt_identity_requires_exact_schema() -> None:
    with pytest.raises(RuntimeError, match="schema differs"):
        verifier._verify_attempt_identity(
            {
                "attempt_id": "b04_w04_r01",
                "batch": 4,
                "workers": 4,
                "repeat": 1,
                "extra": "forged",
            },
            label="probe",
        )


def test_r4_source_roster_is_append_only() -> None:
    assert set(r4.r3.SOURCE_PATHS).issubset(r4.SOURCE_PATHS)
    assert r4.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r4.py",
        "detector/colab/verify_d1_l4_capacity_r4.py",
    )


@pytest.mark.parametrize(
    ("value", "expected"),
    ((True, int), (1.0, int), (1, float), (False, float)),
)
def test_nested_numeric_types_do_not_use_python_equality(
    value: object, expected: type
) -> None:
    with pytest.raises(RuntimeError, match="exact type"):
        verifier._require_exact_type(value, expected, "nested probe")
