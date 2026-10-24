from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).parents[1]
BUILDER = REPO_ROOT / "scripts/build_vgg16_54_r1_launch_r1_notebook.py"
NOTEBOOK = REPO_ROOT / "detector/colab/vgg16_54_r1_launch_r1.ipynb"

CHECKOUT_COMMIT = "762a46c048c5016662a941da98feb5c8ff9e126d"
OWNER_APPROVAL_SHA256 = (
    "f09c7707263b52337957de5dd9ac2bf22712bb9135df8a84880633718ade06af"
)
SOURCE_QA_SHA256 = (
    "10f0ca69e32aed906d0bf8cad36aaacf3d40ea069faec51fb084de0d7ecfb216"
)


def load_builder() -> Any:
    spec = importlib.util.spec_from_file_location(
        "test_vgg16_54_r1_launch_r1_builder", BUILDER
    )
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


def test_notebook_has_clean_l4_fresh_smoke_contract() -> None:
    payload = notebook()
    assert payload["metadata"]["accelerator"] == "GPU"
    assert payload["metadata"]["colab"]["gpuType"] == "L4"
    assert len(payload["cells"]) == 9

    for cell in payload["cells"]:
        if cell["cell_type"] == "code":
            assert cell["execution_count"] is None
            assert cell["outputs"] == []
            compile("".join(cell["source"]), f"cell-{cell.get('id', 'unknown')}", "exec")

    config = source(2)
    assert f"CHECKOUT_COMMIT = '{CHECKOUT_COMMIT}'" in config
    assert f"OWNER_APPROVAL_SHA256 = '{OWNER_APPROVAL_SHA256}'" in config
    assert f"SOURCE_QA_SHA256 = '{SOURCE_QA_SHA256}'" in config
    assert "MODE = 'fresh'" in config
    assert "STOP_AFTER = 1" in config
    assert "runs/vgg16_54_seed_20261018_r1" in config
    assert "SMOKE_QA = None" in config


def test_notebook_pins_checkout_proofs_and_fresh_epoch_one() -> None:
    checkout = source(4)
    command = source(6)
    verification = source(7)
    resume_protocol = source(8)

    assert "git', 'checkout', '--detach', CHECKOUT_COMMIT" in checkout
    assert "assert observed == CHECKOUT_COMMIT" in checkout
    assert "--owner-approval-sha256" in command
    assert "--source-qa-sha256" in command
    assert "--stop-after" in command
    assert "execution['sealed_test_accessed'] is False" in verification
    assert "MODE='resume'" in resume_protocol
    assert "STOP_AFTER=2" in resume_protocol
    assert "independent smoke artifact QA" in resume_protocol


def test_notebook_has_no_test_route_or_unresolved_anchor() -> None:
    serialized = json.dumps(notebook())
    lowered = serialized.lower()
    assert "pending_" not in lowered
    assert "export-test" not in lowered
    assert "--final-eval" not in lowered
    assert "split test" not in lowered
    assert "sealed_test_accessed'] is false" in lowered
    assert hashlib.sha256(NOTEBOOK.read_bytes()).hexdigest() == (
        "11b733725af912d02289d9ce2ddbc80a446d7f621c5ab5861ab0ecf239be90fc"
    )
