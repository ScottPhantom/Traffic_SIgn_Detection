from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[1]
BUILDER = REPO_ROOT / "scripts/build_vgg16_54_r1_launch_r3_notebook.py"
NOTEBOOK = REPO_ROOT / "detector/colab/vgg16_54_r1_launch_r3.ipynb"


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location("vgg16_r3_notebook_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, Any]:
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))


def source(index: int) -> str:
    return "".join(notebook()["cells"][index]["source"])


def test_notebook_is_deterministic_and_clean(tmp_path: Path) -> None:
    builder = load_builder()
    expected = json.dumps(builder.notebook(), indent=1, ensure_ascii=False) + "\n"
    assert expected.encode() == NOTEBOOK.read_bytes()
    generated = tmp_path / "generated.ipynb"
    builder.OUTPUT = generated
    builder.main()
    assert generated.read_bytes() == NOTEBOOK.read_bytes()
    for cell in notebook()["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
            compile("".join(cell["source"]), "notebook-cell", "exec")


def test_notebook_uses_importable_module_and_keeps_r2_contract() -> None:
    command = source(6)
    serialized = json.dumps(notebook())
    assert "'python', '-m', 'colab.run_vgg16_54_r1_r1'" in command
    assert "colab/run_vgg16_54_r1_r1.py" not in command
    assert "runs/vgg16_54_seed_20261018_r2" in serialized
    assert "MODE = 'fresh'" in serialized
    assert "STOP_AFTER = 1" in serialized
    assert "cbd531302429908354858640ac501e8c0d1805c5dec5462bf5e6a1e611b044f5" in serialized


def test_module_invocation_resolves_from_detector_working_directory() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "colab.run_vgg16_54_r1_r1",
            "--help",
        ],
        cwd=REPO_ROOT / "detector",
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--runtime-source-qa" in result.stdout


def test_notebook_has_no_sealed_test_route() -> None:
    lowered = json.dumps(notebook()).lower()
    assert "export-test" not in lowered
    assert "--final-eval" not in lowered
    assert "split test" not in lowered
    assert "sealed_test_accessed'] is false" in lowered
