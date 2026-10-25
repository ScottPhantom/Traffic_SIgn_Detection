from __future__ import annotations

import argparse
import hashlib
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import contract
from m1 import resumable_train_n54_r1 as n54


def arguments(
    tmp_path: Path, *, resume: bool, stop_after_epoch: int | None = None
) -> argparse.Namespace:
    return argparse.Namespace(
        model=tmp_path / "repo/models/pretrained/yolo11n.pt",
        checkpoint_dir=tmp_path / "drive/recovery",
        results_dir=tmp_path / "repo/results/experiments",
        resume=resume,
        stop_after_epoch=(
            stop_after_epoch if stop_after_epoch is not None else (None if resume else 1)
        ),
        seed=20261018,
        epochs=100,
        imgsz=1280,
        batch=4,
        device="0",
        workers=4,
        fraction=1.0,
        patience=30,
        tag="n54_r1",
        cos_lr=True,
    )


def patch_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    model = tmp_path / "repo/models/pretrained/yolo11n.pt"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"approved-nano-model")
    monkeypatch.setattr(n54, "PRETRAINED_SHA256", hashlib.sha256(model.read_bytes()).hexdigest())
    data = tmp_path / "repo/data.yaml"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("train: train\nval: val\n", encoding="utf-8")
    original_bind = contract.bind_training_model

    def bind_model(path: str) -> dict[str, str]:
        assert Path(path) == model
        return {
            "path": path,
            "sha256": n54.PRETRAINED_SHA256,
            "origin": "ultralytics/assets v8.4.0",
        }

    monkeypatch.setattr(contract, "bind_training_model", bind_model)
    monkeypatch.setattr(
        contract,
        "check_contract",
        lambda: {
            "export_manifest_sha256": "b" * 64,
            "class_map_sha256": "c" * 64,
            "split_stem_sha256": {
                "train": "d" * 64,
                "val": "e" * 64,
                "test": "f" * 64,
            },
            "data_yaml": str(data),
        },
    )
    monkeypatch.setattr(
        contract,
        "environment",
        lambda: {"git_commit": "1" * 40, "detector_lock_sha256": "2" * 64},
    )
    monkeypatch.setattr(contract, "disable_telemetry", lambda: None)
    monkeypatch.setattr(contract, "RESULTS_DIR", tmp_path / "repo/results/experiments")
    assert original_bind is not contract.bind_training_model


class FakeYOLO:
    observed: list[dict[str, object]] = []

    def __init__(self, source: str) -> None:
        self.source = source
        self.callbacks: list[object] = []

    def add_callback(self, event: str, callback: object) -> None:
        assert event == "on_model_save"
        self.callbacks.append(callback)

    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        assert kwargs["cos_lr"] is True
        self.observed.append({"resume": resume, **kwargs})
        run = Path(str(kwargs["project"])) / str(kwargs["name"])
        (run / "weights").mkdir(parents=True, exist_ok=True)
        start = 2 if resume else 1
        for epoch in range(start, int(kwargs["epochs"]) + 1):
            (run / "weights/last.pt").write_bytes(f"last-{epoch}".encode())
            (run / "weights/best.pt").write_bytes(f"best-{epoch}".encode())
            (run / "results.csv").write_text(
                "epoch,loss\n" + "\n".join(f"{item},0.5" for item in range(1, epoch + 1)) + "\n",
                encoding="utf-8",
            )
            (run / "args.yaml").write_text(
                "epochs: 100\nfliplr: 0.0\ncos_lr: true\n", encoding="utf-8"
            )
            trainer = SimpleNamespace(save_dir=run, epoch=epoch - 1, stop=False)
            for callback in self.callbacks:
                callback(trainer)
            if trainer.stop:
                break


class EarlyStopYOLO(FakeYOLO):
    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        kwargs["epochs"] = 2
        super().train(resume=resume, **kwargs)


def test_binding_and_train_arguments_freeze_n54(tmp_path: Path) -> None:
    args = arguments(tmp_path, resume=False)
    binding = n54.recovery_binding(
        bound={
            "export_manifest_sha256": "b" * 64,
            "class_map_sha256": "c" * 64,
            "split_stem_sha256": {"train": "d" * 64, "val": "e" * 64, "test": "f" * 64},
        },
        model={"sha256": "a" * 64},
        environment={"git_commit": "1" * 40, "detector_lock_sha256": "2" * 64},
        args=args,
    )
    train_args = n54.train_arguments(
        bound={"data_yaml": "data.yaml"}, args=args, results_dir=tmp_path, name="run"
    )
    assert binding["experiment"] == "YOLO11N-N54-R1"
    assert binding["pretrained_name"] == "yolo11n.pt"
    assert binding["owner_decision_sha256"] == n54.OWNER_DECISION_SHA256
    assert train_args["cos_lr"] is True
    assert train_args["epochs"] == 100


@pytest.mark.parametrize(
    ("field", "value"),
    (("epochs", 40), ("seed", 20261019), ("batch", 8), ("cos_lr", False), ("tag", "other")),
)
def test_frozen_n54_rejects_changed_argument(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    patch_contract(monkeypatch, tmp_path)
    args = arguments(tmp_path, resume=False)
    setattr(args, field, value)
    with pytest.raises(RuntimeError, match="frozen arguments differ"):
        n54._validate_frozen(args)


def test_n54_rejects_wrong_weight_hash(tmp_path: Path) -> None:
    args = arguments(tmp_path, resume=False)
    args.model.parent.mkdir(parents=True)
    args.model.write_bytes(b"wrong")
    with pytest.raises(RuntimeError, match="SHA-256 differs"):
        n54._validate_frozen(args)


def test_fresh_pause_then_resume_completes_epoch_100(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    FakeYOLO.observed.clear()
    fresh = n54.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    assert (fresh["status"], fresh["completed_epoch"]) == ("PAUSED_FOR_RESUME", 1)
    shutil.rmtree(fresh["run_dir"])
    resumed = n54.execute(arguments(tmp_path, resume=True), yolo_factory=FakeYOLO)
    assert (resumed["status"], resumed["completed_epoch"]) == ("COMPLETED", 100)
    record = contract.strict_json(Path(resumed["run_dir"]) / "run_contract.json")
    assert record["experiment"] == "YOLO11N-N54-R1"
    assert record["owner_decision_sha256"] == n54.OWNER_DECISION_SHA256
    assert record["train_args"]["cos_lr"] is True
    assert [item["resume"] for item in FakeYOLO.observed] == [False, True]


def test_fresh_epoch_1_then_resume_epoch_2_smoke(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    FakeYOLO.observed.clear()
    fresh = n54.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    assert (fresh["status"], fresh["completed_epoch"]) == ("PAUSED_FOR_RESUME", 1)
    shutil.rmtree(fresh["run_dir"])
    resume = n54.execute(
        arguments(tmp_path, resume=True, stop_after_epoch=2), yolo_factory=FakeYOLO
    )
    assert (resume["status"], resume["completed_epoch"]) == ("PAUSED_FOR_RESUME", 2)


@pytest.mark.parametrize(
    ("resume", "stop_after"),
    ((False, 2), (True, 1), (True, 3)),
)
def test_n54_rejects_wrong_smoke_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    resume: bool,
    stop_after: int,
) -> None:
    patch_contract(monkeypatch, tmp_path)
    args = arguments(tmp_path, resume=resume, stop_after_epoch=stop_after)
    with pytest.raises(RuntimeError, match="smoke boundary"):
        n54._validate_frozen(args)


def test_n54_rejects_early_stopped_long_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    args = arguments(tmp_path, resume=False)
    args.stop_after_epoch = None
    with pytest.raises(RuntimeError, match="did not complete the frozen 100 epochs"):
        n54.execute(args, yolo_factory=EarlyStopYOLO)


def test_parser_requires_explicit_cosine_flag(tmp_path: Path) -> None:
    common = [
        "--model",
        str(tmp_path / "yolo11n.pt"),
        "--checkpoint-dir",
        str(tmp_path / "recovery"),
    ]
    with pytest.raises(SystemExit):
        n54.parser().parse_args(common)
    parsed = n54.parser().parse_args([*common, "--cos-lr"])
    assert parsed.cos_lr is True
    assert parsed.epochs == 100
