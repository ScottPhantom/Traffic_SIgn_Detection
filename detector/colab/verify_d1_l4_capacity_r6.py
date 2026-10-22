#!/usr/bin/env python3
"""Exact environment/telemetry/manifest verifier for D1 L4 capacity R6."""

from __future__ import annotations

import argparse
import importlib.metadata
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

import run_d1_l4_capacity_r6 as r6_runner  # noqa: E402
import verify_d1_l4_capacity_r5 as r5_verifier  # noqa: E402

from m1 import contract  # noqa: E402

ORIGINAL_TYPE_CHECK = r5_verifier.verify_type_strict_artifacts
ORIGINAL_VERIFY_PACKAGE = r5_verifier.verify_package
GPU_SAMPLE_KEYS = {
    "time",
    "gpu_uuid",
    "utilization_percent",
    "memory_used_mib",
    "memory_total_mib",
    "power_watts",
    "temperature_celsius",
}
COUNT_KEYS = {"measured_batches", "measured_images", "gpu_sample_count"}
METRIC_KEYS = {
    "measurement_seconds",
    "images_per_second",
    "throughput_cv",
    "median_gpu_utilization_percent",
    "p95_gpu_utilization_percent",
    "peak_vram_used_mib",
    "total_vram_mib",
    "peak_vram_fraction",
    "median_power_watts",
}


def _finite_number(value: Any, label: str) -> float:
    if type(value) not in (int, float) or not math.isfinite(float(value)):
        raise RuntimeError(f"{label} must be a finite non-boolean number")
    return float(value)


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
    expected_identity = {
        "torch": importlib.metadata.version("torch"),
        "ultralytics": importlib.metadata.version("ultralytics"),
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


def verify_manifest(manifest: Any) -> None:
    expected_keys = {
        "schema_version",
        "status",
        "plan_sha256",
        "sealed_test_accessed",
        "files",
        "evidence_sha256",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        raise RuntimeError("capacity manifest exact schema differs")
    if type(manifest["status"]) is not str or manifest["status"] != "EVIDENCE_PACKAGED":
        raise RuntimeError("capacity manifest status differs")
    if not isinstance(manifest["files"], list) or not manifest["files"]:
        raise RuntimeError("capacity manifest files differ")
    for record in manifest["files"]:
        if not isinstance(record, dict) or set(record) != {"path", "size", "sha256"}:
            raise RuntimeError("capacity manifest file schema differs")
        if type(record["path"]) is not str or not record["path"]:
            raise RuntimeError("capacity manifest file path differs")
        if type(record["size"]) is not int or record["size"] < 0:
            raise RuntimeError("capacity manifest file size differs")
        if type(record["sha256"]) is not str or len(record["sha256"]) != 64:
            raise RuntimeError("capacity manifest file hash differs")


def verify_telemetry_types(telemetry: Any, *, attempt_id: str) -> None:
    for step in telemetry["steps"]:
        for key in ("batch_index", "images", "planned_batch", "trainer_batch_size"):
            if type(step.get(key)) is not int:
                raise RuntimeError(f"capacity {attempt_id} step {key} must be exact integer")
        for key in ("seconds", "compute_seconds", "inter_batch_gap_seconds"):
            _finite_number(step.get(key), f"capacity {attempt_id} step {key}")
    samples = telemetry["gpu_samples"]
    if not isinstance(samples, list) or not samples:
        raise RuntimeError(f"capacity {attempt_id} GPU samples differ")
    for sample in samples:
        if not isinstance(sample, dict) or set(sample) != GPU_SAMPLE_KEYS:
            raise RuntimeError(f"capacity {attempt_id} GPU sample schema differs")
        r5_verifier.r4_verifier.r3_verifier.r2_verifier.parse_timestamp(
            sample["time"],
            f"capacity {attempt_id} GPU sample",
        )
        if type(sample["gpu_uuid"]) is not str or not sample["gpu_uuid"].startswith("GPU-"):
            raise RuntimeError(f"capacity {attempt_id} GPU sample UUID differs")
        for key in GPU_SAMPLE_KEYS - {"time", "gpu_uuid"}:
            _finite_number(sample[key], f"capacity {attempt_id} GPU sample {key}")


def verify_report_numeric_types(report: dict[str, Any]) -> None:
    for candidate in report["candidates"]:
        for record in (candidate, *candidate["repetitions"]):
            for key in COUNT_KEYS:
                if type(record.get(key)) is not int:
                    raise RuntimeError(f"capacity report {key} must be exact integer")
            for key in METRIC_KEYS:
                if key in record:
                    _finite_number(record[key], f"capacity report {key}")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    ORIGINAL_TYPE_CHECK(output_dir)
    runner = r5_verifier.r4_verifier.r3_verifier.r2_verifier.r1_runner
    plan = runner.strict_json(output_dir / runner.PLAN_NAME)
    report = runner.strict_json(output_dir / runner.REPORT_NAME)
    manifest = runner.strict_json(output_dir / runner.MANIFEST_NAME)
    verify_environment(plan["environment"], git_commit=plan["git_commit"], label="plan environment")
    verify_environment(
        report["environment"],
        git_commit=report["git_commit"],
        label="report environment",
    )
    verify_manifest(manifest)
    verify_report_numeric_types(report)
    for attempt in plan["roster"]:
        telemetry = runner.strict_json(
            output_dir / "attempts" / attempt["attempt_id"] / "raw_telemetry.json"
        )
        verify_telemetry_types(telemetry, attempt_id=attempt["attempt_id"])


def verify_package(output_dir: Path) -> dict[str, Any]:
    original_type_check = r5_verifier.verify_type_strict_artifacts
    original_source_paths = r5_verifier.r5_runner.SOURCE_PATHS
    r5_verifier.verify_type_strict_artifacts = verify_type_strict_artifacts
    r5_verifier.r5_runner.SOURCE_PATHS = r6_runner.SOURCE_PATHS
    try:
        result = ORIGINAL_VERIFY_PACKAGE(output_dir)
    finally:
        r5_verifier.verify_type_strict_artifacts = original_type_check
        r5_verifier.r5_runner.SOURCE_PATHS = original_source_paths
    result["status"] = "D1_L4_CAPACITY_R6_VERIFIED"
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
