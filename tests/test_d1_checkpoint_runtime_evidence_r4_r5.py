from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def load_runner():
    path = REPO_ROOT / "detector/colab/run_d1_colab_checkpoint_r5.py"
    spec = importlib.util.spec_from_file_location("test_d1_runtime_evidence_r4_r5", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def argv(bundle: Path, state: Path) -> list[str]:
    return [
        "--repo-root",
        str(REPO_ROOT),
        "--bundle",
        str(bundle),
        "--state-dir",
        str(state),
        "--mode",
        "resume",
        "--epochs",
        "2",
        "--tag",
        "checkpoint_smoke_r4_r5",
    ]


def configure_boot(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    boot = tmp_path / "boot_id"
    boot.write_text("22222222-2222-4222-8222-222222222222", encoding="ascii")
    monkeypatch.setattr(runner.r2, "BOOT_ID_PATH", boot)


@pytest.mark.parametrize("pointer", ([], "pointer", 7))
def test_non_object_latest_still_records_durable_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pointer: object
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(json.dumps(pointer), encoding="utf-8")
    configure_boot(tmp_path, monkeypatch)
    assert runner.main(argv(bundle, state)) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert execution["checkpoint_binding_sha256"] is None
    assert execution["sealed_test_accessed"] is False
    assert len((state / "execution_attempts.jsonl").read_text().splitlines()) == 1


def test_symlinked_recovery_cannot_inject_failure_binding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = tmp_path / "bundle.tar.gz"
    bundle.write_bytes(b"train-val-only")
    outside = tmp_path / "outside-recovery"
    outside.mkdir()
    (outside / "latest.json").write_text(
        json.dumps({"binding_sha256": "a" * 64}), encoding="utf-8"
    )
    state = tmp_path / "state"
    state.mkdir()
    (state / "recovery").symlink_to(outside, target_is_directory=True)
    configure_boot(tmp_path, monkeypatch)
    assert runner.main(argv(bundle, state)) == 1
    execution = json.loads((state / "colab_execution.json").read_text())
    assert execution["status"] == "FAILED"
    assert execution["checkpoint_binding_sha256"] is None
    assert json.loads((outside / "latest.json").read_text())["binding_sha256"] == "a" * 64


def test_generation_is_validated_before_any_snapshot_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = tmp_path / "state"
    (state / "recovery").mkdir(parents=True)
    (state / "recovery/latest.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "generation": "../../outside",
                "manifest_sha256": "a" * 64,
                "binding_sha256": "b" * 64,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        runner.r4,
        "verify_current_checkpoint",
        lambda *_args: (_ for _ in ()).throw(AssertionError("unsafe delegate reached")),
    )
    with pytest.raises(RuntimeError, match="generation name is unsafe"):
        runner.verify_current_checkpoint(state, "b" * 64)


def test_r5_notebook_is_unexecuted_and_fail_closed() -> None:
    notebook = json.loads(
        (REPO_ROOT / "detector/colab/d1_train_checkpoint_r5.ipynb").read_text()
    )
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    source = "\n".join("".join(cell["source"]) for cell in notebook["cells"])
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in source
    assert "run_d1_colab_checkpoint_r5.py" in source
    assert "checkpoint_smoke_seed_20261018_r4_r5" in source
    assert "export-test" not in source and "--final-eval" not in source
