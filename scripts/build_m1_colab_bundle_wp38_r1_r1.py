#!/usr/bin/env python3
"""QA-bound Colab bundle successor for the R4 WP38-R1 integration.

The predecessor's deterministic archive implementation and exact 5,927-file roster are reused,
but the bundle contract is rebound to the R4 exporter, manifest and independent QA PASS record.
The archive remains train/validation-only and can be built only from a clean committed checkout.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDECESSOR = Path("scripts/build_m1_colab_bundle_wp38_r1.py")
INTEGRATION_EXPORTER = Path(
    "scripts/build_m1_yolo_dataset_wp38_r1_integration_r4.py"
)
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_r4_manifest.json"
)
INTEGRATION_QA = Path(
    "docs/review/m1_wp38_r1_integration_r4_independent_qa_record.md"
)
MANIFEST_MEMBER = "m1_colab_wp38_r1_r4_bundle_manifest.json"
PACKAGE = "M1-COLAB-WP38-R1-R4-TRAIN-VAL-BUNDLE"
STATUS = "CANDIDATE_AWAITING_INDEPENDENT_QA"
SCHEMA_VERSION = 2
PINNED_SOURCES = {
    str(PREDECESSOR): "8502aaa11397ec4d5f82c09d59716b59cd39451086e3c30eaee238f752d7e0d9",
    str(INTEGRATION_EXPORTER): "0ef217775c7dcab70fddda8d5a4f89a5ab260d63a2407b85544f387774844426",
    str(INTEGRATION_MANIFEST): "6982a76f06f7486dd5d14015b7858ea74088f6ab3fcad6d54c576772b3c7e602",
    str(INTEGRATION_QA): "27425608b177b2a29fb92a84e8ba32471cf43964766acaed6a5a3d6137f74591",
}


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
    return _load(repo_root / PREDECESSOR, "m1_wp38_r1_r4_bundle_predecessor")


def load_integration(repo_root: Path) -> ModuleType:
    return _load(repo_root / INTEGRATION_EXPORTER, "m1_wp38_r1_r4_bundle_integration")


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned R4 bundle authority differs: {relative}")


def expected_records(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Reuse the reviewed roster and bind it to the accepted R4 integration authority."""
    verify_pins(repo_root)
    predecessor = load_predecessor(repo_root)
    records, metadata = predecessor.expected_records(repo_root)
    integration = load_integration(repo_root)
    verified = integration.verify(repo_root)
    if verified.get("valid") is not True or verified.get("sealed_test_accessed") is not False:
        raise RuntimeError("R4 integration authority no longer verifies")
    manifest = json.loads((repo_root / INTEGRATION_MANIFEST).read_text(encoding="utf-8"))
    if (
        manifest.get("sealed_test_accessed") is not False
        or manifest.get("training_authorized") is not False
        or manifest.get("splits", {}).get("test", {}).get("stem_list_sha256")
        != metadata["sealed_test_stem_list_sha256"]
    ):
        raise RuntimeError("R4 integration governance binding differs")
    rebound = {
        **metadata,
        "integration_manifest_sha256": PINNED_SOURCES[str(INTEGRATION_MANIFEST)],
        "successor_exporter_sha256": PINNED_SOURCES[str(INTEGRATION_EXPORTER)],
        "integration_qa_record_sha256": PINNED_SOURCES[str(INTEGRATION_QA)],
        "bundle_predecessor_sha256": PINNED_SOURCES[str(PREDECESSOR)],
    }
    return records, rebound


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
        "integration_manifest_sha256",
        "wp38_r1_manifest_sha256",
        "wp38_r1_qa_record_sha256",
        "successor_exporter_sha256",
        "integration_qa_record_sha256",
        "bundle_predecessor_sha256",
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
        raise RuntimeError("R4 successor bundle manifest schema differs")
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != SCHEMA_VERSION
        or manifest["package"] != PACKAGE
        or manifest["status"] != STATUS
        or manifest["allowed_splits"] != ["train", "val"]
        or manifest["test_included"] is not False
        or manifest["sealed_test_accessed"] is not False
        or manifest["regular_files_only"] is not True
        or type(manifest["file_count"]) is not int
        or not isinstance(manifest["files"], list)
        or manifest["file_count"] != len(manifest["files"])
    ):
        raise RuntimeError("R4 successor bundle policy differs")
    predecessor = load_predecessor(repo_root)
    paths: list[str] = []
    for record in manifest["files"]:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "source_split",
            "kind",
            "size",
        }:
            raise RuntimeError("R4 successor bundle file-record schema differs")
        paths.append(predecessor.load_base_bundle(repo_root).safe_member_name(record["path"]))
        if (
            record["source_split"] not in {"train", "val"}
            or type(record["size"]) is not int
            or record["size"] < 0
            or not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
        ):
            raise RuntimeError(f"invalid R4 bundle record: {record['path']}")
    if len(paths) != len(set(paths)):
        raise RuntimeError("R4 successor bundle contains duplicate paths")


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
        if file_count != 5927:
            errors.append("R4 bundle contract file count differs")
        if metadata["counts"] != {
            "raw_train_images": 1912,
            "raw_val_images": 337,
            "wp38_r1_val_images": 39,
            "wp38_r1_val_labels": 39,
            "wp35_train_images": 1800,
            "wp35_train_labels": 1800,
        }:
            errors.append("R4 bundle contract counts differ")
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
