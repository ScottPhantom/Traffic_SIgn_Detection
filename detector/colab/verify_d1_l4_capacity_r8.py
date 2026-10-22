#!/usr/bin/env python3
"""Self-contained exact-runtime verifier for D1 L4 capacity R8."""

from __future__ import annotations

import argparse
import json
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

import run_d1_l4_capacity_r8 as r8_runner  # noqa: E402
import verify_d1_l4_capacity_r7 as r7_verifier  # noqa: E402

ORIGINAL_TYPE_CHECK = r7_verifier.verify_type_strict_artifacts
ORIGINAL_VERIFY_PACKAGE = r7_verifier.verify_package
ORIGINAL_ENVIRONMENT_CHECK = r7_verifier.verify_environment
ORIGINAL_TELEMETRY_CHECK = r7_verifier.verify_telemetry_types
VERIFIED_RUNTIME_IDENTITY = {
    "torch": "2.14.1+cu130",
    "ultralytics": "8.4.172",
    "cuda_version": "13.0",
    "nvidia_driver": "580.82.07",
}


def verify_environment(environment: Any, *, git_commit: str, label: str) -> None:
    ORIGINAL_ENVIRONMENT_CHECK(environment, git_commit=git_commit, label=label)
    for key, expected in VERIFIED_RUNTIME_IDENTITY.items():
        if environment[key] != expected:
            raise RuntimeError(f"{label} differs from verified L4 runtime: {key}")


def verify_telemetry_types(
    telemetry: Any,
    *,
    attempt_id: str,
    expected_gpu_uuid: str | None = None,
    expected_total_vram_mib: float | None = None,
) -> None:
    ORIGINAL_TELEMETRY_CHECK(
        telemetry,
        attempt_id=attempt_id,
        expected_gpu_uuid=expected_gpu_uuid,
        expected_total_vram_mib=expected_total_vram_mib,
    )
    observed_total: float | None = None
    for sample in telemetry["gpu_samples"]:
        total = float(sample["memory_total_mib"])
        if observed_total is None:
            observed_total = total
        if total != observed_total:
            raise RuntimeError(f"capacity {attempt_id} total VRAM changed within the attempt")
        if expected_total_vram_mib is not None and total != expected_total_vram_mib:
            raise RuntimeError(f"capacity {attempt_id} total VRAM differs from the frozen plan")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    r6_verifier = r7_verifier.r6_verifier
    original_r6_environment = r6_verifier.verify_environment
    original_r6_telemetry = r6_verifier.verify_telemetry_types
    original_r7_environment = r7_verifier.verify_environment
    original_r7_telemetry = r7_verifier.verify_telemetry_types
    r6_verifier.verify_environment = verify_environment
    r6_verifier.verify_telemetry_types = verify_telemetry_types
    r7_verifier.verify_environment = verify_environment
    r7_verifier.verify_telemetry_types = verify_telemetry_types
    try:
        ORIGINAL_TYPE_CHECK(output_dir)
    finally:
        r6_verifier.verify_environment = original_r6_environment
        r6_verifier.verify_telemetry_types = original_r6_telemetry
        r7_verifier.verify_environment = original_r7_environment
        r7_verifier.verify_telemetry_types = original_r7_telemetry


def verify_package(output_dir: Path) -> dict[str, Any]:
    original_type_check = r7_verifier.verify_type_strict_artifacts
    original_environment_check = r7_verifier.verify_environment
    original_telemetry_check = r7_verifier.verify_telemetry_types
    original_source_paths = r7_verifier.r7_runner.SOURCE_PATHS
    r7_verifier.verify_type_strict_artifacts = verify_type_strict_artifacts
    r7_verifier.verify_environment = verify_environment
    r7_verifier.verify_telemetry_types = verify_telemetry_types
    r7_verifier.r7_runner.SOURCE_PATHS = r8_runner.SOURCE_PATHS
    try:
        result = ORIGINAL_VERIFY_PACKAGE(output_dir)
    finally:
        r7_verifier.verify_type_strict_artifacts = original_type_check
        r7_verifier.verify_environment = original_environment_check
        r7_verifier.verify_telemetry_types = original_telemetry_check
        r7_verifier.r7_runner.SOURCE_PATHS = original_source_paths
    result["status"] = "D1_L4_CAPACITY_R8_VERIFIED"
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
