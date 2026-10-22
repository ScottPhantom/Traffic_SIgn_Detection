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

r6 = importlib.import_module("run_d1_l4_capacity_r6")
verifier = importlib.import_module("verify_d1_l4_capacity_r6")


@pytest.mark.parametrize("value", (True, False, "1", None, float("nan")))
def test_finite_number_rejects_boolean_non_numeric_and_non_finite(value: object) -> None:
    with pytest.raises(RuntimeError, match="finite non-boolean"):
        verifier._finite_number(value, "probe")


@pytest.mark.parametrize("status", (False, True, "FORGED_STATUS", ""))
def test_manifest_requires_exact_status(status: object) -> None:
    manifest = {
        "schema_version": 1,
        "status": status,
        "plan_sha256": "a" * 64,
        "sealed_test_accessed": False,
        "files": [{"path": "capacity.log", "size": 1, "sha256": "b" * 64}],
        "evidence_sha256": "c" * 64,
    }
    with pytest.raises(RuntimeError, match="status differs"):
        verifier.verify_manifest(manifest)


def test_manifest_rejects_extra_key() -> None:
    manifest = {
        "schema_version": 1,
        "status": "EVIDENCE_PACKAGED",
        "plan_sha256": "a" * 64,
        "sealed_test_accessed": False,
        "files": [{"path": "capacity.log", "size": 1, "sha256": "b" * 64}],
        "evidence_sha256": "c" * 64,
        "extra": "forged",
    }
    with pytest.raises(RuntimeError, match="exact schema"):
        verifier.verify_manifest(manifest)


def test_environment_rejects_dirty_boolean_and_extra_key() -> None:
    environment = {key: "x" for key in verifier.contract.ENVIRONMENT_KEYS}
    environment.update(
        {
            "git_dirty_files": False,
            "mps_available": False,
            "cuda_available": True,
            "gpu_uuid": "GPU-test",
            "total_vram_mib": 24000.0,
            "extra": "forged",
        }
    )
    with pytest.raises(RuntimeError, match="exact schema"):
        verifier.verify_environment(environment, git_commit="a" * 40, label="probe")


def test_gpu_sample_requires_exact_schema_and_numeric_types() -> None:
    sample = {
        "time": "2026-10-21T01:00:00+00:00",
        "gpu_uuid": "GPU-test",
        "utilization_percent": True,
        "memory_used_mib": 100.0,
        "memory_total_mib": 24000.0,
        "power_watts": 60.0,
    }
    with pytest.raises(RuntimeError, match="GPU sample schema differs"):
        verifier.verify_telemetry_types(
            {"steps": [], "gpu_samples": [sample]},
            attempt_id="probe",
        )


def test_r6_source_roster_is_append_only() -> None:
    assert set(r6.r5.SOURCE_PATHS).issubset(r6.SOURCE_PATHS)
    assert r6.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r6.py",
        "detector/colab/verify_d1_l4_capacity_r6.py",
    )
