from __future__ import annotations

import json
from pathlib import Path

import pytest

from m1 import checkpoint_store as legacy
from m1 import checkpoint_store_r2 as r2


def binding() -> dict[str, object]:
    return {
        "experiment": "future-run-r2",
        "seed": 20261018,
        "sealed_test_accessed": False,
    }


def make_run(root: Path, epoch: int) -> Path:
    run = root / "D1_future_run_r2"
    (run / "weights").mkdir(parents=True, exist_ok=True)
    (run / "weights/last.pt").write_bytes(f"last-{epoch}".encode())
    (run / "weights/best.pt").write_bytes(f"best-{epoch}".encode())
    (run / "results.csv").write_text(f"epoch,loss\n{epoch},0.5\n", encoding="utf-8")
    (run / "args.yaml").write_text("fliplr: 0.0\n", encoding="utf-8")
    (run / "run_contract.json").write_text(
        json.dumps({"epoch": epoch, "sealed_test_accessed": False}), encoding="utf-8"
    )
    return run


def test_future_store_bounds_weight_history_and_keeps_chained_telemetry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = r2.EfficientCheckpointStore(tmp_path / "drive")
    verification_calls: list[str] = []
    original = store._verify_generation

    def counted(snapshot: Path, *args, **kwargs):
        verification_calls.append(snapshot.name)
        return original(snapshot, *args, **kwargs)

    monkeypatch.setattr(store, "_verify_generation", counted)
    maximum_calls_for_one_save = 0
    for epoch in range(1, 26):
        before = len(verification_calls)
        run = make_run(tmp_path / "local", epoch)
        store.save(run, epoch=epoch, binding=binding())
        maximum_calls_for_one_save = max(
            maximum_calls_for_one_save, len(verification_calls) - before
        )

    snapshots = sorted(path.name for path in store.snapshots.iterdir())
    assert snapshots == ["epoch-0024", "epoch-0025"]
    assert maximum_calls_for_one_save <= 6
    events = store.verify_telemetry(binding())
    assert [event["epoch"] for event in events] == list(range(1, 26))
    assert all(event["snapshot_count_after_prune"] <= 2 for event in events)
    assert all(event["sealed_test_accessed"] is False for event in events)


def test_future_store_restores_latest_verified_bytes(tmp_path: Path) -> None:
    store = r2.EfficientCheckpointStore(tmp_path / "drive")
    for epoch in (1, 2, 3):
        store.save(make_run(tmp_path / "local", epoch), epoch=epoch, binding=binding())
    restored = store.restore_latest(tmp_path / "restored", binding())
    assert restored.read_bytes() == b"last-3"
    assert store.verify_telemetry(binding())[-1]["epoch"] == 3


def test_future_store_rejects_telemetry_tamper_and_repeated_epoch(tmp_path: Path) -> None:
    store = r2.EfficientCheckpointStore(tmp_path / "drive")
    run = make_run(tmp_path / "local", 1)
    store.save(run, epoch=1, binding=binding())
    with pytest.raises(RuntimeError, match="repeated or older"):
        store.save(run, epoch=1, binding=binding())

    lines = store.telemetry_path.read_text(encoding="utf-8").splitlines()
    event = json.loads(lines[0])
    event["checkpoint_io_seconds"] = -1
    store.telemetry_path.write_text(json.dumps(event) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="duration"):
        store.verify_telemetry(binding())
    restore_root = tmp_path / "tampered-restore"
    with pytest.raises(RuntimeError, match="duration"):
        store.restore_latest(restore_root, binding())
    assert not restore_root.exists()


def test_future_store_rejects_epoch_gap_and_non_false_seal(tmp_path: Path) -> None:
    store = r2.EfficientCheckpointStore(tmp_path / "drive")
    store.save(make_run(tmp_path / "local", 1), epoch=1, binding=binding())
    with pytest.raises(RuntimeError, match="epoch gap"):
        store.save(make_run(tmp_path / "local", 3), epoch=3, binding=binding())

    unsafe_binding = dict(binding())
    unsafe_binding["sealed_test_accessed"] = True
    unsafe_store = r2.EfficientCheckpointStore(tmp_path / "unsafe-drive")
    with pytest.raises(RuntimeError, match="sealed_test_accessed=false"):
        unsafe_store.save(
            make_run(tmp_path / "unsafe-local", 1),
            epoch=1,
            binding=unsafe_binding,
        )


def test_future_store_rejects_symlink_and_hardlink_telemetry(tmp_path: Path) -> None:
    root = tmp_path / "drive"
    store = r2.EfficientCheckpointStore(root)
    outside = tmp_path / "outside.jsonl"
    outside.write_text("", encoding="utf-8")
    store.telemetry_path.symlink_to(outside)
    with pytest.raises(RuntimeError, match="regular non-symlink"):
        store.save(make_run(tmp_path / "local", 1), epoch=1, binding=binding())
    store.telemetry_path.unlink()
    store.telemetry_path.hardlink_to(outside)
    with pytest.raises(RuntimeError, match="exactly one link"):
        store.save(make_run(tmp_path / "local", 1), epoch=1, binding=binding())


def test_future_callback_uses_bounded_store(tmp_path: Path) -> None:
    run = make_run(tmp_path / "local", 7)
    store = r2.EfficientCheckpointStore(tmp_path / "drive")
    callback = r2.make_ultralytics_callback(store, binding())

    class Trainer:
        save_dir = run
        epoch = 6

    callback(Trainer())
    assert store.load_latest(binding())["completed_epoch"] == 7
    assert store.verify_telemetry(binding())[-1]["generation"] == "epoch-0007"


def test_successor_is_append_only_and_legacy_store_remains_unchanged() -> None:
    assert legacy.CheckpointStore.__module__ == "m1.checkpoint_store"
    assert r2.EfficientCheckpointStore.__module__ == "m1.checkpoint_store_r2"
    assert r2.RETENTION == 2
