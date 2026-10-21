#!/usr/bin/env python3
"""Pilot R2 successor: require 100 epochs and reject early-stop before packaging."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

EXPECTED_EPOCHS = 100
EXPECTED_PATIENCE = 0
EXPECTED_SEED = 20261018
EXPECTED_IMGSZ = 1280
EXPECTED_BATCH = 4
EXPECTED_DEVICE = "0"
EXPECTED_TAG = "pilot_100e_seed_20261018_r2"


def _load(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned pilot dependency: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


r6 = _load(
    "d1_pilot_r2_pinned_r6",
    Path(__file__).with_name("run_d1_colab_checkpoint_r6.py"),
)


def validate_pilot_outcome(payload: Any, *, mode: str) -> None:
    if not isinstance(payload, dict):
        raise RuntimeError("pilot training outcome is not an object")
    if payload.get("sealed_test_accessed") is not False:
        raise RuntimeError("pilot training outcome crossed the sealed-test boundary")
    completed_epoch = payload.get("completed_epoch")
    if type(completed_epoch) is not int:
        raise RuntimeError("pilot completed epoch is not an exact integer")
    if mode == "fresh":
        if payload.get("status") != "PAUSED_FOR_RESUME" or completed_epoch != 1:
            raise RuntimeError("pilot fresh leg did not pause exactly after epoch 1")
        return
    if mode != "resume":
        raise RuntimeError("pilot mode is invalid")
    if payload.get("status") not in {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}:
        raise RuntimeError("pilot resume did not complete all configured epochs")
    if completed_epoch != EXPECTED_EPOCHS:
        raise RuntimeError("pilot resume completed fewer than 100 epochs")


def main(argv: list[str] | None = None) -> int:
    args = r6.r2.r1.parser().parse_args(argv)
    if args.epochs != EXPECTED_EPOCHS:
        raise RuntimeError("pilot R2 requires exactly 100 epochs")
    if args.patience != EXPECTED_PATIENCE:
        raise RuntimeError("pilot R2 requires --patience 0")
    if (
        args.seed != EXPECTED_SEED
        or args.imgsz != EXPECTED_IMGSZ
        or args.batch != EXPECTED_BATCH
        or args.device != EXPECTED_DEVICE
        or args.tag != EXPECTED_TAG
    ):
        raise RuntimeError("pilot R2 configuration differs from the reviewed candidate")
    if args.mode == "fresh" and args.stop_after_epoch != 1:
        raise RuntimeError("pilot R2 fresh mode must stop after epoch 1")
    if args.mode == "resume" and args.stop_after_epoch is not None:
        raise RuntimeError("pilot R2 resume mode forbids --stop-after-epoch")

    base = r6.r2.r1.base
    original_strict_json = base.strict_json

    def guarded_strict_json(path: Path) -> Any:
        payload = original_strict_json(path)
        if path.name == "training_outcome.json":
            validate_pilot_outcome(payload, mode=args.mode)
        return payload

    base.strict_json = guarded_strict_json
    try:
        return r6.main(argv)
    finally:
        base.strict_json = original_strict_json


if __name__ == "__main__":
    raise SystemExit(main())
