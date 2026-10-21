#!/usr/bin/env python3
"""R4-R5 successor with path-first validation and durable pointer failures."""

from __future__ import annotations

import importlib.util
import re
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


r4 = _load(
    "d1_checkpoint_r4_r5_pinned_r4",
    Path(__file__).with_name("run_d1_colab_checkpoint_r4.py"),
)
r3 = r4.r3
r2 = r4.r2


def verify_current_checkpoint(state_dir: Path, expected_binding: str) -> dict[str, Any]:
    state = r3.reject_symlink_components(state_dir)
    recovery = r3.reject_symlink_components(state / "recovery")
    latest_path = r3.reject_symlink_components(recovery / "latest.json")
    if not latest_path.is_file():
        raise RuntimeError("checkpoint latest pointer is missing")
    latest = r2.strict_json_bytes(latest_path.read_bytes())
    if not isinstance(latest, dict):
        raise RuntimeError("checkpoint latest pointer must be an object")
    generation = latest.get("generation")
    if not isinstance(generation, str) or re.fullmatch(r"epoch-[0-9]{4}", generation) is None:
        raise RuntimeError("checkpoint generation name is unsafe")
    return r4.verify_current_checkpoint(state, expected_binding)


def durable_preflight_failure(
    state_dir: Path,
    args: Any,
    started_at: str,
    error: Exception,
    *,
    identity: dict[str, str] | None,
    binding: str | None,
    completed: list[dict[str, Any]],
) -> None:
    safe_state = r2.r1.require_unlinked_path(state_dir, directory=True)
    safe_state.mkdir(parents=True, exist_ok=True)
    for child in ("colab_execution.json", "colab_execution.json.tmp", "execution_attempts.jsonl"):
        r2.r1.require_writable_child(safe_state, child)
    finished_at = r2.r1.base.now()
    message = f"{type(error).__name__}: {error}"
    checkpoint = None
    try:
        recovery = r3.reject_symlink_components(safe_state / "recovery")
        latest = r3.reject_symlink_components(recovery / "latest.json")
        if latest.is_file():
            checkpoint = r2.checkpoint_binding(safe_state)
    except Exception:
        checkpoint = None
    attempt = {
        "mode": args.mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "status": "FAILED",
        "error": message,
        "runtime_identity": identity,
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": checkpoint,
    }
    execution = {
        "schema_version": 2,
        "status": "FAILED",
        "mode": args.mode,
        "started_at": started_at,
        "finished_at": finished_at,
        "sealed_test_accessed": False,
        "runtime_identity": identity,
        "run_binding_sha256": binding,
        "checkpoint_binding_sha256": checkpoint,
        "execution_attempts": [*completed, attempt],
        "error": message,
    }
    r2.r1.base.write_json(safe_state / "colab_execution.json", execution)
    r2.r1.append_jsonl(safe_state / "execution_attempts.jsonl", attempt)


def verify_live_state(state_dir: Path) -> dict[str, Any]:
    original = r2.verify_current_checkpoint
    r2.verify_current_checkpoint = verify_current_checkpoint
    try:
        return r2.verify_live_state(state_dir)
    finally:
        r2.verify_current_checkpoint = original


def main(argv: list[str] | None = None) -> int:
    original = r2.record_preflight_failure
    r2.record_preflight_failure = durable_preflight_failure
    try:
        return r2.main(argv)
    finally:
        r2.record_preflight_failure = original


if __name__ == "__main__":
    raise SystemExit(main())
