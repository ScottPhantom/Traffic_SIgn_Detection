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

r7 = importlib.import_module("run_d1_l4_capacity_r7")
verifier = importlib.import_module("verify_d1_l4_capacity_r7")


def valid_environment() -> dict[str, object]:
    return {
        "git_commit": "a" * 40,
        "git_dirty_files": 0,
        "detector_lock_sha256": verifier.contract.DETECTOR_LOCK_SHA256,
        "python": "3.12.3",
        "platform": "Linux-6.1.0-x86_64-with-glibc2.35",
        "machine": "x86_64",
        "hardware_chip": "UNKNOWN",
        "torch": "2.14.1+cu130",
        "ultralytics": "8.4.172",
        "mps_available": False,
        "cuda_available": True,
        "cuda_version": "13.0",
        "gpu_name": "NVIDIA L4",
        "nvidia_driver": "580.95.05",
        "runtime_backend": "cuda",
        "gpu_uuid": "GPU-test",
        "total_vram_mib": 23034.0,
    }


def valid_telemetry() -> dict[str, object]:
    steps = []
    for index in range(11, 21):
        steps.append(
            {
                "batch_index": index,
                "images": 4,
                "seconds": 0.5,
                "compute_seconds": 0.4,
                "inter_batch_gap_seconds": 0.1,
                "planned_batch": 4,
                "trainer_batch_size": 4,
            }
        )
    samples = []
    for second in range(1, 4):
        samples.append(
            {
                "time": f"2026-10-21T01:00:0{second}+00:00",
                "gpu_uuid": "GPU-test",
                "utilization_percent": 75.0,
                "memory_used_mib": 10000.0,
                "memory_total_mib": 23034.0,
                "power_watts": 60.0,
                "temperature_celsius": 55.0,
            }
        )
    return {
        "started_at": "2026-10-21T01:00:00+00:00",
        "finished_at": "2026-10-21T01:00:04+00:00",
        "steps": steps,
        "gpu_samples": samples,
    }


def test_real_colab_torch_build_is_portable_across_verifier_hosts() -> None:
    verifier.verify_environment(valid_environment(), git_commit="a" * 40, label="probe")


@pytest.mark.parametrize("torch_version", ("2.14.1", "2.14.2+cu130", "2.14.1+cu129"))
def test_torch_public_pin_and_cuda_build_must_both_match(torch_version: str) -> None:
    environment = valid_environment()
    environment["torch"] = torch_version
    with pytest.raises(RuntimeError, match="Torch/CUDA build differs"):
        verifier.verify_environment(environment, git_commit="a" * 40, label="probe")


def test_valid_telemetry_chronology_and_ranges_pass() -> None:
    verifier.verify_telemetry_types(
        valid_telemetry(),
        attempt_id="probe",
        expected_gpu_uuid="GPU-test",
        expected_total_vram_mib=23034.0,
    )


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("batch_indexes", "batch index chronology"),
        ("reversed_time", "GPU sample chronology"),
        ("duplicate_time", "GPU sample chronology"),
        ("outside_time", "outside the attempt"),
        ("negative_power", "GPU power is out of range"),
        ("negative_temperature", "GPU temperature is out of range"),
        ("used_above_total", "GPU memory is out of range"),
        ("utilization_above_100", "GPU utilization is out of range"),
        ("wrong_uuid", "GPU UUID differs from the frozen plan"),
    ),
)
def test_invalid_telemetry_is_rejected(mutation: str, message: str) -> None:
    telemetry = deepcopy(valid_telemetry())
    steps = telemetry["steps"]
    samples = telemetry["gpu_samples"]
    if mutation == "batch_indexes":
        steps[0]["batch_index"] = 999
    elif mutation == "reversed_time":
        samples[1]["time"] = "2026-10-21T01:00:00.500000+00:00"
    elif mutation == "duplicate_time":
        samples[1]["time"] = samples[0]["time"]
    elif mutation == "outside_time":
        samples[0]["time"] = "2026-10-21T00:59:59+00:00"
    elif mutation == "negative_power":
        samples[0]["power_watts"] = -1.0
    elif mutation == "negative_temperature":
        samples[0]["temperature_celsius"] = -1.0
    elif mutation == "used_above_total":
        samples[0]["memory_used_mib"] = 24000.0
    elif mutation == "utilization_above_100":
        samples[0]["utilization_percent"] = 101.0
    elif mutation == "wrong_uuid":
        samples[0]["gpu_uuid"] = "GPU-other"
    with pytest.raises(RuntimeError, match=message):
        verifier.verify_telemetry_types(
            telemetry,
            attempt_id="probe",
            expected_gpu_uuid="GPU-test",
            expected_total_vram_mib=23034.0,
        )


def test_r7_source_roster_is_append_only() -> None:
    assert set(r7.r6.SOURCE_PATHS).issubset(r7.SOURCE_PATHS)
    assert r7.SOURCE_PATHS[-2:] == (
        "detector/colab/run_d1_l4_capacity_r7.py",
        "detector/colab/verify_d1_l4_capacity_r7.py",
    )


def test_r7_plan_builder_uses_captured_predecessor_not_patched_r1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        r7,
        "BASE_BUILD_PLAN",
        lambda **_kwargs: {"repo_root": str(REPO_ROOT), "plan_sha256": "old"},
    )
    monkeypatch.setattr(
        r7.r1,
        "build_plan",
        lambda **_kwargs: pytest.fail("dynamic r1 build_plan would recurse after install"),
    )
    plan = r7.build_plan()
    assert set(plan["source_sha256"]) == set(r7.SOURCE_PATHS)
    assert len(plan["plan_sha256"]) == 64
