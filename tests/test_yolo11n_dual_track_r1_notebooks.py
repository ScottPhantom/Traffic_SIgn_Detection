from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts/build_yolo11n_dual_track_r1_notebooks.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("yolo11n_notebook_builder", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def text(payload: dict[str, object]) -> str:
    return "\n".join(
        "".join(cell.get("source", [])) for cell in payload["cells"]  # type: ignore[index,union-attr]
    )


def test_notebooks_are_reproducible_and_frozen() -> None:
    module = load_builder()
    first = module.build()
    second = module.build()
    assert first == second
    assert first["sealed_test_accessed"] is False
    assert first["source_commit"] == "45b7b1fab606032fcfb2956d0207171ae8b4c7f6"
    assert set(first["notebooks"]) == {
        "yolo11n_n54_r1_fresh.ipynb",
        "yolo11n_n54_r1_resume.ipynb",
        "yolo11n_n1_r1_fresh.ipynb",
        "yolo11n_n1_r1_resume.ipynb",
    }
    for name, record in first["notebooks"].items():
        path = ROOT / "detector/colab" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record["sha256"]
        payload = json.loads(path.read_text())
        assert payload["metadata"]["colab"]["gpuType"] == "L4"
        source = text(payload)
        assert "NVIDIA L4" in source
        assert "sealed_test_accessed" in source
        assert "export-test" not in source
        assert "final-eval" not in source
        assert "test/images" not in source


def test_fresh_and_resume_legs_are_strict_and_isolated() -> None:
    load_builder().build()
    for track in ("n54", "n1"):
        fresh = json.loads(
            (ROOT / f"detector/colab/yolo11n_{track}_r1_fresh.ipynb").read_text()
        )
        resume = json.loads(
            (ROOT / f"detector/colab/yolo11n_{track}_r1_resume.ipynb").read_text()
        )
        fresh_text = text(fresh)
        resume_text = text(resume)
        assert "MODE = 'fresh'" in fresh_text and "STOP_AFTER = 1" in fresh_text
        assert "MODE = 'resume'" in resume_text and "STOP_AFTER = 2" in resume_text
        assert "runtime_digest'] !=" in resume_text
        assert "A new L4 runtime is required" in resume_text or track == "n54"
        expected_suffix = (
            "yolo11n_n54_seed_20261018_r1"
            if track == "n54"
            else "yolo11n_n1_seed_20261018_r1"
        )
        assert expected_suffix in fresh_text
        assert expected_suffix in resume_text


def test_n54_and_n1_bind_exact_inputs() -> None:
    module = load_builder()
    module.build()
    n54 = text(json.loads((ROOT / "detector/colab/yolo11n_n54_r1_fresh.ipynb").read_text()))
    n1 = text(json.loads((ROOT / "detector/colab/yolo11n_n1_r1_fresh.ipynb").read_text()))
    assert module.N54_BUNDLE_SHA256 in n54
    assert module.WEIGHT_SHA256 in n54
    assert "--expected-checkout', SOURCE_COMMIT" in n54
    assert module.N1_BUNDLE_SHA256 in n1
    assert module.N1_MANIFEST_SHA256 in n1
    assert "test_included'] is False" in n1
    assert "Classifiers are not retrained" in n1
    assert "SOURCE_QA = REPO /" in n1
    assert "SOURCE_QA = INPUT_ROOT /" not in n1
    assert "cwd=REPO / 'detector'" in n1
    assert "cwd=INPUT_ROOT / 'detector'" not in n1
