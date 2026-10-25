#!/usr/bin/env python3
"""Build append-only Colab notebooks for the QA-binding-only N1 R1-R2 successor."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BASE_BUILDER = ROOT / "scripts/build_yolo11n_n1_r1_r1_notebooks.py"
OUTPUT_DIR = ROOT / "detector/colab"
SOURCE_COMMIT = "0ec545183bf29de035f440bb0307842ae132f4ca"
SOURCE_QA_SHA256 = "5fd51deea1679263b224fc45531f30a3d0a5aac86b3d044d262446e77a48b92a"
SOURCE_QA_PATH = "docs/review/yolo11n_n1_r1_r2_source_independent_qa_record.md"
OLD_SOURCE_COMMIT = "2d5ccdd17d5cb778cb3f7fb2588446eef4816c91"
OLD_SOURCE_QA_SHA256 = "57eb794e7256f1797a2961286330a98baa9a87664c9c6d84b84fe9ffda332254"
OLD_SOURCE_QA_PATH = "docs/review/yolo11n_n1_r1_r1_source_independent_qa_record.md"
STATE = "yolo11n_n1_seed_20261018_r1_r1"
RUNNER = "run_yolo11n_n1_r1_r1.py"


def _load_base() -> Any:
    spec = importlib.util.spec_from_file_location("yolo11n_n1_r1_r1_notebook_builder", BASE_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load base notebook builder: {BASE_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


BASE = _load_base()
REPLACEMENTS = (
    (OLD_SOURCE_COMMIT, SOURCE_COMMIT),
    (OLD_SOURCE_QA_SHA256, SOURCE_QA_SHA256),
    (OLD_SOURCE_QA_PATH, SOURCE_QA_PATH),
    ("YOLO11n N1 R1-R1 —", "YOLO11n N1 R1-R2 —"),
    ("PENDING_R1_R1_LIVE_SMOKE", "PENDING_R1_R2_LIVE_SMOKE"),
)


def _rewrite(value: Any) -> Any:
    if isinstance(value, str):
        for old, new in REPLACEMENTS:
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [_rewrite(item) for item in value]
    if isinstance(value, dict):
        return {key: _rewrite(item) for key, item in value.items()}
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def notebook(mode: str, stop_after: int) -> dict[str, Any]:
    payload = _rewrite(BASE.notebook(mode, stop_after))
    text = json.dumps(payload, sort_keys=True)
    required = (SOURCE_COMMIT, SOURCE_QA_SHA256, SOURCE_QA_PATH, STATE, RUNNER)
    if any(value not in text for value in required):
        raise RuntimeError("R1-R2 notebook is missing an immutable QA binding")
    forbidden = (OLD_SOURCE_COMMIT, OLD_SOURCE_QA_SHA256, OLD_SOURCE_QA_PATH)
    if any(value in text for value in forbidden):
        raise RuntimeError("R1-R2 notebook retained an obsolete QA binding")
    return payload


def build() -> dict[str, Any]:
    outputs = {
        "yolo11n_n1_r1_r2_fresh.ipynb": notebook("fresh", 1),
        "yolo11n_n1_r1_r2_resume.ipynb": notebook("resume", 2),
    }
    result: dict[str, Any] = {
        "schema": 1,
        "package": "YOLO11N-N1-R1-R2-NOTEBOOKS",
        "source_commit": SOURCE_COMMIT,
        "source_qa_sha256": SOURCE_QA_SHA256,
        "state": STATE,
        "sealed_test_accessed": False,
        "notebooks": {},
    }
    for name, payload in outputs.items():
        path = OUTPUT_DIR / name
        path.write_text(
            json.dumps(payload, indent=1, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        result["notebooks"][name] = {"sha256": _sha256(path), "cells": len(payload["cells"])}
    return result


if __name__ == "__main__":
    print(json.dumps(build(), indent=2, sort_keys=True))
