"""Frozen proposal and fail-closed approvals for VGG16-54 R1 preparation."""

from __future__ import annotations

import hashlib
import json
import math
import os
import stat
from pathlib import Path
from typing import Any

from .model import ARCHITECTURE, CLASSES, INPUT_SHAPE

EXPERIMENT = "VGG16-54-R1"
RUN_NAME = "D1_VGG16_54_R1"
STATE_SUFFIX = "M1_D1_Colab/runs/vgg16_54_seed_20261018_r1"
PROPOSED_CONFIG: dict[str, Any] = {
    "architecture": ARCHITECTURE,
    "classes": CLASSES,
    "input_shape": list(INPUT_SHAPE),
    "seed": 20261018,
    "epochs": 100,
    "early_stopping_min_epochs": 30,
    "early_stopping_patience": 15,
    "batch": 256,
    "learning_rate": 0.0001,
    "weight_decay": 0.0001,
    "workers": 2,
    "amp": True,
    "pretrained": False,
    "horizontal_flip": False,
    "selection_metric": "macro_f1_supported_classes_then_negative_val_loss",
    "sealed_test_accessed": False,
}
APPROVAL_KEYS = {
    "decision",
    "experiment",
    "config",
    "sealed_test_accessed",
}
SOURCE_FILES = (
    "detector/pyproject.toml",
    "detector/uv.lock",
    "detector/colab/extract_cascade_b0_r1.py",
    "detector/colab/run_cascade_b0_r1.py",
    "detector/vgg16_54/__init__.py",
    "detector/vgg16_54/model.py",
    "detector/vgg16_54/contract.py",
    "detector/colab/run_vgg16_54_r1.py",
    "detector/d1_cascade_classifier/__init__.py",
    "detector/d1_cascade_classifier/contract.py",
    "detector/d1_cascade_classifier/data.py",
    "detector/d1_cascade_classifier/metrics.py",
    "detector/d1_cascade_classifier/model.py",
    "detector/m1/__init__.py",
    "detector/m1/checkpoint_store.py",
    "detector/m1/checkpoint_store_r2.py",
    "docs/review/vgg16_54_r1_preparation_contract.md",
)


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _regular_file(path: Path, label: str) -> Path:
    lexical = Path(os.path.abspath(path))
    current = lexical
    while True:
        if current.exists() or current.is_symlink():
            info = current.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise RuntimeError(f"{label} path contains a symlink: {current}")
        if current == current.parent:
            break
        current = current.parent
    try:
        info = lexical.lstat()
    except FileNotFoundError as error:
        raise RuntimeError(f"{label} is missing: {lexical}") from error
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError(f"{label} must be a single-link regular file")
    return lexical


def verify_owner_approval(path: Path, expected_sha256: str) -> dict[str, Any]:
    """Require an exact future Owner approval before any GPU execution."""
    path = _regular_file(path, "Owner approval")
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("Owner approval hash differs")
    approval = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(approval, dict) or set(approval) != APPROVAL_KEYS:
        raise RuntimeError("Owner approval schema differs")
    if (
        approval["decision"] != "APPROVED_VGG16_54_R1"
        or approval["experiment"] != EXPERIMENT
        or approval["config"] != PROPOSED_CONFIG
        or approval["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("Owner approval does not authorize the frozen VGG16 configuration")
    return approval


def verify_source_qa(
    path: Path, expected_sha256: str, repo_root: Path
) -> dict[str, Any]:
    """Require machine-readable independent source QA before smoke or training."""
    path = _regular_file(path, "source QA proof")
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("source QA proof hash differs")
    proof = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "verdict",
        "package",
        "config_sha256",
        "reviewed_files",
        "sealed_test_accessed",
    }
    if not isinstance(proof, dict) or set(proof) != required:
        raise RuntimeError("source QA proof schema differs")
    if (
        proof["verdict"] != "PASS"
        or proof["package"] != EXPERIMENT
        or proof["config_sha256"] != canonical_sha256(PROPOSED_CONFIG)
        or proof["sealed_test_accessed"] is not False
        or not isinstance(proof["reviewed_files"], dict)
        or set(proof["reviewed_files"]) != set(SOURCE_FILES)
    ):
        raise RuntimeError("source QA proof does not approve VGG16-54 R1")
    repo_root = repo_root.expanduser().absolute()
    for relative in SOURCE_FILES:
        source = _regular_file(repo_root / relative, f"reviewed source {relative}")
        if proof["reviewed_files"][relative] != sha256_file(source):
            raise RuntimeError(f"source QA proof does not bind current bytes: {relative}")
    return proof


def verify_smoke_qa(
    path: Path, expected_sha256: str, bundle_manifest_sha256: str
) -> dict[str, Any]:
    """Require fresh epoch 1 and different-runtime resume epoch 2 evidence."""
    path = _regular_file(path, "smoke QA proof")
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("smoke QA proof hash differs")
    proof = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "verdict",
        "package",
        "config_sha256",
        "bundle_manifest_sha256",
        "fresh_completed_epoch",
        "resume_started_epoch",
        "resume_completed_epoch",
        "runtime_digests",
        "sealed_test_accessed",
    }
    if not isinstance(proof, dict) or set(proof) != required:
        raise RuntimeError("smoke QA proof schema differs")
    digests = proof["runtime_digests"]
    if (
        proof["verdict"] != "PASS"
        or proof["package"] != EXPERIMENT
        or proof["config_sha256"] != canonical_sha256(PROPOSED_CONFIG)
        or proof["bundle_manifest_sha256"] != bundle_manifest_sha256
        or proof["fresh_completed_epoch"] != 1
        or proof["resume_started_epoch"] != 2
        or proof["resume_completed_epoch"] != 2
        or not isinstance(digests, list)
        or len(digests) != 2
        or len(set(digests)) != 2
        or not all(
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
            for value in digests
        )
        or proof["sealed_test_accessed"] is not False
    ):
        raise RuntimeError("smoke QA proof does not authorize the long VGG16 run")
    return proof


def validate_config(config: dict[str, Any]) -> dict[str, Any]:
    if config != PROPOSED_CONFIG:
        raise RuntimeError("VGG16-54 R1 configuration differs from the frozen proposal")
    for key in ("learning_rate", "weight_decay"):
        if type(config[key]) not in (int, float) or not math.isfinite(config[key]):
            raise RuntimeError(f"VGG16 config {key} must be finite")
    if (
        type(config["epochs"]) is not int
        or type(config["early_stopping_min_epochs"]) is not int
        or type(config["early_stopping_patience"]) is not int
        or not 1 <= config["early_stopping_min_epochs"] <= config["epochs"]
        or not 1 <= config["early_stopping_patience"] < config["epochs"]
    ):
        raise RuntimeError("VGG16 early-stopping configuration is invalid")
    return config


def normalize_state_path(path: Path) -> Path:
    state = path.expanduser().absolute()
    if not state.as_posix().endswith(f"/{STATE_SUFFIX}"):
        raise RuntimeError(f"VGG16 state path must end with {STATE_SUFFIX}")
    return state
