"""Build the train/val-only YOLO11n N1 bundle; never reads the sealed test."""

from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import sys
import tarfile
from pathlib import Path
from typing import Any


def _load_base() -> Any:
    path = Path(__file__).with_name("build_cascade_b0_bundle_r1.py")
    spec = importlib.util.spec_from_file_location("yolo11n_n1_pinned_b0_builder", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load pinned B0 builder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


base = _load_base()
ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "YOLO11N-N1-R1"
WEIGHT = ROOT / "models/pretrained/yolo11n.pt"
WEIGHT_SHA256 = "0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1"
OWNER_DECISION = ROOT / "docs/review/yolo11n_dual_track_r1_owner_decision_record.md"
RUNTIME = ROOT / "detector/colab/run_yolo11n_n1_r1.py"
CONTRACT = ROOT / "docs/review/yolo11n_dual_track_r1_run_contract.md"
SELF = Path(__file__).resolve()


def inputs() -> tuple[dict[str, Path | bytes], dict[str, Any]]:
    if WEIGHT.is_symlink() or not WEIGHT.is_file() or base.file_hash(WEIGHT) != WEIGHT_SHA256:
        raise RuntimeError("YOLO11n N1 official weight is missing, linked or differs")
    original_weight = base.WEIGHT
    original_pins = base.PINS
    base.WEIGHT = WEIGHT
    base.PINS = {path: value for path, value in base.PINS.items() if path != original_weight}
    base.PINS[WEIGHT] = WEIGHT_SHA256
    try:
        members, counts = base.inputs()
    finally:
        base.WEIGHT = original_weight
        base.PINS = original_pins
    legacy_name = "models/yolo11s.pt"
    if members.pop(legacy_name, None) != WEIGHT:
        raise RuntimeError("pinned B0 builder weight routing changed")
    members["models/yolo11n.pt"] = WEIGHT
    additions = {
        "detector/colab/build_yolo11n_n1_bundle_r1.py": SELF,
        "detector/colab/run_yolo11n_n1_r1.py": RUNTIME,
        "docs/review/yolo11n_dual_track_r1_owner_decision_record.md": OWNER_DECISION,
        "docs/review/yolo11n_dual_track_r1_run_contract.md": CONTRACT,
    }
    for name, path in additions.items():
        if path.is_symlink() or not path.is_file():
            raise RuntimeError(f"missing/linked YOLO11n N1 source: {name}")
        members[name] = path
    return members, counts


def build(destination: Path) -> dict[str, Any]:
    destination = base.safe_new_file(destination)
    members, counts = inputs()
    records = {
        name: {
            "sha256": base.file_hash(value) if isinstance(value, Path) else base.digest(value),
            "bytes": value.stat().st_size if isinstance(value, Path) else len(value),
        }
        for name, value in sorted(members.items())
    }
    manifest = {
        "schema": 1,
        "package": PACKAGE,
        "architecture": "YOLO11n",
        "detector_classes": 1,
        "pretrained_weight_sha256": WEIGHT_SHA256,
        "counts": counts,
        "members": records,
        "test_included": False,
        "sealed_test_accessed": False,
        "ignore_subtraction": False,
        "train_val_overlap": False,
    }
    members["manifest.json"] = base.json_bytes(manifest)
    partial = base.safe_new_file(destination.with_name(destination.name + ".partial"))
    try:
        with (
            partial.open("xb") as handle,
            tarfile.open(fileobj=handle, mode="w:gz", dereference=True) as archive,
        ):
            for name, value in sorted(members.items()):
                info = tarfile.TarInfo(name)
                info.mode = 0o600
                info.size = value.stat().st_size if isinstance(value, Path) else len(value)
                if isinstance(value, Path):
                    with value.open("rb") as source:
                        archive.addfile(info, source)
                else:
                    archive.addfile(info, io.BytesIO(value))
        for name, value in members.items():
            if isinstance(value, Path) and base.file_hash(value) != records[name]["sha256"]:
                raise RuntimeError(f"source changed while packaging: {name}")
        os.link(partial, destination)
        partial.unlink()
    except BaseException:
        if partial.is_file() and not partial.is_symlink():
            partial.unlink()
        raise
    return {
        "archive": str(destination),
        "sha256": base.file_hash(destination),
        "manifest_sha256": base.digest(base.json_bytes(manifest)),
        "package": PACKAGE,
        "counts": counts,
        "sealed_test_accessed": False,
        "test_included": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.out), indent=2))
