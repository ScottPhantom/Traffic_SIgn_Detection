"""YOLO54 improvement R1: single-change ablations on top of the QA-passed resumable trainer.

Contract: `docs/review/d1_yolo54_improvement_r1_contract.md`. Each ablation changes exactly one
category of Ultralytics training settings relative to the registered pilot (YOLO11s, 54 classes,
1280 px, batch 4, seed 20261018, `fliplr=0`), so an effect can be attributed. Everything else —
data export, split hashes, class map, checkpoint mirroring, resume and finalisation — is the
unchanged `m1.resumable_train` path.

The overrides enter both the run contract's `train_args` and the checkpoint recovery binding, so a
checkpoint can only be resumed under the same ablation. `plan` prints the exact arguments without
importing Ultralytics or touching data. No ablation may read validation pixels for training, use
the sealed test, change classes or flip images horizontally.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from m1 import contract, resumable_train

PACKAGE = "D1-YOLO54-IMPROVEMENT-R1"
DRIVE_RUN_ROOT = "M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1"
BASELINE_RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
PILOT = {"imgsz": 1280, "batch": 4, "epochs": 100, "seed": 20261018, "patience": 0}

# Ultralytics keys an ablation may set, grouped by the single category each ablation may touch.
CATEGORIES: dict[str, frozenset[str]] = {
    "schedule": frozenset({"epochs", "cos_lr", "lrf"}),
    "optimizer": frozenset({"optimizer", "lr0", "momentum", "weight_decay", "warmup_epochs"}),
    "multi_scale": frozenset({"multi_scale"}),
    "photometric": frozenset({"hsv_h", "hsv_s", "hsv_v"}),
    "geometric": frozenset({"scale", "translate", "degrees"}),
}
# Never settable by an ablation: data/split/class identity, test access and semantic flips.
FORBIDDEN_KEYS = frozenset(
    {
        "data",
        "split",
        "val",
        "classes",
        "single_cls",
        "fliplr",
        "flipud",
        "imgsz",
        "batch",
        "seed",
        "resume",
        "project",
        "name",
        "pretrained",
        "fraction",
    }
)


@dataclass(frozen=True)
class Ablation:
    key: str
    category: str
    overrides: dict[str, Any]
    hypothesis: str
    success: str
    l4_hours: float
    notes: tuple[str, ...] = field(default_factory=tuple)


ABLATIONS: dict[str, Ablation] = {
    a.key: a
    for a in (
        Ablation(
            "A3_schedule_40e_cos",
            "schedule",
            {"epochs": 40, "cos_lr": True},
            "Pilot val mAP50-95 peaks at epoch 20 and then declines; a shorter cosine schedule "
            "avoids the late overfit at ~40 % of the GPU cost.",
            "R3 mAP50-95 >= pilot (0.626) and FP/image <= pilot (0.399) at recall >= 0.85.",
            1.6,
        ),
        Ablation(
            "A4_optimizer_sgd",
            "optimizer",
            {"optimizer": "SGD", "lr0": 0.01, "momentum": 0.937},
            "The pilot's `optimizer=auto` resolved to AdamW with lr0 0.000172 (args.yaml); an "
            "explicit SGD schedule (lr0 0.01) is the standard detection recipe and may "
            "generalise better on 1,912 real frames.",
            "R3 FP/image lower than the pilot by >= 0.05 with recall >= 0.85 and mAP50 not "
            "lower by > 0.01.",
            3.8,
        ),
        Ablation(
            "A5_multi_scale",
            "multi_scale",
            {"multi_scale": 0.25},
            "37 % of boxes are < 0.1 % of the image and AP-small is 0.289; multi-scale training "
            "should help the 11–35 px signs that dominate the class-7/41 misses.",
            "R3 AP-small up by >= 0.03 and recall of classes 7 and 41 each up by >= 0.05.",
            4.5,
            (
                "Ultralytics 8.4 `multi_scale` is a float range: 0.25 trains at ~960–1600 px "
                "(True would mean 1.0, i.e. up to 2560 px). Must pass a 1-epoch L4 smoke first.",
            ),
        ),
        Ablation(
            "A6_photometric_value",
            "photometric",
            {"hsv_v": 0.6},
            "17 of the 36 R10 class-7 misses are dark/backlit (1777–1798); stronger brightness "
            "augmentation (0.4 -> 0.6) targets that failure without flips or new pixels.",
            "R3 class-7 recall up by >= 0.05 and FP/image not up by > 0.03.",
            3.8,
        ),
    )
}


def validate(ablation: Ablation) -> None:
    """Refuse anything but one whitelisted category of overrides."""
    if ablation.category not in CATEGORIES:
        raise ValueError(f"unknown ablation category: {ablation.category}")
    if not ablation.overrides:
        raise ValueError("an ablation must change at least one setting")
    keys = set(ablation.overrides)
    forbidden = keys & FORBIDDEN_KEYS
    if forbidden:
        raise ValueError(f"ablation sets forbidden keys: {sorted(forbidden)}")
    outside = keys - CATEGORIES[ablation.category]
    if outside:
        raise ValueError(
            f"ablation {ablation.key} mixes categories: {sorted(outside)} are not "
            f"{ablation.category} keys"
        )
    scale = ablation.overrides.get("multi_scale", 0.0)
    if isinstance(scale, bool) or not isinstance(scale, float) or not 0.0 <= scale <= 0.5:
        raise ValueError("multi_scale must be a float range in [0, 0.5] (Ultralytics 8.4)")
    if ablation.overrides.get("optimizer", "SGD") not in {"SGD", "AdamW", "Adam"}:
        raise ValueError("optimizer must be SGD, AdamW or Adam")
    epochs = ablation.overrides.get("epochs", PILOT["epochs"])
    if not isinstance(epochs, int) or not 1 <= epochs <= PILOT["epochs"]:
        raise ValueError("epochs must be an integer between 1 and the pilot's 100")


def get(key: str) -> Ablation:
    if key not in ABLATIONS:
        raise ValueError(f"unknown ablation {key!r}; choose one of {sorted(ABLATIONS)}")
    ablation = ABLATIONS[key]
    validate(ablation)
    return ablation


def checkpoint_dir_for(drive_root: Path, ablation: Ablation) -> Path:
    """The only checkpoint directory an ablation may use: a new subfolder of the R1 run root."""
    return drive_root / DRIVE_RUN_ROOT / ablation.key


def _apply(base: dict[str, Any], ablation: Ablation) -> dict[str, Any]:
    merged = {**base, **ablation.overrides}
    merged.update(contract.FORBIDDEN_OVERRIDES)  # fliplr=0 always wins
    return merged


def plan(key: str, *, drive_root: Path = Path("/content/drive/MyDrive")) -> dict[str, Any]:
    """Exact settings an ablation would train with; imports no model and reads no data."""
    ablation = get(key)
    base = {
        "epochs": PILOT["epochs"],
        "imgsz": PILOT["imgsz"],
        "batch": PILOT["batch"],
        "seed": PILOT["seed"],
        "patience": PILOT["patience"],
        "deterministic": True,
        "pretrained": True,
        **contract.FORBIDDEN_OVERRIDES,
    }
    return {
        "package": PACKAGE,
        "ablation": ablation.key,
        "category": ablation.category,
        "changed": dict(sorted(ablation.overrides.items())),
        "train_args": dict(sorted(_apply(base, ablation).items())),
        "checkpoint_dir": str(checkpoint_dir_for(drive_root, ablation)),
        "tag": f"yolo54_improvement_{ablation.key}_r1",
        "baseline_run": BASELINE_RUN,
        "hypothesis": ablation.hypothesis,
        "success": ablation.success,
        "l4_hours_estimate": ablation.l4_hours,
        "notes": list(ablation.notes),
        "sealed_test_accessed": False,
        "training_started": False,
    }


def execute(args: argparse.Namespace, **kwargs: Any) -> dict[str, Any]:
    """Run `resumable_train.execute` with one ablation's overrides bound into the checkpoint."""
    ablation = get(args.ablation)
    expected = checkpoint_dir_for(args.drive_root, ablation).expanduser().absolute()
    if args.checkpoint_dir.expanduser().absolute() != expected:
        raise RuntimeError(f"checkpoint dir must be the ablation's own folder: {expected}")
    for name, value in (("imgsz", PILOT["imgsz"]), ("batch", PILOT["batch"])):
        if getattr(args, name) != value:
            raise RuntimeError(f"--{name} must stay at the pilot value {value}")
    if args.seed != PILOT["seed"]:
        raise RuntimeError("improvement R1 trains seed 20261018 only")
    args.epochs = ablation.overrides.get("epochs", PILOT["epochs"])
    args.patience = PILOT["patience"]
    args.tag = f"yolo54_improvement_{ablation.key}_r1"
    original_train, original_binding = (
        resumable_train.train_arguments,
        resumable_train.recovery_binding,
    )

    def train_arguments(**inner: Any) -> dict[str, Any]:
        return _apply(original_train(**inner), ablation)

    def recovery_binding(**inner: Any) -> dict[str, Any]:
        binding = original_binding(**inner)
        binding["ablation"] = {"package": PACKAGE, "key": ablation.key, **ablation.overrides}
        return _apply(binding, ablation) | {"ablation": binding["ablation"]}

    resumable_train.train_arguments = train_arguments
    resumable_train.recovery_binding = recovery_binding
    try:
        outcome = resumable_train.execute(args, **kwargs)
    finally:
        resumable_train.train_arguments = original_train
        resumable_train.recovery_binding = original_binding
    return {**outcome, "package": PACKAGE, "ablation": ablation.key}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    show = sub.add_parser("plan", help="print the exact settings; no model, no data")
    show.add_argument("ablation", choices=sorted(ABLATIONS))
    sub.add_parser("list", help="list the ablations")
    train = sub.add_parser("train", help="train one ablation (Owner-authorised runs only)")
    train.add_argument("ablation", choices=sorted(ABLATIONS))
    train.add_argument("--drive-root", type=Path, required=True)
    train.add_argument("--model", type=Path, required=True)
    train.add_argument("--checkpoint-dir", type=Path, required=True)
    train.add_argument("--results-dir", type=Path, default=contract.RESULTS_DIR)
    train.add_argument("--resume", action="store_true")
    train.add_argument("--stop-after-epoch", type=int)
    train.add_argument("--seed", type=int, default=PILOT["seed"])
    train.add_argument("--imgsz", type=int, default=PILOT["imgsz"])
    train.add_argument("--batch", type=int, default=PILOT["batch"])
    train.add_argument("--device", default="0")
    train.add_argument("--workers", type=int, default=4)
    train.add_argument("--fraction", type=float, default=1.0)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "list":
            result: Any = {key: plan(key)["changed"] for key in sorted(ABLATIONS)}
        elif args.command == "plan":
            result = plan(args.ablation)
        else:
            args.epochs, args.patience, args.tag = PILOT["epochs"], PILOT["patience"], ""
            result = execute(args)
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
