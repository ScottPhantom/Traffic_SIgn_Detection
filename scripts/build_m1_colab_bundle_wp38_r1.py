#!/usr/bin/env python3
"""Build the append-only Colab bundle for the WP38-R1 train/val integration.

The archive keeps the train roster unchanged, replaces exactly 39 raw validation JPEGs with the
QA-passed corrected PNGs, and includes their corrected labels.  No sealed-test image or label is
ever authorized by this builder.  Building requires a clean committed checkout; verification does
not require the large source files to exist outside the archive.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any, BinaryIO

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_BUNDLE = Path("scripts/build_m1_colab_bundle.py")
BASE_EXPORTER = Path("scripts/build_m1_yolo_dataset.py")
SUCCESSOR_EXPORTER = Path("scripts/build_m1_yolo_dataset_wp38_r1.py")
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_manifest.json"
)
WP38_MANIFEST = Path("docs/review/generated/wp38_r1_orientation_correction_manifest.json")
WP38_QA = Path("docs/review/wp38_r1_orientation_correction_independent_qa_record.md")
DETECTOR_LOCK = Path("detector/uv.lock")
INVENTORY = Path("results/data_audit/DATASET01_052bc980a7206f8d/image_inventory.csv")
WP35_LINEAGE = Path("docs/review/generated/wp35_enrichment_lineage.csv")
RAW_PREFIX = Path("data/raw/DATASET01/staging/052bc980a7206f8d/raw/archive/images")
WP35_PREFIX = Path("data/processed/wp35_enrichment")
MANIFEST_MEMBER = "m1_colab_wp38_r1_bundle_manifest.json"
PACKAGE = "M1-COLAB-WP38-R1-TRAIN-VAL-BUNDLE"
STATUS = "CANDIDATE_AWAITING_INDEPENDENT_QA"
SCHEMA_VERSION = 1

PINNED_SOURCES = {
    str(BASE_BUNDLE): "ac0c4a9a7d15522bb4254221f252fefb640395683b4ee7b7698b61f606d47536",
    str(BASE_EXPORTER): "3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93",
    str(SUCCESSOR_EXPORTER): "62bf884669f2e6670935267d4687472a5ca60e85741299a2b0d35626798933fb",
    str(INTEGRATION_MANIFEST): "87a47ae3ae3118b7109acf03bafb12429c447dd104811fea2642beb5555533e0",
    str(WP38_MANIFEST): "d88f5eae525a4aa6d77cdf3f581b60328a441aec0ff091cd907af20e8405385a",
    str(WP38_QA): "2dbc362408895f2d7a53c68748d12cadbb58604bee14f99a8d329b404a5a7a0a",
}


def _load(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_base_bundle(repo_root: Path) -> ModuleType:
    return _load(repo_root / BASE_BUNDLE, "m1_wp38_r1_base_bundle")


def load_base_exporter(repo_root: Path) -> ModuleType:
    return _load(repo_root / BASE_EXPORTER, "m1_wp38_r1_base_export")


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
        raise RuntimeError("bundle must be built from a Git checkout") from error


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


def _verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = repo_root / relative
        if not path.is_file() or path.is_symlink() or sha256_file(path) != expected:
            raise RuntimeError(f"pinned bundle source differs: {relative}")


def expected_records(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive the exact train/val roster without reading large image sources."""
    _verify_pins(repo_root)
    base_bundle = load_base_bundle(repo_root)
    exporter = load_base_exporter(repo_root)
    if exporter.verify(repo_root).get("valid") is not True:
        raise RuntimeError("base M1 exporter no longer verifies")
    data = exporter.derive(repo_root)
    train, val, test = (set(data["lists"][name]) for name in ("train", "val", "test"))
    if train & val or train & test or val & test:
        raise RuntimeError("WP36-R1 stem lists overlap")

    correction = json.loads((repo_root / WP38_MANIFEST).read_text(encoding="utf-8"))
    corrected = set(correction.get("stems", []))
    if corrected != {f"{number:04d}" for number in range(1319, 1358)}:
        raise RuntimeError("WP38-R1 stem roster differs")
    if not corrected <= val or corrected & (train | test):
        raise RuntimeError("WP38-R1 correction is not validation-only")
    if correction.get("sealed_test_accessed") is not False:
        raise RuntimeError("WP38-R1 sealed-test boundary differs")
    artifacts = {record["path"]: record for record in correction.get("artifacts", [])}

    inventory = {
        row["stem"]: row for row in base_bundle.read_csv(repo_root / INVENTORY)
    }
    records: list[dict[str, Any]] = []
    for stem in sorted(train):
        records.append(
            _record(
                RAW_PREFIX / f"{stem}.jpg",
                inventory[stem]["image_sha256"],
                "train",
                "raw_image",
            )
        )
    for stem in sorted(val - corrected):
        records.append(
            _record(
                RAW_PREFIX / f"{stem}.jpg",
                inventory[stem]["image_sha256"],
                "val",
                "raw_image",
            )
        )
    for stem in sorted(corrected):
        image = Path("data/processed/wp38_r1_orientation_corrected/images") / f"{stem}.png"
        label = Path("data/processed/wp38_r1_orientation_corrected/labels") / f"{stem}.txt"
        image_record = artifacts.get(str(image))
        label_record = artifacts.get(str(label))
        if image_record is None or label_record is None:
            raise RuntimeError(f"WP38-R1 artifact roster is missing stem: {stem}")
        records.extend(
            (
                _record(image, image_record["sha256"], "val", "wp38_r1_image"),
                _record(label, label_record["sha256"], "val", "wp38_r1_label"),
            )
        )

    lineage = base_bundle.read_csv(repo_root / WP35_LINEAGE)
    if len(lineage) != len(data["wp35"]):
        raise RuntimeError("WP35 roster differs from base export contract")
    for row in sorted(lineage, key=lambda item: item["augmented_id"]):
        augmented_id = row["augmented_id"]
        if data["wp35"].get(augmented_id) != {
            "image_sha256": row["image_sha256"],
            "label_sha256": row["label_sha256"],
        }:
            raise RuntimeError(f"WP35 lineage differs: {augmented_id}")
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
        raise RuntimeError("bundle roster contains duplicate paths")
    integration = json.loads((repo_root / INTEGRATION_MANIFEST).read_text(encoding="utf-8"))
    metadata = {
        "repo_git_commit": git_commit(repo_root),
        "integration_manifest_sha256": PINNED_SOURCES[str(INTEGRATION_MANIFEST)],
        "wp38_r1_manifest_sha256": PINNED_SOURCES[str(WP38_MANIFEST)],
        "wp38_r1_qa_record_sha256": PINNED_SOURCES[str(WP38_QA)],
        "successor_exporter_sha256": PINNED_SOURCES[str(SUCCESSOR_EXPORTER)],
        "detector_lock_sha256": sha256_file(repo_root / DETECTOR_LOCK),
        "class_map_sha256": integration["class_map_sha256"],
        "train_stem_list_sha256": integration["splits"]["train"]["stem_list_sha256"],
        "val_stem_list_sha256": integration["splits"]["val"]["stem_list_sha256"],
        "sealed_test_stem_list_sha256": integration["splits"]["test"]["stem_list_sha256"],
        "counts": {
            "raw_train_images": len(train),
            "raw_val_images": len(val - corrected),
            "wp38_r1_val_images": len(corrected),
            "wp38_r1_val_labels": len(corrected),
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
            raise RuntimeError(f"bundle source must be a regular file: {source}")
        if sha256_file(source) != record["sha256"]:
            raise RuntimeError(f"bundle source differs: {record['path']}")
        with_sizes.append({**record, "size": source.stat().st_size})
    return {
        "schema_version": SCHEMA_VERSION,
        "package": PACKAGE,
        "status": STATUS,
        "allowed_splits": ["train", "val"],
        "test_included": False,
        "sealed_test_accessed": False,
        "regular_files_only": True,
        **metadata,
        "file_count": len(with_sizes),
        "files": with_sizes,
    }


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
        raise RuntimeError("successor bundle manifest schema differs")
    if (
        type(manifest["schema_version"]) is not int
        or manifest["schema_version"] != SCHEMA_VERSION
        or manifest["package"] != PACKAGE
        or manifest["status"] != STATUS
        or manifest["allowed_splits"] != ["train", "val"]
        or manifest["test_included"] is not False
        or manifest["sealed_test_accessed"] is not False
        or manifest["regular_files_only"] is not True
    ):
        raise RuntimeError("successor bundle policy differs")
    if not isinstance(manifest["files"], list) or manifest["file_count"] != len(
        manifest["files"]
    ):
        raise RuntimeError("successor bundle file count differs")
    base = load_base_bundle(repo_root)
    paths = []
    for record in manifest["files"]:
        if not isinstance(record, dict) or set(record) != {
            "path",
            "sha256",
            "source_split",
            "kind",
            "size",
        }:
            raise RuntimeError("successor bundle file record schema differs")
        paths.append(base.safe_member_name(record["path"]))
        if (
            record["source_split"] not in {"train", "val"}
            or type(record["size"]) is not int
            or record["size"] < 0
            or not isinstance(record["sha256"], str)
            or len(record["sha256"]) != 64
        ):
            raise RuntimeError(f"invalid successor bundle record: {record['path']}")
    if len(paths) != len(set(paths)):
        raise RuntimeError("successor bundle has duplicate paths")


def read_archive_manifest(
    repo_root: Path, archive: Path
) -> tuple[dict[str, Any], dict[str, tarfile.TarInfo]]:
    if not archive.is_file() or archive.is_symlink():
        raise RuntimeError(f"bundle archive is missing or linked: {archive}")
    base = load_base_bundle(repo_root)
    with tarfile.open(archive, mode="r:gz") as bundle:
        members: dict[str, tarfile.TarInfo] = {}
        for member in bundle.getmembers():
            name = base.safe_member_name(member.name)
            if name in members or not member.isreg():
                raise RuntimeError(f"unsafe or duplicate bundle member: {name}")
            members[name] = member
        if MANIFEST_MEMBER not in members:
            raise RuntimeError("successor bundle has no embedded manifest")
        handle = bundle.extractfile(members[MANIFEST_MEMBER])
        if handle is None:
            raise RuntimeError("cannot read successor bundle manifest")
        manifest = base.strict_json_bytes(handle.read())
    _validate_manifest(repo_root, manifest)
    return manifest, members


def verify_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    manifest, members = read_archive_manifest(repo_root, archive)
    expected, metadata = expected_records(repo_root)
    expected_by_path = {record["path"]: record for record in expected}
    manifest_by_path = {record["path"]: record for record in manifest["files"]}
    if set(manifest_by_path) != set(expected_by_path):
        raise RuntimeError("successor bundle roster differs")
    if set(members) != set(expected_by_path) | {MANIFEST_MEMBER}:
        raise RuntimeError("successor bundle members differ")
    for key, value in metadata.items():
        if manifest.get(key) != value:
            raise RuntimeError(f"successor bundle binding differs: {key}")
    for path, expected_record in expected_by_path.items():
        actual = manifest_by_path[path]
        for key in ("sha256", "source_split", "kind"):
            if actual[key] != expected_record[key]:
                raise RuntimeError(f"successor bundle record differs: {path} {key}")
        if members[path].size != actual["size"]:
            raise RuntimeError(f"successor bundle size differs: {path}")
    with tarfile.open(archive, mode="r:gz") as bundle:
        for record in manifest["files"]:
            handle = bundle.extractfile(record["path"])
            if handle is None or sha256_stream(handle) != record["sha256"]:
                raise RuntimeError(f"successor bundle bytes differ: {record['path']}")
    return {
        "package": PACKAGE,
        "status": "VERIFIED",
        "archive": str(archive),
        "archive_sha256": sha256_file(archive),
        "file_count": manifest["file_count"],
        "counts": manifest["counts"],
        "test_included": False,
        "sealed_test_accessed": False,
    }


def build_archive(repo_root: Path, archive: Path) -> dict[str, Any]:
    require_clean_checkout(repo_root)
    sidecar = archive.with_name(f"{archive.name}.manifest.json")
    partial = archive.with_name(f".{archive.name}.partial")
    sidecar_partial = sidecar.with_name(f".{sidecar.name}.partial")
    output_paths = (archive, sidecar, partial, sidecar_partial)
    if any(path.exists() or path.is_symlink() for path in output_paths):
        raise RuntimeError("refused to overwrite successor bundle output")
    archive.parent.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(repo_root)
    payload = canonical_json(manifest)
    base = load_base_bundle(repo_root)
    try:
        with partial.open("xb") as raw:
            import gzip

            with gzip.GzipFile(filename="", mode="wb", compresslevel=1, mtime=0, fileobj=raw) as gz:
                with tarfile.open(fileobj=gz, mode="w", format=tarfile.GNU_FORMAT) as bundle:
                    bundle.addfile(
                        base._tar_info(MANIFEST_MEMBER, len(payload)), io.BytesIO(payload)
                    )
                    for record in manifest["files"]:
                        with (repo_root / record["path"]).open("rb") as handle:
                            bundle.addfile(
                                base._tar_info(record["path"], record["size"]), handle
                            )
        with sidecar_partial.open("xb") as handle:
            handle.write(payload)
        os.replace(partial, archive)
        os.replace(sidecar_partial, sidecar)
    finally:
        partial.unlink(missing_ok=True)
        sidecar_partial.unlink(missing_ok=True)
    verified = verify_archive(repo_root, archive)
    return {
        **verified,
        "status": STATUS,
        "manifest": str(sidecar),
        "manifest_sha256": hashlib.sha256(payload).hexdigest(),
    }


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    commands = root.add_subparsers(dest="command", required=True)
    for name in ("build", "verify"):
        command = commands.add_parser(name)
        command.add_argument("--repo-root", type=Path, default=REPO_ROOT)
        command.add_argument("--archive", type=Path, required=True)
    return root


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    repo_root = args.repo_root.expanduser().resolve()
    archive = args.archive.expanduser().resolve()
    try:
        result = (
            build_archive(repo_root, archive)
            if args.command == "build"
            else verify_archive(repo_root, archive)
        )
    except (OSError, RuntimeError, ValueError, tarfile.TarError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
