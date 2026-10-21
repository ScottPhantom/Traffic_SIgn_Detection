#!/usr/bin/env python3
"""R4-R3 successor with pinned-store checkpoint verification and safe paths."""

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


r2 = _load(
    "d1_checkpoint_r4_r3_pinned_r2",
    Path(__file__).with_name("run_d1_colab_checkpoint_r2.py"),
)
checkpoint_store = _load(
    "d1_checkpoint_r4_r3_store",
    Path(__file__).parents[1] / "m1/checkpoint_store.py",
)


def reject_symlink_components(path: Path) -> Path:
    lexical = path.expanduser().absolute()
    current = lexical
    while True:
        if current.is_symlink():
            raise RuntimeError(f"checkpoint path contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    return lexical


def verify_current_checkpoint(state_dir: Path, expected_binding: str) -> dict[str, Any]:
    state = reject_symlink_components(state_dir)
    recovery = reject_symlink_components(state / "recovery")
    latest_path = reject_symlink_components(recovery / "latest.json")
    if not latest_path.is_file():
        raise RuntimeError("checkpoint latest pointer is missing")
    latest = r2.strict_json_bytes(latest_path.read_bytes())
    if not isinstance(latest, dict) or set(latest) != {
        "schema_version",
        "generation",
        "manifest_sha256",
        "binding_sha256",
    }:
        raise RuntimeError("checkpoint latest pointer schema differs")
    generation = latest["generation"]
    if (
        latest["schema_version"] != 1
        or not isinstance(generation, str)
        or re.fullmatch(r"epoch-[0-9]{4}", generation) is None
        or not r2._is_sha256(latest["manifest_sha256"])
        or latest["binding_sha256"] != expected_binding
    ):
        raise RuntimeError("checkpoint latest pointer identity differs")
    snapshots = reject_symlink_components(recovery / "snapshots")
    snapshot = reject_symlink_components(snapshots / generation)
    weights = reject_symlink_components(snapshot / "weights")
    if not snapshot.is_dir() or not weights.is_dir():
        raise RuntimeError("checkpoint snapshot directories are missing")
    manifest_path = reject_symlink_components(snapshot / "checkpoint_manifest.json")
    if not manifest_path.is_file():
        raise RuntimeError("checkpoint manifest is missing")
    manifest = r2.strict_json_bytes(manifest_path.read_bytes())
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "status",
        "run",
        "completed_epoch",
        "binding",
        "binding_sha256",
        "files",
    }:
        raise RuntimeError("checkpoint manifest schema differs")
    if not isinstance(manifest["run"], str) or checkpoint_store.RUN_PATTERN.fullmatch(
        manifest["run"]
    ) is None:
        raise RuntimeError("checkpoint run identity differs")
    epoch = manifest["completed_epoch"]
    if type(epoch) is not int or epoch < 1 or epoch > 9999:
        raise RuntimeError("checkpoint completed epoch differs")
    if generation != f"epoch-{epoch:04d}":
        raise RuntimeError("checkpoint epoch and generation differ")
    if r2.canonical_sha256(manifest["binding"]) != expected_binding:
        raise RuntimeError("checkpoint manifest binding differs")
    verified = checkpoint_store.CheckpointStore(recovery).load_latest(manifest["binding"])
    if verified != manifest:
        raise RuntimeError("strict and pinned checkpoint verification differ")
    return verified


def verify_live_state(state_dir: Path) -> dict[str, Any]:
    original = r2.verify_current_checkpoint
    r2.verify_current_checkpoint = verify_current_checkpoint
    try:
        return r2.verify_live_state(state_dir)
    finally:
        r2.verify_current_checkpoint = original


def main(argv: list[str] | None = None) -> int:
    return r2.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
