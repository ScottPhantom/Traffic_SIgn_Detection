import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = REPO_ROOT / "detector/colab/run_d1_colab_pilot_r2.py"
NOTEBOOK = REPO_ROOT / "detector/colab/d1_train_pilot_r2.ipynb"


def load_runner():
    spec = importlib.util.spec_from_file_location("test_d1_pilot_r2_runner", RUNNER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


runner = load_runner()


def source() -> str:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join("".join(cell["source"]) for cell in notebook["cells"])


def outcome(status: str, completed_epoch: int) -> dict:
    return {
        "status": status,
        "completed_epoch": completed_epoch,
        "sealed_test_accessed": False,
    }


def test_pilot_r2_accepts_only_the_planned_fresh_pause() -> None:
    runner.validate_pilot_outcome(outcome("PAUSED_FOR_RESUME", 1), mode="fresh")
    with pytest.raises(RuntimeError, match="pause exactly"):
        runner.validate_pilot_outcome(outcome("PAUSED_FOR_RESUME", 2), mode="fresh")


@pytest.mark.parametrize(
    ("mode", "completed"),
    (("fresh", 1.0), ("fresh", True), ("resume", 100.0), ("resume", True)),
)
def test_pilot_r2_requires_exact_integer_epoch(mode: str, completed: object) -> None:
    status = "PAUSED_FOR_RESUME" if mode == "fresh" else "COMPLETED"
    with pytest.raises(RuntimeError, match="exact integer"):
        runner.validate_pilot_outcome(outcome(status, completed), mode=mode)


@pytest.mark.parametrize(
    ("status", "completed"),
    (("COMPLETED_EARLY_STOPPED", 70), ("COMPLETED", 99), ("PAUSED_FOR_RESUME", 99)),
)
def test_pilot_r2_rejects_every_below_100_terminal_outcome(
    status: str, completed: int
) -> None:
    with pytest.raises(RuntimeError):
        runner.validate_pilot_outcome(outcome(status, completed), mode="resume")


@pytest.mark.parametrize("status", ("COMPLETED", "COMPLETED_FROM_FINAL_CHECKPOINT"))
def test_pilot_r2_accepts_only_complete_epoch_100(status: str) -> None:
    runner.validate_pilot_outcome(outcome(status, 100), mode="resume")


def test_pilot_r2_rejects_sealed_test_marker() -> None:
    payload = outcome("COMPLETED", 100)
    payload["sealed_test_accessed"] = True
    with pytest.raises(RuntimeError, match="sealed-test"):
        runner.validate_pilot_outcome(payload, mode="resume")


def pilot_argv(*, patience: int = 0) -> list[str]:
    return [
        "--repo-root",
        "/repo",
        "--bundle",
        "/bundle",
        "--state-dir",
        "/state",
        "--mode",
        "resume",
        "--epochs",
        "100",
        "--patience",
        str(patience),
        "--seed",
        "20261018",
        "--imgsz",
        "1280",
        "--batch",
        "4",
        "--device",
        "0",
        "--tag",
        "pilot_100e_seed_20261018_r2",
    ]


def test_pilot_r2_guard_rejects_early_stop_before_delegate_can_continue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = runner.r6.r2.r1.base
    monkeypatch.setattr(base, "strict_json", lambda _path: outcome("COMPLETED_EARLY_STOPPED", 70))

    def inherited_runner(_argv):
        base.strict_json(Path("training_outcome.json"))
        raise AssertionError("guard returned to inherited packaging path")

    monkeypatch.setattr(runner.r6, "main", inherited_runner)
    with pytest.raises(RuntimeError, match="all configured epochs"):
        runner.main(pilot_argv())


def test_pilot_r2_requires_patience_zero_before_delegation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        runner.r6,
        "main",
        lambda _argv: pytest.fail("invalid configuration reached inherited runner"),
    )
    with pytest.raises(RuntimeError, match="patience 0"):
        runner.main(pilot_argv(patience=30))


@pytest.mark.parametrize(
    ("flag", "value"),
    (("--seed", "20261019"), ("--imgsz", "640"), ("--batch", "8"), ("--device", "1")),
)
def test_pilot_r2_rejects_configuration_drift(
    monkeypatch: pytest.MonkeyPatch, flag: str, value: str
) -> None:
    argv = pilot_argv()
    argv[argv.index(flag) + 1] = value
    monkeypatch.setattr(
        runner.r6,
        "main",
        lambda _argv: pytest.fail("drifted configuration reached inherited runner"),
    )
    with pytest.raises(RuntimeError, match="reviewed candidate"):
        runner.main(argv)


def test_pilot_r2_notebook_is_unexecuted_and_fail_closed() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = [cell for cell in notebook["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    text = source()
    assert 'CODE_COMMIT = "PENDING_AFTER_QA"' in text
    assert 'RUN_LABEL = "pilot_seed_20261018_r2"' in text
    assert "run_d1_colab_pilot_r2.py" in text
    assert '    "--epochs",\n    "100",' in text
    assert '    "--patience",\n    "0",' in text
    assert '    "--batch",\n    "4",' in text
    assert 'execution["training_outcome"]["completed_epoch"] == 100' in text
    assert 'latest["generation"] == "epoch-0100"' in text
    assert "export-test" not in text and "--final-eval" not in text


def test_pilot_r2_builder_pins_source_hash_and_exact_cardinalities() -> None:
    builder = (REPO_ROOT / "scripts/build_d1_pilot_notebook_r2.py").read_text(
        encoding="utf-8"
    )
    assert runner.r6.r2.r1.base.sha256_file(
        REPO_ROOT / "detector/colab/d1_train_checkpoint_r6.ipynb"
    ) == "e42716fad4eb7b8d651565b611f11936d6a7b8b624832dccad8e513c55263fa6"
    assert "combined.count(before) != expected_count" in builder
