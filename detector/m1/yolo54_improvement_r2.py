"""YOLO54 improvement R2: single-change ablations on top of the QA-passed resumable trainer.

Contract: `docs/review/d1_yolo54_improvement_r2_contract.md`. Append-only successor of
`m1.yolo54_improvement_r1` (QA PASS, 0 Critical / 0 High / 2 Medium / 6 Low); R1 is unchanged.
R2 closes the R1 findings: every runtime knob that changes what is trained (`--fraction`,
`--workers`) must equal the pilot, A3 is restated as a non-inferiority schedule test, A4 pins the
pilot's `warmup_bias_lr`, `plan` is built from the real `resumable_train.train_arguments`, and the
success criteria are labelled as screening criteria at conf 0.20.

Each ablation changes exactly one category of Ultralytics training settings relative to the
registered pilot (YOLO11s, 54 classes, 1280 px, batch 4, seed 20261018, workers 4, fraction 1.0,
`fliplr=0`). Everything else — data export, split hashes, class map, checkpoint mirroring, resume
and finalisation — is the unchanged `m1.resumable_train` path. The overrides and the package/key
enter the checkpoint recovery binding, so a checkpoint resumes only under the same R2 ablation.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from m1 import contract, resumable_train

PACKAGE = "D1-YOLO54-IMPROVEMENT-R2"
# The Owner-named run root; R1 never trained, and the package in the binding keeps R1/R2 apart.
DRIVE_RUN_ROOT = "M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1"
BASELINE_RUN = "D1_yolo11s_wp33_afa03d4b_20261018_20261021T111233_pilot_100e_seed_20261018_r2"
PILOT = {
    "imgsz": 1280,
    "batch": 4,
    "epochs": 100,
    "seed": 20261018,
    "patience": 0,
    "workers": 4,
    "fraction": 1.0,
}
# Pilot knobs that must equal the pilot at `train` time (args.yaml of the baseline run).
PINNED_RUNTIME = ("imgsz", "batch", "seed", "workers", "fraction")
SCREENING_CONF = 0.20

# Ultralytics keys an ablation may set, grouped by the single category each ablation may touch.
CATEGORIES: dict[str, frozenset[str]] = {
    "schedule": frozenset({"epochs", "cos_lr", "lrf"}),
    "optimizer": frozenset(
        {"optimizer", "lr0", "momentum", "weight_decay", "warmup_epochs", "warmup_bias_lr"}
    ),
    "multi_scale": frozenset({"multi_scale"}),
    "photometric": frozenset({"hsv_h", "hsv_s", "hsv_v"}),
    "geometric": frozenset({"scale", "translate", "degrees"}),
}
# Never settable by an ablation: data/split/class identity, test access, semantic flips and the
# runtime knobs pinned above.
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
        "workers",
        "device",
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
            "Pilot val mAP50-95 peaks at epoch 20 (0.589) and `best.pt` is already that epoch, "
            "so late overfit does not affect the evaluated model. The plausible mechanism is "
            "the learning rate near the peak: the pilot's linear schedule is still at ~0.8 x lr0 "
            "at epoch 20, while a 40-epoch cosine schedule has decayed to ~0.5 x lr0 there. The "
            "test is whether the same quality is reachable at ~40 % of the GPU cost.",
            "Screening, non-inferiority: R3 mAP50-95 not lower than the pilot (0.626) by more "
            "than 0.01, FP/image not higher than the pilot (0.399) by more than 0.02, and "
            "recall >= 0.85, at conf 0.20.",
            1.6,
            ("A pass is a cost result (same quality, fewer epochs), not an accuracy gain.",),
        ),
        Ablation(
            "A4_optimizer_sgd",
            "optimizer",
            {"optimizer": "SGD", "lr0": 0.01, "momentum": 0.937, "warmup_bias_lr": 0.0},
            "The pilot's `optimizer=auto` resolved to AdamW with lr0 0.000172 and beta1 0.9 "
            "(args.yaml); an explicit SGD schedule (lr0 0.01, momentum 0.937) is the standard "
            "detection recipe and may generalise better on 1,912 real frames.",
            "Screening: R3 FP/image lower than the pilot by >= 0.05 with recall >= 0.85 and "
            "mAP50 not lower by > 0.01, at conf 0.20.",
            3.8,
            (
                "`warmup_bias_lr` is pinned at the pilot's effective 0.0; explicit SGD would "
                "otherwise use 0.1. The momentum term changes from AdamW beta1 0.9 to SGD "
                "momentum 0.937 as part of the optimizer change.",
            ),
        ),
        Ablation(
            "A5_multi_scale",
            "multi_scale",
            {"multi_scale": 0.25},
            "37 % of boxes are < 0.1 % of the image and R3 AP-small is 0.289; multi-scale "
            "training targets small signs. Small size explains a minority of the class-7 misses "
            "(19 of 45 are 11–17 px) and most class-41 misses (small, distant signs).",
            "Screening: R3 AP-small up by >= 0.03 and recall of classes 7 and 41 each up by "
            ">= 0.05, at conf 0.20.",
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
            "On the earlier R10 labels, 17 of 36 class-7 misses were dark/backlit (frames "
            "1777–1798); that breakdown has not been recomputed on R3. Stronger brightness "
            "augmentation (0.4 -> 0.6) targets that failure without flips or new pixels.",
            "Screening: R3 class-7 recall up by >= 0.05 and FP/image not up by > 0.03, at "
            "conf 0.20.",
            3.8,
            ("The dark/backlit basis is R10; the evaluator successor recounts it on R3.",),
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
    """The only checkpoint directory an ablation may use: its own subfolder of the run root."""
    return drive_root / DRIVE_RUN_ROOT / ablation.key


def tag_for(ablation: Ablation) -> str:
    return f"yolo54_improvement_{ablation.key}_r2"


def _apply(base: dict[str, Any], ablation: Ablation) -> dict[str, Any]:
    merged = {**base, **ablation.overrides}
    merged.update(contract.FORBIDDEN_OVERRIDES)  # fliplr=0 always wins
    return merged


def _binding_ablation(ablation: Ablation) -> dict[str, Any]:
    return {"package": PACKAGE, "key": ablation.key, **ablation.overrides}


def plan(key: str, *, drive_root: Path = Path("/content/drive/MyDrive")) -> dict[str, Any]:
    """Settings from the real `train_arguments`; placeholders mark the values bound at run time."""
    ablation = get(key)
    args = argparse.Namespace(
        **{name: PILOT[name] for name in PINNED_RUNTIME},
        epochs=ablation.overrides.get("epochs", PILOT["epochs"]),
        patience=PILOT["patience"],
        device="0",
    )
    base = resumable_train.train_arguments(
        bound={"data_yaml": "<bound at train time: verified export data.yaml>"},
        args=args,
        results_dir=contract.RESULTS_DIR,
        name="<bound at train time: governed run name>",
    )
    return {
        "package": PACKAGE,
        "ablation": ablation.key,
        "category": ablation.category,
        "changed": dict(sorted(ablation.overrides.items())),
        "train_args": dict(sorted(_apply(base, ablation).items())),
        "runtime_placeholders": ["data", "name", "device"],
        "checkpoint_dir": str(checkpoint_dir_for(drive_root, ablation)),
        "tag": tag_for(ablation),
        "baseline_run": BASELINE_RUN,
        "hypothesis": ablation.hypothesis,
        "success": ablation.success,
        "success_kind": "screening",
        "screening_conf": SCREENING_CONF,
        "l4_hours_estimate": ablation.l4_hours,
        "notes": list(ablation.notes),
        "sealed_test_accessed": False,
        "training_started": False,
    }


_ACTIVE: list[str] = []


def execute(args: argparse.Namespace, **kwargs: Any) -> dict[str, Any]:
    """Run `resumable_train.execute` with one ablation's overrides bound into the checkpoint."""
    if _ACTIVE:
        raise RuntimeError(f"another improvement run is active in this process: {_ACTIVE[0]}")
    ablation = get(args.ablation)
    expected = checkpoint_dir_for(args.drive_root, ablation).expanduser().absolute()
    if args.checkpoint_dir.expanduser().absolute() != expected:
        raise RuntimeError(f"checkpoint dir must be the ablation's own folder: {expected}")
    for name in PINNED_RUNTIME:
        value = getattr(args, name)
        if isinstance(value, bool) or value != PILOT[name]:
            raise RuntimeError(f"--{name} must stay at the pilot value {PILOT[name]}")
    args.epochs = ablation.overrides.get("epochs", PILOT["epochs"])
    args.patience = PILOT["patience"]
    args.tag = tag_for(ablation)
    original_train, original_binding = (
        resumable_train.train_arguments,
        resumable_train.recovery_binding,
    )

    def train_arguments(**inner: Any) -> dict[str, Any]:
        return _apply(original_train(**inner), ablation)

    def recovery_binding(**inner: Any) -> dict[str, Any]:
        return _apply(original_binding(**inner), ablation) | {
            "ablation": _binding_ablation(ablation)
        }

    _ACTIVE.append(ablation.key)
    resumable_train.train_arguments = train_arguments
    resumable_train.recovery_binding = recovery_binding
    try:
        outcome = resumable_train.execute(args, **kwargs)
    finally:
        resumable_train.train_arguments = original_train
        resumable_train.recovery_binding = original_binding
        _ACTIVE.clear()
    return {**outcome, "package": PACKAGE, "ablation": ablation.key}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    sub = root.add_subparsers(dest="command", required=True)
    show = sub.add_parser("plan", help="print the settings; no model, no data")
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
    train.add_argument("--workers", type=int, default=PILOT["workers"])
    train.add_argument("--fraction", type=float, default=PILOT["fraction"])
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
