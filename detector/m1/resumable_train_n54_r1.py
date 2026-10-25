"""Owner-approved YOLO11n 54-class, 100-epoch resumable training successor."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from m1 import resumable_train as base

BASE_RECOVERY_BINDING = base.recovery_binding
BASE_TRAIN_ARGUMENTS = base.train_arguments
EXPERIMENT = "YOLO11N-N54-R1"
OWNER_DECISION = "docs/review/yolo11n_dual_track_r1_owner_decision_record.md"
OWNER_DECISION_SHA256 = "b2b40c5937e25316c6806d5bcb6babbdcf284860a2305f2fc7b5915a058e2b8c"
PRETRAINED_NAME = "yolo11n.pt"
PRETRAINED_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
FROZEN = {
    "seed": 20261018,
    "epochs": 100,
    "imgsz": 1280,
    "batch": 4,
    "workers": 4,
    "fraction": 1.0,
    "patience": 30,
    "cos_lr": True,
    "tag": "n54_r1",
}


def _validate_model(path: Path) -> Path:
    model = path.expanduser().absolute()
    if model.name != PRETRAINED_NAME or model.is_symlink() or not model.is_file():
        raise RuntimeError(f"{EXPERIMENT} requires a regular {PRETRAINED_NAME}")
    if base.contract.sha256_file(model) != PRETRAINED_SHA256:
        raise RuntimeError(f"{EXPERIMENT} pretrained SHA-256 differs")
    return model


def _validate_frozen(args: argparse.Namespace) -> None:
    observed = {key: getattr(args, key) for key in FROZEN}
    if observed != FROZEN:
        raise RuntimeError(f"{EXPERIMENT} frozen arguments differ: {observed!r}")
    if str(args.device) != "0":
        raise RuntimeError(f"{EXPERIMENT} requires CUDA device 0")
    if args.stop_after_epoch is not None:
        expected_stop = 2 if args.resume else 1
        if args.stop_after_epoch != expected_stop:
            raise RuntimeError(
                f"{EXPERIMENT} smoke boundary must be epoch {expected_stop} "
                f"for {'resume' if args.resume else 'fresh'} mode"
            )
    _validate_model(args.model)


def recovery_binding(
    *,
    bound: dict[str, Any],
    model: dict[str, str],
    environment: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    binding = BASE_RECOVERY_BINDING(
        bound=bound,
        model=model,
        environment=environment,
        args=args,
    )
    return {
        **binding,
        "experiment": EXPERIMENT,
        "owner_decision": OWNER_DECISION,
        "owner_decision_sha256": OWNER_DECISION_SHA256,
        "pretrained_name": PRETRAINED_NAME,
        "cos_lr": True,
    }


def train_arguments(
    *,
    bound: dict[str, Any],
    args: argparse.Namespace,
    results_dir: Path,
    name: str,
) -> dict[str, Any]:
    return {
        **BASE_TRAIN_ARGUMENTS(
            bound=bound,
            args=args,
            results_dir=results_dir,
            name=name,
        ),
        "cos_lr": True,
    }


def execute(
    args: argparse.Namespace,
    *,
    yolo_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    _validate_frozen(args)
    model_path = args.model.expanduser().absolute()
    original_binding = base.recovery_binding
    original_arguments = base.train_arguments
    original_write_json = base.write_json
    original_weight = base.contract.PRETRAINED_WEIGHTS
    original_weight_hash = base.contract.PRETRAINED_WEIGHTS_SHA256

    def write_n54_json(path: Path, payload: dict[str, Any]) -> None:
        if path.name == "run_contract.json":
            payload = {
                **payload,
                "experiment": EXPERIMENT,
                "owner_decision": OWNER_DECISION,
                "owner_decision_sha256": OWNER_DECISION_SHA256,
            }
        original_write_json(path, payload)

    base.recovery_binding = recovery_binding
    base.train_arguments = train_arguments
    base.write_json = write_n54_json
    base.contract.PRETRAINED_WEIGHTS = model_path
    base.contract.PRETRAINED_WEIGHTS_SHA256 = PRETRAINED_SHA256
    try:
        outcome = base.execute(args, yolo_factory=yolo_factory)
    finally:
        base.recovery_binding = original_binding
        base.train_arguments = original_arguments
        base.write_json = original_write_json
        base.contract.PRETRAINED_WEIGHTS = original_weight
        base.contract.PRETRAINED_WEIGHTS_SHA256 = original_weight_hash

    if args.stop_after_epoch is None and (
        outcome.get("status") not in {"COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"}
        or outcome.get("completed_epoch") != FROZEN["epochs"]
    ):
        raise RuntimeError(
            f"{EXPERIMENT} did not complete the frozen {FROZEN['epochs']} epochs: {outcome!r}"
        )
    return outcome


def parser() -> argparse.ArgumentParser:
    root = base.parser()
    root.description = __doc__
    root.set_defaults(
        seed=FROZEN["seed"],
        epochs=FROZEN["epochs"],
        imgsz=FROZEN["imgsz"],
        batch=FROZEN["batch"],
        workers=FROZEN["workers"],
        fraction=FROZEN["fraction"],
        patience=FROZEN["patience"],
        tag=FROZEN["tag"],
    )
    root.add_argument("--cos-lr", action="store_true", required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        outcome = execute(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}))
        return 1
    print(json.dumps(outcome, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
