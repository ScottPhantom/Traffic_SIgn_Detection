import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = REPO_ROOT / "detector/colab/d1_train_pilot_r1.ipynb"


def notebook_source() -> str:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    return "\n".join("".join(cell["source"]) for cell in payload["cells"])


def test_pilot_notebook_is_unexecuted_and_pins_qa_passed_runner() -> None:
    payload = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    code = [cell for cell in payload["cells"] if cell["cell_type"] == "code"]
    assert all(cell.get("execution_count") is None and not cell.get("outputs") for cell in code)
    source = notebook_source()
    assert 'MODE = "fresh"' in source
    assert 'CODE_COMMIT = "47c86d17430808ceeee6e1a1a553cf6fef88e5ed"' in source
    assert 'RUN_LABEL = "pilot_seed_20261018_r1"' in source
    assert "run_d1_colab_checkpoint_r6.py" in source


def test_pilot_notebook_locks_the_reviewed_training_configuration() -> None:
    source = notebook_source()
    assert '    "--epochs",\n    "100",' in source
    assert '    "--imgsz",\n    "1280",' in source
    assert '    "--batch",\n    "4",' in source
    assert '    "--seed",\n    "20261018",' in source
    assert '    "pilot_100e_seed_20261018_r1",' in source
    assert 'command += ["--stop-after-epoch", "1"]' in source
    assert 'latest["generation"] == "epoch-0100"' in source


def test_pilot_notebook_remains_train_val_only_and_sealed_test_closed() -> None:
    source = notebook_source()
    assert 'execution["sealed_test_accessed"] is False' in source
    assert "export-test" not in source
    assert "--final-eval" not in source
    assert "data/processed/m1_yolo/test" not in source
