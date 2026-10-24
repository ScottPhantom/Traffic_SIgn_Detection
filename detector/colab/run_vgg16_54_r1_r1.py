#!/usr/bin/env python3
"""Append-only VGG16-54 R1 runner with bound NVIDIA L4 runtime evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import torch

from colab import run_vgg16_54_r1 as base
from colab.run_d1_colab_checkpoint_r2 import BOOT_ID_PATH, derive_runtime_identity
from vgg16_54.contract import canonical_sha256
from vgg16_54.contract_r1 import (
    normalize_state_path,
    verify_prior_smoke_state,
    verify_successor_source_qa,
)

RUNTIME_TAG = "vgg16_54_r1_runtime_r1"


def runtime_evidence() -> tuple[dict[str, str], dict[str, Any]]:
    if not torch.cuda.is_available():
        raise RuntimeError("VGG16-54 R1 requires CUDA")
    device_name = torch.cuda.get_device_name(0).strip()
    if device_name != "NVIDIA L4":
        raise RuntimeError(f"VGG16-54 R1 requires NVIDIA L4, got {device_name!r}")
    cuda_version = torch.version.cuda
    if not isinstance(cuda_version, str) or not cuda_version:
        raise RuntimeError("CUDA runtime version is unavailable")
    properties = torch.cuda.get_device_properties(0)
    identity = derive_runtime_identity(RUNTIME_TAG, BOOT_ID_PATH.read_text(encoding="ascii"))
    gpu = {
        "device_name": device_name,
        "cuda_version": cuda_version,
        "device_count": torch.cuda.device_count(),
        "capability": list(torch.cuda.get_device_capability(0)),
        "total_memory_bytes": int(properties.total_memory),
    }
    return identity, gpu


def parser():
    result = base.parser()
    result.add_argument("--runtime-source-qa", type=Path, required=True)
    result.add_argument("--runtime-source-qa-sha256", required=True)
    return result


def make_governed_event(
    original_event, identity: dict[str, str], gpu: dict[str, Any], binding_sha256: str
):
    def governed_event(state_path: Path, stage: str, name: str, **values: Any) -> None:
        if name == "ATTEMPT":
            reserved = {
                "runtime_identity",
                "gpu",
                "run_binding_sha256",
                "checkpoint_binding_sha256",
            }
            if reserved.intersection(values):
                raise RuntimeError("runtime evidence fields may not be overridden")
            values.update(
                runtime_identity=identity,
                gpu=gpu,
                run_binding_sha256=binding_sha256,
                checkpoint_binding_sha256=binding_sha256,
            )
        original_event(state_path, stage, name, **values)

    return governed_event


def run(argv: list[str] | None = None) -> None:
    args = parser().parse_args(argv)
    repo_root = Path(__file__).resolve().parents[2]
    verify_successor_source_qa(
        args.runtime_source_qa, args.runtime_source_qa_sha256, repo_root
    )
    state = normalize_state_path(args.state)
    identity, gpu = runtime_evidence()
    binding_sha256 = canonical_sha256(base.binding(args.bundle_manifest_sha256))
    verify_prior_smoke_state(
        state,
        mode=args.mode,
        stop_after=args.stop_after,
        binding_sha256=binding_sha256,
        current_digest=identity["digest"],
    )

    original_event = base.event
    base.event = make_governed_event(original_event, identity, gpu, binding_sha256)
    base.normalize_state_path = normalize_state_path
    try:
        base.train(args)
    finally:
        base.event = original_event


def main(argv: list[str] | None = None) -> int:
    try:
        run(argv)
    except (OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
