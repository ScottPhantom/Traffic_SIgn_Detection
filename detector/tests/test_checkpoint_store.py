from __future__ import annotations

import json
from pathlib import Path

import pytest

from m1 import checkpoint_store


def binding(*, batch: int = 4) -> dict[str, object]:
    return {
        "git_commit": "a" * 40,
        "detector_lock_sha256": "b" * 64,
        "model_sha256": "c" * 64,
        "export_manifest_sha256": "d" * 64,
        "train_stem_sha256": "e" * 64,
        "val_stem_sha256": "f" * 64,
        "seed": 20261018,
        "epochs": 100,
        "imgsz": 1280,
        "batch": batch,
        "workers": 4,
        "fraction": 1.0,
        "patience": 30,
        "fliplr": 0.0,
    }


def make_run(root: Path, epoch: int) -> Path:
    run = root / "D1_yolo11s_wp33_deadbeef_20261018_checkpoint_r1"
    (run / "weights").mkdir(parents=True, exist_ok=True)
    (run / "weights/last.pt").write_bytes(f"last-{epoch}".encode())
    (run / "weights/best.pt").write_bytes(f"best-{epoch}".encode())
    (run / "results.csv").write_text(f"epoch,loss\n{epoch},0.5\n", encoding="utf-8")
    (run / "args.yaml").write_text("epochs: 100\nfliplr: 0.0\n", encoding="utf-8")
    (run / "run_contract.json").write_text(
        json.dumps({"status": "STARTED", "epoch": epoch}), encoding="utf-8"
    )
    return run


def test_checkpoint_survives_interruption_and_restores_verified_bytes(tmp_path: Path) -> None:
    run = make_run(tmp_path / "local", 1)
    store = checkpoint_store.CheckpointStore(tmp_path / "drive", retention=2)
    first = store.save(run, epoch=1, binding=binding())
    assert first["completed_epoch"] == 1

    make_run(tmp_path / "local", 2)
    original_copy = checkpoint_store._copy_verified_atomic

    def interrupt(source: Path, destination: Path) -> dict[str, object]:
        if destination.name == "best.pt":
            raise RuntimeError("simulated runtime loss")
        return original_copy(source, destination)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(checkpoint_store, "_copy_verified_atomic", interrupt)
        with pytest.raises(RuntimeError, match="simulated runtime loss"):
            store.save(run, epoch=2, binding=binding())

    # latest.json still selects the complete epoch-1 generation.
    assert store.load_latest(binding())["completed_epoch"] == 1
    last = store.restore_latest(tmp_path / "restored", binding())
    assert last.read_bytes() == b"last-1"
    assert (last.parents[1] / "weights/best.pt").read_bytes() == b"best-1"

    # A new runtime restores epoch 1 and must be able to checkpoint epoch 2 itself.
    resumed_run = last.parents[1]
    (resumed_run / "weights/last.pt").write_bytes(b"last-2")
    (resumed_run / "weights/best.pt").write_bytes(b"best-2")
    (resumed_run / "results.csv").write_text("epoch,loss\n2,0.4\n", encoding="utf-8")
    store.save(resumed_run, epoch=2, binding=binding())
    assert (tmp_path / "drive/snapshots/epoch-0001").is_dir()
    assert store.load_latest(binding())["completed_epoch"] == 2
    assert any((tmp_path / "drive/snapshots").glob(".epoch-0002.*.partial"))


def test_checkpoint_rejects_config_change_and_tampering(tmp_path: Path) -> None:
    run = make_run(tmp_path / "local", 1)
    store = checkpoint_store.CheckpointStore(tmp_path / "drive")
    store.save(run, epoch=1, binding=binding())
    with pytest.raises(RuntimeError, match="binding differs"):
        store.load_latest(binding(batch=8))

    snapshot = tmp_path / "drive/snapshots/epoch-0001/weights/last.pt"
    snapshot.write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="hash/size differs"):
        store.load_latest(binding())


def test_checkpoint_keeps_current_and_previous_verified_generations(tmp_path: Path) -> None:
    run = make_run(tmp_path / "local", 1)
    store = checkpoint_store.CheckpointStore(tmp_path / "drive", retention=2)
    for epoch in (1, 2, 3):
        make_run(tmp_path / "local", epoch)
        store.save(run, epoch=epoch, binding=binding())
    names = sorted(path.name for path in (tmp_path / "drive/snapshots").iterdir())
    assert names == ["epoch-0002", "epoch-0003"]
    assert store.load_latest(binding())["completed_epoch"] == 3


def test_checkpoint_rejects_symlinked_store_and_artifact(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    linked = tmp_path / "linked"
    linked.symlink_to(outside, target_is_directory=True)
    with pytest.raises(RuntimeError, match="contains a symlink"):
        checkpoint_store.CheckpointStore(linked)

    run = make_run(tmp_path / "local", 1)
    (run / "weights/last.pt").unlink()
    (run / "weights/last.pt").symlink_to(tmp_path / "outside.pt")
    with pytest.raises(RuntimeError, match="regular non-symlink"):
        checkpoint_store.CheckpointStore(tmp_path / "drive").save(
            run, epoch=1, binding=binding()
        )


def test_ultralytics_callback_snapshots_after_model_save(tmp_path: Path) -> None:
    run = make_run(tmp_path / "local", 7)
    store = checkpoint_store.CheckpointStore(tmp_path / "drive")
    callback = checkpoint_store.make_ultralytics_callback(store, binding())

    class Trainer:
        save_dir = run
        epoch = 6

    callback(Trainer())
    assert store.load_latest(binding())["completed_epoch"] == 7
