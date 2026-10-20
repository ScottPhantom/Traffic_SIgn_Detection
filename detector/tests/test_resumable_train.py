from __future__ import annotations

import argparse
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

from m1 import contract, resumable_train


def arguments(tmp_path: Path, *, resume: bool) -> argparse.Namespace:
    return argparse.Namespace(
        model=tmp_path / "repo/models/pretrained/yolo11s.pt",
        checkpoint_dir=tmp_path / "drive/recovery",
        results_dir=tmp_path / "repo/results/experiments",
        resume=resume,
        stop_after_epoch=None if resume else 1,
        seed=20261018,
        epochs=2,
        imgsz=1280,
        batch=4,
        device="0",
        workers=4,
        fraction=1.0,
        patience=30,
        tag="resume_test",
    )


def patch_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    model = tmp_path / "repo/models/pretrained/yolo11s.pt"
    model.parent.mkdir(parents=True)
    model.write_bytes(b"approved-model")
    data = tmp_path / "repo/data.yaml"
    data.parent.mkdir(parents=True, exist_ok=True)
    data.write_text("train: train\nval: val\n", encoding="utf-8")
    monkeypatch.setattr(
        contract,
        "bind_training_model",
        lambda path: {"path": path, "sha256": "a" * 64, "origin": "test"},
    )
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
        lambda: {
            "git_commit": "1" * 40,
            "detector_lock_sha256": "2" * 64,
        },
    )
    monkeypatch.setattr(contract, "disable_telemetry", lambda: None)
    monkeypatch.setattr(contract, "RESULTS_DIR", tmp_path / "repo/results/experiments")


class FakeYOLO:
    def __init__(self, source: str) -> None:
        self.source = Path(source)
        self.callbacks: list[object] = []

    def add_callback(self, event: str, callback: object) -> None:
        assert event == "on_model_save"
        self.callbacks.append(callback)

    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        run = Path(str(kwargs["project"])) / str(kwargs["name"])
        (run / "weights").mkdir(parents=True, exist_ok=True)
        start = 2 if resume else 1
        target = int(kwargs["epochs"])
        for epoch in range(start, target + 1):
            (run / "weights/last.pt").write_bytes(f"last-{epoch}".encode())
            (run / "weights/best.pt").write_bytes(f"best-{epoch}".encode())
            (run / "results.csv").write_text(
                "epoch,loss\n" + "\n".join(f"{item},0.5" for item in range(1, epoch + 1)) + "\n",
                encoding="utf-8",
            )
            (run / "args.yaml").write_text("epochs: 2\nfliplr: 0.0\n", encoding="utf-8")
            trainer = SimpleNamespace(save_dir=run, epoch=epoch - 1, stop=False)
            for callback in self.callbacks:
                callback(trainer)
            if trainer.stop:
                break


class EarlyStopYOLO(FakeYOLO):
    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        kwargs["epochs"] = 1
        super().train(resume=resume, **kwargs)


class GapResumeYOLO(FakeYOLO):
    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        assert resume
        run = Path(str(kwargs["project"])) / str(kwargs["name"])
        (run / "weights").mkdir(parents=True, exist_ok=True)
        (run / "weights/last.pt").write_bytes(b"last-3")
        (run / "weights/best.pt").write_bytes(b"best-3")
        (run / "results.csv").write_text("epoch,loss\n3,0.3\n", encoding="utf-8")
        (run / "args.yaml").write_text("epochs: 3\n", encoding="utf-8")
        trainer = SimpleNamespace(save_dir=run, epoch=2, stop=False)
        for callback in self.callbacks:
            callback(trainer)


class ReplayResumeYOLO(GapResumeYOLO):
    def train(self, *, resume: bool = False, **kwargs: object) -> None:
        assert resume
        run = Path(str(kwargs["project"])) / str(kwargs["name"])
        trainer = SimpleNamespace(save_dir=run, epoch=0, stop=False)
        for callback in self.callbacks:
            callback(trainer)


def test_fresh_pause_then_real_resume_restores_next_epoch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    fresh = resumable_train.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    assert fresh["status"] == "PAUSED_FOR_RESUME"
    assert fresh["completed_epoch"] == 1
    original_run = Path(fresh["run_dir"])
    assert (tmp_path / "drive/recovery/latest.json").is_file()

    # A new Colab runtime has no local results, only the mounted Drive checkpoint.
    shutil.rmtree(original_run)

    resumed = resumable_train.execute(arguments(tmp_path, resume=True), yolo_factory=FakeYOLO)
    assert resumed["status"] == "COMPLETED"
    assert resumed["completed_epoch"] == 2
    restored = Path(resumed["run_dir"])
    assert (restored / "weights/last.pt").read_bytes() == b"last-2"
    assert contract.strict_json(restored / "run_contract.json")["status"] == "TRAINED"


def test_resume_rejects_changed_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    patch_contract(monkeypatch, tmp_path)
    resumable_train.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    changed = arguments(tmp_path, resume=True)
    changed.batch = 8
    with pytest.raises(RuntimeError, match="binding differs"):
        resumable_train.execute(changed, yolo_factory=FakeYOLO)


def test_normal_early_stop_is_finalized_not_paused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    args = arguments(tmp_path, resume=False)
    args.stop_after_epoch = None
    args.epochs = 3
    outcome = resumable_train.execute(args, yolo_factory=EarlyStopYOLO)
    assert outcome["status"] == "COMPLETED_EARLY_STOPPED"
    assert outcome["completed_epoch"] == 1
    run_contract = contract.strict_json(Path(outcome["run_dir"]) / "run_contract.json")
    assert run_contract["status"] == "TRAINED"


def test_resume_rejects_skipped_epoch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    patch_contract(monkeypatch, tmp_path)
    fresh = resumable_train.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    shutil.rmtree(fresh["run_dir"])
    with pytest.raises(RuntimeError, match="expected 2, got 3"):
        resumable_train.execute(arguments(tmp_path, resume=True), yolo_factory=GapResumeYOLO)


def test_resume_rejects_replayed_epoch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    patch_contract(monkeypatch, tmp_path)
    fresh = resumable_train.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    shutil.rmtree(fresh["run_dir"])
    with pytest.raises(RuntimeError, match="expected 2, got 1"):
        resumable_train.execute(arguments(tmp_path, resume=True), yolo_factory=ReplayResumeYOLO)


def test_results_root_symlink_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_contract(monkeypatch, tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "results_link"
    link.symlink_to(outside, target_is_directory=True)
    args = arguments(tmp_path, resume=False)
    args.results_dir = link
    with pytest.raises(RuntimeError, match="contains a symlink"):
        resumable_train.execute(args, yolo_factory=FakeYOLO)
    assert not any(outside.iterdir())


@pytest.mark.parametrize("attack", ("root", "ancestor", "nested"))
def test_resume_rejects_results_path_symlinks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, attack: str
) -> None:
    patch_contract(monkeypatch, tmp_path)
    fresh = resumable_train.execute(arguments(tmp_path, resume=False), yolo_factory=FakeYOLO)
    run = Path(fresh["run_dir"])
    run_name = run.name
    shutil.rmtree(run)
    results = contract.RESULTS_DIR
    outside = tmp_path / f"outside-{attack}"
    outside.mkdir()
    if attack == "root":
        results.rmdir()
        results.symlink_to(outside, target_is_directory=True)
    elif attack == "ancestor":
        results.rmdir()
        results.parent.rmdir()
        results.parent.symlink_to(outside, target_is_directory=True)
    else:
        (results / run_name).symlink_to(outside, target_is_directory=True)
    with pytest.raises((OSError, RuntimeError), match="symlink|already exists"):
        resumable_train.execute(arguments(tmp_path, resume=True), yolo_factory=FakeYOLO)
    assert not any(outside.iterdir())
