#!/usr/bin/env python3
"""Build, verify, and safely extract the private M1 Colab train/val bundle.

The archive contains only regular-file copies of the governed train/val source images and the
WP35 train-only image/label pairs. It never contains sealed-test files. Original train/val labels
are regenerated from the pinned WP33 tables after extraction, so raw vendor labels are unnecessary.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any, BinaryIO

REPO_ROOT = Path(__file__).resolve().parents[1]
EXPORT_BUILDER = Path("scripts/build_m1_yolo_dataset.py")
EXPORT_MANIFEST = Path("docs/review/generated/m1_yolo_export_manifest.json")
DETECTOR_LOCK = Path("detector/uv.lock")
INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
WP35_LINEAGE = Path("docs/review/generated/wp35_enrichment_lineage.csv")
RAW_IMAGE_PREFIX = Path(
    "data/raw/DATASET01/staging/052bc980a7206f8d/raw/archive/images"
)
WP35_PREFIX = Path("data/processed/wp35_enrichment")
MANIFEST_MEMBER = "m1_colab_bundle_manifest.json"
PACKAGE = "M1-COLAB-TRAIN-VAL-BUNDLE"
STATUS = "TRAIN_VAL_ONLY_READY"
SCHEMA_VERSION = 1


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_stream(handle: BinaryIO) -> str:
    digest = hashlib.sha256()
    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Any) -> bytes:
    return (
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode("utf-8")


def strict_json_bytes(payload: bytes) -> Any:
    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON constant is forbidden: {value}")

    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key is forbidden: {key}")
            result[key] = value
        return result

    return json.loads(
        payload.decode("utf-8"),
        parse_constant=reject_constant,
        object_pairs_hook=unique_object,
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_export_builder(repo_root: Path) -> ModuleType:
    path = repo_root / EXPORT_BUILDER
    spec = importlib.util.spec_from_file_location("m1_colab_export_contract", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load M1 export builder: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def git_commit(repo_root: Path) -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("bundle must be built and verified from a Git checkout") from error


def require_clean_checkout(repo_root: Path) -> None:
    try:
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError("cannot verify Git worktree state") from error
    if dirty:
        raise RuntimeError("refused: build the upload bundle only from a clean committed checkout")


def _record(path: Path, sha256: str, split: str, kind: str) -> dict[str, Any]:
    return {
        "path": path.as_posix(),
        "sha256": sha256,
        "source_split": split,
        "kind": kind,
    }


def expected_records(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive the exact authorized roster without requiring source data to be present."""
    export = load_export_builder(repo_root)
    verification = export.verify(repo_root)
    if verification["valid"] is not True:
        raise RuntimeError(f"M1 export manifest is invalid: {verification['errors']}")
    derived = export.derive(repo_root)
    train = set(derived["lists"]["train"])
    val = set(derived["lists"]["val"])
    test = set(derived["lists"]["test"])
    if train & val or train & test or val & test:
        raise RuntimeError("governed train/val/test stem lists are not disjoint")

    inventory = {row["stem"]: row for row in read_csv(repo_root / INVENTORY)}
    records: list[dict[str, Any]] = []
    for split, stems in (("train", train), ("val", val)):
        for stem in sorted(stems):
            row = inventory.get(stem)
            if row is None:
                raise RuntimeError(f"image inventory is missing governed {split} stem {stem}")
            records.append(
                _record(
                    RAW_IMAGE_PREFIX / f"{stem}.jpg",
                    row["image_sha256"],
                    split,
                    "raw_image",
                )
            )

    lineage = read_csv(repo_root / WP35_LINEAGE)
    if len(lineage) != len(derived["wp35"]):
        raise RuntimeError("WP35 lineage roster differs from the M1 export contract")
    for row in sorted(lineage, key=lambda item: item["augmented_id"]):
        augmented_id = row["augmented_id"]
        expected = derived["wp35"].get(augmented_id)
        if expected != {
            "image_sha256": row["image_sha256"],
            "label_sha256": row["label_sha256"],
        }:
            raise RuntimeError(f"WP35 lineage differs from export contract: {augmented_id}")
        records.extend(
            (
                _record(
                    WP35_PREFIX / "images" / f"{augmented_id}.jpg",
                    row["image_sha256"],
                    "train",
                    "wp35_image",
                ),
                _record(
                    WP35_PREFIX / "labels" / f"{augmented_id}.txt",
                    row["label_sha256"],
                    "train",
                    "wp35_label",
                ),
            )
        )

    paths = [record["path"] for record in records]
    if len(paths) != len(set(paths)):
        raise RuntimeError("authorized Colab bundle roster contains duplicate paths")
    manifest = strict_json_bytes((repo_root / EXPORT_MANIFEST).read_bytes())
    metadata = {
        "repo_git_commit": git_commit(repo_root),
        "export_manifest_sha256": sha256_file(repo_root / EXPORT_MANIFEST),
        "detector_lock_sha256": sha256_file(repo_root / DETECTOR_LOCK),
        "class_map_sha256": manifest["class_map_sha256"],
        "train_stem_list_sha256": manifest["splits"]["train"]["stem_list_sha256"],
        "val_stem_list_sha256": manifest["splits"]["val"]["stem_list_sha256"],
        "sealed_test_stem_list_sha256": manifest["splits"]["test"]["stem_list_sha256"],
        "counts": {
            "raw_train_images": len(train),
            "raw_val_images": len(val),
            "wp35_train_images": len(lineage),
            "wp35_train_labels": len(lineage),
        },
    }
    return sorted(records, key=lambda item: item["path"]), metadata


def build_manifest(repo_root: Path) -> dict[str, Any]:
    records, metadata = expected_records(repo_root)
    with_sizes = []
    for record in records:
        source = repo_root / record["path"]
        if not source.is_file() or source.is_symlink():
            raise RuntimeError(f"bundle source must be a regular non-symlink file: {source}")
        actual = sha256_file(source)
        if actual != record["sha256"]:
            raise RuntimeError(f"bundle source differs from governed SHA-256: {record['path']}")
        with_sizes.append({**record, "size": source.stat().st_size})
    return {
        "schema_version": SCHEMA_VERSION,
        "package": PACKAGE,
        "status": STATUS,
        "allowed_splits": ["train", "val"],
        "test_included": False,
        "regular_files_only": True,
        **metadata,
        "file_count": len(with_sizes),
        "files": with_sizes,
    }


def safe_member_name(name: str) -> str:
    path = PurePosixPath(name)
    if (
        not name
        or name != path.as_posix()
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
        or "\\" in name
    ):
        raise RuntimeError(f"unsafe archive member path: {name!r}")
    return name


def _tar_info(name: str, size: int) -> tarfile.TarInfo:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mode = 0o644
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def build_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    require_clean_checkout(repo_root)
    sidecar = archive.with_name(f"{archive.name}.manifest.json")
    partial = archive.with_name(f".{archive.name}.partial")
    sidecar_partial = sidecar.with_name(f".{sidecar.name}.partial")
    existing = [path for path in (archive, sidecar, partial, sidecar_partial) if path.exists()]
    if existing:
        raise RuntimeError(f"refused to overwrite existing bundle output path(s): {existing}")
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(repo_root)
    manifest_payload = canonical_json(manifest)
    created_partial = False
    try:
        with partial.open("xb") as raw:
            created_partial = True
            with gzip.GzipFile(filename="", mode="wb", compresslevel=1, mtime=0, fileobj=raw) as gz:
                with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as bundle:
                    bundle.addfile(
                        _tar_info(MANIFEST_MEMBER, len(manifest_payload)),
                        io.BytesIO(manifest_payload),
                    )
                    for record in manifest["files"]:
                        source = repo_root / record["path"]
                        with source.open("rb") as handle:
                            bundle.addfile(_tar_info(record["path"], record["size"]), handle)
        with sidecar_partial.open("xb") as handle:
            handle.write(manifest_payload)
        os.replace(partial, archive)
        created_partial = False
        os.replace(sidecar_partial, sidecar)
    finally:
        if created_partial:
            partial.unlink(missing_ok=True)
        sidecar_partial.unlink(missing_ok=True)
    verified = verify_archive(repo_root, archive)
    return {
        "status": STATUS,
        "archive": str(archive),
        "archive_size": archive.stat().st_size,
        "archive_sha256": sha256_file(archive),
        "manifest": str(sidecar),
        "manifest_sha256": hashlib.sha256(manifest_payload).hexdigest(),
        "files": verified["file_count"],
        "test_included": False,
    }


def _validate_manifest_shape(manifest: Any) -> None:
    required = {
        "schema_version",
        "package",
        "status",
        "allowed_splits",
        "test_included",
        "regular_files_only",
        "repo_git_commit",
        "export_manifest_sha256",
        "detector_lock_sha256",
        "class_map_sha256",
        "train_stem_list_sha256",
        "val_stem_list_sha256",
        "sealed_test_stem_list_sha256",
        "counts",
        "file_count",
        "files",
    }
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise RuntimeError("Colab bundle manifest schema differs")
    if (
        manifest["schema_version"] != SCHEMA_VERSION
        or manifest["package"] != PACKAGE
        or manifest["status"] != STATUS
        or manifest["allowed_splits"] != ["train", "val"]
        or manifest["test_included"] is not False
        or manifest["regular_files_only"] is not True
    ):
        raise RuntimeError("Colab bundle manifest status/split policy differs")
    if not isinstance(manifest["files"], list) or manifest["file_count"] != len(manifest["files"]):
        raise RuntimeError("Colab bundle manifest file count differs")
    paths: list[str] = []
    for record in manifest["files"]:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "source_split",
            "kind",
            "size",
        }:
            raise RuntimeError("Colab bundle file record schema differs")
        paths.append(safe_member_name(record["path"]))
        if (
            record["source_split"] not in {"train", "val"}
            or type(record["size"]) is not int
            or record["size"] < 0
            or not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
        ):
            raise RuntimeError(f"invalid Colab bundle file record: {record['path']}")
    if len(paths) != len(set(paths)):
        raise RuntimeError("Colab bundle manifest contains duplicate file paths")


def read_archive_manifest(archive: Path) -> tuple[dict[str, Any], dict[str, tarfile.TarInfo]]:
    if not archive.is_file() or archive.is_symlink():
        raise RuntimeError(f"bundle archive is missing or not a regular file: {archive}")
    with tarfile.open(archive, mode="r:gz") as bundle:
        members: dict[str, tarfile.TarInfo] = {}
        for member in bundle.getmembers():
            name = safe_member_name(member.name)
            if name in members:
                raise RuntimeError(f"duplicate archive member: {name}")
            if not member.isreg():
                raise RuntimeError(f"archive member is not a regular file: {name}")
            members[name] = member
        if MANIFEST_MEMBER not in members:
            raise RuntimeError("bundle archive has no embedded manifest")
        handle = bundle.extractfile(members[MANIFEST_MEMBER])
        if handle is None:
            raise RuntimeError("cannot read embedded bundle manifest")
        manifest = strict_json_bytes(handle.read())
    _validate_manifest_shape(manifest)
    return manifest, members


def verify_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    manifest, members = read_archive_manifest(archive)
    expected, metadata = expected_records(repo_root)
    expected_by_path = {record["path"]: record for record in expected}
    manifest_by_path = {record["path"]: record for record in manifest["files"]}
    if set(manifest_by_path) != set(expected_by_path):
        raise RuntimeError("bundle archive roster differs from the governed train/val-only roster")
    expected_members = set(expected_by_path) | {MANIFEST_MEMBER}
    if set(members) != expected_members:
        raise RuntimeError("bundle archive contains missing or extra members")
    for key, value in metadata.items():
        if manifest[key] != value:
            raise RuntimeError(f"bundle manifest binding differs: {key}")
    for path, expected_record in expected_by_path.items():
        actual_record = manifest_by_path[path]
        for key in ("sha256", "source_split", "kind"):
            if actual_record[key] != expected_record[key]:
                raise RuntimeError(f"bundle manifest record differs for {path}: {key}")
        member = members[path]
        if member.size != actual_record["size"]:
            raise RuntimeError(f"bundle member size differs from manifest: {path}")
    with tarfile.open(archive, mode="r:gz") as bundle:
        for record in manifest["files"]:
            handle = bundle.extractfile(record["path"])
            if handle is None or sha256_stream(handle) != record["sha256"]:
                raise RuntimeError(f"bundle member SHA-256 differs: {record['path']}")
    return {
        "status": "VERIFIED",
        "archive": str(archive),
        "archive_sha256": sha256_file(archive),
        "file_count": manifest["file_count"],
        "counts": manifest["counts"],
        "repo_git_commit": manifest["repo_git_commit"],
        "test_included": False,
        "train_stem_list_sha256": manifest["train_stem_list_sha256"],
        "val_stem_list_sha256": manifest["val_stem_list_sha256"],
    }


def _safe_destination(repo_root: Path, relative: str) -> Path:
    root = repo_root.resolve()
    destination = root / PurePosixPath(safe_member_name(relative))
    try:
        destination.resolve(strict=False).relative_to(root)
    except ValueError as error:
        raise RuntimeError(f"archive destination escapes repository: {relative}") from error
    current = destination.parent
    while current != root:
        if current.is_symlink():
            raise RuntimeError(f"archive destination parent is a symlink: {current}")
        current = current.parent
    return destination


def extract_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    verification = verify_archive(repo_root, archive)
    manifest, _members = read_archive_manifest(archive)
    written = 0
    reused = 0
    with tarfile.open(archive, mode="r:gz") as bundle:
        for record in manifest["files"]:
            destination = _safe_destination(repo_root, record["path"])
            if destination.is_symlink():
                raise RuntimeError(f"refused to replace destination symlink: {destination}")
            if destination.exists():
                if not destination.is_file() or sha256_file(destination) != record["sha256"]:
                    raise RuntimeError(f"refused to overwrite differing destination: {destination}")
                reused += 1
                continue
            destination.parent.mkdir(parents=True, exist_ok=True)
            handle = bundle.extractfile(record["path"])
            if handle is None:
                raise RuntimeError(f"cannot read archive member: {record['path']}")
            with destination.open("xb") as output:
                while chunk := handle.read(1024 * 1024):
                    output.write(chunk)
            if sha256_file(destination) != record["sha256"]:
                raise RuntimeError(f"extracted file SHA-256 differs: {destination}")
            written += 1
    return {**verification, "status": "EXTRACTED", "written": written, "reused": reused}


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify", "extract"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--archive", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    archive = args.archive.expanduser().resolve()
    try:
        if args.command == "build":
            result = build_archive(repo_root, archive)
        elif args.command == "verify":
            result = verify_archive(repo_root, archive)
        else:
            result = extract_archive(repo_root, archive)
    except (OSError, RuntimeError, ValueError, tarfile.TarError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
