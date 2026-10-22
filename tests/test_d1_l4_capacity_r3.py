from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COLAB_ROOT = REPO_ROOT / "detector/colab"
DETECTOR_ROOT = REPO_ROOT / "detector"
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

r3 = importlib.import_module("run_d1_l4_capacity_r3")
verifier = importlib.import_module("verify_d1_l4_capacity_r3")


def step(images: int, *, batch: int = 16, index: int = 11) -> dict:
    return {
        "batch_index": index,
        "images": images,
        "seconds": 1.2,
        "compute_seconds": 1.0,
        "inter_batch_gap_seconds": 0.2,
        "planned_batch": batch,
        "trainer_batch_size": batch,
    }


def test_only_final_measured_step_may_be_partial() -> None:
    accepted = {"steps": [step(16, index=11), step(4, index=12)]}
    assert r3.validate_effective_batch(accepted, planned_batch=16) == {
        "effective_batch": 16,
        "full_batch_count": 1,
    }
    rejected = {
        "steps": [
            step(16, index=11),
            step(4, index=12),
            step(4, index=13),
        ]
    }
    with pytest.raises(RuntimeError, match="non-final measured step"):
        r3.validate_effective_batch(rejected, planned_batch=16)


@pytest.mark.parametrize("schema_version", (True, 1.0, "1", None))
def test_execution_schema_version_is_exact_integer(
    tmp_path: Path, schema_version: object
) -> None:
    journal = tmp_path / "capacity_execution.jsonl"
    rows = (
        {
            "schema_version": schema_version,
            "status": "STARTED",
            "started_at": "2026-10-21T01:00:00+00:00",
            "plan_sha256": "p",
            "sealed_test_accessed": False,
        },
        {
            "schema_version": 1,
            "status": "SUCCEEDED",
            "finished_at": "2026-10-21T01:01:00+00:00",
            "plan_sha256": "p",
            "report_sha256": "r",
            "sealed_test_accessed": False,
        },
    )
    journal.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    with pytest.raises(RuntimeError, match="must be an integer"):
        verifier.verify_execution(journal, plan_sha256="p", report_sha256="r")


@pytest.mark.parametrize("sealed_marker", (0, 1, "false", None))
def test_execution_sealed_marker_is_exact_boolean(
    tmp_path: Path, sealed_marker: object
) -> None:
    journal = tmp_path / "capacity_execution.jsonl"
    rows = (
        {
            "schema_version": 1,
            "status": "STARTED",
            "started_at": "2026-10-21T01:00:00+00:00",
            "plan_sha256": "p",
            "sealed_test_accessed": sealed_marker,
        },
        {
            "schema_version": 1,
            "status": "SUCCEEDED",
            "finished_at": "2026-10-21T01:01:00+00:00",
            "plan_sha256": "p",
            "report_sha256": "r",
            "sealed_test_accessed": False,
        },
    )
    journal.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    with pytest.raises(RuntimeError, match="must be boolean"):
        verifier.verify_execution(journal, plan_sha256="p", report_sha256="r")


def test_r3_source_roster_is_append_only() -> None:
    assert set(r3.r2.SOURCE_PATHS).issubset(r3.SOURCE_PATHS)
    assert r3.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r3.py",
        "detector/colab/verify_d1_l4_capacity_r3.py",
    )


def test_exact_type_helper_rejects_python_equality_confusion() -> None:
    for value in (True, 1.0, "1", None):
        with pytest.raises(RuntimeError, match="exact type int"):
            verifier._require_exact_type(value, int, "schema")
    for value in (0, 1, "false", None):
        with pytest.raises(RuntimeError, match="exact type bool"):
            verifier._require_exact_type(value, bool, "sealed marker")
