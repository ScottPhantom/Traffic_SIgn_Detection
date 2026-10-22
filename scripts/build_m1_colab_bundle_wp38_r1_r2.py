#!/usr/bin/env python3
"""Type-strict successor for the QA-failed WP38-R1 R4 Colab bundle R1."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = Path("scripts/build_m1_colab_bundle_wp38_r1_r1.py")
PREDECESSOR_QA = Path(
    "docs/review/m1_colab_wp38_r1_r4_bundle_r1_independent_qa_record.md"
)
MANIFEST_MEMBER = "m1_colab_wp38_r1_r4_bundle_r2_manifest.json"
PACKAGE = "M1-COLAB-WP38-R1-R4-TRAIN-VAL-BUNDLE-R2"
STATUS = "CANDIDATE_AWAITING_INDEPENDENT_QA"
SCHEMA_VERSION = 3
PINNED_SOURCES = {
    str(PREDECESSOR): "64cfa2d3f52db838f38e113d08c71c25418ce885e89b95322d9880263b7969d9",
    str(PREDECESSOR_QA): "35bd63cbd5906834ec1674312096286b3343bf18f056f3051a7e9e28875f3fb6",
}
SHA_FIELDS = {
    "integration_manifest_sha256",
    "wp38_r1_manifest_sha256",
    "wp38_r1_qa_record_sha256",
    "successor_exporter_sha256",
    "integration_qa_record_sha256",
    "bundle_predecessor_sha256",
    "bundle_predecessor_qa_record_sha256",
    "detector_lock_sha256",
    "class_map_sha256",
    "train_stem_list_sha256",
    "val_stem_list_sha256",
    "sealed_test_stem_list_sha256",
}
COUNT_VALUES = {
    "raw_train_images": 1912,
    "raw_val_images": 337,
    "wp38_r1_val_images": 39,
    "wp38_r1_val_labels": 39,
    "wp35_train_images": 1800,
    "wp35_train_labels": 1800,
}
KINDS = {
    "raw_image",
    "wp38_r1_image",
    "wp38_r1_label",
    "wp35_image",
    "wp35_label",
}
LOWER_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
LOWER_HEX_40 = re.compile(r"[0-9a-f]{40}\Z")


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
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_r4_bundle_r2_predecessor")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned bundle R1 evidence differs: {relative}")


def expected_records(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    records, metadata = predecessor.expected_records(repo_root)
    return records, {
        **metadata,
        "bundle_predecessor_sha256": PINNED_SOURCES[str(PREDECESSOR)],
        "bundle_predecessor_qa_record_sha256": PINNED_SOURCES[str(PREDECESSOR_QA)],
    }


def _require_hex(value: Any, pattern: re.Pattern[str], label: str) -> None:
    if type(value) is not str or pattern.fullmatch(value) is None:
        raise RuntimeError(f"{label} must be lowercase hexadecimal")


def _validate_manifest(repo_root: Path, manifest: Any) -> None:
    required = {
        "schema_version",
        "package",
        "status",
        "allowed_splits",
        "test_included",
        "sealed_test_accessed",
        "regular_files_only",
        "repo_git_commit",
        *SHA_FIELDS,
        "counts",
        "file_count",
        "files",
    }
    if type(manifest) is not dict or set(manifest) != required:
        raise RuntimeError("R4 bundle R2 manifest schema differs")
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != SCHEMA_VERSION
        or type(manifest["package"]) is not str
        or manifest["package"] != PACKAGE
        or type(manifest["status"]) is not str
        or manifest["status"] != STATUS
        or type(manifest["allowed_splits"]) is not list
        or manifest["allowed_splits"] != ["train", "val"]
        or type(manifest["test_included"]) is not bool
        or manifest["test_included"] is not False
        or type(manifest["sealed_test_accessed"]) is not bool
        or manifest["sealed_test_accessed"] is not False
        or type(manifest["regular_files_only"]) is not bool
        or manifest["regular_files_only"] is not True
    ):
        raise RuntimeError("R4 bundle R2 policy differs")
    _require_hex(manifest["repo_git_commit"], LOWER_HEX_40, "repo_git_commit")
    for field in SHA_FIELDS:
        _require_hex(manifest[field], LOWER_HEX_64, field)
    if type(manifest["counts"]) is not dict or set(manifest["counts"]) != set(COUNT_VALUES):
        raise RuntimeError("R4 bundle R2 counts schema differs")
    for key, expected in COUNT_VALUES.items():
        value = manifest["counts"][key]
        if type(value) is not int or value != expected:
            raise RuntimeError(f"R4 bundle R2 count differs: {key}")
    if (
        type(manifest["file_count"]) is not int
        or manifest["file_count"] != 5927
        or type(manifest["files"]) is not list
        or len(manifest["files"]) != manifest["file_count"]
    ):
        raise RuntimeError("R4 bundle R2 file count differs")
    predecessor = load_predecessor(repo_root)
    base = predecessor.load_predecessor(repo_root).load_base_bundle(repo_root)
    paths: list[str] = []
    for record in manifest["files"]:
        if type(record) is not dict or set(record) != {
            "path",
            "sha256",
            "source_split",
            "kind",
            "size",
        }:
            raise RuntimeError("R4 bundle R2 file-record schema differs")
        if type(record["path"]) is not str:
            raise RuntimeError("R4 bundle R2 record path must be a string")
        paths.append(base.safe_member_name(record["path"]))
        _require_hex(record["sha256"], LOWER_HEX_64, "file sha256")
        if (
            type(record["source_split"]) is not str
            or record["source_split"] not in {"train", "val"}
            or type(record["kind"]) is not str
            or record["kind"] not in KINDS
            or type(record["size"]) is not int
            or record["size"] < 0
        ):
            raise RuntimeError(f"invalid R4 bundle R2 record: {record['path']}")
    if len(paths) != len(set(paths)):
        raise RuntimeError("R4 bundle R2 contains duplicate paths")


def _configured_predecessor(repo_root: Path) -> ModuleType:
    predecessor = load_predecessor(repo_root)
    predecessor.PACKAGE = PACKAGE
    predecessor.STATUS = STATUS
    predecessor.SCHEMA_VERSION = SCHEMA_VERSION
    predecessor.MANIFEST_MEMBER = MANIFEST_MEMBER
    predecessor.expected_records = expected_records
    predecessor._validate_manifest = _validate_manifest
    return predecessor


def build_manifest(repo_root: Path) -> dict[str, Any]:
    return _configured_predecessor(repo_root).build_manifest(repo_root)


def read_archive_manifest(
    repo_root: Path, archive: Path
) -> tuple[dict[str, Any], dict[str, tarfile.TarInfo]]:
    return _configured_predecessor(repo_root).read_archive_manifest(repo_root, archive)


def verify_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    return _configured_predecessor(repo_root).verify_archive(repo_root, archive)


def build_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    return _configured_predecessor(repo_root).build_archive(repo_root, archive)


def verify_contract(repo_root: Path) -> dict[str, Any]:
    errors: list[str] = []
    file_count = 0
    try:
        records, metadata = expected_records(repo_root)
        file_count = len(records)
        if file_count != 5927 or metadata["counts"] != COUNT_VALUES:
            errors.append("R4 bundle R2 contract counts differ")
        for field in SHA_FIELDS:
            _require_hex(metadata[field], LOWER_HEX_64, field)
        _require_hex(metadata["repo_git_commit"], LOWER_HEX_40, "repo_git_commit")
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        errors.append(str(error))
    return {
        "package": PACKAGE,
        "status": STATUS,
        "valid": not errors,
        "errors": errors,
        "file_count": file_count,
        "test_included": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("contract", "build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        if name != "contract":
            command.add_argument("--archive", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    try:
        if args.command == "contract":
            result = verify_contract(repo_root)
        else:
            archive = args.archive.expanduser().resolve()
            result = (
                build_archive(repo_root, archive)
                if args.command == "build"
                else verify_archive(repo_root, archive)
            )
    except (OSError, RuntimeError, ValueError, tarfile.TarError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
