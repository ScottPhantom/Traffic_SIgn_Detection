"""M1 training/evaluation CLI for the Vietnamese traffic-sign detector (track D1).

Run from `detector/`:

    uv run python -m m1.cli check
    uv run python -m m1.cli train --seed 20261018 --model yolo11n.yaml --epochs 100
    uv run python -m m1.cli evaluate --weights <run>/weights/best.pt --split val
    uv run python -m m1.cli latency --weights <run>/weights/best.pt

Every run first checks the governed contract (D-05 record, M1 export manifest, exported stems).
Train/val use `data.yaml`, which has no test entry. `evaluate --split test` needs `--final-eval
--reason` and is logged in the sealed-test access log. Horizontal flip is forced to 0.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from m1 import contract
from m1.metrics import Frame, group_bootstrap, latency_stats, operating_point, select_threshold

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}


def run_name(model: str, seed: int, tag: str) -> str:
    seal = contract.check_contract()["split_stem_sha256"]["test"][:8]
    stem = Path(model).stem
    return f"D1_{stem}_wp33_{seal}_{seed}_{contract.now()}{('_' + tag) if tag else ''}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def cmd_check(_args: argparse.Namespace) -> dict[str, Any]:
    return {
        "contract": contract.check_contract(),
        "environment": contract.environment(),
        "gates": contract.GATES,
    }


def cmd_train(args: argparse.Namespace) -> dict[str, Any]:
    if args.seed not in contract.SEEDS:
        raise SystemExit(f"seed {args.seed} is not one of the D-05 seeds {contract.SEEDS}")
    bound = contract.check_contract()
    contract.disable_telemetry()
    from ultralytics import YOLO

    name = run_name(args.model, args.seed, args.tag)
    results_dir = Path(args.results_dir).resolve() if args.results_dir else contract.RESULTS_DIR
    out = results_dir / name
    if out.exists():
        raise SystemExit(f"run directory already exists: {out}")
    train_args = {
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
        "plots": args.plots,
        "project": str(results_dir),
        "name": name,
        "exist_ok": True,  # the run dir is new (checked above) and holds run_contract.json
        "pretrained": args.model.endswith(".pt"),
        **contract.FORBIDDEN_OVERRIDES,
    }
    write_json(
        out / "run_contract.json",
        {
            "experiment": "D1",
            "run": name,
            "model": args.model,
            "train_args": train_args,
            "contract": bound,
            "environment": contract.environment(),
            "d05_gates": contract.GATES,
            "status": "STARTED",
        },
    )
    model = YOLO(args.model)
    model.train(**train_args)
    record = json.loads((out / "run_contract.json").read_text(encoding="utf-8"))
    record["status"] = "TRAINED"
    write_json(out / "run_contract.json", record)
    return {"run": name, "dir": str(out)}


def load_frames(split: str, weights: str, imgsz: int, device: str) -> list[Frame]:
    from PIL import Image
    from ultralytics import YOLO

    images = sorted(
        p
        for p in (contract.EXPORT_DIR / "images" / split).iterdir()
        if p.suffix.lower() in IMAGE_SUFFIXES
    )
    groups = contract.group_of()
    model = YOLO(weights)
    frames = []
    results = model.predict(
        source=[str(p) for p in images],
        conf=0.001,
        iou=0.7,
        imgsz=imgsz,
        device=device,
        max_det=300,
        stream=True,
        verbose=False,
    )
    for path, result in zip(images, results, strict=True):
        with Image.open(path) as image:
            width, height = image.size
        rows = [
            line.split()
            for line in (contract.EXPORT_DIR / "labels" / split / f"{path.stem}.txt")
            .read_text()
            .splitlines()
            if line.strip()
        ]
        gt = np.array([[float(v) for v in r[1:]] for r in rows]).reshape(-1, 4)
        xyxy = (
            np.column_stack(
                [
                    (gt[:, 0] - gt[:, 2] / 2) * width,
                    (gt[:, 1] - gt[:, 3] / 2) * height,
                    (gt[:, 0] + gt[:, 2] / 2) * width,
                    (gt[:, 1] + gt[:, 3] / 2) * height,
                ]
            )
            if len(gt)
            else np.zeros((0, 4))
        )
        boxes = result.boxes
        frames.append(
            Frame(
                stem=path.stem,
                group_id=groups[path.stem],
                gt_boxes=xyxy,
                gt_classes=np.array([int(r[0]) for r in rows], dtype=int),
                pred_boxes=boxes.xyxy.cpu().numpy(),
                pred_classes=boxes.cls.cpu().numpy().astype(int),
                pred_scores=boxes.conf.cpu().numpy(),
            )
        )
    return frames


def gate_report(map50: float, map50_95: float, point: Any, ids: dict[str, int]) -> dict[str, Any]:
    gates = contract.GATES
    names = {v: k for k, v in ids.items()}
    critical = {ids[k] for k in contract.CRITICAL_KEYS}
    classes = {}
    for cls, recall in point.per_class_recall.items():
        support = point.per_class_support[cls]
        gated = support >= gates["min_support_for_class_gate"]
        threshold = (
            gates["critical_class_recall"] if cls in critical else gates["other_class_recall"]
        )
        classes[names[cls]] = {
            "recall": round(recall, 4),
            "support": support,
            "critical": cls in critical,
            "gated": gated,
            "passed": (recall >= threshold) if gated else None,
        }
    checks = {
        "map50": map50 >= gates["map50"],
        "map50_95": map50_95 >= gates["map50_95"],
        "agnostic_recall": point.agnostic_recall >= gates["agnostic_recall"],
        "fp_per_image": point.fp_per_image <= gates["fp_per_image"],
        "critical_classes": all(
            c["passed"] for c in classes.values() if c["critical"] and c["gated"]
        ),
    }
    return {"checks": checks, "all_passed": all(checks.values()), "classes": classes}


def cmd_evaluate(args: argparse.Namespace) -> dict[str, Any]:
    if args.split == "test":
        if not (args.final_eval and args.reason.strip()):
            raise SystemExit(
                "refused: the sealed test is evaluated only with --final-eval and --reason (D-05)"
            )
        contract.log_test_access("evaluate", f"{args.reason.strip()} | weights={args.weights}")
    bound = contract.check_contract(args.split)
    contract.disable_telemetry()
    from ultralytics import YOLO

    validation = YOLO(args.weights).val(
        data=bound["data_yaml"],
        split=args.split,
        imgsz=args.imgsz,
        device=args.device,
        conf=0.001,
        iou=0.7,
        plots=False,
        verbose=False,
        project=str(Path(args.weights).resolve().parents[1]),
        name=f"ultralytics_{args.split}",
        exist_ok=True,
    )
    frames = load_frames(args.split, args.weights, args.imgsz, args.device)
    if args.split == "val":
        point = select_threshold(frames, contract.GATES["agnostic_recall"])
    else:
        if args.conf is None:
            raise SystemExit("--conf (locked on val) is required for the test split")
        point = operating_point(frames, args.conf)
    ids = contract.class_ids()
    names = {v: k for k, v in ids.items()}
    report = {
        "split": args.split,
        "weights": args.weights,
        "imgsz": args.imgsz,
        "map50": float(validation.box.map50),
        "map50_95": float(validation.box.map),
        "per_class_ap50": {
            names[int(cls)]: float(validation.box.ap50[i])
            for i, cls in enumerate(validation.box.ap_class_index.tolist())
        },
        "operating_point": {
            "conf": point.conf,
            "agnostic_recall": point.agnostic_recall,
            "fp_per_image": point.fp_per_image,
        },
        "ci95_group_bootstrap": group_bootstrap(frames, point.conf) if args.bootstrap else None,
        "gates": gate_report(float(validation.box.map50), float(validation.box.map), point, ids),
        "note": "val is indicative; D-05 gates are judged on the sealed test (3-seed mean)",
    }
    out = Path(args.weights).resolve().parents[1] / f"eval_{args.split}.json"
    write_json(out, report)
    return {
        "report": str(out),
        "map50": report["map50"],
        "operating_point": report["operating_point"],
        "all_gates_passed": report["gates"]["all_passed"],
    }


def cmd_latency(args: argparse.Namespace) -> dict[str, Any]:
    contract.check_contract()
    contract.disable_telemetry()
    import torch
    from ultralytics import YOLO

    images = sorted((contract.EXPORT_DIR / "images" / "val").glob("*.jpg"))
    model = YOLO(args.weights)
    timings = []
    for index in range(contract.LATENCY_WARMUP + contract.LATENCY_ITERATIONS):
        path = str(images[index % len(images)])
        start = time.perf_counter()
        model.predict(path, imgsz=args.imgsz, conf=args.conf, device=args.device, verbose=False)
        if args.device == "mps":
            torch.mps.synchronize()
        if index >= contract.LATENCY_WARMUP:
            timings.append((time.perf_counter() - start) * 1000)
    stats = latency_stats(timings)
    stats.update(
        device=args.device,
        imgsz=args.imgsz,
        batch=1,
        warmup=contract.LATENCY_WARMUP,
        passed=stats["p95_ms"] <= contract.GATES["latency_p95_ms"],
    )
    out = Path(args.weights).resolve().parents[1] / f"latency_{args.device}.json"
    write_json(out, {**stats, "environment": contract.environment()})
    return {"report": str(out), **stats}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    commands = root.add_subparsers(dest="command", required=True)
    commands.add_parser("check")
    train = commands.add_parser("train")
    train.add_argument("--seed", type=int, required=True)
    train.add_argument(
        "--model", default="yolo11n.yaml", help="cfg (from scratch) or local .pt weights"
    )
    train.add_argument("--epochs", type=int, default=100)
    train.add_argument("--imgsz", type=int, default=1280)
    train.add_argument("--batch", type=int, default=8)
    train.add_argument("--device", default="mps")
    train.add_argument("--workers", type=int, default=4)
    train.add_argument("--fraction", type=float, default=1.0)
    train.add_argument("--patience", type=int, default=30)
    train.add_argument("--plots", action="store_true")
    train.add_argument("--tag", default="")
    train.add_argument("--results-dir", default="", help="override for smoke runs")
    for name in ("evaluate", "latency"):
        command = commands.add_parser(name)
        command.add_argument("--weights", required=True)
        command.add_argument("--imgsz", type=int, default=1280)
        command.add_argument("--device", default="mps")
    commands.choices["evaluate"].add_argument("--split", choices=("val", "test"), default="val")
    commands.choices["evaluate"].add_argument("--conf", type=float)
    commands.choices["evaluate"].add_argument("--bootstrap", action="store_true")
    commands.choices["evaluate"].add_argument("--final-eval", action="store_true")
    commands.choices["evaluate"].add_argument("--reason", default="")
    commands.choices["latency"].add_argument("--conf", type=float, default=0.25)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    handler = {
        "check": cmd_check,
        "train": cmd_train,
        "evaluate": cmd_evaluate,
        "latency": cmd_latency,
    }[args.command]
    try:
        result = handler(args)
    except RuntimeError as error:
        print(f"contract check failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
