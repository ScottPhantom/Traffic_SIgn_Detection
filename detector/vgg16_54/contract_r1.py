"""Append-only runtime-evidence contract for the VGG16-54 R1 successor."""

from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path
from typing import Any

from .contract import EXPERIMENT, sha256_file

SUCCESSOR_PACKAGE = f"{EXPERIMENT}-RUNTIME-R1"
STATE_SUFFIX = "M1_D1_Colab/runs/vgg16_54_seed_20261018_r2"
SUCCESSOR_SOURCE_FILES = (
    "detector/vgg16_54/contract_r1.py",
    "detector/colab/run_vgg16_54_r1_r1.py",
    "detector/colab/run_d1_colab_checkpoint_r2.py",
)
RUNTIME_SCHEMA = "sha256:d1-runtime-v1:tag+linux-boot-id"
ATTEMPT_REQUIRED_KEYS = {
    "time",
    "stage",
    "event",
    "sealed_test_accessed",
    "mode",
    "completed_epoch",
    "runtime_identity",
    "gpu",
    "run_binding_sha256",
    "checkpoint_binding_sha256",
}
GPU_KEYS = {
    "device_name",
    "cuda_version",
    "device_count",
    "capability",
    "total_memory_bytes",
}


def _strict_json(path: Path, label: str) -> dict[str, Any]:
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

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    payload = json.loads(
        lexical.read_text(encoding="utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )
    if not isinstance(payload, dict):
        raise RuntimeError(f"{label} must be a JSON object")
    return payload


def normalize_state_path(path: Path) -> Path:
    state = path.expanduser().absolute()
    if not state.as_posix().endswith(f"/{STATE_SUFFIX}"):
        raise RuntimeError(f"VGG16 runtime-evidence state must end with {STATE_SUFFIX}")
    return state


def verify_successor_source_qa(
    path: Path, expected_sha256: str, repo_root: Path
) -> dict[str, Any]:
    if sha256_file(path) != expected_sha256:
        raise RuntimeError("runtime successor source QA proof hash differs")
    proof = _strict_json(path, "runtime successor source QA proof")
    required = {"verdict", "package", "reviewed_files", "sealed_test_accessed"}
    if set(proof) != required:
        raise RuntimeError("runtime successor source QA proof schema differs")
    if (
        proof["verdict"] != "PASS"
        or proof["package"] != SUCCESSOR_PACKAGE
        or proof["sealed_test_accessed"] is not False
        or not isinstance(proof["reviewed_files"], dict)
        or set(proof["reviewed_files"]) != set(SUCCESSOR_SOURCE_FILES)
    ):
        raise RuntimeError("runtime successor source QA proof does not authorize these bytes")
    for relative in SUCCESSOR_SOURCE_FILES:
        source = repo_root / relative
        if not source.is_file() or source.is_symlink() or source.stat().st_nlink != 1:
            raise RuntimeError(f"runtime successor source is unsafe: {relative}")
        if proof["reviewed_files"][relative] != sha256_file(source):
            raise RuntimeError(f"runtime successor source QA does not bind: {relative}")
    return proof


def validate_attempt(
    attempt: dict[str, Any], *, mode: str, completed_epoch: int, binding_sha256: str
) -> str:
    if not isinstance(attempt, dict) or set(attempt) != ATTEMPT_REQUIRED_KEYS:
        raise RuntimeError("runtime ATTEMPT schema differs")
    identity = attempt["runtime_identity"]
    gpu = attempt["gpu"]
    digest = identity.get("digest") if isinstance(identity, dict) else None
    if (
        attempt["stage"] != "vgg16_classifier"
        or attempt["event"] != "ATTEMPT"
        or attempt["mode"] != mode
        or attempt["completed_epoch"] != completed_epoch
        or attempt["sealed_test_accessed"] is not False
        or type(attempt["time"]) not in (int, float)
        or not math.isfinite(attempt["time"])
        or not isinstance(identity, dict)
        or set(identity) != {"schema", "digest"}
        or identity["schema"] != RUNTIME_SCHEMA
        or not isinstance(digest, str)
        or len(digest) != 64
        or any(character not in "0123456789abcdef" for character in digest)
        or not isinstance(gpu, dict)
        or set(gpu) != GPU_KEYS
        or gpu["device_name"] != "NVIDIA L4"
        or not isinstance(gpu["cuda_version"], str)
        or not gpu["cuda_version"]
        or type(gpu["device_count"]) is not int
        or gpu["device_count"] < 1
        or not isinstance(gpu["capability"], list)
        or len(gpu["capability"]) != 2
        or not all(type(value) is int and value >= 0 for value in gpu["capability"])
        or type(gpu["total_memory_bytes"]) is not int
        or gpu["total_memory_bytes"] <= 0
        or attempt["run_binding_sha256"] != binding_sha256
        or attempt["checkpoint_binding_sha256"] != binding_sha256
    ):
        raise RuntimeError("runtime ATTEMPT evidence differs")
    return digest


def verify_prior_smoke_state(
    state: Path, *, mode: str, stop_after: int | None, binding_sha256: str, current_digest: str
) -> list[str]:
    if mode == "fresh":
        if stop_after != 1:
            raise RuntimeError("VGG16 fresh mode is restricted to the epoch-1 smoke run")
        return []
    if mode != "resume":
        raise RuntimeError("VGG16 mode must be fresh or resume")
    execution = _strict_json(state / "colab_execution.json", "VGG16 execution state")
    expected_epoch = 1 if stop_after == 2 else 2
    if (
        execution.get("status") != "SMOKE_STOP"
        or execution.get("event") != "SMOKE_STOP"
        or execution.get("epoch") != expected_epoch
        or execution.get("sealed_test_accessed") is not False
    ):
        raise RuntimeError("VGG16 prior smoke terminal state differs")
    attempts = execution.get("execution_attempts")
    expected_count = 1 if stop_after == 2 else 2
    if not isinstance(attempts, list) or len(attempts) != expected_count:
        raise RuntimeError("VGG16 prior smoke attempt count differs")
    digests = [
        validate_attempt(
            attempt,
            mode="fresh" if index == 0 else "resume",
            completed_epoch=index,
            binding_sha256=binding_sha256,
        )
        for index, attempt in enumerate(attempts)
    ]
    if len(set(digests)) != len(digests):
        raise RuntimeError("VGG16 prior smoke runtimes are not distinct")
    if stop_after == 2 and current_digest == digests[0]:
        raise RuntimeError("VGG16 resume requires a genuinely new runtime")
    if stop_after is None and current_digest != digests[-1]:
        raise RuntimeError("VGG16 long run must continue on the QA-reviewed resume runtime")
    return digests
