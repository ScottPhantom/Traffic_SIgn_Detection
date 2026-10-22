from __future__ import annotations

import importlib
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COLAB_ROOT = REPO_ROOT / "detector/colab"
DETECTOR_ROOT = REPO_ROOT / "detector"
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

r7_tests = importlib.import_module("test_d1_l4_capacity_r7")
r8 = importlib.import_module("run_d1_l4_capacity_r8")
verifier = importlib.import_module("verify_d1_l4_capacity_r8")


def valid_environment() -> dict[str, object]:
    environment = r7_tests.valid_environment()
    environment["nvidia_driver"] = "580.82.07"
    return environment


@pytest.mark.parametrize(
    ("cuda_version", "torch_version", "driver"),
    (
        ("13..0", "2.14.1+cu130", "580.82.07"),
        ("1.3.0", "2.14.1+cu130", "580.82.07"),
        ("99.9", "2.14.1+cu999", "580.82.07"),
        ("13.0+evil", "2.14.1+cu130+evil", "580.82.07"),
        ("13.0", "2.14.1+cu130", "forged-driver"),
        ("13.0", "2.14.1+cu130", "x"),
    ),
)
def test_only_previously_verified_l4_runtime_is_accepted(
    cuda_version: str, torch_version: str, driver: str
) -> None:
    environment = valid_environment()
    environment["cuda_version"] = cuda_version
    environment["torch"] = torch_version
    environment["nvidia_driver"] = driver
    with pytest.raises(RuntimeError):
        verifier.verify_environment(environment, git_commit="a" * 40, label="probe")


def test_canonical_verified_l4_runtime_is_accepted() -> None:
    verifier.verify_environment(valid_environment(), git_commit="a" * 40, label="probe")


def test_tiny_total_vram_drift_is_rejected_exactly() -> None:
    telemetry = deepcopy(r7_tests.valid_telemetry())
    telemetry["gpu_samples"][1]["memory_total_mib"] = 23034.00001
    with pytest.raises(RuntimeError, match="total VRAM"):
        verifier.verify_telemetry_types(
            telemetry,
            attempt_id="probe",
            expected_gpu_uuid="GPU-test",
            expected_total_vram_mib=23034.0,
        )


def test_direct_type_helper_installs_and_restores_r8_context(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    r6_verifier = verifier.r7_verifier.r6_verifier
    original_r6_environment = r6_verifier.verify_environment
    original_r6_telemetry = r6_verifier.verify_telemetry_types
    original_r7_environment = verifier.r7_verifier.verify_environment
    original_r7_telemetry = verifier.r7_verifier.verify_telemetry_types

    def probe(_output_dir: Path) -> None:
        assert r6_verifier.verify_environment is verifier.verify_environment
        assert r6_verifier.verify_telemetry_types is verifier.verify_telemetry_types
        assert verifier.r7_verifier.verify_environment is verifier.verify_environment
        assert verifier.r7_verifier.verify_telemetry_types is verifier.verify_telemetry_types

    monkeypatch.setattr(verifier, "ORIGINAL_TYPE_CHECK", probe)
    verifier.verify_type_strict_artifacts(tmp_path)
    assert r6_verifier.verify_environment is original_r6_environment
    assert r6_verifier.verify_telemetry_types is original_r6_telemetry
    assert verifier.r7_verifier.verify_environment is original_r7_environment
    assert verifier.r7_verifier.verify_telemetry_types is original_r7_telemetry


def test_r8_source_roster_is_append_only() -> None:
    assert set(r8.r7.SOURCE_PATHS).issubset(r8.SOURCE_PATHS)
    assert r8.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r8.py",
        "detector/colab/verify_d1_l4_capacity_r8.py",
    )
