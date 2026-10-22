#!/usr/bin/env python3
"""Governance-boolean-strict independent verifier for D1 L4 capacity R5."""

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

import run_d1_l4_capacity_r5 as r5_runner  # noqa: E402
import verify_d1_l4_capacity_r4 as r4_verifier  # noqa: E402

ORIGINAL_TYPE_CHECK = r4_verifier.verify_type_strict_artifacts
ORIGINAL_VERIFY_PACKAGE = r4_verifier.verify_package


def _require_boolean(record: dict[str, Any], key: str, expected: bool, label: str) -> None:
    value = record.get(key)
    if type(value) is not bool or value is not expected:
        raise RuntimeError(f"{label} {key} must be exact boolean {expected}")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    ORIGINAL_TYPE_CHECK(output_dir)
    runner = r4_verifier.r3_verifier.r2_verifier.r1_runner
    plan = runner.strict_json(output_dir / runner.PLAN_NAME)
    report = runner.strict_json(output_dir / runner.REPORT_NAME)
    proposal = runner.strict_json(output_dir / runner.LOCK_CANDIDATE_NAME)
    manifest = runner.strict_json(output_dir / runner.MANIFEST_NAME)
    _require_boolean(plan, "sealed_test_accessed", False, "capacity plan")
    _require_boolean(report, "sealed_test_accessed", False, "capacity report")
    _require_boolean(
        report,
        "not_model_quality_evidence",
        True,
        "capacity report",
    )
    _require_boolean(proposal, "sealed_test_accessed", False, "capacity proposal")
    _require_boolean(manifest, "sealed_test_accessed", False, "capacity manifest")
    for label, environment in (
        ("plan environment", plan["environment"]),
        ("report environment", report["environment"]),
    ):
        _require_boolean(environment, "mps_available", False, label)
        _require_boolean(environment, "cuda_available", True, label)
    for attempt in plan["roster"]:
        attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
        result = runner.strict_json(attempt_dir / "result.json")
        telemetry = runner.strict_json(attempt_dir / "raw_telemetry.json")
        _require_boolean(result, "oom", result["status"] == "OOM", "capacity result")
        _require_boolean(
            telemetry,
            "sealed_test_accessed",
            False,
            "capacity telemetry",
        )


def verify_package(output_dir: Path) -> dict[str, Any]:
    original_type_check = r4_verifier.verify_type_strict_artifacts
    original_source_paths = r4_verifier.r4_runner.SOURCE_PATHS
    r4_verifier.verify_type_strict_artifacts = verify_type_strict_artifacts
    r4_verifier.r4_runner.SOURCE_PATHS = r5_runner.SOURCE_PATHS
    try:
        result = ORIGINAL_VERIFY_PACKAGE(output_dir)
    finally:
        r4_verifier.verify_type_strict_artifacts = original_type_check
        r4_verifier.r4_runner.SOURCE_PATHS = original_source_paths
    result["status"] = "D1_L4_CAPACITY_R5_VERIFIED"
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
