#!/usr/bin/env python3
"""Strict-marker and descriptor-cleanup successor for M1/WP38-R1 integration R2."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = Path("scripts/build_m1_yolo_dataset_wp38_r1_integration_r2.py")
PREDECESSOR_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r2_manifest.json"
)
PREDECESSOR_QA = Path(
    "docs/review/m1_wp38_r1_integration_r2_independent_qa_record.md"
)
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r3_manifest.json"
)
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_WP38_ROOT = REPO_ROOT / "data/processed/wp38_r1_orientation_corrected"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r3"
PACKAGE = "M1-YOLO-WP38-R1-INTEGRATION-R3"
STATUS = "AWAITING_INDEPENDENT_QA"
COMPLETE_MARKER = "EXPORT_COMPLETE.json"
EXPECTED_WRITTEN = {"train": 1912, "train_wp35": 1800, "val": 376}
PINNED_SOURCES = {
    str(PREDECESSOR): "a26f1ee3a778086cef35fcd56df7df508dbdaee58d23ba34decba49de264ae4c",
    str(PREDECESSOR_MANIFEST): "7538697ba4fcdf59d86f62b7ce867ee0c609042a1d25922d2ff959607bc6f9de",
    str(PREDECESSOR_QA): "b37c7bf34e6160b496dd28cd56993e7a786689ac7733968513aac09c0464f7eb",
}


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_predecessor(repo_root: Path) -> ModuleType:
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_integration_r2_predecessor")


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned R2 evidence differs: {relative}")


def derive(repo_root: Path, wp38_root: Path = DEFAULT_WP38_ROOT) -> dict[str, Any]:
    verify_pins(repo_root)
    return load_predecessor(repo_root).derive(repo_root, wp38_root)


def render(repo_root: Path) -> bytes:
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    if predecessor.verify(repo_root).get("valid") is not True:
        raise RuntimeError("QA-failed R2 predecessor no longer reproduces mechanically")
    payload = json.loads(predecessor.render(repo_root))
    payload.update(
        package=PACKAGE,
        status=STATUS,
        predecessor_package=predecessor.PACKAGE,
        predecessor_qa_status="INDEPENDENT_QA_FAIL",
        predecessor_exporter_sha256=PINNED_SOURCES[str(PREDECESSOR)],
        predecessor_manifest_sha256=PINNED_SOURCES[str(PREDECESSOR_MANIFEST)],
        predecessor_qa_record_sha256=PINNED_SOURCES[str(PREDECESSOR_QA)],
        completion_marker_schema={
            "package": PACKAGE,
            "sealed_test_accessed": False,
            "status": "COMPLETE",
            "test_included": False,
            "written": EXPECTED_WRITTEN,
        },
        descriptor_cleanup="close every opened descendant descriptor on partial tree failure",
        training_authorized=False,
        sealed_test_accessed=False,
        note="Append-only R2 marker/descriptor remediation candidate; independent QA required.",
    )
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def build(repo_root: Path) -> dict[str, Any]:
    payload = render(repo_root)
    target = repo_root / INTEGRATION_MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(payload)
    return {
        "package": PACKAGE,
        "status": STATUS,
        "manifest": str(INTEGRATION_MANIFEST),
        "manifest_sha256": sha256_bytes(payload),
        "sealed_test_accessed": False,
    }


def verify(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    try:
        expected = render(repo_root)
        path = repo_root / INTEGRATION_MANIFEST
        if not path.is_file() or path.is_symlink() or path.read_bytes() != expected:
            errors.append(f"integration manifest differs: {INTEGRATION_MANIFEST}")
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    return {
        "package": PACKAGE,
        "status": STATUS,
        "valid": not errors,
        "errors": errors,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


def _safe_tree_fd(root_fd: int) -> dict[str, int]:
    predecessor = load_predecessor(REPO_ROOT)
    opened: list[int] = []
    try:
        images = predecessor._mkdir_open(root_fd, "images")
        opened.append(images)
        labels = predecessor._mkdir_open(root_fd, "labels")
        opened.append(labels)
        image_train = predecessor._mkdir_open(images, "train")
        opened.append(image_train)
        image_val = predecessor._mkdir_open(images, "val")
        opened.append(image_val)
        label_train = predecessor._mkdir_open(labels, "train")
        opened.append(label_train)
        label_val = predecessor._mkdir_open(labels, "val")
        opened.append(label_val)
        return {
            "images": images,
            "labels": labels,
            "image_train": image_train,
            "image_val": image_val,
            "label_train": label_train,
            "label_val": label_val,
        }
    except Exception:
        for fd in reversed(opened):
            os.close(fd)
        raise


def _validate_marker(marker: Any) -> None:
    if not isinstance(marker, dict) or set(marker) != {
        "package",
        "sealed_test_accessed",
        "status",
        "test_included",
        "written",
    }:
        raise RuntimeError("completion marker schema differs")
    if (
        marker["package"] != PACKAGE
        or marker["status"] != "COMPLETE"
        or marker["test_included"] is not False
        or marker["sealed_test_accessed"] is not False
        or not isinstance(marker["written"], dict)
        or set(marker["written"]) != set(EXPECTED_WRITTEN)
    ):
        raise RuntimeError("completion marker policy differs")
    for key, expected in EXPECTED_WRITTEN.items():
        value = marker["written"][key]
        if type(value) is not int or value != expected:
            raise RuntimeError(f"completion marker count differs: {key}")


def verify_materialised(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        r2 = load_predecessor(repo_root)
        r1 = r2.load_predecessor(repo_root)
        r1.require_safe_existing_directory(out)
        marker_path = out / COMPLETE_MARKER
        info = marker_path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError("completion marker is not a single-link regular file")
        _validate_marker(json.loads(marker_path.read_text(encoding="utf-8")))
        initial = r1.load_predecessor(repo_root)
        result = initial.verify_materialised(repo_root, raw_root, wp35_root, wp38_root, out)
        if result.get("valid") is not True:
            errors.extend(result.get("errors", ["semantic verification failed"]))
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    return {
        "package": PACKAGE,
        "status": "MATERIALISED_VERIFICATION",
        "valid": not errors,
        "errors": errors[:50],
        "sealed_test_accessed": False,
    }


def materialise(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    r2 = load_predecessor(repo_root)
    r2.PACKAGE = PACKAGE
    r2.verify = verify
    r2._safe_tree_fd = _safe_tree_fd
    r2.verify_materialised = verify_materialised
    return r2.materialise(repo_root, raw_root, wp35_root, wp38_root, out)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("manifest", "verify", "export", "verify-export"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        if name in {"export", "verify-export"}:
            command.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
            command.add_argument("--wp35-root", type=Path, default=DEFAULT_WP35_ROOT)
            command.add_argument("--wp38-root", type=Path, default=DEFAULT_WP38_ROOT)
            command.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = _absolute_lexical(args.repo_root.expanduser())
    try:
        if args.command == "manifest":
            result = build(repo_root)
        elif args.command == "verify":
            result = verify(repo_root)
        elif args.command == "export":
            result = materialise(
                repo_root,
                _absolute_lexical(args.raw_root.expanduser()),
                _absolute_lexical(args.wp35_root.expanduser()),
                _absolute_lexical(args.wp38_root.expanduser()),
                _absolute_lexical(args.out.expanduser()),
            )
        else:
            result = verify_materialised(
                repo_root,
                _absolute_lexical(args.raw_root.expanduser()),
                _absolute_lexical(args.wp35_root.expanduser()),
                _absolute_lexical(args.wp38_root.expanduser()),
                _absolute_lexical(args.out.expanduser()),
            )
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
