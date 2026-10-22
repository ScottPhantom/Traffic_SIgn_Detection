#!/usr/bin/env python3
"""Fail-closed successor for the M1/WP38-R1 train/val integration.

The predecessor remains preserved as QA-failed evidence.  This wrapper reuses only its
read-only derivation logic and replaces every writable operation with an atomic, lexical-path
checked materialiser.  It deliberately exposes no sealed-test export command.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import uuid
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = Path("scripts/build_m1_yolo_dataset_wp38_r1.py")
PREDECESSOR_QA = Path("docs/review/m1_wp38_r1_integration_independent_qa_record.md")
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r1_manifest.json"
)
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_WP38_ROOT = REPO_ROOT / "data/processed/wp38_r1_orientation_corrected"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r1"
PACKAGE = "M1-YOLO-WP38-R1-INTEGRATION-R1"
STATUS = "AWAITING_INDEPENDENT_QA"
PINNED_SOURCES = {
    str(PREDECESSOR): "62bf884669f2e6670935267d4687472a5ca60e85741299a2b0d35626798933fb",
    str(PREDECESSOR_QA): "3f676588350e089c72457b3159ddb434122642671258c7d0f46dbc605feae338",
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
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_integration_failed_predecessor")


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _lstat_kind(path: Path) -> str:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        return "symlink"
    if stat.S_ISDIR(mode):
        return "directory"
    if stat.S_ISREG(mode):
        return "regular file"
    return "special file"


def require_safe_existing_directory(path: Path) -> Path:
    """Walk an absolute path lexically and reject every linked/non-directory component."""
    candidate = _absolute_lexical(path)
    current = Path(candidate.anchor)
    for part in candidate.parts[1:]:
        current /= part
        if not os.path.lexists(current):
            raise RuntimeError(f"required directory is missing: {current}")
        kind = _lstat_kind(current)
        if kind != "directory":
            raise RuntimeError(f"unsafe writable path component ({kind}): {current}")
    return candidate


def require_new_output(path: Path) -> tuple[Path, Path]:
    output = _absolute_lexical(path)
    parent = require_safe_existing_directory(output.parent)
    if os.path.lexists(output):
        raise RuntimeError(f"refused: output path already exists: {output}")
    return output, parent


def _mkdir(parent: Path, name: str) -> Path:
    target = parent / name
    os.mkdir(target, 0o755)
    if _lstat_kind(target) != "directory":
        raise RuntimeError(f"created path is not a directory: {target}")
    return target


def _write_regular_exclusive(path: Path, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o644)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise RuntimeError(f"unsafe output file: {path}")
        with os.fdopen(fd, "wb", closefd=False) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    finally:
        os.close(fd)


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned predecessor evidence differs: {relative}")


def derive(repo_root: Path, wp38_root: Path = DEFAULT_WP38_ROOT) -> dict[str, Any]:
    verify_pins(repo_root)
    return load_predecessor(repo_root).derive(repo_root, wp38_root)


def render(repo_root: Path) -> bytes:
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    if predecessor.verify(repo_root).get("valid") is not True:
        raise RuntimeError("QA-failed predecessor no longer reproduces mechanically")
    payload = json.loads(predecessor.render(repo_root))
    payload.update(
        package=PACKAGE,
        status=STATUS,
        predecessor_package=predecessor.PACKAGE,
        predecessor_qa_status="INDEPENDENT_QA_FAIL",
        predecessor_exporter_sha256=PINNED_SOURCES[str(PREDECESSOR)],
        predecessor_qa_record_sha256=PINNED_SOURCES[str(PREDECESSOR_QA)],
        materialisation_policy=(
            "new output only; lexical lstat checks; exclusive regular writes; "
            "private staging tree; atomic promotion"
        ),
        training_authorized=False,
        sealed_test_accessed=False,
        note="Append-only H-1 remediation candidate; independent QA is required.",
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


def _safe_tree(out: Path) -> tuple[Path, Path, Path, Path, Path]:
    images = _mkdir(out, "images")
    labels = _mkdir(out, "labels")
    return (
        _mkdir(images, "train"),
        _mkdir(images, "val"),
        _mkdir(labels, "train"),
        _mkdir(labels, "val"),
        out,
    )


def _symlink_exclusive(source: Path, destination: Path) -> None:
    if os.path.lexists(destination):
        raise RuntimeError(f"refused existing output leaf: {destination}")
    os.symlink(source, destination)
    if not destination.is_symlink():
        raise RuntimeError(f"image output is not a symlink: {destination}")


def materialise(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    output, parent = require_new_output(out)
    if verify(repo_root)["valid"] is not True:
        raise RuntimeError("R1 integration manifest does not verify")
    staging = parent / f".{output.name}.tmp-{uuid.uuid4().hex}"
    if os.path.lexists(staging):
        raise RuntimeError(f"refused existing staging path: {staging}")
    os.mkdir(staging, 0o700)
    promoted = False
    try:
        image_train, image_val, label_train, label_val, _ = _safe_tree(staging)
        predecessor = load_predecessor(repo_root)
        base = predecessor.load_base(repo_root)
        data = derive(repo_root, wp38_root)
        names = {row["yolo_id"]: row["name"] for row in data["classes"]}
        written = {"train": 0, "val": 0, "train_wp35": 0}
        for split, image_dir, label_dir in (
            ("train", image_train, label_train),
            ("val", image_val, label_val),
        ):
            for stem, text in data["labels"][split].items():
                source, expected_hash, extension = predecessor.image_record(
                    repo_root,
                    raw_root,
                    split,
                    stem,
                    data["correction"]["records"],
                    data["inventory"],
                )
                if sha256_file(source) != expected_hash:
                    raise RuntimeError(f"image source differs: {split}/{stem}")
                _symlink_exclusive(source, image_dir / f"{stem}{extension}")
                _write_regular_exclusive(
                    label_dir / f"{stem}.txt", text.encode("utf-8")
                )
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
                    _symlink_exclusive(image, image_dir / f"{augmented_id}.jpg")
                    text = base._wp35_label_text(label, data["ids"])
                    _write_regular_exclusive(
                        label_dir / f"{augmented_id}.txt", text.encode("utf-8")
                    )
                    written["train_wp35"] += 1
        yaml_bytes = base.dataset_yaml(output, ("train", "val"), names)
        _write_regular_exclusive(staging / "data.yaml", yaml_bytes)
        os.replace(staging, output)
        promoted = True
        result = verify_materialised(repo_root, raw_root, wp35_root, wp38_root, output)
        if result["valid"] is not True:
            raise RuntimeError(f"materialised R1 integration differs: {result['errors']}")
        return {
            "package": PACKAGE,
            "status": "EXPORTED_TRAIN_VAL_ONLY",
            "out": str(output),
            "written": written,
            "verified": True,
            "sealed_test_accessed": False,
        }
    except Exception:
        if not promoted and os.path.lexists(staging):
            shutil.rmtree(staging)
        raise


def _validate_output_tree(out: Path) -> None:
    output = require_safe_existing_directory(out)
    expected_dirs = (
        output / "images",
        output / "images/train",
        output / "images/val",
        output / "labels",
        output / "labels/train",
        output / "labels/val",
    )
    for directory in expected_dirs:
        require_safe_existing_directory(directory)
    yaml = output / "data.yaml"
    info = yaml.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise RuntimeError("data.yaml is not a single-link regular file")


def verify_materialised(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        _validate_output_tree(out)
        predecessor = load_predecessor(repo_root)
        result = predecessor.verify_materialised(
            repo_root, raw_root, wp35_root, wp38_root, out
        )
        if result.get("valid") is not True:
            errors.extend(result.get("errors", ["predecessor semantic verification failed"]))
        for split in ("train", "val"):
            for path in (out / "labels" / split).iterdir():
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                    errors.append(f"unsafe label output: {split}/{path.name}")
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
