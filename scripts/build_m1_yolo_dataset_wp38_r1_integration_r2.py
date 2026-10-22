#!/usr/bin/env python3
"""Directory-fd-anchored successor for M1/WP38-R1 integration materialisation.

R1 remains preserved as QA-failed evidence. R2 never writes through a pathname after opening the
new output directory: all descendants are created relative to no-follow directory descriptors.
"""

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
PREDECESSOR = Path("scripts/build_m1_yolo_dataset_wp38_r1_integration_r1.py")
PREDECESSOR_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r1_manifest.json"
)
PREDECESSOR_QA = Path(
    "docs/review/m1_wp38_r1_integration_r1_independent_qa_record.md"
)
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r2_manifest.json"
)
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_WP38_ROOT = REPO_ROOT / "data/processed/wp38_r1_orientation_corrected"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r2"
PACKAGE = "M1-YOLO-WP38-R1-INTEGRATION-R2"
STATUS = "AWAITING_INDEPENDENT_QA"
COMPLETE_MARKER = "EXPORT_COMPLETE.json"
PINNED_SOURCES = {
    str(PREDECESSOR): "29839def04afa2ba8915195a8362f3e65fcde1fc22700bac242dc804e7461fa1",
    str(PREDECESSOR_MANIFEST): "6fbc33e8cd168a203d798e8abfee077f8f34450e8e9b66c03f9812d675e75675",
    str(PREDECESSOR_QA): "245ceb491886a79c121595f65b751f85fbc3a18f4d26461f0afeedc14cfc0b8d",
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
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_integration_r1_predecessor")


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _directory_flags() -> int:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    return flags


def _same_inode(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned R1 evidence differs: {relative}")


def derive(repo_root: Path, wp38_root: Path = DEFAULT_WP38_ROOT) -> dict[str, Any]:
    verify_pins(repo_root)
    return load_predecessor(repo_root).derive(repo_root, wp38_root)


def render(repo_root: Path) -> bytes:
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    if predecessor.verify(repo_root).get("valid") is not True:
        raise RuntimeError("QA-failed R1 predecessor no longer reproduces mechanically")
    payload = json.loads(predecessor.render(repo_root))
    payload.update(
        package=PACKAGE,
        status=STATUS,
        predecessor_package=predecessor.PACKAGE,
        predecessor_qa_status="INDEPENDENT_QA_FAIL",
        predecessor_exporter_sha256=PINNED_SOURCES[str(PREDECESSOR)],
        predecessor_manifest_sha256=PINNED_SOURCES[str(PREDECESSOR_MANIFEST)],
        predecessor_qa_record_sha256=PINNED_SOURCES[str(PREDECESSOR_QA)],
        materialisation_policy=(
            "new output only; lexical parent lstat; root identity pin; all descendant writes "
            "relative to no-follow directory descriptors; complete marker written last"
        ),
        training_authorized=False,
        sealed_test_accessed=False,
        note="Append-only H-1-R1 TOCTOU remediation candidate; independent QA is required.",
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


def _open_new_root(predecessor: ModuleType, out: Path) -> tuple[int, int, Path, os.stat_result]:
    output, parent = predecessor.require_new_output(out)
    parent_before = parent.lstat()
    parent_fd = os.open(parent, _directory_flags())
    try:
        if not _same_inode(parent_before, os.fstat(parent_fd)):
            raise RuntimeError("output parent identity changed before open")
        os.mkdir(output.name, 0o700, dir_fd=parent_fd)
        created = os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
        if not stat.S_ISDIR(created.st_mode):
            raise RuntimeError("new output root is not a directory")
        root_fd = os.open(output.name, _directory_flags(), dir_fd=parent_fd)
        if not _same_inode(created, os.fstat(root_fd)):
            os.close(root_fd)
            raise RuntimeError("output root identity changed during open")
        return parent_fd, root_fd, output, created
    except Exception:
        os.close(parent_fd)
        raise


def _mkdir_open(parent_fd: int, name: str) -> int:
    os.mkdir(name, 0o755, dir_fd=parent_fd)
    created = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(created.st_mode):
        raise RuntimeError(f"created child is not a directory: {name}")
    child_fd = os.open(name, _directory_flags(), dir_fd=parent_fd)
    if not _same_inode(created, os.fstat(child_fd)):
        os.close(child_fd)
        raise RuntimeError(f"directory identity changed during open: {name}")
    return child_fd


def _safe_tree_fd(root_fd: int) -> dict[str, int]:
    images = _mkdir_open(root_fd, "images")
    labels = _mkdir_open(root_fd, "labels")
    try:
        return {
            "images": images,
            "labels": labels,
            "image_train": _mkdir_open(images, "train"),
            "image_val": _mkdir_open(images, "val"),
            "label_train": _mkdir_open(labels, "train"),
            "label_val": _mkdir_open(labels, "val"),
        }
    except Exception:
        os.close(images)
        os.close(labels)
        raise


def _write_exclusive_at(directory_fd: int, name: str, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(name, flags, 0o644, dir_fd=directory_fd)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError(f"unsafe output file: {name}")
        offset = 0
        while offset < len(payload):
            offset += os.write(fd, payload[offset:])
        os.fsync(fd)
    finally:
        os.close(fd)


def _symlink_exclusive_at(directory_fd: int, name: str, source: Path) -> None:
    try:
        os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise RuntimeError(f"refused existing output leaf: {name}")
    os.symlink(source, name, dir_fd=directory_fd)


def _require_root_identity(parent_fd: int, output: Path, root_fd: int) -> None:
    current = os.stat(output.name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(current.st_mode) or not _same_inode(current, os.fstat(root_fd)):
        raise RuntimeError("output root identity changed during materialisation")


def materialise(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    predecessor = load_predecessor(repo_root)
    output, _parent = predecessor.require_new_output(out)
    if verify(repo_root)["valid"] is not True:
        raise RuntimeError("R2 integration manifest does not verify")
    parent_fd, root_fd, output, _created = _open_new_root(predecessor, output)
    child_fds: dict[str, int] = {}
    try:
        child_fds = _safe_tree_fd(root_fd)
        r1 = predecessor.load_predecessor(repo_root)
        base = r1.load_base(repo_root)
        data = derive(repo_root, wp38_root)
        names = {row["yolo_id"]: row["name"] for row in data["classes"]}
        written = {"train": 0, "val": 0, "train_wp35": 0}
        for split in ("train", "val"):
            image_fd = child_fds[f"image_{split}"]
            label_fd = child_fds[f"label_{split}"]
            for stem, text in data["labels"][split].items():
                source, expected_hash, extension = r1.image_record(
                    repo_root,
                    raw_root,
                    split,
                    stem,
                    data["correction"]["records"],
                    data["inventory"],
                )
                if sha256_file(source) != expected_hash:
                    raise RuntimeError(f"image source differs: {split}/{stem}")
                _symlink_exclusive_at(image_fd, f"{stem}{extension}", source)
                _write_exclusive_at(label_fd, f"{stem}.txt", text.encode("utf-8"))
                written[split] += 1
            if split == "train":
                for augmented_id, hashes in sorted(data["wp35"].items()):
                    image = wp35_root / "images" / f"{augmented_id}.jpg"
                    label = wp35_root / "labels" / f"{augmented_id}.txt"
                    if (
                        sha256_file(image) != hashes["image_sha256"]
                        or sha256_file(label) != hashes["label_sha256"]
                    ):
                        raise RuntimeError(f"WP35 source differs: {augmented_id}")
                    _symlink_exclusive_at(image_fd, f"{augmented_id}.jpg", image)
                    text = base._wp35_label_text(label, data["ids"])
                    _write_exclusive_at(label_fd, f"{augmented_id}.txt", text.encode())
                    written["train_wp35"] += 1
        _write_exclusive_at(
            root_fd, "data.yaml", base.dataset_yaml(output, ("train", "val"), names)
        )
        _require_root_identity(parent_fd, output, root_fd)
        marker = {
            "package": PACKAGE,
            "status": "COMPLETE",
            "written": written,
            "test_included": False,
            "sealed_test_accessed": False,
        }
        _write_exclusive_at(
            root_fd,
            COMPLETE_MARKER,
            (json.dumps(marker, indent=2, sort_keys=True) + "\n").encode(),
        )
        os.fsync(root_fd)
        _require_root_identity(parent_fd, output, root_fd)
    finally:
        for fd in child_fds.values():
            os.close(fd)
        os.close(root_fd)
        os.close(parent_fd)
    result = verify_materialised(repo_root, raw_root, wp35_root, wp38_root, output)
    if result["valid"] is not True:
        raise RuntimeError(f"materialised R2 integration differs: {result['errors']}")
    return {
        "package": PACKAGE,
        "status": "EXPORTED_TRAIN_VAL_ONLY",
        "out": str(output),
        "written": written,
        "verified": True,
        "sealed_test_accessed": False,
    }


def verify_materialised(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        predecessor = load_predecessor(repo_root)
        predecessor.require_safe_existing_directory(out)
        marker_path = out / COMPLETE_MARKER
        info = marker_path.lstat()
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or marker.get("package") != PACKAGE
            or marker.get("status") != "COMPLETE"
            or marker.get("test_included") is not False
            or marker.get("sealed_test_accessed") is not False
        ):
            errors.append("completion marker differs")
        r1 = predecessor.load_predecessor(repo_root)
        result = r1.verify_materialised(repo_root, raw_root, wp35_root, wp38_root, out)
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
