#!/usr/bin/env python3
"""Generate the append-only VGG16-54 R1 module-invocation fresh launcher."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "detector/colab/vgg16_54_r1_launch_r3.ipynb"
R2_BUILDER = ROOT / "scripts/build_vgg16_54_r1_launch_r2_notebook.py"


def _load_r2() -> Any:
    spec = importlib.util.spec_from_file_location("vgg16_54_r1_launch_r2_pinned", R2_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned R2 builder: {R2_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def notebook() -> dict[str, object]:
    payload = json.loads(json.dumps(_load_r2().notebook()))
    title = "".join(payload["cells"][0]["source"])
    payload["cells"][0]["source"] = title.replace(
        "VGG16-54 R1 R2 — governed fresh epoch-1 smoke",
        "VGG16-54 R1 R3 — module-invocation fresh epoch-1 smoke",
    ).splitlines(keepends=True)

    command = "".join(payload["cells"][6]["source"])
    old = "    'uv', 'run', 'python', 'colab/run_vgg16_54_r1_r1.py',\n"
    new = "    'uv', 'run', 'python', '-m', 'colab.run_vgg16_54_r1_r1',\n"
    if command.count(old) != 1:
        raise RuntimeError("R2 runner invocation anchor differs")
    payload["cells"][6]["source"] = command.replace(old, new).splitlines(keepends=True)

    gate = (
        "## Gate after this notebook\n\n"
        "R3 changes only the Python invocation from a script path to the package module so the "
        "reviewed `colab` package resolves from the detector working directory. Stop after epoch "
        "1 for independent artifact QA. Resume and long training remain forbidden. The sealed "
        "test remains unopened.\n"
    )
    payload["cells"][8]["source"] = gate.splitlines(keepends=True)
    return payload


def main() -> None:
    OUTPUT.write_text(json.dumps(notebook(), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
