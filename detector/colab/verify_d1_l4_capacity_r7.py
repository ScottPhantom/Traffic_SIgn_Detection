#!/usr/bin/env python3
"""Portable-runtime and chronological-telemetry verifier for L4 capacity R7."""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

COLAB_ROOT = Path(__file__).resolve().parent
DETECTOR_ROOT = COLAB_ROOT.parent
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_d1_l4_capacity_r7 as r7_runner  # noqa: E402
import verify_d1_l4_capacity_r6 as r6_verifier  # noqa: E402

from m1 import contract, l4_capacity  # noqa: E402

ORIGINAL_TYPE_CHECK = r6_verifier.verify_type_strict_artifacts
ORIGINAL_VERIFY_PACKAGE = r6_verifier.verify_package
ORIGINAL_TELEMETRY_CHECK = r6_verifier.verify_telemetry_types
PINNED_TORCH_PUBLIC = "2.14.1"
PINNED_ULTRALYTICS = "8.4.172"
MIN_TEMPERATURE_CELSIUS = 0.0
MAX_TEMPERATURE_CELSIUS = 125.0


def _finite_number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise RuntimeError(f"{label} must be a finite non-boolean number")
    return float(value)


def _torch_build_matches_cuda(torch_version: str, cuda_version: str) -> bool:
    public, separator, local = torch_version.partition("+")
    expected_local = "cu" + cuda_version.replace(".", "")
    return public == PINNED_TORCH_PUBLIC and separator == "+" and local == expected_local


def verify_environment(environment: Any, *, git_commit: str, label: str) -> None:
    expected_keys = contract.ENVIRONMENT_KEYS | {"gpu_uuid", "total_vram_mib"}
    if not isinstance(environment, dict) or set(environment) != expected_keys:
        raise RuntimeError(f"{label} exact schema differs")
    base = {key: environment[key] for key in contract.ENVIRONMENT_KEYS}
    contract.validate_environment_record(base, label, require_clean=True)
    if base["git_commit"] != git_commit:
        raise RuntimeError(f"{label} Git commit differs")
    python_parts = environment["python"].split(".")
    if len(python_parts) != 3 or not all(part.isdigit() for part in python_parts):
        raise RuntimeError(f"{label} Python version is malformed")
    if tuple(int(part) for part in python_parts[:2]) != (3, 12):
        raise RuntimeError(f"{label} Python version is outside the detector constraint")
    if environment["ultralytics"] != PINNED_ULTRALYTICS:
        raise RuntimeError(f"{label} Ultralytics version differs from the detector pin")
    if not _torch_build_matches_cuda(environment["torch"], environment["cuda_version"]):
        raise RuntimeError(f"{label} Torch/CUDA build differs from the detector pin")
    expected_identity = {
        "machine": "x86_64",
        "hardware_chip": "UNKNOWN",
        "gpu_name": "NVIDIA L4",
        "runtime_backend": "cuda",
    }
    for key, expected in expected_identity.items():
        if environment[key] != expected:
            raise RuntimeError(f"{label} identity differs: {key}")
    if not environment["platform"].startswith("Linux-"):
        raise RuntimeError(f"{label} platform is not the governed Colab Linux runtime")
    if not environment["gpu_uuid"].startswith("GPU-"):
        raise RuntimeError(f"{label} GPU UUID differs")
    if _finite_number(environment["total_vram_mib"], f"{label} total VRAM") <= 0:
        raise RuntimeError(f"{label} total VRAM is not positive")


def verify_telemetry_types(
    telemetry: Any,
    *,
    attempt_id: str,
    expected_gpu_uuid: str | None = None,
    expected_total_vram_mib: float | None = None,
) -> None:
    ORIGINAL_TELEMETRY_CHECK(telemetry, attempt_id=attempt_id)
    parser = r6_verifier.r5_verifier.r4_verifier.r3_verifier.r2_verifier.parse_timestamp
    started_at = parser(telemetry["started_at"], f"capacity {attempt_id} start")
    finished_at = parser(telemetry["finished_at"], f"capacity {attempt_id} finish")
    if not started_at < finished_at:
        raise RuntimeError(f"capacity {attempt_id} attempt chronology differs")
    expected_indexes = list(
        range(
            l4_capacity.WARMUP_BATCHES + 1,
            l4_capacity.WARMUP_BATCHES + len(telemetry["steps"]) + 1,
        )
    )
    if [step["batch_index"] for step in telemetry["steps"]] != expected_indexes:
        raise RuntimeError(f"capacity {attempt_id} batch index chronology differs")
    previous_time = None
    observed_uuid = None
    observed_total = None
    for sample in telemetry["gpu_samples"]:
        observed_time = parser(sample["time"], f"capacity {attempt_id} GPU sample")
        if not started_at <= observed_time <= finished_at:
            raise RuntimeError(f"capacity {attempt_id} GPU sample lies outside the attempt")
        if previous_time is not None and not previous_time < observed_time:
            raise RuntimeError(f"capacity {attempt_id} GPU sample chronology differs")
        previous_time = observed_time
        uuid = sample["gpu_uuid"]
        total = _finite_number(sample["memory_total_mib"], "GPU total VRAM")
        used = _finite_number(sample["memory_used_mib"], "GPU used VRAM")
        utilization = _finite_number(sample["utilization_percent"], "GPU utilization")
        power = _finite_number(sample["power_watts"], "GPU power")
        temperature = _finite_number(sample["temperature_celsius"], "GPU temperature")
        if observed_uuid is None:
            observed_uuid = uuid
            observed_total = total
        if uuid != observed_uuid or not math.isclose(total, observed_total):
            raise RuntimeError(f"capacity {attempt_id} GPU identity changed within the attempt")
        if expected_gpu_uuid is not None and uuid != expected_gpu_uuid:
            raise RuntimeError(f"capacity {attempt_id} GPU UUID differs from the frozen plan")
        if expected_total_vram_mib is not None and not math.isclose(
            total, expected_total_vram_mib
        ):
            raise RuntimeError(f"capacity {attempt_id} total VRAM differs from the frozen plan")
        if not 0.0 <= utilization <= 100.0:
            raise RuntimeError(f"capacity {attempt_id} GPU utilization is out of range")
        if total <= 0.0 or not 0.0 <= used <= total:
            raise RuntimeError(f"capacity {attempt_id} GPU memory is out of range")
        if power < 0.0:
            raise RuntimeError(f"capacity {attempt_id} GPU power is out of range")
        if not MIN_TEMPERATURE_CELSIUS <= temperature <= MAX_TEMPERATURE_CELSIUS:
            raise RuntimeError(f"capacity {attempt_id} GPU temperature is out of range")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    ORIGINAL_TYPE_CHECK(output_dir)
    runner = r6_verifier.r5_verifier.r4_verifier.r3_verifier.r2_verifier.r1_runner
    plan = runner.strict_json(output_dir / runner.PLAN_NAME)
    environment = plan["environment"]
    for attempt in plan["roster"]:
        telemetry = runner.strict_json(
            output_dir / "attempts" / attempt["attempt_id"] / "raw_telemetry.json"
        )
        verify_telemetry_types(
            telemetry,
            attempt_id=attempt["attempt_id"],
            expected_gpu_uuid=environment["gpu_uuid"],
            expected_total_vram_mib=float(environment["total_vram_mib"]),
        )


def verify_package(output_dir: Path) -> dict[str, Any]:
    original_type_check = r6_verifier.verify_type_strict_artifacts
    original_environment_check = r6_verifier.verify_environment
    original_telemetry_check = r6_verifier.verify_telemetry_types
    original_source_paths = r6_verifier.r6_runner.SOURCE_PATHS
    r6_verifier.verify_type_strict_artifacts = verify_type_strict_artifacts
    r6_verifier.verify_environment = verify_environment
    r6_verifier.verify_telemetry_types = verify_telemetry_types
    r6_verifier.r6_runner.SOURCE_PATHS = r7_runner.SOURCE_PATHS
    try:
        result = ORIGINAL_VERIFY_PACKAGE(output_dir)
    finally:
        r6_verifier.verify_type_strict_artifacts = original_type_check
        r6_verifier.verify_environment = original_environment_check
        r6_verifier.verify_telemetry_types = original_telemetry_check
        r6_verifier.r6_runner.SOURCE_PATHS = original_source_paths
    result["status"] = "D1_L4_CAPACITY_R7_VERIFIED"
    return result


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--output-dir", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = verify_package(args.output_dir.expanduser().absolute())
    except (
        OSError,
        RuntimeError,
        ValueError,
        sqlite3.DatabaseError,
        subprocess.CalledProcessError,
        tarfile.TarError,
    ) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
