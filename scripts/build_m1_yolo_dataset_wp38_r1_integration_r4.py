#!/usr/bin/env python3
"""Descriptor-bound successor for M1/WP38-R1 integration R3.

R4 preserves every earlier package.  It binds verification to retained no-follow
directory and marker descriptors, replays the complete train/validation roster
through those descriptors, and requires materialisation to verify the exact root
inode created by the current invocation.
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
PREDECESSOR = Path("scripts/build_m1_yolo_dataset_wp38_r1_integration_r3.py")
PREDECESSOR_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r3_manifest.json"
)
PREDECESSOR_QA = Path(
    "docs/review/m1_wp38_r1_integration_r3_independent_qa_record.md"
)
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json"
)
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_WP38_ROOT = REPO_ROOT / "data/processed/wp38_r1_orientation_corrected"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo_wp38_r1_integration_r4"
PACKAGE = "M1-YOLO-WP38-R1-INTEGRATION-R4"
STATUS = "AWAITING_INDEPENDENT_QA"
COMPLETE_MARKER = "EXPORT_COMPLETE.json"
EXPECTED_WRITTEN = {"train": 1912, "train_wp35": 1800, "val": 376}
PINNED_SOURCES = {
    str(PREDECESSOR): "729277d443fffd4fa21d3a793f7f5b0b18744bf703cf9ecf9088a0c6bcfb5226",
    str(PREDECESSOR_MANIFEST): "734b082d49e607de97e61a8a7db7203993fe7645b552be8c99e5cc2aed31be9e",
    str(PREDECESSOR_QA): "2e5820573e8efcac03b176fdf79717ef74604c81700e98ac5d046b2b8825fc17",
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
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_integration_r3_predecessor")


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
            raise RuntimeError(f"pinned R3 evidence differs: {relative}")


def derive(repo_root: Path, wp38_root: Path = DEFAULT_WP38_ROOT) -> dict[str, Any]:
    verify_pins(repo_root)
    return load_predecessor(repo_root).derive(repo_root, wp38_root)


def render(repo_root: Path) -> bytes:
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    if predecessor.verify(repo_root).get("valid") is not True:
        raise RuntimeError("QA-failed R3 predecessor no longer reproduces mechanically")
    payload = json.loads(predecessor.render(repo_root))
    payload.update(
        package=PACKAGE,
        status=STATUS,
        predecessor_package=predecessor.PACKAGE,
        predecessor_qa_status="INDEPENDENT_QA_FAIL",
        predecessor_exporter_sha256=PINNED_SOURCES[str(PREDECESSOR)],
        predecessor_manifest_sha256=PINNED_SOURCES[str(PREDECESSOR_MANIFEST)],
        predecessor_qa_record_sha256=PINNED_SOURCES[str(PREDECESSOR_QA)],
        verification_policy=(
            "retain no-follow descriptors for every output path component and governed "
            "directory; read marker and regular payloads from bound descriptors; replay the "
            "exact train/validation roster descriptor-relatively; revalidate every directory "
            "binding before return; materialiser must verify its created root inode"
        ),
        completion_marker_schema=_expected_marker(),
        training_authorized=False,
        sealed_test_accessed=False,
        note="Append-only H-1-R3 identity/race remediation candidate; independent QA required.",
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


def _expected_marker() -> dict[str, Any]:
    return {
        "package": PACKAGE,
        "sealed_test_accessed": False,
        "status": "COMPLETE",
        "test_included": False,
        "written": dict(EXPECTED_WRITTEN),
    }


def _marker_bytes() -> bytes:
    return (json.dumps(_expected_marker(), indent=2, sort_keys=True) + "\n").encode()


def _open_directory_chain(
    path: Path,
) -> tuple[int, list[int], list[tuple[int, str, int]]]:
    candidate = _absolute_lexical(path)
    fds: list[int] = []
    relations: list[tuple[int, str, int]] = []
    try:
        parent_fd = os.open(candidate.anchor, _directory_flags())
        fds.append(parent_fd)
        for name in candidate.parts[1:]:
            before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            if not stat.S_ISDIR(before.st_mode):
                raise RuntimeError(f"unsafe output path component: {name}")
            child_fd = os.open(name, _directory_flags(), dir_fd=parent_fd)
            fds.append(child_fd)
            if not _same_inode(before, os.fstat(child_fd)):
                raise RuntimeError(f"output path component identity changed: {name}")
            relations.append((parent_fd, name, child_fd))
            parent_fd = child_fd
        return parent_fd, fds, relations
    except Exception:
        for fd in reversed(fds):
            os.close(fd)
        raise


def _open_child_directory(
    parent_fd: int,
    name: str,
    retained_fds: list[int],
    relations: list[tuple[int, str, int]],
) -> int:
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISDIR(before.st_mode):
        raise RuntimeError(f"expected directory differs: {name}")
    child_fd = os.open(name, _directory_flags(), dir_fd=parent_fd)
    retained_fds.append(child_fd)
    if not _same_inode(before, os.fstat(child_fd)):
        raise RuntimeError(f"directory identity changed during open: {name}")
    relations.append((parent_fd, name, child_fd))
    return child_fd


def _validate_relations(relations: list[tuple[int, str, int]]) -> None:
    for parent_fd, name, child_fd in relations:
        retained = os.fstat(child_fd)
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        if (
            not stat.S_ISDIR(retained.st_mode)
            or not stat.S_ISDIR(current.st_mode)
            or not _same_inode(current, retained)
        ):
            raise RuntimeError(f"directory binding changed during verification: {name}")


def _open_bound_regular(parent_fd: int, name: str) -> tuple[int, os.stat_result]:
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise RuntimeError(f"expected single-link regular file differs: {name}")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(name, flags, dir_fd=parent_fd)
    opened = os.fstat(fd)
    if not _same_inode(before, opened) or opened.st_nlink != 1:
        os.close(fd)
        raise RuntimeError(f"regular file identity changed during open: {name}")
    return fd, opened


def _read_all(fd: int) -> bytes:
    os.lseek(fd, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _validate_open_regular(
    parent_fd: int,
    name: str,
    fd: int,
    opened: os.stat_result,
) -> None:
    retained = os.fstat(fd)
    current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if (
        not stat.S_ISREG(retained.st_mode)
        or retained.st_nlink != 1
        or not _same_inode(opened, retained)
        or not _same_inode(current, retained)
    ):
        raise RuntimeError(f"regular file binding changed during verification: {name}")


def _read_bound_regular(parent_fd: int, name: str) -> bytes:
    fd, opened = _open_bound_regular(parent_fd, name)
    try:
        payload = _read_all(fd)
        _validate_open_regular(parent_fd, name, fd, opened)
        return payload
    finally:
        os.close(fd)


def _require_exact_entries(directory_fd: int, expected: set[str], label: str) -> None:
    actual = set(os.listdir(directory_fd))
    if actual != expected:
        missing = sorted(expected - actual)[:5]
        extra = sorted(actual - expected)[:5]
        raise RuntimeError(f"{label} roster differs; missing={missing}; extra={extra}")


def _require_bound_symlink(parent_fd: int, name: str, expected: Path) -> None:
    before = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not stat.S_ISLNK(before.st_mode):
        raise RuntimeError(f"expected image symlink differs: {name}")
    target = os.readlink(name, dir_fd=parent_fd)
    after = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    if not _same_inode(before, after) or target != os.fspath(expected):
        raise RuntimeError(f"image symlink binding differs: {name}")


def _expected_split(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    split: str,
) -> tuple[dict[str, tuple[Path, str]], dict[str, bytes], dict[str, Any]]:
    r3 = load_predecessor(repo_root)
    r2 = r3.load_predecessor(repo_root)
    r1 = r2.load_predecessor(repo_root)
    initial = r1.load_predecessor(repo_root)
    base = initial.load_base(repo_root)
    data = derive(repo_root, wp38_root)
    images: dict[str, tuple[Path, str]] = {}
    labels: dict[str, bytes] = {}
    for stem, text in data["labels"][split].items():
        source, expected_hash, extension = initial.image_record(
            repo_root,
            raw_root,
            split,
            stem,
            data["correction"]["records"],
            data["inventory"],
        )
        images[f"{stem}{extension}"] = (source, expected_hash)
        labels[f"{stem}.txt"] = text.encode("utf-8")
    if split == "train":
        for augmented_id, hashes in sorted(data["wp35"].items()):
            image = wp35_root / "images" / f"{augmented_id}.jpg"
            label = wp35_root / "labels" / f"{augmented_id}.txt"
            images[f"{augmented_id}.jpg"] = (image, hashes["image_sha256"])
            labels[f"{augmented_id}.txt"] = base._wp35_label_text(
                label, data["ids"]
            ).encode()
    return images, labels, {"base": base, "data": data}


def _verify_descriptor_tree(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
    root_fd: int,
    retained_fds: list[int],
    relations: list[tuple[int, str, int]],
) -> None:
    _require_exact_entries(
        root_fd,
        {"images", "labels", "data.yaml", COMPLETE_MARKER},
        "output root",
    )
    images_fd = _open_child_directory(root_fd, "images", retained_fds, relations)
    labels_fd = _open_child_directory(root_fd, "labels", retained_fds, relations)
    _require_exact_entries(images_fd, {"train", "val"}, "images")
    _require_exact_entries(labels_fd, {"train", "val"}, "labels")

    shared: dict[str, Any] | None = None
    for split in ("train", "val"):
        image_fd = _open_child_directory(images_fd, split, retained_fds, relations)
        label_fd = _open_child_directory(labels_fd, split, retained_fds, relations)
        expected_images, expected_labels, context = _expected_split(
            repo_root, raw_root, wp35_root, wp38_root, split
        )
        shared = context
        _require_exact_entries(image_fd, set(expected_images), f"images/{split}")
        _require_exact_entries(label_fd, set(expected_labels), f"labels/{split}")
        for name, (source, expected_hash) in expected_images.items():
            if sha256_file(source) != expected_hash:
                raise RuntimeError(f"image source differs: {split}/{name}")
            _require_bound_symlink(image_fd, name, source)
        for name, expected in expected_labels.items():
            if _read_bound_regular(label_fd, name) != expected:
                raise RuntimeError(f"label payload differs: {split}/{name}")

    if shared is None:
        raise RuntimeError("empty integration roster")
    names = {row["yolo_id"]: row["name"] for row in shared["data"]["classes"]}
    expected_yaml = shared["base"].dataset_yaml(out, ("train", "val"), names)
    if _read_bound_regular(root_fd, "data.yaml") != expected_yaml:
        raise RuntimeError("data.yaml differs")


def verify_materialised(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
    *,
    expected_root_identity: tuple[int, int] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    retained_fds: list[int] = []
    marker_fd: int | None = None
    try:
        root_fd, retained_fds, relations = _open_directory_chain(out)
        root_info = os.fstat(root_fd)
        if expected_root_identity is not None and (
            root_info.st_dev,
            root_info.st_ino,
        ) != expected_root_identity:
            raise RuntimeError("public output root is not the inode created by materialiser")

        marker_fd, marker_opened = _open_bound_regular(root_fd, COMPLETE_MARKER)
        if _read_all(marker_fd) != _marker_bytes():
            raise RuntimeError("completion marker differs")
        _validate_open_regular(
            root_fd, COMPLETE_MARKER, marker_fd, marker_opened
        )

        _verify_descriptor_tree(
            repo_root,
            raw_root,
            wp35_root,
            wp38_root,
            out,
            root_fd,
            retained_fds,
            relations,
        )
        _validate_open_regular(
            root_fd, COMPLETE_MARKER, marker_fd, marker_opened
        )
        _validate_relations(relations)
        if expected_root_identity is not None:
            final_root = os.fstat(root_fd)
            if (final_root.st_dev, final_root.st_ino) != expected_root_identity:
                raise RuntimeError("materialised root identity changed")
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    finally:
        if marker_fd is not None:
            os.close(marker_fd)
        for fd in reversed(retained_fds):
            os.close(fd)
    return {
        "package": PACKAGE,
        "status": "MATERIALISED_VERIFICATION",
        "valid": not errors,
        "errors": errors[:50],
        "sealed_test_accessed": False,
    }


def _safe_tree_fd(root_fd: int) -> dict[str, int]:
    r3 = load_predecessor(REPO_ROOT)
    r2 = r3.load_predecessor(REPO_ROOT)
    opened: list[int] = []
    try:
        images = r2._mkdir_open(root_fd, "images")
        opened.append(images)
        labels = r2._mkdir_open(root_fd, "labels")
        opened.append(labels)
        image_train = r2._mkdir_open(images, "train")
        opened.append(image_train)
        image_val = r2._mkdir_open(images, "val")
        opened.append(image_val)
        label_train = r2._mkdir_open(labels, "train")
        opened.append(label_train)
        label_val = r2._mkdir_open(labels, "val")
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


def materialise(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    r3 = load_predecessor(repo_root)
    r2 = r3.load_predecessor(repo_root)
    original_open_new_root = r2._open_new_root
    created_identity: dict[str, tuple[int, int]] = {}

    def capture_open_new_root(
        predecessor: ModuleType, output: Path
    ) -> tuple[int, int, Path, os.stat_result]:
        opened = original_open_new_root(predecessor, output)
        created = opened[3]
        created_identity["root"] = (created.st_dev, created.st_ino)
        return opened

    def verify_created(
        inner_repo_root: Path,
        inner_raw_root: Path,
        inner_wp35_root: Path,
        inner_wp38_root: Path,
        inner_out: Path,
    ) -> dict[str, Any]:
        identity = created_identity.get("root")
        if identity is None:
            raise RuntimeError("materialised root identity was not captured")
        return verify_materialised(
            inner_repo_root,
            inner_raw_root,
            inner_wp35_root,
            inner_wp38_root,
            inner_out,
            expected_root_identity=identity,
        )

    r2.PACKAGE = PACKAGE
    r2.verify = verify
    r2._open_new_root = capture_open_new_root
    r2._safe_tree_fd = _safe_tree_fd
    r2.verify_materialised = verify_created
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
