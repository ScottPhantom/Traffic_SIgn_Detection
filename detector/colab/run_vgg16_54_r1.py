#!/usr/bin/env python3
"""Resumable VGG16 54-class crop-classifier candidate for an L4 runtime.

The runner consumes the already reviewed Cascade B0 train/validation bundle,
has no sealed-test route, and refuses GPU work until Owner approval and
independent source-QA proofs are hash-pinned.  Long training additionally
requires an independently approved two-runtime fresh/resume smoke proof.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import pickle
import random
import shutil
import stat
import sys
import tarfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

os.environ.update(
    WANDB_MODE="disabled",
    HF_HUB_OFFLINE="1",
    TRANSFORMERS_OFFLINE="1",
    TORCH_HOME="/content/vgg16_54_torch_cache",
    CUBLAS_WORKSPACE_CONFIG=":4096:8",
)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.dont_write_bytecode = True

import numpy as np  # noqa: E402
import torch  # noqa: E402
from torch.utils.data import DataLoader  # noqa: E402

from colab.run_cascade_b0_r1 import event, verify_package  # noqa: E402
from d1_cascade_classifier.data import CropDataset  # noqa: E402
from d1_cascade_classifier.metrics import classification_metrics  # noqa: E402
from m1.checkpoint_store import require_safe_directory, write_json_atomic  # noqa: E402
from m1.checkpoint_store_r2 import EfficientCheckpointStore  # noqa: E402
from vgg16_54.contract import (  # noqa: E402
    EXPERIMENT,
    PROPOSED_CONFIG,
    RUN_NAME,
    normalize_state_path,
    sha256_file,
    validate_config,
    verify_owner_approval,
    verify_smoke_qa,
    verify_source_qa,
)
from vgg16_54.model import build_model  # noqa: E402


def binding(manifest_sha256: str) -> dict[str, Any]:
    return {
        "schema": "vgg16-54-r1-binding-v1",
        "experiment": EXPERIMENT,
        "bundle_manifest_sha256": manifest_sha256,
        "config": validate_config(dict(PROPOSED_CONFIG)),
        "sealed_test_accessed": False,
    }


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=False)
    torch.backends.cudnn.benchmark = False


def _load_arrays(root: Path) -> dict[str, dict[str, np.ndarray]]:
    arrays: dict[str, dict[str, np.ndarray]] = {}
    for split, filename, count in (
        ("train", "train.p", 12621),
        ("val", "valid.p", 624),
    ):
        path = root / "data" / filename
        with path.open("rb") as handle:
            value = pickle.load(handle)  # bundle bytes were verified before deserialization
        if not isinstance(value, dict) or set(value) < {"features", "labels"}:
            raise RuntimeError(f"VGG16 {split} arrays schema differs")
        features, labels = value["features"], value["labels"]
        if (
            not isinstance(features, np.ndarray)
            or features.dtype != np.uint8
            or features.shape != (count, 32, 32, 3)
            or not isinstance(labels, np.ndarray)
            or labels.dtype != np.uint8
            or labels.shape != (count,)
            or int(labels.min()) < 0
            or int(labels.max()) >= 54
        ):
            raise RuntimeError(f"VGG16 {split} arrays identity differs")
        arrays[split] = {"features": features, "labels": labels}
    if len(set(arrays["train"]["labels"].tolist())) != 54:
        raise RuntimeError("VGG16 train split must represent all 54 classes")
    return arrays


def _loader(
    arrays: dict[str, np.ndarray], *, shuffle: bool, epoch: int, config: dict[str, Any]
) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
    generator = torch.Generator().manual_seed(int(config["seed"]) + epoch)
    return DataLoader(
        CropDataset(arrays),
        batch_size=int(config["batch"]),
        shuffle=shuffle,
        generator=generator,
        num_workers=int(config["workers"]),
        pin_memory=True,
        persistent_workers=False,
        drop_last=False,
    )


def _evaluate(
    model: torch.nn.Module,
    arrays: dict[str, np.ndarray],
    criterion: torch.nn.Module,
    config: dict[str, Any],
) -> tuple[dict[str, Any], float]:
    model.eval()
    targets_out: list[np.ndarray] = []
    probabilities: list[np.ndarray] = []
    loss_sum = 0.0
    with torch.inference_mode():
        for inputs, targets in _loader(arrays, shuffle=False, epoch=0, config=config):
            inputs = inputs.cuda(non_blocking=True)
            targets_cuda = targets.cuda(non_blocking=True)
            with torch.autocast(device_type="cuda", dtype=torch.float16, enabled=config["amp"]):
                logits = model(inputs)
                loss = criterion(logits, targets_cuda)
            loss_sum += float(loss.item()) * len(targets)
            targets_out.append(targets.numpy())
            probabilities.append(torch.softmax(logits.float(), dim=1).cpu().numpy())
    labels = np.concatenate(targets_out)
    metrics = classification_metrics(labels, np.concatenate(probabilities))
    return metrics, loss_sum / len(labels)


def _save_epoch(
    run: Path,
    *,
    epoch: int,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    best: tuple[float, float],
    best_epoch: int,
    history: list[dict[str, Any]],
    run_binding: dict[str, Any],
    improved: bool,
) -> None:
    payload = {
        "epoch": epoch,
        "model": model.state_dict(),
        "optimizer": optimizer.state_dict(),
        "scaler": scaler.state_dict(),
        "best": best,
        "best_epoch": best_epoch,
        "history": history,
        "python_rng": random.getstate(),
        "numpy_rng": np.random.get_state(),
        "torch_rng": torch.get_rng_state(),
        "cuda_rng": torch.cuda.get_rng_state_all(),
        "binding": run_binding,
    }
    last = run / "weights/last.pt"
    temporary = last.with_name(f".{last.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("xb") as handle:
        torch.save(payload, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, last)
    best_path = run / "weights/best.pt"
    if improved:
        shutil.copyfile(last, best_path)
    if not best_path.is_file() or best_path.is_symlink():
        raise RuntimeError("VGG16 best checkpoint is missing or linked")
    with (run / "results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(history[0]))
        writer.writeheader()
        writer.writerows(history)
        handle.flush()
        os.fsync(handle.fileno())


def _restore(
    checkpoint: Path,
    *,
    model: torch.nn.Module,
    optimizer: torch.optim.Optimizer,
    scaler: torch.amp.GradScaler,
    run_binding: dict[str, Any],
) -> tuple[int, tuple[float, float], int, list[dict[str, Any]]]:
    saved = torch.load(checkpoint, map_location="cpu", weights_only=False)
    if saved.get("binding") != run_binding or type(saved.get("epoch")) is not int:
        raise RuntimeError("VGG16 recovery binding or epoch differs")
    model.load_state_dict(saved["model"], strict=True)
    optimizer.load_state_dict(saved["optimizer"])
    scaler.load_state_dict(saved["scaler"])
    random.setstate(saved["python_rng"])
    np.random.set_state(saved["numpy_rng"])
    torch.set_rng_state(saved["torch_rng"])
    torch.cuda.set_rng_state_all(saved["cuda_rng"])
    best_epoch = saved.get("best_epoch")
    if type(best_epoch) is not int or not 1 <= best_epoch <= int(saved["epoch"]):
        raise RuntimeError("VGG16 recovery best epoch differs")
    return (
        int(saved["epoch"]),
        tuple(saved["best"]),
        best_epoch,
        list(saved["history"]),
    )


def should_stop_early(epoch: int, best_epoch: int, config: dict[str, Any]) -> bool:
    """Stop only after the original 30-epoch baseline window and a stale patience window."""
    return (
        epoch >= int(config["early_stopping_min_epochs"])
        and epoch - best_epoch >= int(config["early_stopping_patience"])
    )


def validate_smoke_start(mode: str, stop_after: int | None, completed_epoch: int) -> None:
    """Fail closed unless each smoke phase begins at its exact governed boundary."""
    if stop_after is None:
        return
    expected = {"fresh": 0, "resume": 1}.get(mode)
    if expected is None or completed_epoch != expected:
        raise RuntimeError(
            "VGG16 smoke start differs: "
            f"mode={mode} requires completed_epoch={expected}, observed={completed_epoch}"
        )


def _package_result(
    state: Path,
    store: EfficientCheckpointStore,
    run_binding: dict[str, Any],
    *,
    completed_epoch: int,
    stopped_early: bool,
) -> None:
    latest = store.load_latest(run_binding)
    if latest["completed_epoch"] != completed_epoch:
        raise RuntimeError("VGG16 result cannot package an incomplete run")
    if stopped_early:
        if not (
            PROPOSED_CONFIG["early_stopping_min_epochs"] <= completed_epoch
            < PROPOSED_CONFIG["epochs"]
        ):
            raise RuntimeError("VGG16 early-stop terminal epoch differs")
    elif completed_epoch != PROPOSED_CONFIG["epochs"]:
        raise RuntimeError("VGG16 non-early terminal epoch differs")
    telemetry = store.verify_telemetry(run_binding)
    snapshot = store.snapshots / f"epoch-{latest['completed_epoch']:04d}"
    output = require_safe_directory(state / "results", create=True)
    archive = output / "result.tar.gz"
    manifest_path = output / "result_manifest.json"
    destination_exists = (
        archive.exists()
        or archive.is_symlink()
        or manifest_path.exists()
        or manifest_path.is_symlink()
    )
    if destination_exists:
        raise RuntimeError("VGG16 result destination already exists")
    members = {row["path"]: snapshot / row["path"] for row in latest["files"]}
    members.update(
        {
            "checkpoint_io.jsonl": store.telemetry_path,
            "train.log": state / "train.log",
            "DB_logger.db": state / "DB_logger.db",
            "colab_execution.json": state / "colab_execution.json",
        }
    )
    records: dict[str, Any] = {}
    temporary = archive.with_name(f".{archive.name}.{uuid.uuid4().hex}.partial")
    try:
        with temporary.open("xb") as raw, tarfile.open(fileobj=raw, mode="w:gz") as tar:
            for name, path in sorted(members.items()):
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    raise RuntimeError(f"unsafe VGG16 result member: {path}")
                records[name] = {"sha256": sha256_file(path), "bytes": info.st_size}
                member = tarfile.TarInfo(name)
                member.size = info.st_size
                with path.open("rb") as source:
                    tar.addfile(member, source)
        os.replace(temporary, archive)
    finally:
        temporary.unlink(missing_ok=True)
    write_json_atomic(
        manifest_path,
        {
            "experiment": EXPERIMENT,
            "completed_epoch": latest["completed_epoch"],
            "max_epochs": PROPOSED_CONFIG["epochs"],
            "stopped_early": stopped_early,
            "binding": run_binding,
            "archive_sha256": sha256_file(archive),
            "members": records,
            "checkpoint_events": len(telemetry),
            "sealed_test_accessed": False,
        },
    )


def train(
    args: argparse.Namespace,
    model_factory: Callable[[], torch.nn.Module] = build_model,
) -> None:
    if not torch.cuda.is_available():
        raise RuntimeError("VGG16-54 R1 requires CUDA for GPU execution")
    root = require_safe_directory(args.root)
    manifest = verify_package(root, args.bundle_manifest_sha256)
    state = normalize_state_path(args.state)
    require_safe_directory(state, create=True)
    verify_owner_approval(args.owner_approval, args.owner_approval_sha256)
    repo_root = Path(__file__).resolve().parents[2]
    verify_source_qa(args.source_qa, args.source_qa_sha256, repo_root)
    config = validate_config(dict(PROPOSED_CONFIG))
    run_binding = binding(args.bundle_manifest_sha256)
    if args.stop_after is None:
        if args.smoke_qa is None or args.smoke_qa_sha256 is None:
            raise RuntimeError("long VGG16 run requires independent smoke QA")
        verify_smoke_qa(args.smoke_qa, args.smoke_qa_sha256, args.bundle_manifest_sha256)
    elif (args.mode, args.stop_after) not in {("fresh", 1), ("resume", 2)}:
        raise RuntimeError("VGG16 smoke must be fresh epoch 1 then resume epoch 2")
    if manifest["counts"]["train"]["boxes"] != 12621 or manifest["counts"]["val"]["boxes"] != 624:
        raise RuntimeError("VGG16 bundle train/validation counts differ")

    set_seed(int(config["seed"]))
    arrays = _load_arrays(root)
    work_root = require_safe_directory(args.work_root, create=True)
    run = work_root / RUN_NAME
    store = EfficientCheckpointStore(state / "recovery")
    checkpoint: Path | None = None
    if args.mode == "resume":
        checkpoint = store.restore_latest(work_root, run_binding)
    elif run.exists() or (store.root / "latest.json").exists():
        raise RuntimeError("fresh VGG16 run refuses existing local or Drive state")
    (run / "weights").mkdir(parents=True, exist_ok=True)
    write_json_atomic(run / "run_contract.json", run_binding)
    (run / "args.yaml").write_text(json.dumps(config, sort_keys=True) + "\n", encoding="utf-8")

    model = model_factory().cuda()
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=float(config["learning_rate"]),
        weight_decay=float(config["weight_decay"]),
    )
    scaler = torch.amp.GradScaler("cuda", enabled=bool(config["amp"]))
    start, best, best_epoch, history = 0, (-1.0, float("-inf")), 0, []
    if checkpoint is not None:
        start, best, best_epoch, history = _restore(
            checkpoint,
            model=model,
            optimizer=optimizer,
            scaler=scaler,
            run_binding=run_binding,
        )
    validate_smoke_start(args.mode, args.stop_after, start)
    event(state, "vgg16_classifier", "ATTEMPT", mode=args.mode, completed_epoch=start)
    event(state, "vgg16_classifier", "RESUMED" if checkpoint else "FRESH", completed_epoch=start)
    criterion = torch.nn.CrossEntropyLoss()
    last_epoch = start
    try:
        for epoch in range(start + 1, int(config["epochs"]) + 1):
            model.train()
            total_loss, seen = 0.0, 0
            started = time.monotonic()
            train_loader = _loader(arrays["train"], shuffle=True, epoch=epoch, config=config)
            for inputs, targets in train_loader:
                inputs = inputs.cuda(non_blocking=True)
                targets = targets.cuda(non_blocking=True)
                optimizer.zero_grad(set_to_none=True)
                with torch.autocast(
                    device_type="cuda", dtype=torch.float16, enabled=bool(config["amp"])
                ):
                    loss = criterion(model(inputs), targets)
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
                total_loss += float(loss.item()) * len(targets)
                seen += len(targets)
            metrics, val_loss = _evaluate(model, arrays["val"], criterion, config)
            score = (float(metrics["macro_f1_supported_classes"]), -val_loss)
            improved = score > best
            if improved:
                best = score
                best_epoch = epoch
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": total_loss / seen,
                    "val_loss": val_loss,
                    "val_top1": float(metrics["top1_accuracy"]),
                    "val_macro_f1_supported": score[0],
                    "gpu_train_and_val_seconds": time.monotonic() - started,
                }
            )
            _save_epoch(
                run,
                epoch=epoch,
                model=model,
                optimizer=optimizer,
                scaler=scaler,
                best=best,
                best_epoch=best_epoch,
                history=history,
                run_binding=run_binding,
                improved=improved,
            )
            store.save(run, epoch=epoch, binding=run_binding)
            event(
                state,
                "vgg16_classifier",
                "CHECKPOINT",
                epoch=epoch,
                val_top1=metrics["top1_accuracy"],
                val_macro_f1_supported=score[0],
            )
            last_epoch = epoch
            if args.stop_after is not None and epoch >= args.stop_after:
                break
            if args.stop_after is None and should_stop_early(epoch, best_epoch, config):
                event(
                    state,
                    "vgg16_classifier",
                    "EARLY_STOPPED",
                    epoch=epoch,
                    best_epoch=best_epoch,
                )
                break
        stopped_early = last_epoch < int(config["epochs"]) and should_stop_early(
            last_epoch, best_epoch, config
        )
        if last_epoch == int(config["epochs"]) or stopped_early:
            event(
                state,
                "vgg16_classifier",
                "TRAINING_COMPLETE",
                epoch=last_epoch,
                max_epochs=config["epochs"],
                stopped_early=stopped_early,
            )
            _package_result(
                state,
                store,
                run_binding,
                completed_epoch=last_epoch,
                stopped_early=stopped_early,
            )
            event(state, "vgg16_classifier", "SUCCEEDED", epoch=last_epoch)
        else:
            event(state, "vgg16_classifier", "SMOKE_STOP", epoch=last_epoch)
    except BaseException as error:
        event(state, "vgg16_classifier", "FAILED", error=repr(error), epoch=last_epoch)
        raise


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    root.add_argument("--root", type=Path, required=True)
    root.add_argument("--state", type=Path, required=True)
    root.add_argument("--work-root", type=Path, default=Path("/content/vgg16_54_work"))
    root.add_argument("--bundle-manifest-sha256", required=True)
    root.add_argument("--owner-approval", type=Path, required=True)
    root.add_argument("--owner-approval-sha256", required=True)
    root.add_argument("--source-qa", type=Path, required=True)
    root.add_argument("--source-qa-sha256", required=True)
    root.add_argument("--mode", choices=("fresh", "resume"), required=True)
    root.add_argument("--stop-after", type=int, choices=(1, 2))
    root.add_argument("--smoke-qa", type=Path)
    root.add_argument("--smoke-qa-sha256")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        train(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
