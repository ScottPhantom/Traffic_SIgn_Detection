#!/usr/bin/env python3
"""Build the append-only M1 train/val view that consumes QA-passed WP38-R1.

This successor leaves the pinned M1 exporter, WP36-R1 split and raw DATASET01 bytes unchanged.
It substitutes exactly the 39 validation frames in D02-C0034 with the reviewed 960x540 PNG
derivatives and their rotated YOLO labels.  It deliberately has no sealed-test export command.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import sys
from collections import Counter
from pathlib import Path
from types import ModuleType
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
BASE_EXPORTER = Path("scripts/build_m1_yolo_dataset.py")
WP38_BUILDER = Path("scripts/build_wp38_r1_orientation_correction.py")
WP38_MANIFEST = Path("docs/review/generated/wp38_r1_orientation_correction_manifest.json")
WP38_LINEAGE = Path("docs/review/generated/wp38_r1_orientation_correction_lineage.csv")
WP38_QA = Path("docs/review/wp38_r1_orientation_correction_independent_qa_record.md")
INTEGRATION_MANIFEST = Path(
    "docs/review/generated/m1_yolo_wp38_r1_integration_manifest.json"
)
DEFAULT_RAW_ROOT = REPO_ROOT / "data/raw/DATASET01/staging/052bc980a7206f8d/raw"
DEFAULT_WP35_ROOT = REPO_ROOT / "data/processed/wp35_enrichment"
DEFAULT_WP38_ROOT = REPO_ROOT / "data/processed/wp38_r1_orientation_corrected"
DEFAULT_OUT = REPO_ROOT / "data/processed/m1_yolo_wp38_r1"
PACKAGE = "M1-YOLO-WP38-R1-INTEGRATION"
STATUS = "AWAITING_INDEPENDENT_QA"

PINNED_SOURCES = {
    str(BASE_EXPORTER): "3b52c63f2aeeea9e93f779ebe4102715def96a1f176e809cfd0dc12fbe9cef93",
    str(WP38_BUILDER): "f54ca45ba46269f2ebbf459a856de307cd77403aaefb5503ce58485b086da2e0",
    str(WP38_MANIFEST): "d88f5eae525a4aa6d77cdf3f581b60328a441aec0ff091cd907af20e8405385a",
    str(WP38_LINEAGE): "459fbb8990713b2d63b112ac4561f8509c2dfa07a295bf711fe1bad98ed7304d",
    str(WP38_QA): "2dbc362408895f2d7a53c68748d12cadbb58604bee14f99a8d329b404a5a7a0a",
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


def load_base(repo_root: Path) -> ModuleType:
    return _load(repo_root / BASE_EXPORTER, "m1_wp38_r1_base_exporter")


def load_wp38(repo_root: Path) -> ModuleType:
    return _load(repo_root / WP38_BUILDER, "m1_wp38_r1_correction")


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _require_regular(repo_root: Path, path: Path) -> Path:
    repo = _absolute_lexical(repo_root)
    candidate = _absolute_lexical(path)
    try:
        relative = candidate.relative_to(repo)
    except ValueError as error:
        raise RuntimeError(f"path escapes repository: {candidate}") from error
    current = repo
    for part in relative.parts:
        current /= part
        if not os.path.lexists(current):
            raise RuntimeError(f"required path is missing: {current}")
        mode = current.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"symlink is forbidden in governed source path: {current}")
    if not stat.S_ISREG(candidate.lstat().st_mode):
        raise RuntimeError(f"governed source is not a regular file: {candidate}")
    return candidate


def verify_pins(repo_root: Path) -> None:
    for relative, expected in PINNED_SOURCES.items():
        path = _require_regular(repo_root, repo_root / relative)
        if sha256_file(path) != expected:
            raise RuntimeError(f"pinned integration source changed: {relative}")


def correction_contract(repo_root: Path, wp38_root: Path) -> dict[str, Any]:
    verify_pins(repo_root)
    wp38 = load_wp38(repo_root)
    verification = wp38.verify(repo_root, repo_root / wp38.RAW_ROOT_RELATIVE)
    if verification.get("valid") is not True:
        raise RuntimeError(f"WP38-R1 package does not verify: {verification.get('errors')}")
    manifest = json.loads((repo_root / WP38_MANIFEST).read_text(encoding="utf-8"))
    required = {
        "package": "M0-WP38-R1",
        "group_id": "D02-C0034",
        "split": "val",
        "rotation": "CCW_90",
        "frame_count": 39,
        "box_count": 29,
        "derived_size": [960, 540],
        "raw_mutated": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
    }
    for key, expected in required.items():
        if manifest.get(key) != expected:
            raise RuntimeError(f"WP38-R1 contract differs: {key}")
    stems = manifest.get("stems")
    if stems != [f"{number:04d}" for number in range(1319, 1358)]:
        raise RuntimeError("WP38-R1 corrected stem roster differs")
    artifacts = {record["path"]: record for record in manifest.get("artifacts", [])}
    records: dict[str, dict[str, str]] = {}
    for stem in stems:
        image_relative = Path("data/processed/wp38_r1_orientation_corrected/images") / f"{stem}.png"
        label_relative = Path("data/processed/wp38_r1_orientation_corrected/labels") / f"{stem}.txt"
        image_record = artifacts.get(str(image_relative))
        label_record = artifacts.get(str(label_relative))
        if image_record is None or label_record is None:
            raise RuntimeError(f"WP38-R1 manifest is missing corrected pair: {stem}")
        image = _require_regular(repo_root, repo_root / image_relative)
        label = _require_regular(repo_root, repo_root / label_relative)
        if image.parent.parent != _absolute_lexical(wp38_root):
            raise RuntimeError(f"WP38-R1 root differs for stem: {stem}")
        if sha256_file(image) != image_record["sha256"]:
            raise RuntimeError(f"WP38-R1 image differs: {stem}")
        if sha256_file(label) != label_record["sha256"]:
            raise RuntimeError(f"WP38-R1 label differs: {stem}")
        records[stem] = {
            "image_path": str(image_relative),
            "image_sha256": image_record["sha256"],
            "label_path": str(label_relative),
            "label_sha256": label_record["sha256"],
        }
    return {"manifest": manifest, "records": records}


def derive(repo_root: Path, wp38_root: Path = DEFAULT_WP38_ROOT) -> dict[str, Any]:
    base = load_base(repo_root)
    base_verification = base.verify(repo_root)
    if base_verification.get("valid") is not True:
        raise RuntimeError(f"base M1 exporter does not verify: {base_verification.get('errors')}")
    data = base.derive(repo_root)
    correction = correction_contract(repo_root, wp38_root)
    corrected_stems = set(correction["records"])
    if not corrected_stems <= set(data["lists"]["val"]):
        raise RuntimeError("WP38-R1 stems are not an exact subset of WP36-R1 validation")
    if corrected_stems & (set(data["lists"]["train"]) | set(data["lists"]["test"])):
        raise RuntimeError("WP38-R1 stems overlap train or sealed test")
    for stem, record in correction["records"].items():
        data["labels"]["val"][stem] = (repo_root / record["label_path"]).read_text(
            encoding="utf-8"
        )
    data["correction"] = correction
    data["inventory"] = {
        row["stem"]: row for row in base.read_csv(repo_root / base.IMAGE_INVENTORY)
    }
    return data


def image_record(
    repo_root: Path,
    raw_root: Path,
    split: str,
    stem: str,
    correction_records: dict[str, dict[str, str]],
    inventory: dict[str, dict[str, str]],
) -> tuple[Path, str, str]:
    if split == "val" and stem in correction_records:
        record = correction_records[stem]
        return repo_root / record["image_path"], record["image_sha256"], ".png"
    source = raw_root / "archive/images" / f"{stem}.jpg"
    return source, inventory[stem]["image_sha256"], ".jpg"


def _split_summary(labels: dict[str, str], base: ModuleType) -> dict[str, Any]:
    box_counts = Counter(
        int(line.split()[0]) for text in labels.values() for line in text.splitlines()
    )
    return {
        "frames": len(labels),
        "empty_label_frames": sum(1 for text in labels.values() if not text),
        "boxes": sum(box_counts.values()),
        "classes_with_boxes": len(box_counts),
        "stem_list_sha256": base.list_sha256(list(labels)),
        "labels_sha256": sha256_bytes(
            "".join(f"{stem}\n{labels[stem]}" for stem in sorted(labels)).encode("utf-8")
        ),
    }


def render(repo_root: Path) -> bytes:
    base = load_base(repo_root)
    data = derive(repo_root)
    original = json.loads((repo_root / base.MANIFEST_PATH).read_text(encoding="utf-8"))
    correction_manifest = data["correction"]["manifest"]
    manifest = {
        "schema_version": 1,
        "package": PACKAGE,
        "status": STATUS,
        "base_export_manifest_sha256": sha256_file(repo_root / base.MANIFEST_PATH),
        "wp38_r1_manifest_sha256": PINNED_SOURCES[str(WP38_MANIFEST)],
        "wp38_r1_qa_record_sha256": PINNED_SOURCES[str(WP38_QA)],
        "splits": {
            split: _split_summary(data["labels"][split], base)
            for split in base.SPLITS
        },
        "orientation_correction": {
            "group_id": correction_manifest["group_id"],
            "split": "val",
            "rotation": correction_manifest["rotation"],
            "frames": correction_manifest["frame_count"],
            "boxes": correction_manifest["box_count"],
            "raw_mutated": False,
        },
        "wp35_train_only": original["wp35_train_only"],
        "class_map_sha256": original["class_map_sha256"],
        "test_policy": "stem/hash metadata only; this successor exposes no test export command",
        "test_included": False,
        "sealed_test_accessed": False,
        "training_authorized": False,
        "note": (
            "Candidate downstream integration; independent QA is required before evaluation "
            "or training."
        ),
        "pinned_sources": PINNED_SOURCES,
    }
    return (json.dumps(manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode(
        "utf-8"
    )


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


def _link(source: Path, destination: Path) -> None:
    if destination.exists() or destination.is_symlink():
        destination.unlink()
    os.symlink(source, destination)


def materialise(
    repo_root: Path,
    raw_root: Path,
    wp35_root: Path,
    wp38_root: Path,
    out: Path,
) -> dict[str, Any]:
    if verify(repo_root)["valid"] is not True:
        raise RuntimeError("WP38-R1 integration manifest does not verify")
    base = load_base(repo_root)
    data = derive(repo_root, wp38_root)
    names = {row["yolo_id"]: row["name"] for row in data["classes"]}
    written = Counter()
    for split in ("train", "val"):
        image_dir = out / "images" / split
        label_dir = out / "labels" / split
        image_dir.mkdir(parents=True, exist_ok=True)
        label_dir.mkdir(parents=True, exist_ok=True)
        for stem, text in data["labels"][split].items():
            source, expected_hash, extension = image_record(
                repo_root,
                raw_root,
                split,
                stem,
                data["correction"]["records"],
                data["inventory"],
            )
            if sha256_file(source) != expected_hash:
                raise RuntimeError(f"image source differs: {split}/{stem}")
            _link(source.resolve(), image_dir / f"{stem}{extension}")
            (label_dir / f"{stem}.txt").write_text(text, encoding="utf-8")
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
                _link(image.resolve(), image_dir / f"{augmented_id}.jpg")
                (label_dir / f"{augmented_id}.txt").write_text(
                    base._wp35_label_text(label, data["ids"]), encoding="utf-8"
                )
                written["train_wp35"] += 1
    (out / "data.yaml").write_bytes(base.dataset_yaml(out, ("train", "val"), names))
    result = verify_materialised(repo_root, raw_root, wp35_root, wp38_root, out)
    if result["valid"] is not True:
        raise RuntimeError(f"materialised WP38-R1 integration differs: {result['errors']}")
    return {
        "package": PACKAGE,
        "status": "EXPORTED_TRAIN_VAL_ONLY",
        "out": str(out),
        "written": dict(written),
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
        base = load_base(repo_root)
        data = derive(repo_root, wp38_root)
        names = {row["yolo_id"]: row["name"] for row in data["classes"]}
        if (out / "data.yaml").read_bytes() != base.dataset_yaml(out, ("train", "val"), names):
            errors.append("data.yaml differs")
        for split in ("train", "val"):
            expected_images: dict[str, tuple[Path, str]] = {}
            expected_labels = dict(data["labels"][split])
            for stem in data["lists"][split]:
                source, expected_hash, extension = image_record(
                    repo_root,
                    raw_root,
                    split,
                    stem,
                    data["correction"]["records"],
                    data["inventory"],
                )
                expected_images[f"{stem}{extension}"] = (source, expected_hash)
            if split == "train":
                for augmented_id, hashes in data["wp35"].items():
                    expected_images[f"{augmented_id}.jpg"] = (
                        wp35_root / "images" / f"{augmented_id}.jpg",
                        hashes["image_sha256"],
                    )
                    expected_labels[augmented_id] = base._wp35_label_text(
                        wp35_root / "labels" / f"{augmented_id}.txt", data["ids"]
                    )
            image_dir, label_dir = out / "images" / split, out / "labels" / split
            actual_images = (
                {path.name for path in image_dir.iterdir()} if image_dir.is_dir() else set()
            )
            actual_labels = (
                {path.name for path in label_dir.iterdir()} if label_dir.is_dir() else set()
            )
            if actual_images != set(expected_images):
                errors.append(f"{split} image roster differs")
            if actual_labels != {f"{stem}.txt" for stem in expected_labels}:
                errors.append(f"{split} label roster differs")
            for name, (source, expected_hash) in expected_images.items():
                path = image_dir / name
                if not path.is_file() or sha256_file(path) != expected_hash:
                    errors.append(f"image differs: {split}/{name}")
                elif path.is_symlink() and path.resolve() != source.resolve():
                    errors.append(f"image link target differs: {split}/{name}")
            for stem, text in expected_labels.items():
                path = label_dir / f"{stem}.txt"
                if (
                    not path.is_file()
                    or path.is_symlink()
                    or path.read_text(encoding="utf-8") != text
                ):
                    errors.append(f"label differs: {split}/{stem}.txt")
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
    repo_root = args.repo_root.expanduser().resolve()
    try:
        if args.command == "manifest":
            result = build(repo_root)
        elif args.command == "verify":
            result = verify(repo_root)
        elif args.command == "export":
            result = materialise(
                repo_root,
                args.raw_root.expanduser().resolve(),
                args.wp35_root.expanduser().resolve(),
                args.wp38_root.expanduser().resolve(),
                args.out.expanduser().resolve(),
            )
        else:
            result = verify_materialised(
                repo_root,
                args.raw_root.expanduser().resolve(),
                args.wp35_root.expanduser().resolve(),
                args.wp38_root.expanduser().resolve(),
                args.out.expanduser().resolve(),
            )
    except (KeyError, OSError, RuntimeError, ValueError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    return 0 if result.get("valid", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
