#!/usr/bin/env python3
"""Nested-schema-strict independent verifier for D1 L4 capacity R4."""

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

import run_d1_l4_capacity_r4 as r4_runner  # noqa: E402
import verify_d1_l4_capacity_r3 as r3_verifier  # noqa: E402

ORIGINAL_TYPE_CHECK = r3_verifier.verify_type_strict_artifacts
ORIGINAL_VERIFY_PACKAGE = r3_verifier.verify_package


def _require_exact_type(value: Any, expected: type, label: str) -> None:
    if type(value) is not expected:
        raise RuntimeError(f"{label} must have exact type {expected.__name__}")


def _verify_attempt_identity(record: Any, *, label: str) -> None:
    if not isinstance(record, dict) or set(record) != {
        "attempt_id",
        "batch",
        "workers",
        "repeat",
    }:
        raise RuntimeError(f"{label} identity schema differs")
    _require_exact_type(record["attempt_id"], str, f"{label} attempt_id")
    for key in ("batch", "workers", "repeat"):
        _require_exact_type(record[key], int, f"{label} {key}")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    ORIGINAL_TYPE_CHECK(output_dir)
    runner = r3_verifier.r2_verifier.r1_runner
    plan = runner.strict_json(output_dir / runner.PLAN_NAME)
    integer_profile_keys = {"epochs", "imgsz", "seed", "warmup_batches", "repetitions"}
    float_profile_keys = {
        "fraction",
        "max_vram_fraction",
        "max_throughput_cv",
        "throughput_tie_fraction",
    }
    for key in integer_profile_keys:
        _require_exact_type(plan["profile"].get(key), int, f"capacity plan profile {key}")
    for key in float_profile_keys:
        _require_exact_type(plan["profile"].get(key), float, f"capacity plan profile {key}")
    for index, attempt in enumerate(plan["roster"], start=1):
        _verify_attempt_identity(attempt, label=f"capacity plan roster row {index}")
        attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
        telemetry = runner.strict_json(attempt_dir / "raw_telemetry.json")
        if telemetry["schema_version"] != 1:
            raise RuntimeError("capacity telemetry schema version differs")
        _verify_attempt_identity(
            telemetry.get("attempt"),
            label=f"capacity telemetry {attempt['attempt_id']}",
        )
        if telemetry["attempt"] != attempt:
            raise RuntimeError(f"capacity telemetry identity differs: {attempt['attempt_id']}")
    report = runner.strict_json(output_dir / runner.REPORT_NAME)
    for key in integer_profile_keys:
        _require_exact_type(report["profile"].get(key), int, f"capacity report profile {key}")
    for key in ("fraction", "max_vram_fraction", "max_throughput_cv"):
        _require_exact_type(report["profile"].get(key), float, f"capacity report profile {key}")
    for candidate in report["candidates"]:
        _require_exact_type(candidate.get("batch"), int, "capacity report candidate batch")
        _require_exact_type(candidate.get("workers"), int, "capacity report candidate workers")
        _require_exact_type(candidate.get("oom"), bool, "capacity report candidate OOM")
        for repetition in candidate["repetitions"]:
            _require_exact_type(repetition.get("repeat"), int, "capacity report repeat")
            _require_exact_type(repetition.get("oom"), bool, "capacity report repetition OOM")
    proposal = runner.strict_json(output_dir / runner.LOCK_CANDIDATE_NAME)
    selection = proposal["selection"]
    for key in ("batch", "workers", "imgsz", "epochs", "patience"):
        _require_exact_type(selection.get(key), int, f"capacity proposal {key}")
    for seed in selection.get("seeds", []):
        _require_exact_type(seed, int, "capacity proposal seed")
    _require_exact_type(selection.get("fraction"), float, "capacity proposal fraction")
    _require_exact_type(selection.get("fliplr"), float, "capacity proposal fliplr")
    for key in ("deterministic", "pretrained"):
        _require_exact_type(selection.get(key), bool, f"capacity proposal {key}")


def verify_package(output_dir: Path) -> dict[str, Any]:
    original_type_check = r3_verifier.verify_type_strict_artifacts
    original_source_paths = r3_verifier.r3_runner.SOURCE_PATHS
    r3_verifier.verify_type_strict_artifacts = verify_type_strict_artifacts
    r3_verifier.r3_runner.SOURCE_PATHS = r4_runner.SOURCE_PATHS
    try:
        result = ORIGINAL_VERIFY_PACKAGE(output_dir)
    finally:
        r3_verifier.verify_type_strict_artifacts = original_type_check
        r3_verifier.r3_runner.SOURCE_PATHS = original_source_paths
    result["status"] = "D1_L4_CAPACITY_R4_VERIFIED"
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
