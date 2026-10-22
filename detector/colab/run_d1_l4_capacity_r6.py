#!/usr/bin/env python3
"""Exact environment/telemetry/manifest R6 successor for D1 L4 capacity."""

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
import run_d1_l4_capacity_r5 as r5  # noqa: E402

from m1 import l4_capacity  # noqa: E402

SOURCE_PATHS = (
    *r5.SOURCE_PATHS,
    "detector/colab/run_d1_l4_capacity_r6.py",
    "detector/colab/verify_d1_l4_capacity_r6.py",
)


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
    r5._install_hardening()
    r1.build_plan = build_plan
    r1._candidate_command = _candidate_command


def parser() -> argparse.ArgumentParser:
    return r5.parser()


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    _install_hardening()
    try:
        return r1.run_matrix(args) if args.command == "run" else r5.r4.r3.run_candidate(args)
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
