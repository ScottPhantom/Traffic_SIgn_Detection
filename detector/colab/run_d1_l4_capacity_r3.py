#!/usr/bin/env python3
"""Type-strict append-only R3 successor for the D1 L4 capacity study."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

COLAB_ROOT = Path(__file__).resolve().parent
DETECTOR_ROOT = COLAB_ROOT.parent
for import_root in (DETECTOR_ROOT, COLAB_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import run_d1_l4_capacity_r1 as r1  # noqa: E402
import run_d1_l4_capacity_r2 as r2  # noqa: E402

from m1 import l4_capacity  # noqa: E402

SOURCE_PATHS = (
    *r2.SOURCE_PATHS,
    "detector/colab/run_d1_l4_capacity_r3.py",
    "detector/colab/verify_d1_l4_capacity_r3.py",
)


def validate_effective_batch(
    telemetry: dict[str, Any], *, planned_batch: int
) -> dict[str, Any]:
    summary = r2.validate_effective_batch(telemetry, planned_batch=planned_batch)
    steps = telemetry["steps"]
    for index, step in enumerate(steps):
        is_final_measured_step = index == len(steps) - 1
        if not is_final_measured_step and step["images"] != planned_batch:
            raise RuntimeError("non-final measured step is not a full planned batch")
    return summary


def build_plan(**kwargs: Any) -> dict[str, Any]:
    plan = r2.R1_BUILD_PLAN(**kwargs)
    plan.pop("plan_sha256")
    repo_root = Path(plan["repo_root"])
    plan["source_sha256"] = {
        relative: r1.sha256_file(repo_root / relative) for relative in SOURCE_PATHS
    }
    plan["plan_sha256"] = l4_capacity.canonical_sha256(plan)
    return plan


def _candidate_command(
    *, runner: Path, plan_path: Path, plan_sha256: str, attempt: dict[str, Any]
) -> list[str]:
    del runner
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "_candidate",
        "--plan",
        str(plan_path),
        "--plan-sha256",
        plan_sha256,
        "--attempt-id",
        attempt["attempt_id"],
        "--batch",
        str(attempt["batch"]),
        "--workers",
        str(attempt["workers"]),
        "--repeat",
        str(attempt["repeat"]),
    ]


def _install_hardening() -> None:
    r2._install_hardening()
    r1.build_plan = build_plan
    r1._candidate_command = _candidate_command


def run_candidate(args: argparse.Namespace) -> int:
    return_code = r2.run_candidate(args)
    if return_code:
        return return_code
    plan = r1.strict_json(args.plan.expanduser().absolute())
    attempt_dir = Path(plan["output_dir"]) / "attempts" / args.attempt_id
    result = r1.strict_json(attempt_dir / "result.json")
    if result["status"] == "SUCCEEDED":
        telemetry = r1.strict_json(attempt_dir / "raw_telemetry.json")
        try:
            validate_effective_batch(telemetry, planned_batch=args.batch)
        except RuntimeError as error:
            print(json.dumps({"status": "FAILED", "error": str(error)}))
            return 1
    return 0


def parser() -> argparse.ArgumentParser:
    return r2.parser()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    _install_hardening()
    try:
        return r1.run_matrix(args) if args.command == "run" else run_candidate(args)
    except (
        OSError,
        RuntimeError,
        ValueError,
        sqlite3.DatabaseError,
        subprocess.CalledProcessError,
    ) as error:
        print(json.dumps({"status": "FAILED", "error": f"{type(error).__name__}: {error}"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
