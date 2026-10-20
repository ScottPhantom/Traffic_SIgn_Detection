"""Contract-bound D1 training with crash-safe Drive checkpoints and real resume."""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from m1 import checkpoint_store, contract
from m1.cli import run_name, write_json

OUTCOME = "training_outcome.json"


def recovery_binding(
    *,
    bound: dict[str, Any],
    model: dict[str, str],
    environment: dict[str, Any],
    args: argparse.Namespace,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "experiment": "D1",
        "git_commit": environment["git_commit"],
        "detector_lock_sha256": environment["detector_lock_sha256"],
        "model_sha256": model["sha256"],
        "export_manifest_sha256": bound["export_manifest_sha256"],
        "class_map_sha256": bound["class_map_sha256"],
        "split_stem_sha256": bound["split_stem_sha256"],
        "test_seal_sha256": bound["split_stem_sha256"]["test"],
        "seed": args.seed,
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "workers": args.workers,
        "fraction": args.fraction,
        "patience": args.patience,
        "deterministic": True,
        "pretrained": True,
        "plots": False,
        **contract.FORBIDDEN_OVERRIDES,
    }


def train_arguments(
    *,
    bound: dict[str, Any],
    args: argparse.Namespace,
    results_dir: Path,
    name: str,
) -> dict[str, Any]:
    return {
        "data": bound["data_yaml"],
        "epochs": args.epochs,
        "imgsz": args.imgsz,
        "batch": args.batch,
        "device": args.device,
        "seed": args.seed,
        "deterministic": True,
        "workers": args.workers,
        "fraction": args.fraction,
        "patience": args.patience,
        "plots": False,
        "project": str(results_dir),
        "name": name,
        "exist_ok": True,
        "pretrained": True,
        **contract.FORBIDDEN_OVERRIDES,
    }


def _finalize_run(run_dir: Path) -> None:
    record = json.loads((run_dir / "run_contract.json").read_text(encoding="utf-8"))
    weights = {}
    for filename in ("best.pt", "last.pt"):
        path = run_dir / "weights" / filename
        if not path.is_file() or path.is_symlink():
            raise RuntimeError(f"training did not produce a regular required weight: {path}")
        weights[filename] = {"path": str(path), "sha256": contract.sha256_file(path)}
    record["artifacts"] = {"weights": weights}
    record["status"] = "TRAINED"
    write_json(run_dir / "run_contract.json", record)


def execute(
    args: argparse.Namespace,
    *,
    yolo_factory: Callable[[str], Any] | None = None,
) -> dict[str, Any]:
    if args.seed not in contract.SEEDS:
        raise RuntimeError(f"seed {args.seed} is not one of the D-05 seeds {contract.SEEDS}")
    if args.stop_after_epoch is not None and not 1 <= args.stop_after_epoch < args.epochs:
        raise RuntimeError("--stop-after-epoch must be at least 1 and below --epochs")
    results_dir = checkpoint_store.require_safe_directory(args.results_dir)
    expected_results_dir = checkpoint_store.require_safe_directory(contract.RESULTS_DIR)
    if results_dir != expected_results_dir:
        raise RuntimeError(
            f"--results-dir must be the governed repository results root: {expected_results_dir}"
        )
    checkpoint_store.require_safe_directory(results_dir, create=True)
    checkpoint_dir = args.checkpoint_dir.expanduser().absolute()
    model_binding = contract.bind_training_model(str(args.model))
    bound = contract.check_contract()
    environment = contract.environment()
    binding = recovery_binding(
        bound=bound, model=model_binding, environment=environment, args=args
    )
    store = checkpoint_store.CheckpointStore(checkpoint_dir)
    contract.disable_telemetry()
    if yolo_factory is None:
        from ultralytics import YOLO

        yolo_factory = YOLO

    if args.resume:
        latest = store.load_latest(binding)
        expected_epoch = latest["completed_epoch"] + 1
        last = store.restore_latest(results_dir, binding)
        run_dir = last.parents[1]
        if latest["completed_epoch"] == args.epochs:
            _finalize_run(run_dir)
            outcome = {
                "status": "COMPLETED_FROM_FINAL_CHECKPOINT",
                "run": run_dir.name,
                "run_dir": str(run_dir),
                "completed_epoch": args.epochs,
                "resumed": True,
                "sealed_test_accessed": False,
            }
            checkpoint_store.write_json_atomic(checkpoint_dir / OUTCOME, outcome)
            return outcome
        model = yolo_factory(str(last))
        name = run_dir.name
    else:
        if (checkpoint_dir / checkpoint_store.LATEST).exists():
            raise RuntimeError("fresh training refuses an existing checkpoint latest pointer")
        name = run_name(
            model_binding["path"], args.seed, args.tag, bound["split_stem_sha256"]["test"]
        )
        run_dir = results_dir / name
        if run_dir.exists():
            raise RuntimeError(f"run directory already exists: {run_dir}")
        run_dir.mkdir(parents=True)
        train_args = train_arguments(
            bound=bound, args=args, results_dir=results_dir, name=name
        )
        write_json(
            run_dir / "run_contract.json",
            {
                "experiment": "D1",
                "run": name,
                "seed": args.seed,
                "model": model_binding,
                "train_args": train_args,
                "contract": bound,
                "environment": environment,
                "d05_gates": contract.GATES,
                "status": "STARTED",
            },
        )
        model = yolo_factory(model_binding["path"])
        expected_epoch = 1

    train_args = train_arguments(bound=bound, args=args, results_dir=results_dir, name=name)
    mirror = checkpoint_store.make_ultralytics_callback(store, binding)
    callback_count = 0

    def checkpoint_and_maybe_pause(trainer: Any) -> None:
        nonlocal callback_count, expected_epoch
        observed_epoch = int(trainer.epoch) + 1
        if observed_epoch != expected_epoch:
            raise RuntimeError(
                f"non-contiguous checkpoint epoch: expected {expected_epoch}, got {observed_epoch}"
            )
        mirror(trainer)
        callback_count += 1
        expected_epoch += 1
        if args.stop_after_epoch == observed_epoch:
            trainer.stop = True

    model.add_callback("on_model_save", checkpoint_and_maybe_pause)
    if args.resume:
        model.train(resume=True, **train_args)
    else:
        model.train(**train_args)
    latest = store.load_latest(binding)
    if callback_count == 0 and latest["completed_epoch"] < args.epochs:
        raise RuntimeError("training returned without producing the required next checkpoint")
    if args.stop_after_epoch is not None:
        if latest["completed_epoch"] != args.stop_after_epoch:
            raise RuntimeError("recovery drill did not pause at --stop-after-epoch")
        outcome = {
            "status": "PAUSED_FOR_RESUME",
            "run": name,
            "run_dir": str(run_dir),
            "completed_epoch": latest["completed_epoch"],
            "resumed": args.resume,
            "sealed_test_accessed": False,
        }
    else:
        _finalize_run(run_dir)
        outcome = {
            "status": (
                "COMPLETED"
                if latest["completed_epoch"] == args.epochs
                else "COMPLETED_EARLY_STOPPED"
            ),
            "run": name,
            "run_dir": str(run_dir),
            "completed_epoch": latest["completed_epoch"],
            "resumed": args.resume,
            "sealed_test_accessed": False,
        }
    checkpoint_store.write_json_atomic(checkpoint_dir / OUTCOME, outcome)
    return outcome


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--model", type=Path, required=True)
    root.add_argument("--checkpoint-dir", type=Path, required=True)
    root.add_argument("--results-dir", type=Path, default=contract.RESULTS_DIR)
    root.add_argument("--resume", action="store_true")
    root.add_argument("--stop-after-epoch", type=int)
    root.add_argument("--seed", type=int, default=20261018)
    root.add_argument("--epochs", type=int, default=100)
    root.add_argument("--imgsz", type=int, default=1280)
    root.add_argument("--batch", type=int, default=8)
    root.add_argument("--device", default="0")
    root.add_argument("--workers", type=int, default=4)
    root.add_argument("--fraction", type=float, default=1.0)
    root.add_argument("--patience", type=int, default=30)
    root.add_argument("--tag", default="colab_checkpoint_r1")
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
