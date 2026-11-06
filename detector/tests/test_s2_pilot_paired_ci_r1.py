"""Synthetic binding and scope checks for the prepared S2/pilot paired CI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from m1 import s2_pilot_paired_ci_r1 as ci


def test_rejects_missing_s2_artifacts_before_scoring(tmp_path: Path) -> None:
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        ci.verify_inputs(tmp_path, "0" * 64, "1" * 64, Path("docs/review/qa.md"), "2" * 64)


def test_ci_requires_independent_s2_result_qa() -> None:
    with pytest.raises(RuntimeError, match="S2 result QA path is invalid"):
        ci._verify_prerequisites({}, Path("outside/qa.md"), "0" * 64)


@pytest.mark.parametrize("value", ["bad", "A" * 64, "0" * 63])
def test_rejects_malformed_sha_before_reading_file(tmp_path: Path, value: str) -> None:
    with pytest.raises(RuntimeError, match="malformed"):
        ci._require(tmp_path / "missing", value, "candidate")


def test_pilot_focus_map_is_derived_key_not_raw_id() -> None:
    names = ci.a3ci.class_names(ci.BUNDLE)
    assert {key: names.index(key) for key in ci.FOCUS} == {"7": 7, "32": 33, "41": 42}


def test_canonical_output_is_strict_json_and_preserves_seal_flag() -> None:
    value = {"sealed_test_accessed": False, "thresholds_locked": False, "split": "val"}
    text = ci.canonical(value)
    assert json.loads(text) == value
    assert text.endswith("\n")
