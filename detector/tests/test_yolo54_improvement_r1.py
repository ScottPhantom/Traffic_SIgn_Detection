from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from m1 import contract, resumable_train
from m1 import yolo54_improvement_r1 as imp

DETECTOR = Path(__file__).parents[1]


def _args(tmp_path: Path, key: str, **overrides) -> argparse.Namespace:
    ablation = imp.get(key)
    values = {
        "ablation": key,
        "drive_root": tmp_path,
        "model": tmp_path / "yolo11s.pt",
        "checkpoint_dir": imp.checkpoint_dir_for(tmp_path, ablation),
        "results_dir": contract.RESULTS_DIR,
        "resume": False,
        "stop_after_epoch": None,
        "seed": 20261018,
        "imgsz": 1280,
        "batch": 4,
        "device": "0",
        "workers": 4,
        "fraction": 1.0,
        "epochs": 100,
        "patience": 0,
        "tag": "",
    }
    values.update(overrides)
    return argparse.Namespace(**values)


@pytest.mark.parametrize("key", sorted(imp.ABLATIONS))
def test_every_registered_ablation_is_a_single_whitelisted_category(key) -> None:
    ablation = imp.get(key)
    assert set(ablation.overrides) <= imp.CATEGORIES[ablation.category]
    assert not set(ablation.overrides) & imp.FORBIDDEN_KEYS
    assert ablation.hypothesis and ablation.success and ablation.l4_hours > 0


@pytest.mark.parametrize(
    ("overrides", "category", "message"),
    [
        ({"fliplr": 0.5}, "geometric", "forbidden"),
        ({"data": "other.yaml"}, "schedule", "forbidden"),
        ({"imgsz": 1536}, "multi_scale", "forbidden"),
        ({"hsv_v": 0.6, "scale": 0.7}, "photometric", "mixes categories"),
        ({"epochs": 40, "lr0": 0.02}, "schedule", "mixes categories"),
        ({}, "schedule", "at least one"),
        ({"epochs": 150}, "schedule", "between 1"),
        ({"hsv_v": 0.6}, "colour", "unknown ablation category"),
        ({"multi_scale": True}, "multi_scale", "float range"),
        ({"multi_scale": 1.0}, "multi_scale", "float range"),
        ({"optimizer": "auto"}, "optimizer", "SGD, AdamW or Adam"),
    ],
)
def test_validation_refuses_unsafe_or_mixed_changes(overrides, category, message) -> None:
    bad = replace(imp.ABLATIONS["A6_photometric_value"], overrides=overrides, category=category)
    with pytest.raises(ValueError, match=message):
        imp.validate(bad)


def test_plan_keeps_flip_off_and_changes_only_the_named_keys(tmp_path) -> None:
    result = imp.plan("A6_photometric_value", drive_root=tmp_path)
    assert result["changed"] == {"hsv_v": 0.6}
    args = result["train_args"]
    assert args["fliplr"] == 0.0 and args["imgsz"] == 1280 and args["batch"] == 4
    assert args["seed"] == 20261018 and args["epochs"] == 100
    assert result["checkpoint_dir"].endswith(
        "M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1/A6_photometric_value"
    )
    assert result["training_started"] is False and result["sealed_test_accessed"] is False
    assert imp.plan("A3_schedule_40e_cos")["train_args"]["epochs"] == 40


def test_plan_command_imports_no_model_code() -> None:
    code = (
        "import sys, json; from m1 import yolo54_improvement_r1 as imp; "
        "imp.plan('A5_multi_scale'); print(json.dumps('ultralytics' in sys.modules))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=DETECTOR, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert json.loads(out) is False


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"checkpoint_dir": Path("/tmp/baseline_run")}, "ablation's own folder"),
        ({"imgsz": 1536}, "pilot value 1280"),
        ({"batch": 8}, "pilot value 4"),
        ({"seed": 20261019}, "seed 20261018 only"),
    ],
)
def test_execute_refuses_before_training(tmp_path, monkeypatch, change, message) -> None:
    monkeypatch.setattr(
        resumable_train, "execute", lambda *a, **k: pytest.fail("training must not start")
    )
    with pytest.raises(RuntimeError, match=message):
        imp.execute(_args(tmp_path, "A6_photometric_value", **change))


def test_execute_binds_overrides_into_train_args_and_checkpoint_then_restores(
    tmp_path, monkeypatch
) -> None:
    seen = {}
    original = (resumable_train.train_arguments, resumable_train.recovery_binding)

    def fake_execute(args, **_kwargs):
        bound = {
            "data_yaml": "data.yaml",
            "export_manifest_sha256": "e",
            "class_map_sha256": "c",
            "split_stem_sha256": {"test": "t"},
        }
        env = {"git_commit": "g", "detector_lock_sha256": "d"}
        seen["train"] = resumable_train.train_arguments(
            bound=bound, args=args, results_dir=tmp_path, name="run"
        )
        seen["binding"] = resumable_train.recovery_binding(
            bound=bound, model={"sha256": "m"}, environment=env, args=args
        )
        seen["args"] = args
        return {"status": "COMPLETED", "completed_epoch": args.epochs}

    monkeypatch.setattr(resumable_train, "execute", fake_execute)
    outcome = imp.execute(_args(tmp_path, "A3_schedule_40e_cos"))
    assert outcome["ablation"] == "A3_schedule_40e_cos" and outcome["completed_epoch"] == 40
    assert seen["train"]["epochs"] == 40 and seen["train"]["cos_lr"] is True
    assert seen["train"]["fliplr"] == 0.0
    assert seen["binding"]["cos_lr"] is True and seen["binding"]["epochs"] == 40
    assert seen["binding"]["ablation"]["key"] == "A3_schedule_40e_cos"
    assert seen["args"].tag == "yolo54_improvement_A3_schedule_40e_cos_r1"
    assert (resumable_train.train_arguments, resumable_train.recovery_binding) == original


def test_patches_are_restored_when_training_fails(tmp_path, monkeypatch) -> None:
    original = (resumable_train.train_arguments, resumable_train.recovery_binding)

    def boom(*_a, **_k):
        raise RuntimeError("colab disconnected")

    monkeypatch.setattr(resumable_train, "execute", boom)
    with pytest.raises(RuntimeError, match="colab disconnected"):
        imp.execute(_args(tmp_path, "A5_multi_scale"))
    assert (resumable_train.train_arguments, resumable_train.recovery_binding) == original


def test_different_ablations_have_different_checkpoint_bindings(tmp_path, monkeypatch) -> None:
    bindings = {}

    def capture(args, **_kwargs):
        bound = {
            "export_manifest_sha256": "e",
            "class_map_sha256": "c",
            "split_stem_sha256": {"test": "t"},
        }
        bindings[args.ablation] = resumable_train.recovery_binding(
            bound=bound,
            model={"sha256": "m"},
            environment={"git_commit": "g", "detector_lock_sha256": "d"},
            args=args,
        )
        return {"status": "COMPLETED"}

    monkeypatch.setattr(resumable_train, "execute", capture)
    for key in ("A5_multi_scale", "A6_photometric_value"):
        imp.execute(_args(tmp_path, key))
    assert bindings["A5_multi_scale"] != bindings["A6_photometric_value"]
