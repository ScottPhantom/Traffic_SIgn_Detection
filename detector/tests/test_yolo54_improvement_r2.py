from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from m1 import checkpoint_store, contract, resumable_train
from m1 import yolo54_improvement_r2 as imp

DETECTOR = Path(__file__).parents[1]
BOUND = {
    "data_yaml": "data.yaml",
    "export_manifest_sha256": "e",
    "class_map_sha256": "c",
    "split_stem_sha256": {"test": "t"},
}
ENVIRONMENT = {"git_commit": "g", "detector_lock_sha256": "d"}


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


def _binding_under(tmp_path: Path, key: str, monkeypatch) -> dict:
    """The checkpoint binding the wrapped trainer would compute for one ablation."""
    seen = {}

    def capture(args, **_kwargs):
        seen["binding"] = resumable_train.recovery_binding(
            bound=BOUND, model={"sha256": "m"}, environment=ENVIRONMENT, args=args
        )
        return {"status": "COMPLETED"}

    monkeypatch.setattr(resumable_train, "execute", capture)
    imp.execute(_args(tmp_path, key))
    return seen["binding"]


@pytest.mark.parametrize("key", sorted(imp.ABLATIONS))
def test_every_registered_ablation_is_a_single_whitelisted_category(key) -> None:
    ablation = imp.get(key)
    assert set(ablation.overrides) <= imp.CATEGORIES[ablation.category]
    assert not set(ablation.overrides) & imp.FORBIDDEN_KEYS
    assert ablation.hypothesis and ablation.l4_hours > 0
    assert ablation.success.startswith("Screening") and "conf 0.20" in ablation.success


@pytest.mark.parametrize(
    ("overrides", "category", "message"),
    [
        ({"fliplr": 0.5}, "geometric", "forbidden"),
        ({"data": "other.yaml"}, "schedule", "forbidden"),
        ({"imgsz": 1536}, "multi_scale", "forbidden"),
        ({"fraction": 0.5}, "schedule", "forbidden"),
        ({"workers": 8}, "schedule", "forbidden"),
        ({"device": "cpu"}, "schedule", "forbidden"),
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


def test_plan_is_the_real_train_arguments_with_flip_off(tmp_path) -> None:
    result = imp.plan("A6_photometric_value", drive_root=tmp_path)
    assert result["changed"] == {"hsv_v": 0.6}
    args = result["train_args"]
    real_keys = set(
        resumable_train.train_arguments(
            bound=BOUND,
            args=_args(tmp_path, "A6_photometric_value"),
            results_dir=tmp_path,
            name="run",
        )
    )
    assert set(args) == real_keys | {"hsv_v"}
    assert args["fliplr"] == 0.0 and args["imgsz"] == 1280 and args["batch"] == 4
    assert args["seed"] == 20261018 and args["epochs"] == 100 and args["patience"] == 0
    assert args["workers"] == 4 and args["fraction"] == 1.0 and args["plots"] is False
    assert args["data"].startswith("<bound at train time")
    assert result["checkpoint_dir"].endswith(
        "M1_D1_Colab/runs/yolo54_improvement_seed_20261018_r1/A6_photometric_value"
    )
    assert result["success_kind"] == "screening" and result["screening_conf"] == 0.20
    assert result["training_started"] is False and result["sealed_test_accessed"] is False
    assert imp.plan("A3_schedule_40e_cos")["train_args"]["epochs"] == 40


def test_a4_pins_the_pilots_effective_warmup_bias_lr() -> None:
    args = imp.plan("A4_optimizer_sgd")["train_args"]
    assert args["optimizer"] == "SGD" and args["warmup_bias_lr"] == 0.0


def test_a3_hypothesis_is_the_lr_mechanism_not_late_overfit() -> None:
    a3 = imp.get("A3_schedule_40e_cos")
    assert "best.pt` is already that epoch" in a3.hypothesis
    assert "non-inferiority" in a3.success
    # Ultralytics lr lambdas at epoch 20 with lrf 0.01: linear over 100, cosine over 40.
    linear = (1 - 20 / 100) * (1 - 0.01) + 0.01
    cosine = ((1 - math.cos(20 * math.pi / 40)) / 2) * (0.01 - 1) + 1
    assert round(linear, 1) == 0.8 and round(cosine, 1) == 0.5


def test_plan_command_imports_no_model_or_image_code() -> None:
    code = (
        "import sys, json; from m1 import yolo54_improvement_r2 as imp; "
        "imp.plan('A5_multi_scale'); "
        "print(json.dumps(sorted(m for m in ('ultralytics', 'torch', 'cv2', 'PIL') "
        "if m in sys.modules)))"
    )
    out = subprocess.run(
        [sys.executable, "-c", code], cwd=DETECTOR, capture_output=True, text=True, check=True
    ).stdout.strip()
    assert json.loads(out) == []


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"checkpoint_dir": Path("/tmp/baseline_run")}, "ablation's own folder"),
        ({"imgsz": 1536}, "pilot value 1280"),
        ({"batch": 8}, "pilot value 4"),
        ({"seed": 20261019}, "pilot value 20261018"),
        ({"workers": 8}, "--workers must stay at the pilot value 4"),
        ({"workers": 0}, "--workers must stay at the pilot value 4"),
        ({"fraction": 0.5}, "--fraction must stay at the pilot value 1.0"),
        ({"fraction": 1.0001}, "--fraction must stay at the pilot value 1.0"),
    ],
)
def test_execute_refuses_before_training(tmp_path, monkeypatch, change, message) -> None:
    monkeypatch.setattr(
        resumable_train, "execute", lambda *a, **k: pytest.fail("training must not start")
    )
    with pytest.raises(RuntimeError, match=message):
        imp.execute(_args(tmp_path, "A6_photometric_value", **change))


def test_cli_refuses_a_partial_fraction_without_training(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        resumable_train, "execute", lambda *a, **k: pytest.fail("training must not start")
    )
    ablation = imp.get("A5_multi_scale")
    code = imp.main(
        [
            "train",
            ablation.key,
            "--drive-root",
            str(tmp_path),
            "--model",
            str(tmp_path / "m.pt"),
            "--checkpoint-dir",
            str(imp.checkpoint_dir_for(tmp_path, ablation)),
            "--fraction",
            "0.25",
        ]
    )
    assert code == 1 and "--fraction must stay" in capsys.readouterr().err


def test_execute_binds_overrides_into_train_args_and_checkpoint_then_restores(
    tmp_path, monkeypatch
) -> None:
    seen = {}
    original = (resumable_train.train_arguments, resumable_train.recovery_binding)

    def fake_execute(args, **_kwargs):
        seen["train"] = resumable_train.train_arguments(
            bound=BOUND, args=args, results_dir=tmp_path, name="run"
        )
        seen["binding"] = resumable_train.recovery_binding(
            bound=BOUND, model={"sha256": "m"}, environment=ENVIRONMENT, args=args
        )
        seen["args"] = args
        return {"status": "COMPLETED", "completed_epoch": args.epochs}

    monkeypatch.setattr(resumable_train, "execute", fake_execute)
    outcome = imp.execute(_args(tmp_path, "A3_schedule_40e_cos"))
    assert outcome["ablation"] == "A3_schedule_40e_cos" and outcome["completed_epoch"] == 40
    assert outcome["package"] == "D1-YOLO54-IMPROVEMENT-R2"
    assert seen["train"]["epochs"] == 40 and seen["train"]["cos_lr"] is True
    assert seen["train"]["fliplr"] == 0.0 and seen["train"]["workers"] == 4
    assert seen["binding"]["cos_lr"] is True and seen["binding"]["epochs"] == 40
    assert seen["binding"]["ablation"]["package"] == "D1-YOLO54-IMPROVEMENT-R2"
    assert seen["binding"]["ablation"]["key"] == "A3_schedule_40e_cos"
    assert seen["args"].tag == "yolo54_improvement_A3_schedule_40e_cos_r2"
    assert (resumable_train.train_arguments, resumable_train.recovery_binding) == original


def test_patches_are_restored_when_training_fails(tmp_path, monkeypatch) -> None:
    original = (resumable_train.train_arguments, resumable_train.recovery_binding)

    def boom(*_a, **_k):
        raise RuntimeError("colab disconnected")

    monkeypatch.setattr(resumable_train, "execute", boom)
    with pytest.raises(RuntimeError, match="colab disconnected"):
        imp.execute(_args(tmp_path, "A5_multi_scale"))
    assert (resumable_train.train_arguments, resumable_train.recovery_binding) == original
    assert imp._ACTIVE == []


def test_nested_execute_is_refused(tmp_path, monkeypatch) -> None:
    def nested(args, **_kwargs):
        imp.execute(_args(tmp_path, "A6_photometric_value"))

    monkeypatch.setattr(resumable_train, "execute", nested)
    with pytest.raises(RuntimeError, match="another improvement run is active"):
        imp.execute(_args(tmp_path, "A5_multi_scale"))
    assert imp._ACTIVE == []


def test_checkpoint_store_refuses_to_resume_under_another_ablation(tmp_path, monkeypatch) -> None:
    a5 = _binding_under(tmp_path, "A5_multi_scale", monkeypatch)
    a6 = _binding_under(tmp_path, "A6_photometric_value", monkeypatch)
    store = checkpoint_store.CheckpointStore(tmp_path / "store")
    pointer = {
        "schema_version": checkpoint_store.SCHEMA_VERSION,
        "generation": "epoch-0001",
        "manifest_sha256": "0" * 64,
        "binding_sha256": checkpoint_store.canonical_sha256(a5),
    }
    (store.root / checkpoint_store.LATEST).write_text(json.dumps(pointer), encoding="utf-8")
    with pytest.raises(RuntimeError, match="binding differs"):
        store.load_latest(a6)
    # The A5 binding passes the binding check and fails only later, on the missing snapshot.
    with pytest.raises(RuntimeError, match="checkpoint manifest"):
        store.load_latest(a5)


def test_r1_and_r2_bindings_differ_for_the_same_overrides(tmp_path, monkeypatch) -> None:
    from m1 import yolo54_improvement_r1 as r1

    r2_binding = _binding_under(tmp_path, "A5_multi_scale", monkeypatch)
    seen = {}

    def capture(args, **_kwargs):
        seen["binding"] = resumable_train.recovery_binding(
            bound=BOUND, model={"sha256": "m"}, environment=ENVIRONMENT, args=args
        )
        return {"status": "COMPLETED"}

    monkeypatch.setattr(resumable_train, "execute", capture)
    r1.execute(_args(tmp_path, "A5_multi_scale"))
    assert checkpoint_store.canonical_sha256(seen["binding"]) != (
        checkpoint_store.canonical_sha256(r2_binding)
    )
