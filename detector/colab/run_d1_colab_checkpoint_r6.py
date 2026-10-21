#!/usr/bin/env python3
"""R4-R6 successor with exact execution schema-version typing."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned successor module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r5 = _load(
    "d1_checkpoint_r4_r6_pinned_r5",
    Path(__file__).with_name("run_d1_colab_checkpoint_r5.py"),
)
r2 = r5.r2
ORIGINAL_VALIDATE_RUNTIME_EVIDENCE = r2.validate_runtime_evidence


def validate_runtime_evidence(execution: Any, attempts: Any) -> dict[str, Any]:
    if (
        not isinstance(execution, dict)
        or type(execution.get("schema_version")) is not int
        or execution["schema_version"] != 2
    ):
        raise RuntimeError("execution schema version type differs")
    return ORIGINAL_VALIDATE_RUNTIME_EVIDENCE(execution, attempts)


def _with_strict_runtime_validator(function, *args):
    original = r2.validate_runtime_evidence
    r2.validate_runtime_evidence = validate_runtime_evidence
    try:
        return function(*args)
    finally:
        r2.validate_runtime_evidence = original


def verify_r4_result_archive(archive_path: Path, manifest_path: Path) -> dict[str, Any]:
    return _with_strict_runtime_validator(
        r2.verify_r4_result_archive, archive_path, manifest_path
    )


def verify_live_state(state_dir: Path) -> dict[str, Any]:
    return _with_strict_runtime_validator(r5.verify_live_state, state_dir)


def main(argv: list[str] | None = None) -> int:
    return _with_strict_runtime_validator(r5.main, argv)


if __name__ == "__main__":
    raise SystemExit(main())
