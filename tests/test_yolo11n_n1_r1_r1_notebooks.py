from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_yolo11n_n1_r1_r1_notebooks.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("yolo11n_n1_r1_r1_notebooks", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook_text(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return "\n".join("".join(cell.get("source", [])) for cell in payload["cells"])


def test_r1_r1_notebooks_are_reproducible_and_exactly_bound() -> None:
    builder = load_builder()
    first = builder.build()
    second = builder.build()
    assert first == second
    assert first["sealed_test_accessed"] is False
    assert first["source_commit"] == builder.SOURCE_COMMIT
    assert first["source_qa_sha256"] == builder.SOURCE_QA_SHA256
    assert set(first["notebooks"]) == {
        "yolo11n_n1_r1_r1_fresh.ipynb",
        "yolo11n_n1_r1_r1_resume.ipynb",
    }
    for name in first["notebooks"]:
        text = notebook_text(ROOT / "detector/colab" / name)
        assert builder.SOURCE_COMMIT in text
        assert builder.SOURCE_QA_SHA256 in text
        assert builder.SOURCE_QA_PATH in text
        assert builder.STATE in text
        assert builder.RUNNER in text
        assert builder.OLD_RUNNER not in text
        assert "export-test" not in text
        assert "final-eval" not in text
        assert "sealed_test_accessed" in text


def test_r1_r1_fresh_and_resume_are_strict() -> None:
    builder = load_builder()
    builder.build()
    fresh = notebook_text(ROOT / "detector/colab/yolo11n_n1_r1_r1_fresh.ipynb")
    resume = notebook_text(ROOT / "detector/colab/yolo11n_n1_r1_r1_resume.ipynb")
    assert "MODE = 'fresh'" in fresh and "STOP_AFTER = 1" in fresh
    assert "MODE = 'resume'" in resume and "STOP_AFTER = 2" in resume
    assert "A new L4 runtime is required" in resume
    assert "runtime_digest'] !=" in resume
