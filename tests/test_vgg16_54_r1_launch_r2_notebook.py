from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[1]
BUILDER = REPO_ROOT / "scripts/build_vgg16_54_r1_launch_r2_notebook.py"
NOTEBOOK = REPO_ROOT / "detector/colab/vgg16_54_r1_launch_r2.ipynb"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("vgg16_r2_notebook_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, Any]:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def source(index: int) -> str:
    return "".join(notebook()["cells"][index]["source"])


def test_notebook_is_deterministic_and_matches_builder(tmp_path: Path) -> None:
    builder = load_builder()
    expected = json.dumps(builder.notebook(), indent=1, ensure_ascii=False) + "\n"
    assert expected.encode() == NOTEBOOK.read_bytes()
    first = tmp_path / "first.ipynb"
    second = tmp_path / "second.ipynb"
    builder.OUTPUT = first
    builder.main()
    builder.OUTPUT = second
    builder.main()
    assert first.read_bytes() == second.read_bytes() == NOTEBOOK.read_bytes()


def test_notebook_pins_r2_runtime_evidence_contract() -> None:
    payload = notebook()
    assert payload["metadata"]["colab"]["gpuType"] == "L4"
    assert len(payload["cells"]) == 9
    for cell in payload["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
            compile("".join(cell["source"]), "notebook-cell", "exec")

    config = source(2)
    assert "2e1d981e70e02b19d1998fa17be8c8a0de033df0" in config
    assert "vgg16_54_r1_runtime_r1_source_qa_proof.json" in config
    assert "cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5" in config
    assert "runs/vgg16_54_seed_20261018_r2" in config
    assert "MODE = 'fresh'" in config
    assert "STOP_AFTER = 1" in config


def test_notebook_runs_successor_and_stops_before_resume() -> None:
    preflight = source(3)
    command = source(6)
    verification = source(7)
    gate = source(8)
    assert "assert sha256(path) == value" in preflight
    assert "colab/run_vgg16_54_r1_r1.py" in command
    assert "--runtime-source-qa-sha256" in command
    assert "--stop-after" in command
    assert "device_name'] == 'NVIDIA L4'" in verification
    assert "runtime_identity" in verification
    assert "Long training is still forbidden" in gate


def test_notebook_has_no_sealed_test_route() -> None:
    lowered = json.dumps(notebook()).lower()
    assert "export-test" not in lowered
    assert "--final-eval" not in lowered
    assert "split test" not in lowered
    assert "sealed_test_accessed'] is false" in lowered
