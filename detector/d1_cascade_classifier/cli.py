"""CLI for the D1 54-class crop-classifier comparison baseline.

Only the governed train and validation arrays are reachable. This package has no test command,
test split or final-evaluation flag.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader

from . import contract
from .data import CropDataset
from .metrics import classification_metrics, latency_stats
from .model import build_model


def now() -> str:
    return datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y%m%dT%H%M%S%z")


def set_seed(seed: int) -> None:
    contract.validate_seed(seed)
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=False)


def resolve_device(requested: str) -> torch.device:
    if requested == "auto":
        if torch.cuda.is_available():
            requested = "cuda"
        elif torch.backends.mps.is_available():
            requested = "mps"
        else:
            requested = "cpu"
    if requested == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested but unavailable")
    if requested == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS requested but unavailable")
    return torch.device(requested)


def loader(
    arrays: dict[str, np.ndarray], batch_size: int, *, shuffle: bool, seed: int
) -> DataLoader[tuple[torch.Tensor, torch.Tensor]]:
    generator = torch.Generator().manual_seed(seed)
    return DataLoader(
        CropDataset(arrays),
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator,
        num_workers=0,
        drop_last=False,
    )


def predict(
    model: nn.Module,
    arrays: dict[str, np.ndarray],
    device: torch.device,
    batch_size: int,
    seed: int,
) -> tuple[np.ndarray, np.ndarray, float]:
    model.eval()
    probabilities: list[np.ndarray] = []
    targets: list[np.ndarray] = []
    total_loss = 0.0
    criterion = nn.CrossEntropyLoss(reduction="sum")
    with torch.inference_mode():
        for inputs, labels in loader(arrays, batch_size, shuffle=False, seed=seed):
            inputs, labels = inputs.to(device), labels.to(device)
            logits = model(inputs)
            total_loss += float(criterion(logits, labels).item())
            probabilities.append(torch.softmax(logits, dim=1).cpu().numpy())
            targets.append(labels.cpu().numpy())
    return (
        np.concatenate(targets),
        np.concatenate(probabilities),
        total_loss / len(arrays["labels"]),
    )


def cmd_check(args: argparse.Namespace) -> dict[str, Any]:
    bound, _ = contract.check_data_contract(Path(args.data_root), Path(args.manifest))
    return {
        "status": "PASS",
        "data": bound,
        "architectures": list(contract.ARCHITECTURES),
        "classes": contract.CLASSES,
        "seeds": list(contract.SEEDS),
        "horizontal_flip": False,
        "network": "disabled/no network API",
        "environment": contract.environment(),
    }


def cmd_train(args: argparse.Namespace) -> dict[str, Any]:
    architecture = contract.validate_architecture(args.architecture)
    seed = contract.validate_seed(args.seed)
    if args.epochs < 1 or args.batch < 1 or not np.isfinite(args.lr) or args.lr <= 0:
        raise RuntimeError("epochs, batch and learning rate must be positive")
    if not re.fullmatch(r"[A-Za-z0-9_.-]*", args.tag):
        raise RuntimeError("tag contains unsafe characters")
    set_seed(seed)
    device = resolve_device(args.device)
    data_contract, arrays = contract.check_data_contract(Path(args.data_root), Path(args.manifest))
    config = {
        "architecture": architecture,
        "seed": seed,
        "epochs": args.epochs,
        "batch": args.batch,
        "learning_rate": args.lr,
        "device": str(device),
        "workers": 0,
        "horizontal_flip": False,
        "weights": None,
        "model_config_sha256": contract.canonical_sha256(contract.model_config(architecture)),
    }
    name = f"D1CC_{architecture}_{seed}_{now()}{('_' + args.tag) if args.tag else ''}"
    run_dir = contract.prepare_run_directory(contract.RESULTS_DIR / name)
    weights_dir = run_dir / "weights"
    model_contract = contract.model_config(architecture)
    environment_contract = contract.environment()
    record: dict[str, Any] = {
        "experiment": "D1_CASCADE_CLASSIFIER",
        "run": name,
        "seed": seed,
        "model": model_contract,
        "config": config,
        "data": data_contract,
        "environment": environment_contract,
        "bindings": {
            "config_sha256": contract.canonical_sha256(config),
            "data_sha256": contract.canonical_sha256(data_contract),
            "environment_sha256": contract.canonical_sha256(environment_contract),
            "model_sha256": contract.canonical_sha256(model_contract),
        },
        "status": "STARTED",
        "artifacts": {},
    }
    contract.write_json(run_dir / "run_contract.json", record)
    with contract.offline_mode():
        model = build_model(architecture).to(device)
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr)
        criterion = nn.CrossEntropyLoss()
        best_accuracy = -1.0
        history = []
        for epoch in range(1, args.epochs + 1):
            model.train()
            loss_sum = 0.0
            seen = 0
            batches = loader(arrays["train"], args.batch, shuffle=True, seed=seed + epoch)
            for inputs, labels in batches:
                inputs, labels = inputs.to(device), labels.to(device)
                optimizer.zero_grad(set_to_none=True)
                loss = criterion(model(inputs), labels)
                loss.backward()
                optimizer.step()
                loss_sum += float(loss.item()) * len(labels)
                seen += len(labels)
            targets, probabilities, val_loss = predict(
                model, arrays["val"], device, args.batch, seed
            )
            val_accuracy = float(np.mean(probabilities.argmax(axis=1) == targets))
            history.append(
                {
                    "epoch": epoch,
                    "train_loss": loss_sum / seen,
                    "val_loss": val_loss,
                    "val_top1_accuracy": val_accuracy,
                }
            )
            torch.save(model.state_dict(), weights_dir / "last.pt")
            if val_accuracy > best_accuracy:
                best_accuracy = val_accuracy
                torch.save(model.state_dict(), weights_dir / "best.pt")
    contract.write_json(run_dir / "history.json", {"epochs": history})
    record["status"] = "TRAINED"
    record["artifacts"] = {
        path.name: {"path": str(path), "sha256": contract.sha256_file(path)}
        for path in (weights_dir / "best.pt", weights_dir / "last.pt")
    }
    record["artifacts"]["history.json"] = {
        "path": str(run_dir / "history.json"),
        "sha256": contract.sha256_file(run_dir / "history.json"),
    }
    contract.write_json(run_dir / "run_contract.json", record)
    return {"run": name, "run_dir": str(run_dir), "best_val_top1": best_accuracy}


def load_model(weights: str, device: torch.device) -> tuple[nn.Module, Path, dict[str, Any]]:
    weight_path, record = contract.load_run_weights(weights)
    model = build_model(record["model"]["architecture"])
    try:
        state = torch.load(weight_path, map_location="cpu", weights_only=True)
    except (OSError, RuntimeError, ValueError) as error:
        raise RuntimeError(f"invalid classifier checkpoint: {error}") from error
    model.load_state_dict(state, strict=True)
    return model.to(device), weight_path, record


def cmd_evaluate(args: argparse.Namespace) -> dict[str, Any]:
    # There is intentionally no split parameter: evaluation means governed validation only.
    device = resolve_device(args.device)
    with contract.offline_mode():
        model, weights, record = load_model(args.weights, device)
        _bound, arrays = contract.check_data_contract()
        targets, probabilities, loss = predict(
            model, arrays["val"], device, args.batch, record["seed"]
        )
    report = {
        "split": "val",
        "seed": record["seed"],
        "architecture": record["model"]["architecture"],
        "weights": {"path": str(weights), "sha256": contract.sha256_file(weights)},
        "validation_loss": loss,
        "metrics": classification_metrics(targets, probabilities),
        "limitations": {
            "selection_split": "validation only",
            "absent_validation_classes": "cannot select models or thresholds",
            "sealed_test_accessed": False,
        },
    }
    out = weights.parent.parent / "eval_val.json"
    contract.write_json(out, report)
    return {"report": str(out), **report["metrics"]}


def synchronize(device: torch.device) -> None:
    if device.type == "cuda":
        torch.cuda.synchronize()
    elif device.type == "mps":
        torch.mps.synchronize()


def cmd_latency(args: argparse.Namespace) -> dict[str, Any]:
    if args.batch != 1:
        raise RuntimeError("latency contract requires batch 1")
    device = resolve_device(args.device)
    with contract.offline_mode():
        model, weights, record = load_model(args.weights, device)
        _bound, arrays = contract.check_data_contract()
        dataset = CropDataset(arrays["val"])
        model.eval()
        timings: list[float] = []
        with torch.inference_mode():
            for index in range(contract.LATENCY_WARMUP + contract.LATENCY_ITERATIONS):
                inputs = dataset[index % len(dataset)][0].unsqueeze(0).to(device)
                synchronize(device)
                start = time.perf_counter()
                output = model(inputs)
                _ = torch.softmax(output, dim=1).argmax(dim=1)
                synchronize(device)
                if index >= contract.LATENCY_WARMUP:
                    timings.append((time.perf_counter() - start) * 1000.0)
    stats = latency_stats(timings)
    report = {
        **stats,
        "batch": 1,
        "warmup": contract.LATENCY_WARMUP,
        "iterations": contract.LATENCY_ITERATIONS,
        "device": str(device),
        "seed": record["seed"],
        "architecture": record["model"]["architecture"],
        "weights": {"path": str(weights), "sha256": contract.sha256_file(weights)},
        "environment": contract.environment(),
        "sealed_test_accessed": False,
    }
    out = weights.parent.parent / f"latency_{device.type}.json"
    contract.write_json(out, report)
    return {"report": str(out), **stats}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("--data-root", default=str(contract.DATA_ROOT))
    check.add_argument("--manifest", default=str(contract.MANIFEST_PATH))
    train = commands.add_parser("train")
    train.add_argument("--architecture", required=True, choices=contract.ARCHITECTURES)
    train.add_argument("--seed", required=True, type=int, choices=contract.SEEDS)
    train.add_argument("--epochs", type=int, default=100)
    train.add_argument("--batch", type=int, default=128)
    train.add_argument("--lr", type=float, default=1e-3)
    train.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    train.add_argument("--tag", default="")
    train.add_argument("--data-root", default=str(contract.DATA_ROOT))
    train.add_argument("--manifest", default=str(contract.MANIFEST_PATH))
    evaluate = commands.add_parser("evaluate")
    evaluate.add_argument("--weights", required=True)
    evaluate.add_argument("--batch", type=int, default=256)
    evaluate.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    latency = commands.add_parser("latency")
    latency.add_argument("--weights", required=True)
    latency.add_argument("--batch", type=int, default=1)
    latency.add_argument("--device", choices=("auto", "cpu", "mps", "cuda"), default="auto")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        result = {
            "check": cmd_check,
            "train": cmd_train,
            "evaluate": cmd_evaluate,
            "latency": cmd_latency,
        }[args.command](args)
    except (RuntimeError, ValueError, OSError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
