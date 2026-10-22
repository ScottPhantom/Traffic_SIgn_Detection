#!/usr/bin/env python3
"""Type-strict independent verifier for D1 L4 capacity R3 evidence."""

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

import run_d1_l4_capacity_r2 as r2_runner  # noqa: E402
import run_d1_l4_capacity_r3 as r3_runner  # noqa: E402
import verify_d1_l4_capacity_r2 as r2_verifier  # noqa: E402

ORIGINAL_ANCHORS = r2_verifier.verify_independent_anchors
ORIGINAL_ATTEMPT = r2_verifier.verify_attempt_hardening
ORIGINAL_EXECUTION = r2_verifier.verify_execution


def _require_exact_type(value: Any, expected: type, label: str) -> None:
    if type(value) is not expected:
        raise RuntimeError(f"{label} must have exact type {expected.__name__}")


def verify_type_strict_artifacts(output_dir: Path) -> None:
    runner = r2_verifier.r1_runner
    plan = runner.strict_json(output_dir / runner.PLAN_NAME)
    report = runner.strict_json(output_dir / runner.REPORT_NAME)
    proposal = runner.strict_json(output_dir / runner.LOCK_CANDIDATE_NAME)
    manifest = runner.strict_json(output_dir / runner.MANIFEST_NAME)
    for label, record in (
        ("plan", plan),
        ("report", report),
        ("proposal", proposal),
        ("manifest", manifest),
    ):
        _require_exact_type(record.get("schema_version"), int, f"capacity {label} schema")
        _require_exact_type(
            record.get("sealed_test_accessed"),
            bool,
            f"capacity {label} sealed-test marker",
        )
        if record["schema_version"] != 1 or record["sealed_test_accessed"] is not False:
            raise RuntimeError(f"capacity {label} governance value differs")
    for attempt in plan["roster"]:
        attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
        result = runner.strict_json(attempt_dir / "result.json")
        telemetry = runner.strict_json(attempt_dir / "raw_telemetry.json")
        _require_exact_type(telemetry.get("schema_version"), int, "capacity telemetry schema")
        _require_exact_type(
            telemetry.get("sealed_test_accessed"),
            bool,
            "capacity telemetry sealed-test marker",
        )
        _require_exact_type(result.get("oom"), bool, "capacity result OOM marker")
        for key in ("attempt_id", "batch", "workers", "repeat"):
            expected_type = str if key == "attempt_id" else int
            _require_exact_type(result.get(key), expected_type, f"capacity result {key}")
        train_args = telemetry.get("train_args", {})
        for key in (
            "deterministic",
            "plots",
            "val",
            "save",
            "cache",
            "amp",
            "verbose",
            "exist_ok",
            "pretrained",
        ):
            _require_exact_type(train_args.get(key), bool, f"capacity train_args {key}")
        _require_exact_type(train_args.get("fliplr"), float, "capacity train_args fliplr")
        for key in ("epochs", "imgsz", "batch", "seed", "workers", "patience"):
            _require_exact_type(train_args.get(key), int, f"capacity train_args {key}")


def verify_execution(path: Path, *, plan_sha256: str, report_sha256: str) -> None:
    rows = [
        r2_verifier.strict_json_line(line)
        for line in path.read_text(encoding="utf-8").splitlines()
    ]
    if any(type(row.get("schema_version")) is not int for row in rows):
        raise RuntimeError("capacity execution schema version must be an integer")
    if any(type(row.get("sealed_test_accessed")) is not bool for row in rows):
        raise RuntimeError("capacity execution sealed-test marker must be boolean")
    ORIGINAL_EXECUTION(
        path,
        plan_sha256=plan_sha256,
        report_sha256=report_sha256,
    )


def verify_independent_anchors(plan: dict[str, Any]) -> None:
    original_paths = r2_runner.SOURCE_PATHS
    r2_runner.SOURCE_PATHS = r3_runner.SOURCE_PATHS
    try:
        ORIGINAL_ANCHORS(plan)
    finally:
        r2_runner.SOURCE_PATHS = original_paths


def verify_attempt_hardening(
    output_dir: Path,
    *,
    attempt: dict[str, Any],
    plan: dict[str, Any],
) -> None:
    ORIGINAL_ATTEMPT(output_dir, attempt=attempt, plan=plan)
    attempt_dir = output_dir / "attempts" / attempt["attempt_id"]
    result = r2_verifier.r1_runner.strict_json(attempt_dir / "result.json")
    if result["status"] == "SUCCEEDED":
        telemetry = r2_verifier.r1_runner.strict_json(
            attempt_dir / "raw_telemetry.json"
        )
        r3_runner.validate_effective_batch(
            telemetry,
            planned_batch=attempt["batch"],
        )


def verify_package(output_dir: Path) -> dict[str, Any]:
    verify_type_strict_artifacts(output_dir)
    originals = (
        r2_verifier.verify_independent_anchors,
        r2_verifier.verify_attempt_hardening,
        r2_verifier.verify_execution,
    )
    r2_verifier.verify_independent_anchors = verify_independent_anchors
    r2_verifier.verify_attempt_hardening = verify_attempt_hardening
    r2_verifier.verify_execution = verify_execution
    try:
        result = r2_verifier.verify_package(output_dir)
    finally:
        (
            r2_verifier.verify_independent_anchors,
            r2_verifier.verify_attempt_hardening,
            r2_verifier.verify_execution,
        ) = originals
    result["status"] = "D1_L4_CAPACITY_R3_VERIFIED"
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
